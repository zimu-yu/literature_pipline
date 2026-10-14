# evaluate.py

import json
from pathlib import Path
from collections import Counter, defaultdict


OUTPUT_DIR = Path("output")


def load_manifests():
    manifests = []

    for path in OUTPUT_DIR.glob("*/manifest.json"):

        try:
            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)

            manifests.append(data)

        except Exception as e:
            print(
                f"Failed to read {path}: {e}"
            )

    return manifests


def percent(n, total):
    if total == 0:
        return 0.0

    return round(
        n / total * 100,
        1
    )


def evaluate(manifests):

    total = len(manifests)

    fulltext_success = 0
    pdf_success = 0
    xml_success = 0
    si_complete = 0

    status_counter = Counter()
    route_counter = Counter()

    publisher_stats = defaultdict(
        lambda: {
            "total": 0,
            "fulltext": 0,
            "pdf": 0,
            "si_complete": 0,
            "success": 0,
            "partial": 0,
            "failed": 0,
        }
    )

    failures = []

    for manifest in manifests:

        publisher = manifest.get(
            "publisher",
            "Unknown"
        )

        status = manifest.get(
            "status",
            "unknown"
        )

        article = manifest.get(
            "fulltext"
        )

        status_counter[status] += 1

        stats = publisher_stats[publisher]
        stats["total"] += 1

        if status in stats:
            stats[status] += 1

        # --------------------------
        # Full text
        # --------------------------

        if article and article.get("valid"):

            fulltext_success += 1
            stats["fulltext"] += 1

            fmt = article.get(
                "format"
            )

            source = article.get(
                "source",
                "Unknown"
            )

            route_counter[source] += 1

            if fmt == "pdf":
                pdf_success += 1
                stats["pdf"] += 1

            elif fmt == "xml":
                xml_success += 1

        # --------------------------
        # SI
        # --------------------------

        if manifest.get("si_complete"):
            si_complete += 1
            stats["si_complete"] += 1

        # --------------------------
        # Failures
        # --------------------------

        if status != "success":

            failures.append({
                "doi": manifest.get("doi"),
                "publisher": publisher,
                "status": status,
                "error": manifest.get(
                    "error",
                    ""
                )
            })

    # ==================================================
    # Overall
    # ==================================================

    print()
    print("=" * 60)
    print("OVERALL")
    print("=" * 60)

    print(f"Total DOI: {total}")

    print(
        f"Full-text acquisition: "
        f"{fulltext_success}/{total} "
        f"({percent(fulltext_success, total)}%)"
    )

    print(
        f"PDF acquisition: "
        f"{pdf_success}/{total} "
        f"({percent(pdf_success, total)}%)"
    )

    print(
        f"XML fallback: "
        f"{xml_success}/{total} "
        f"({percent(xml_success, total)}%)"
    )

    print(
        f"SI complete: "
        f"{si_complete}/{total} "
        f"({percent(si_complete, total)}%)"
    )

    print()

    for status, count in status_counter.items():

        print(
            f"{status}: "
            f"{count}/{total} "
            f"({percent(count, total)}%)"
        )

    # ==================================================
    # Publisher breakdown
    # ==================================================

    print()
    print("=" * 60)
    print("BY PUBLISHER")
    print("=" * 60)

    for publisher, stats in publisher_stats.items():

        n = stats["total"]

        print()
        print(publisher)

        print(
            f"  Full text: "
            f'{stats["fulltext"]}/{n} '
            f'({percent(stats["fulltext"], n)}%)'
        )

        print(
            f"  PDF: "
            f'{stats["pdf"]}/{n} '
            f'({percent(stats["pdf"], n)}%)'
        )

        print(
            f"  SI complete: "
            f'{stats["si_complete"]}/{n} '
            f'({percent(stats["si_complete"], n)}%)'
        )

        print(
            f'  success: {stats["success"]}'
        )

        print(
            f'  partial: {stats["partial"]}'
        )

        print(
            f'  failed: {stats["failed"]}'
        )

    # ==================================================
    # Routes
    # ==================================================

    print()
    print("=" * 60)
    print("FULL-TEXT ROUTES")
    print("=" * 60)

    for source, count in route_counter.most_common():

        print(
            f"{source}: {count}"
        )

    # ==================================================
    # Failures
    # ==================================================

    print()
    print("=" * 60)
    print("NON-SUCCESS ARTICLES")
    print("=" * 60)

    if not failures:

        print("None")

    else:

        for item in failures:

            print()
            print(
                item["doi"],
                "->",
                item["status"]
            )

            if item["error"]:
                print(
                    " ",
                    item["error"].replace(
                        "\n",
                        " | "
                    )
                )


if __name__ == "__main__":

    manifests = load_manifests()

    if not manifests:
        print(
            "No manifest.json files found "
            "under output/"
        )

    else:
        evaluate(manifests)