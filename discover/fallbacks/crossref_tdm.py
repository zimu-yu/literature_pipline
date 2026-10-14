# discover/fallbacks/crossref_tdm.py

from curl_cffi import requests


def discover_crossref_tdm(doi: str) -> dict:

    url = f"https://api.crossref.org/works/{doi}"

    response = requests.get(
        url,
        impersonate="chrome",
        timeout=30
    )

    response.raise_for_status()

    data = response.json()["message"]

    candidates = []

    for link in data.get("link", []):

        fulltext_url = link.get("URL")
        content_type = (
            link.get("content-type", "")
            .lower()
        )

        if not fulltext_url:
            continue

        if "pdf" in content_type:
            fmt = "pdf"

        elif (
            "xml" in content_type
            or "text" in content_type
        ):
            fmt = "xml"

        else:
            continue

        candidate = {
            "url": fulltext_url,
            "format": fmt,
            "headers": None
        }

        if candidate not in candidates:
            candidates.append(candidate)

    # PDF 优先，XML 后面再试
    candidates.sort(
        key=lambda x: 0
        if x["format"] == "pdf"
        else 1
    )

    return {
        "source": "Crossref TDM",
        "candidates": candidates
    }


if __name__ == "__main__":

    doi = "10.1016/j.xcrp.2021.100620"

    print(
        discover_crossref_tdm(doi)
    )