# run.py

import sys
from pathlib import Path

from acquire import acquire
from normalize import normalize_doi


def run_one(doi: str):

    try:
        result = acquire(doi)

        print(
            doi,
            "->",
            result["status"]
        )

    except Exception as e:

        print(
            doi,
            "-> failed:",
            str(e)
        )


def load_dois(path: str) -> list:

    lines = Path(path).read_text(
        encoding="utf-8"
    ).splitlines()

    return [
        line.strip()
        for line in lines
        if line.strip()
    ]


def run_many(dois: list):

    seen = set()
    for raw_doi in dois:
        try:
            doi = normalize_doi(raw_doi)
        except ValueError as exc:
            print(raw_doi, "-> failed:", str(exc))
            continue
        if doi in seen:
            continue
        seen.add(doi)
        run_one(doi)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(
            "Usage:\n"
            "  python run.py DOI\n"
            "  python run.py DOI1 DOI2 ...\n"
            "  python run.py --file dois.txt"
        )
        sys.exit(1)

    if sys.argv[1] == "--file":

        dois = load_dois(
            sys.argv[2]
        )

    else:

        dois = sys.argv[1:]

    run_many(dois)