import os
from pathlib import Path

import pandas as pd
import requests

SCRIPT_DIR = Path(__file__).resolve().parent
STATE_AGENCIES_FILE = SCRIPT_DIR / "localAndStateAgencies-NC.xlsx"
API_ENDPOINT = "https://api.usa.gov/crime/fbi/sapi/api/data/nibrs/animal-cruelty/offender/agencies/{}/count"


def get_api_key():
    try:
        return os.environ["FBI_API_KEY"]
    except KeyError as exc:
        raise RuntimeError(
            "Set FBI_API_KEY in your environment before running api-test.py."
        ) from exc


def load_identifiers():
    df = pd.read_excel(STATE_AGENCIES_FILE)
    column_names = df.columns.tolist()
    print(column_names)

    identifiers = [
        str(identifier).strip()
        for identifier in df[column_names[3]].dropna().tolist()
        if str(identifier).strip()
    ]
    return identifiers


def main():
    api_key = get_api_key()
    identifiers = load_identifiers()

    for identifier in identifiers:
        response = requests.get(
            API_ENDPOINT.format(identifier),
            params={"API_KEY": api_key},
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        agency = data.get("agency", identifier)
        pages = data.get("pages", 0)
        print(f"{agency}: {pages}")


if __name__ == "__main__":
    main()
