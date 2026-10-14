import re

DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$", re.I)


def normalize_doi(raw_doi: str) -> str:
    doi = raw_doi.strip().lower()

    for prefix in (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
        "doi:",
    ):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]

    doi = doi.strip()

    if not DOI_PATTERN.match(doi):
        raise ValueError(f"Invalid DOI: {raw_doi}")

    return doi