# acquire.py

import sys
import zipfile
from pathlib import Path
from urllib.parse import urlparse, unquote

from normalize import normalize_doi
from discover.router import discover_resources
from download import download_file
from validate import validate_article, validate_si, validate_si_complete
from manifest import save_manifest


def check_elsevier(candidate: dict, article: dict, article_path: Path):
    """
    Elsevier 有时会返回非完整全文，
    所以额外检查 PDF entitlement 和 XML 内容。
    """

    if candidate["source"] != "Elsevier":
        return

    # Elsevier PDF
    if candidate["format"] == "pdf":
        headers = {
            key.lower(): value
            for key, value in article.get(
                "response_headers",
                {}
            ).items()
        }

        status = headers.get(
            "x-els-status",
            ""
        )

        if "not entitled" in status.lower():
            raise PermissionError(
                "Elsevier PDF is not fully entitled"
            )

    # Elsevier XML
    if candidate["format"] == "xml":
        xml_text = article_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        if (
            "<coredata" in xml_text
            and "<ce:para" not in xml_text
            and "<xocs:rawtext" not in xml_text
        ):
            raise PermissionError(
                "Elsevier XML is abstract-only"
            )


def build_error_lines(resources: dict, attempts: list) -> list:
    """
    把 discovery 和 download 的失败信息整理成可读文本。
    """

    lines = []

    for attempt in resources.get(
        "discovery_attempts",
        []
    ):
        status = attempt["status"]

        if status == "found":
            message = "found"

        elif status == "not_found":
            message = "not found"

        else:
            message = attempt.get(
                "error",
                "error"
            )

        lines.append(
            f'{attempt["source"]} discovery: {message}'
        )

    for attempt in attempts:
        lines.append(
            f'{attempt["source"]} '
            f'{attempt["format"]}: '
            f'{attempt.get("error", attempt["status"])}'
        )

    return lines


def acquire(raw_doi: str):

    # 1. Normalize DOI
    doi = normalize_doi(raw_doi)

    output_dir = (
        Path("output")
        / doi.replace("/", "_")
    )

    si_dir = output_dir / "SI"

    # 2. Discover resources
    resources = discover_resources(doi)

    # =====================================================
    # 3. Full text
    # =====================================================

    article = None
    fulltext_attempts = []

    for candidate in resources["fulltext_candidates"]:

        article_path = (
            output_dir
            / f'article.{candidate["format"]}'
        )

        try:
            article = download_file(
                candidate["url"],
                article_path,
                headers=candidate.get("headers")
            )

            check_elsevier(
                candidate,
                article,
                article_path
            )

            valid = validate_article(
                article_path,
                doi
            )

            if not valid:
                raise ValueError(
                    "Downloaded full text failed validation"
                )

            article["source_url"] = candidate["url"]
            article["source"] = candidate["source"]
            article["format"] = candidate["format"]
            article["valid"] = True

            fulltext_attempts.append({
                "source": candidate["source"],
                "format": candidate["format"],
                "url": candidate["url"],
                "status": "success"
            })

            break

        except Exception as e:

            fulltext_attempts.append({
                "source": candidate["source"],
                "format": candidate["format"],
                "url": candidate["url"],
                "status": "failed",
                "error": str(e)
            })

            article = None

            if article_path.exists():
                article_path.unlink()

    # =====================================================
    # 4. Supplementary files
    #
    # 注意：
    # 即使 article == None，也继续执行这里。
    # =====================================================

    supplements = []
    si_attempts = []

    for url in resources["si_urls"]:

        try:

            # -----------------------------
            # Europe PMC
            # supplementaryFiles 是 ZIP
            # -----------------------------

            if resources["si_source"] == "Europe PMC":

                zip_path = (
                    si_dir
                    / "supplementaryFiles.zip"
                )

                download_file(
                    url,
                    zip_path
                )

                with zipfile.ZipFile(
                    zip_path,
                    "r"
                ) as z:

                    z.extractall(si_dir)

                    for member in z.namelist():

                        si_path = si_dir / member

                        if si_path.is_dir():
                            continue

                        result = {
                            "source_url": url,
                            "local_path": str(si_path),
                            "source": "Europe PMC",
                            "size_mb": round(
                                si_path.stat().st_size
                                / (1024 * 1024),
                                2
                            )
                        }

                        result["valid"] = validate_si(
                            si_path,
                            url,
                            doi,
                            resources["si_source"],
                            resources["pmcid"]
                        )

                        supplements.append(
                            result
                        )

                si_attempts.append({
                    "source": "Europe PMC",
                    "url": url,
                    "status": "success"
                })

            # -----------------------------
            # Publisher SI
            # 一个 URL 对应一个文件
            # -----------------------------

            else:

                filename = Path(
                    unquote(
                        urlparse(url).path
                    )
                ).name

                si_path = (
                    si_dir
                    / filename
                )

                result = download_file(
                    url,
                    si_path
                )

                result["source_url"] = url
                result["source"] = resources["si_source"]

                result["valid"] = validate_si(
                    si_path,
                    url,
                    doi,
                    resources["si_source"],
                    resources["pmcid"]
                )

                supplements.append(
                    result
                )

                si_attempts.append({
                    "source": resources["si_source"],
                    "url": url,
                    "status": "success"
                })

        except Exception as e:

            si_attempts.append({
                "source": resources["si_source"],
                "url": url,
                "status": "failed",
                "error": str(e)
            })

    # =====================================================
    # 5. SI completeness
    # =====================================================

    si_complete = validate_si_complete(
        resources["si_urls"],
        supplements
    )

    if any(
        attempt["status"] == "failed"
        for attempt in si_attempts
    ):
        si_complete = False

    # =====================================================
    # 6. Final status
    # =====================================================

    if article is None:
        status = "failed"

    elif not si_complete:
        status = "partial"

    else:
        status = "success"

    error_lines = build_error_lines(
        resources,
        fulltext_attempts
    )

    # =====================================================
    # 7. Manifest
    # =====================================================

    manifest = {
        "doi": doi,
        "publisher": resources["publisher"],
        "title": resources["title"],
        "landing_url": resources["landing_url"],

        "status": status,

        "discovery_attempts": resources.get(
            "discovery_attempts",
            []
        ),

        "fulltext": article,
        "fulltext_attempts": fulltext_attempts,

        "supplements": supplements,
        "si_attempts": si_attempts,
        "si_complete": si_complete,
    }

    if article is None:
        manifest["error"] = "\n".join(
            error_lines
        )

    save_manifest(
        manifest,
        output_dir / "manifest.json"
    )

    # =====================================================
    # 8. Only raise AFTER SI + manifest
    # =====================================================

    if article is None:
        raise RuntimeError(
            f"All fulltext routes failed for {doi}\n"
            + "\n".join(error_lines)
        )

    return manifest


if __name__ == "__main__":

    doi = sys.argv[1]

    result = acquire(doi)

    print(result)