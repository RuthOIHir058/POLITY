"""Load Transparency International CPI 2024 scores from the strict XLSX file."""

from __future__ import annotations

import sqlite3
import zipfile
import xml.etree.ElementTree as ET

from tools.etl._common import DATABASE_PATH, raw_path, upsert_rows

NAMESPACE = {"a": "http://purl.oclc.org/ooxml/spreadsheetml/main"}


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return [
        "".join(node.text or "" for node in item.findall(".//a:t", NAMESPACE))
        for item in root.findall(".//a:si", NAMESPACE)
    ]


def _cell_value(cell: ET.Element, shared: list[str]) -> str:
    value = cell.find("a:v", NAMESPACE)
    if value is None or value.text is None:
        return ""
    return shared[int(value.text)] if cell.attrib.get("t") == "s" else value.text


def main() -> int:
    source = raw_path("cpi/cpi_2024.xlsx")
    rows_to_load: list[tuple[str, int, float]] = []
    with zipfile.ZipFile(source) as archive:
        shared = _shared_strings(archive)
        root = ET.fromstring(archive.read("xl/worksheets/sheet5.xml"))
        sheet_data = root.find("a:sheetData", NAMESPACE)
        if sheet_data is None:
            raise ValueError("CPI workbook does not contain sheet data")
        for row in sheet_data.findall("a:row", NAMESPACE)[3:]:
            values = [_cell_value(cell, shared) for cell in row.findall("a:c", NAMESPACE)]
            if len(values) < 5 or not values[1] or not values[2] or not values[4]:
                continue
            rows_to_load.append((values[1], int(values[2]), float(values[4])))

    with sqlite3.connect(DATABASE_PATH) as connection:
        count = upsert_rows(
            connection, "governance_indicators", "corruption_index", rows_to_load
        )
    print(f"Loaded {count} CPI records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
