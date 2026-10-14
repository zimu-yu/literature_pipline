# discover/fallbacks/unpaywall.py

import os
from curl_cffi import requests


def discover_unpaywall(doi: str) -> dict:

    email = os.getenv("UNPAYWALL_EMAIL")

    url = f"https://api.unpaywall.org/v2/{doi}"

    response = requests.get(
        url,
        params={"email": email},
        impersonate="chrome",
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    fulltext_urls = []

    # 1. 先放 best OA location
    best = data.get("best_oa_location")

    if best:
        pdf_url = best.get("url_for_pdf")

        if pdf_url:
            fulltext_urls.append(pdf_url)

    # 2. 再遍历所有 OA locations
    for location in data.get("oa_locations", []):

        pdf_url = location.get("url_for_pdf")

        if (
            pdf_url
            and pdf_url not in fulltext_urls
        ):
            fulltext_urls.append(pdf_url)

    return {
        "source": "Unpaywall",
        "fulltext_urls": fulltext_urls
    }


if __name__ == "__main__":

    doi = "10.1021/acsomega.2c05637"

    print(
        discover_unpaywall(doi)
    )