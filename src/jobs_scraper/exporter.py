import csv
import json
from pathlib import Path
from .models import BusinessRecord


def export_csv(records: list[BusinessRecord], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "company_name",
                "category_query",
                "city",
                "phone",
                "email",
                "website",
                "address",
                "google_place_id",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(record.model_dump())


def export_json(records: list[BusinessRecord], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        json.dump([record.model_dump() for record in records], f, indent=2)

