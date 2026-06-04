import json
from pathlib import Path


def load_data_from_json(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)


def extract_company_post(title):
    company_json_path = Path(__file__).parent.parent / "company.json"
    data = load_data_from_json(company_json_path)
    company_aliases = data.get("company_aliases", {})

    reverse_mapping = {}
    for standard_name, aliases in company_aliases.items():
        reverse_mapping[standard_name.lower()] = standard_name
        for alias in aliases:
            reverse_mapping[alias.lower()] = standard_name

    title_lower = title.lower()
    company = "未知公司"

    sorted_aliases = sorted(reverse_mapping.keys(), key=len, reverse=True)
    for alias in sorted_aliases:
        if alias in title_lower:
            company = reverse_mapping[alias]
            break

    return company
