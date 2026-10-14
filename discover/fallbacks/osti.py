# discover/fallbacks/osti.py

from curl_cffi import requests


def discover_osti(doi: str) -> dict:

    url = "https://www.osti.gov/api/v1/records"

    response = requests.get(
        url,
        params={
            "doi": doi,
            "has_fulltext": "true"
        },
        headers={
            "Accept": "application/json"
        },
        impersonate="chrome",
        timeout=30
    )

    response.raise_for_status()

    records = response.json()

    candidates = []
    seen = set()

    for record in records:

        for link in record.get("links", []):

            if link.get("rel") != "fulltext":
                continue

            fulltext_url = link.get("href")

            if (
                not fulltext_url
                or fulltext_url in seen
            ):
                continue

            seen.add(fulltext_url)

            candidates.append({
                "url": fulltext_url,
                "format": "pdf",
                "headers": None
            })

        # 有记录但没有显式 fulltext link 时，
        # 尝试 OSTI 自己的 purl
        if (
            not candidates
            and record.get("osti_id")
        ):

            fulltext_url = (
                "https://www.osti.gov/"
                "servlets/purl/"
                + str(record["osti_id"])
            )

            if fulltext_url not in seen:

                seen.add(fulltext_url)

                candidates.append({
                    "url": fulltext_url,
                    "format": "pdf",
                    "headers": None
                })

    return {
        "source": "OSTI",
        "candidates": candidates
    }


if __name__ == "__main__":

    doi = "10.1021/acs.chemmater.4c00303"

    print(
        discover_osti(doi)
    )