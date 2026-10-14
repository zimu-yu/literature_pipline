# discover/router.py

from .crossref import get_metadata

from .publishers.acs import ACSAdapter
from .publishers.elsevier import ElsevierAdapter
from .publishers.springer import SpringerAdapter
from .publishers.wiley import WileyAdapter

from .fallbacks.unpaywall import discover_unpaywall
from .fallbacks.europepmc import discover_europepmc
from .fallbacks.crossref_tdm import discover_crossref_tdm
from .fallbacks.openalex import discover_openalex
from .fallbacks.osti import discover_osti
from .fallbacks.semantic import discover_semantic


def discover_resources(doi: str) -> dict:

    metadata = get_metadata(doi)

    publisher = metadata["publisher"]
    title = metadata["title"]

    # --------------------------
    # Publisher adapter
    # --------------------------

    if "American Chemical Society" in publisher:
        adapter = ACSAdapter()

    elif "Elsevier" in publisher:
        adapter = ElsevierAdapter()

    elif "Springer" in publisher:
        adapter = SpringerAdapter()

    elif "Wiley" in publisher:
        adapter = WileyAdapter()

    else:
        raise ValueError(
            f"Unsupported publisher: {publisher}"
        )

    fulltext_candidates = []
    discovery_attempts = []

    si_urls = []
    si_source = None

    pmcid = None
    landing_url = None

    # ==================================================
    # 1. Publisher
    # ==================================================

    try:

        result = adapter.discover(doi)

        landing_url = result["landing_url"]

        if result.get("fulltext_candidates"):

            fulltext_candidates.extend(
                result["fulltext_candidates"]
            )

            discovery_attempts.append({
                "source": result["publisher"],
                "status": "found",
                "count": len(
                    result["fulltext_candidates"]
                )
            })

        elif result.get("fulltext_url"):

            fulltext_candidates.append({
                "url": result["fulltext_url"],
                "source": result["publisher"],
                "format": "pdf",
                "headers": result.get(
                    "fulltext_headers"
                )
            })

            discovery_attempts.append({
                "source": result["publisher"],
                "status": "found",
                "count": 1
            })

        else:

            discovery_attempts.append({
                "source": publisher,
                "status": "not_found"
            })

        if result.get("si_urls"):

            si_urls = result["si_urls"]
            si_source = result["publisher"]

    except Exception as e:

        discovery_attempts.append({
            "source": publisher,
            "status": "error",
            "error": str(e)
        })

    # ==================================================
    # 2. Unpaywall
    # ==================================================

    try:

        result = discover_unpaywall(doi)

        urls = result["fulltext_urls"]

        if urls:

            for url in urls:

                fulltext_candidates.append({
                    "url": url,
                    "source": "Unpaywall",
                    "format": "pdf",
                    "headers": None
                })

            discovery_attempts.append({
                "source": "Unpaywall",
                "status": "found",
                "count": len(urls)
            })

        else:

            discovery_attempts.append({
                "source": "Unpaywall",
                "status": "not_found"
            })

    except Exception as e:

        discovery_attempts.append({
            "source": "Unpaywall",
            "status": "error",
            "error": str(e)
        })

    # ==================================================
    # 3. Europe PMC
    # ==================================================

    try:

        result = discover_europepmc(doi)

        pmcid = result["pmcid"]

        if result["fulltext_url"]:

            fulltext_candidates.append({
                "url": result["fulltext_url"],
                "source": "Europe PMC",
                "format": "xml",
                "headers": None
            })

            discovery_attempts.append({
                "source": "Europe PMC",
                "status": "found"
            })

        else:

            discovery_attempts.append({
                "source": "Europe PMC",
                "status": "not_found"
            })

        if (
            not si_urls
            and result["si_url"]
        ):

            si_urls = [
                result["si_url"]
            ]

            si_source = "Europe PMC"

    except Exception as e:

        discovery_attempts.append({
            "source": "Europe PMC",
            "status": "error",
            "error": str(e)
        })

    # ==================================================
    # 4. OpenAlex
    # ==================================================

    try:

        result = discover_openalex(doi)

        candidates = result["candidates"]

        for candidate in candidates:

            fulltext_candidates.append({
                "url": candidate["url"],
                "source": "OpenAlex",
                "format": candidate["format"],
                "headers": candidate.get(
                    "headers"
                )
            })

        discovery_attempts.append({
            "source": "OpenAlex",
            "status": (
                "found"
                if candidates
                else "not_found"
            ),
            "count": len(candidates)
        })

    except Exception as e:

        discovery_attempts.append({
            "source": "OpenAlex",
            "status": "error",
            "error": str(e)
        })

    # ==================================================
    # 5. OSTI
    # ==================================================

    try:

        result = discover_osti(doi)

        candidates = result["candidates"]

        for candidate in candidates:

            fulltext_candidates.append({
                "url": candidate["url"],
                "source": "OSTI",
                "format": candidate["format"],
                "headers": candidate.get(
                    "headers"
                )
            })

        discovery_attempts.append({
            "source": "OSTI",
            "status": (
                "found"
                if candidates
                else "not_found"
            ),
            "count": len(candidates)
        })

    except Exception as e:

        discovery_attempts.append({
            "source": "OSTI",
            "status": "error",
            "error": str(e)
        })

    # ==================================================
    # 6. Semantic Scholar
    # ==================================================

    try:

        result = discover_semantic(doi)

        candidates = result["candidates"]

        for candidate in candidates:

            fulltext_candidates.append({
                "url": candidate["url"],
                "source": "Semantic Scholar",
                "format": candidate["format"],
                "headers": candidate.get(
                    "headers"
                )
            })

        discovery_attempts.append({
            "source": "Semantic Scholar",
            "status": (
                "found"
                if candidates
                else "not_found"
            ),
            "count": len(candidates)
        })

    except Exception as e:

        discovery_attempts.append({
            "source": "Semantic Scholar",
            "status": "error",
            "error": str(e)
        })

    # ==================================================
    # 7. Crossref TDM
    # ==================================================

    try:

        result = discover_crossref_tdm(doi)

        candidates = result["candidates"]

        for candidate in candidates:

            fulltext_candidates.append({
                "url": candidate["url"],
                "source": "Crossref TDM",
                "format": candidate["format"],
                "headers": candidate.get(
                    "headers"
                )
            })

        discovery_attempts.append({
            "source": "Crossref TDM",
            "status": (
                "found"
                if candidates
                else "not_found"
            ),
            "count": len(candidates)
        })

    except Exception as e:

        discovery_attempts.append({
            "source": "Crossref TDM",
            "status": "error",
            "error": str(e)
        })

    # ==================================================
    # Return
    # ==================================================

    return {
        "publisher": publisher,
        "title": title,
        "landing_url": landing_url,
        "fulltext_candidates": fulltext_candidates,
        "discovery_attempts": discovery_attempts,
        "si_urls": si_urls,
        "si_source": si_source,
        "pmcid": pmcid,
    }