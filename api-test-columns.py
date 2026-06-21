from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
STATE_AGENCIES_FILE = SCRIPT_DIR / "localAndStateAgencies-NC.xlsx"


def main():
    df = pd.read_excel(STATE_AGENCIES_FILE)
    column_names = df.columns.tolist()
    print(column_names)


if __name__ == "__main__":
    main()
