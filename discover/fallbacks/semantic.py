# discover/fallbacks/semantic.py

import os

from curl_cffi import requests


def discover_semantic(doi: str) -> dict:

    url = (
        "https://api.semanticscholar.org/"
        "graph/v1/paper/"
        f"DOI:{doi}"
    )

    headers = {}

    api_key = os.getenv(
        "SEMANTIC_SCHOLAR_API_KEY"
    )

    if api_key:
        headers["x-api-key"] = api_key

    response = requests.get(
        url,
        params={
            "fields": (
                "title,"
                "isOpenAccess,"
                "openAccessPdf"
            )
        },
        headers=headers,
        impersonate="chrome",
        timeout=30
    )

    # 查不到 DOI 时直接当作没发现
    if response.status_code == 404:
        return {
            "source": "Semantic Scholar",
            "candidates": []
        }

    response.raise_for_status()

    data = response.json()

    candidates = []

    pdf = data.get("openAccessPdf")

    if pdf:

        pdf_url = pdf.get("url")

        if pdf_url:

            candidates.append({
                "url": pdf_url,
                "format": "pdf",
                "headers": None
            })

    return {
        "source": "Semantic Scholar",
        "candidates": candidates
    }


if __name__ == "__main__":

    doi = "10.1016/j.xcrp.2021.100620"

    print(
        discover_semantic(doi)
    )