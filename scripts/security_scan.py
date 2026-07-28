"""Fail closed on publish-time secrets, personal paths, and repository artifacts.

The scanner reports finding categories and locations, never candidate values. It
covers text, SQLite text cells/schema, OOXML/ZIP XML members, PNG text chunks,
and printable strings from otherwise unknown binary files.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import struct
import subprocess
import zipfile
from collections import Counter
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    ".idea",
    ".vscode",
    ".vs",
    ".ipynb_checkpoints",
    "htmlcov",
    "node_modules",
    "build",
    "dist",
    ".eggs",
    "venv",
    ".venv",
    "env",
}
FORBIDDEN_FILE_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini", ".coverage"}
FORBIDDEN_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".bak",
    ".old",
    ".tmp",
    ".swp",
    ".swo",
    ".orig",
    ".rej",
    ".log",
}

SENSITIVE_NAME_RE = re.compile(
    r"(?i)(^|/)(?:\.env(?:\..*)?|\.netrc|\.npmrc|\.pypirc|\.aws(?:/|$)|"
    r"\.ssh(?:/|$)|\.gnupg(?:/|$)|id_(?:rsa|dsa|ecdsa|ed25519)(?:\..*)?$|"
    r".*(?:credential|password|passwd|oauth|cookie|session|private[_-]?key|"
    r"client[_-]?secret|connection[_-]?string|wireguard|openvpn|\.ovpn$|"
    r"\.pem$|\.p12$|\.pfx$|\.kdbx$).*)"
)

# Strings are split where necessary so this source file does not look like a
# credential container to its own scanner.
PRIVATE_KEY_HEADER = re.compile(
    r"-----BEGIN (?:RSA |DSA |EC |OPENSSH |PGP )?" + r"PRIVATE KEY-----"
)
CERTIFICATE_HEADER = re.compile(r"-----BEGIN " + r"CERTIFICATE-----")

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key", PRIVATE_KEY_HEADER),
    ("certificate", CERTIFICATE_HEADER),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("github_token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b")),
    ("gitlab_token", re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b")),
    ("openai_key", re.compile(r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}\b")),
    ("anthropic_key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("huggingface_token", re.compile(r"\bhf_[A-Za-z0-9]{20,}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("google_oauth_secret", re.compile(r"\bGOCSPX-[A-Za-z0-9_-]{20,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("stripe_key", re.compile(r"\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),
    (
        "credentialed_url",
        re.compile(r"\b[a-zA-Z][a-zA-Z0-9+.-]*://[^\s/:]+:[^\s/@]+@"),
    ),
    (
        "azure_connection_string",
        re.compile(
            r"(?i)DefaultEndpointsProtocol=https?;AccountName=[^;\s]+;"
            r"AccountKey=[^;\s]+"
        ),
    ),
    (
        "generic_secret_assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret(?:[_-]?key)?|access[_-]?token|"
            r"auth[_-]?token|refresh[_-]?token|client[_-]?secret|password|"
            r"passwd|session[_-]?id|cookie|connection[_-]?string|database[_-]?url)"
            r"\b\s*[:=]\s*['\"]?(?!none\b|null\b|false\b|true\b|"
            r"changeme\b|placeholder\b|your[_-]|example\b|<)[^\s'\"#]{8,}"
        ),
    ),
)

PII_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "personal_email",
        re.compile(
            r"(?<![A-Za-z0-9._%+-])(?!git@github\.com\b)"
            r"[A-Za-z0-9._%+-]+@"
            r"(?!users\.noreply\.github\.com\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
        ),
    ),
    ("windows_user_path", re.compile(r"(?i)\b[A-Z]:\\Users\\(?!<|YOUR_)[^\\\s]+")),
    ("mac_user_path", re.compile(r"/" + r"Users/(?!<|YOUR_)[^/\s]+")),
    ("linux_home_path", re.compile(r"/" + r"home/(?!<|YOUR_)[^/\s]+")),
    ("root_home_path", re.compile(r"/" + r"root(?:/|\b)")),
    ("workspace_path", re.compile(r"/(?:mnt/data|tmp)/(?!<|YOUR_)[^\s`'\"]*")),
    (
        "private_ipv4",
        re.compile(
            r"(?<!\d)(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|"
            r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})(?!\d)"
        ),
    ),
    (
        "phone_number",
        re.compile(
            r"(?<!\d)\+\d{1,3}[ .-]?(?:\(\d{2,4}\)|\d{2,4})"
            r"[ .-]?\d{3,4}[ .-]?\d{3,4}(?!\d)"
        ),
    ),
)

TEXT_SUFFIXES = {
    ".py",
    ".pyi",
    ".md",
    ".rst",
    ".txt",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".jsonl",
    ".xml",
    ".ini",
    ".cfg",
    ".conf",
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
    ".bat",
    ".cmd",
    ".sql",
    ".csv",
    ".tsv",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".properties",
}
TEXT_NAMES = {
    "Dockerfile",
    "Makefile",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
}


def _looks_text(data: bytes) -> bool:
    if not data:
        return True
    sample = data[:8192]
    if b"\x00" in sample:
        return False
    printable = sum(
        byte in b"\t\n\r\f\b" or 32 <= byte <= 126 or byte >= 128
        for byte in sample
    )
    return printable / len(sample) >= 0.90


def _scan_text(text: str, location: str, findings: list[dict[str, object]]) -> None:
    for line_number, line in enumerate(text.splitlines() or [text], 1):
        for category, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                findings.append(
                    {
                        "severity": "critical",
                        "category": category,
                        "location": location,
                        "line": line_number,
                    }
                )
        for category, pattern in PII_PATTERNS:
            if pattern.search(line):
                findings.append(
                    {
                        "severity": "high",
                        "category": category,
                        "location": location,
                        "line": line_number,
                    }
                )


def _scan_sqlite(path: Path, rel: str, findings: list[dict[str, object]]) -> None:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        schema = "\n".join(
            row[0] or ""
            for row in connection.execute(
                "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL"
            )
        )
        _scan_text(schema, f"{rel}:sqlite-schema", findings)
        tables = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        ]
        for table in tables:
            safe_table = table.replace('"', '""')
            columns = list(connection.execute(f'PRAGMA table_info("{safe_table}")'))
            for column in columns:
                if str(column[2]).upper() not in {"TEXT", "VARCHAR", "CHAR", "CLOB", ""}:
                    continue
                name = str(column[1])
                safe_name = name.replace('"', '""')
                query = (
                    f'SELECT rowid, "{safe_name}" FROM "{safe_table}" '
                    f'WHERE "{safe_name}" IS NOT NULL'
                )
                for rowid, value in connection.execute(query):
                    if isinstance(value, str):
                        _scan_text(
                            value,
                            f"{rel}:sqlite:{table}.{name}:rowid={rowid}",
                            findings,
                        )
    finally:
        connection.close()


def _scan_zip(path: Path, rel: str, findings: list[dict[str, object]]) -> None:
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            member_name = member.filename
            if SENSITIVE_NAME_RE.search(member_name):
                findings.append(
                    {
                        "severity": "critical",
                        "category": "sensitive_archive_member",
                        "location": f"{rel}:{member_name}",
                        "line": 0,
                    }
                )
            if member_name.lower().endswith(
                (".xml", ".rels", ".txt", ".json", ".csv", ".vml")
            ):
                text = archive.read(member).decode("utf-8", errors="replace")
                _scan_text(text, f"{rel}:zip:{member_name}", findings)


def _scan_png(path: Path, rel: str, findings: list[dict[str, object]]) -> None:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return
    offset = 8
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        if chunk_type in {b"tEXt", b"zTXt", b"iTXt"}:
            _scan_text(
                payload.decode("utf-8", errors="replace"),
                f"{rel}:png:{chunk_type.decode('ascii')}",
                findings,
            )
        offset += length + 12


def _artifact_findings(root: Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if ".git" in path.parts:
            continue
        if path.is_symlink():
            findings.append(
                {
                    "severity": "high",
                    "category": "symlink",
                    "location": rel,
                    "line": 0,
                }
            )
            continue
        if path.is_dir():
            if path.name in FORBIDDEN_DIR_NAMES or path.name.endswith(".egg-info"):
                findings.append(
                    {
                        "severity": "medium",
                        "category": "generated_directory",
                        "location": rel,
                        "line": 0,
                    }
                )
            if SENSITIVE_NAME_RE.search(rel):
                findings.append(
                    {
                        "severity": "critical",
                        "category": "sensitive_path_name",
                        "location": rel,
                        "line": 0,
                    }
                )
            continue
        if not path.is_file():
            findings.append(
                {
                    "severity": "high",
                    "category": "special_file",
                    "location": rel,
                    "line": 0,
                }
            )
            continue

        if (
            path.name in FORBIDDEN_FILE_NAMES
            or path.suffix.lower() in FORBIDDEN_SUFFIXES
            or ".pre_" in path.name
            or path.name.endswith("~")
        ):
            findings.append(
                {
                    "severity": "medium",
                    "category": "generated_or_backup_file",
                    "location": rel,
                    "line": 0,
                }
            )
        if SENSITIVE_NAME_RE.search(rel):
            findings.append(
                {
                    "severity": "critical",
                    "category": "sensitive_path_name",
                    "location": rel,
                    "line": 0,
                }
            )

        data = path.read_bytes()
        if data.startswith(b"SQLite format 3\x00"):
            _scan_sqlite(path, rel, findings)
        elif zipfile.is_zipfile(path):
            _scan_zip(path, rel, findings)
        elif path.suffix.lower() == ".png":
            _scan_png(path, rel, findings)
        elif path.suffix.lower() in TEXT_SUFFIXES or path.name in TEXT_NAMES or _looks_text(data):
            _scan_text(data.decode("utf-8", errors="replace"), rel, findings)
        else:
            printable = re.findall(rb"[\x20-\x7e]{8,}", data)
            if printable:
                _scan_text(
                    "\n".join(item.decode("ascii", errors="replace") for item in printable),
                    f"{rel}:binary-strings",
                    findings,
                )
    return findings


def _scan_git_history(root: Path) -> list[dict[str, object]]:
    if not (root / ".git").is_dir():
        return []
    findings: list[dict[str, object]] = []
    commits = subprocess.run(
        ["git", "rev-list", "--all"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    for commit in commits:
        names = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", commit],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        for name in names:
            if SENSITIVE_NAME_RE.search(name):
                findings.append(
                    {
                        "severity": "critical",
                        "category": "sensitive_history_path",
                        "location": f"{commit[:12]}:{name}",
                        "line": 0,
                    }
                )
                continue
            blob = subprocess.run(
                ["git", "show", f"{commit}:{name}"],
                cwd=root,
                check=False,
                capture_output=True,
            )
            if blob.returncode != 0:
                continue
            data = blob.stdout
            if _looks_text(data):
                _scan_text(
                    data.decode("utf-8", errors="replace"),
                    f"history:{commit[:12]}:{name}",
                    findings,
                )
    return findings


def _deduplicate(findings: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[tuple[object, ...]] = set()
    result: list[dict[str, object]] = []
    for finding in findings:
        key = (
            finding["severity"],
            finding["category"],
            finding["location"],
            finding["line"],
        )
        if key not in seen:
            seen.add(key)
            result.append(finding)
    return sorted(
        result,
        key=lambda item: (
            str(item["severity"]),
            str(item["category"]),
            str(item["location"]),
            int(item["line"]),
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--history", action="store_true", help="Also scan every Git commit")
    parser.add_argument("--json-report", type=Path)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    findings = _artifact_findings(root)
    if args.history:
        findings.extend(_scan_git_history(root))
    findings = _deduplicate(findings)

    counts = Counter(str(item["category"]) for item in findings)
    try:
        display_root = root.relative_to(PROJECT_ROOT).as_posix() or "."
    except ValueError:
        display_root = root.name

    report = {
        "root": display_root,
        "files_scanned": sum(
            1
            for path in root.rglob("*")
            if path.is_file() and ".git" not in path.parts
        ),
        "history_scanned": bool(args.history and (root / ".git").is_dir()),
        "finding_count": len(findings),
        "categories": dict(sorted(counts.items())),
        "findings": findings,
    }
    if args.json_report is not None:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if findings:
        print(f"SECURITY SCAN FAILED: {len(findings)} finding(s)")
        for item in findings:
            print(
                f"- {item['severity']} {item['category']} at "
                f"{item['location']}:{item['line']}"
            )
        return 1

    print(
        f"SECURITY SCAN PASSED: {report['files_scanned']} files; "
        f"history_scanned={report['history_scanned']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
