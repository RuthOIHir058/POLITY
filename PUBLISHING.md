# Publishing POLITY to GitHub

The repository is prepared for GitHub account `RuthOlHir058`, but release preparation must not create or expose credentials. These commands assume authentication is already configured locally through GitHub CLI, an SSH agent, or a credential manager.

Do not paste a personal access token into a terminal command that will enter shell history, a document, an issue, or a chat.

## 1. Verify the prepared release

From the repository root:

```bash
git status --short
git log --oneline --decorate --graph --all
git show --stat v1.0.0
python scripts/security_scan.py --root . --history
coverage erase
coverage run --branch -m pytest
coverage report --fail-under=90
python -m tools.validation.check_database_sync
python -m tools.validation.check_determinism
```

The working tree should be clean after removing generated coverage and cache files. The security scan must report zero findings.

## 2. Check existing authentication without revealing it

With GitHub CLI:

```bash
gh auth status
```

For SSH:

```bash
ssh -T git@github.com
```

An authentication test may print the account name, but it should never print a private key or token.

## 3. Check whether the repository exists

```bash
gh repo view RuthOlHir058/POLITY
```

A not-found response means the repository may not exist or the authenticated account may not have access. Do not infer which without checking the account context.

## 4A. Create a new repository when it does not exist

Create the repository and connect the current source:

```bash
gh repo create RuthOlHir058/POLITY \
  --public \
  --description "Deterministic, explainable country policy simulation engine" \
  --source . \
  --remote origin
```

Run one final scan immediately before upload:

```bash
python scripts/security_scan.py --root . --history
```

Push the branch and annotated tag:

```bash
git push -u origin main
git push origin v1.0.0
```

Create the GitHub release from the prepared notes:

```bash
gh release create v1.0.0 \
  --title "POLITY Engine v1.0.0" \
  --notes-file RELEASE_NOTES_v1.0.0.md
```

Optional binary/source assets can then be attached explicitly after verifying their checksums.

## 4B. Connect to an existing empty repository

```bash
git remote add origin git@github.com:RuthOlHir058/POLITY.git
git ls-remote --heads origin
```

If no branch is returned, run the final scan and push:

```bash
python scripts/security_scan.py --root . --history
git push -u origin main
git push origin v1.0.0
gh release create v1.0.0 --title "POLITY Engine v1.0.0" --notes-file RELEASE_NOTES_v1.0.0.md
```

Use the HTTPS remote only when a secure credential manager is already configured:

```bash
git remote add origin https://github.com/RuthOlHir058/POLITY.git
```

## 4C. Handle an existing non-empty repository safely

Never force-push over an existing default branch without inspecting it.

```bash
git remote add origin git@github.com:RuthOlHir058/POLITY.git
git fetch origin --tags
git branch -r
git log --oneline --decorate --graph --all --max-count=50
```

If `origin/main` already contains work, preserve it. Push the prepared release to a new review branch rather than replacing `main`:

```bash
python scripts/security_scan.py --root . --history
git push origin main:publication/v1.0.0
```

Inspect the branch on GitHub and decide whether to merge, import, or reconcile histories. Do not push the `v1.0.0` tag until the release commit is present in the repository's accepted history.

When histories are compatible and the review branch is merged, update local `main` safely:

```bash
git fetch origin --tags
git switch main
git merge --ff-only origin/main
```

If histories are unrelated or conflict, stop and resolve them in a dedicated integration branch. Do not use `--force`, `--force-with-lease`, or `--allow-unrelated-histories` as an automatic publication shortcut.

## 5. Verify GitHub after publication

```bash
gh repo view RuthOlHir058/POLITY --web
gh run list --workflow ci.yml
gh release view v1.0.0
```

Confirm:

- the default branch is `main`;
- all logical commits are visible;
- the `v1.0.0` tag points to the release-preparation commit;
- CI runs on Python 3.11–3.13;
- `LICENSE_PENDING.md` is visible and GitHub does not display an unintended license;
- raw downloads, caches, backups, and credentials are absent;
- the release notes include the failed calibration disclosure;
- Security Advisories/private reporting are enabled if available.

## 6. Suggested repository settings

Use GitHub settings to:

- protect `main`;
- require the test workflow before merge;
- disallow force pushes and branch deletion on `main`;
- require pull-request review for scientific changes;
- enable secret scanning and push protection when available;
- enable Dependabot alerts for optional/development dependencies;
- enable private vulnerability reporting;
- preserve tag protection for `v*` releases.

## 7. Browser-only publication path

When GitHub CLI is unavailable:

1. Sign in to GitHub in a trusted browser.
2. Create `RuthOlHir058/POLITY` without adding a README, license, or `.gitignore` remotely.
3. Copy the repository's SSH URL from GitHub.
4. Run:

```bash
git remote add origin git@github.com:RuthOlHir058/POLITY.git
python scripts/security_scan.py --root . --history
git push -u origin main
git push origin v1.0.0
```

5. Create a release for tag `v1.0.0` and paste the contents of `RELEASE_NOTES_v1.0.0.md` through the GitHub release form.

No publication step requires revealing a password, private key, or token in this repository or conversation.
