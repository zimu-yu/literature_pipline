# discover/fallbacks/openalex.py

from urllib.parse import quote

from curl_cffi import requests


def discover_openalex(doi: str) -> dict:

    doi_url = f"https://doi.org/{doi}"

    url = (
        "https://api.openalex.org/works/"
        + quote(doi_url, safe="")
    )

    response = requests.get(
        url,
        impersonate="chrome",
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    candidates = []
    seen = set()

    locations = []

    best = data.get("best_oa_location")

    if best:
        locations.append(best)

    locations.extend(
        data.get("locations", [])
    )

    for location in locations:

        if not location:
            continue

        pdf_url = location.get("pdf_url")

        if (
            not pdf_url
            or pdf_url in seen
        ):
            continue

        seen.add(pdf_url)

        candidates.append({
            "url": pdf_url,
            "format": "pdf",
            "headers": None
        })

    return {
        "source": "OpenAlex",
        "candidates": candidates
    }


if __name__ == "__main__":

    doi = "10.1016/j.xcrp.2021.100620"

    print(
        discover_openalex(doi)
    )