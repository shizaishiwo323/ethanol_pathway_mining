import csv
import re
import time
from pathlib import Path
from urllib.parse import quote

import requests


ROOT = Path(__file__).resolve().parents[1]
INPUT_FILES = [
    ROOT / "outputs" / "literature_metadata_initial.csv",
    ROOT / "outputs" / "literature_metadata_batch2.csv",
]
PDF_DIR = ROOT / "paper_pdf_folder"
MANIFEST = ROOT / "outputs" / "pdf_download_manifest.csv"


def safe_name(value):
    value = re.sub(r"^https?://doi\.org/", "", value.strip(), flags=re.I)
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    return value.strip("_")[:120]


def load_rows():
    rows = []
    seen = set()
    for path in INPUT_FILES:
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                doi = row["doi"].lower().strip()
                if doi in seen:
                    continue
                seen.add(doi)
                row["source_csv"] = path.name
                rows.append(row)
    return rows


def openalex_work(doi, session):
    url = "https://api.openalex.org/works/https://doi.org/" + quote(doi, safe="")
    response = session.get(
        url,
        params={"mailto": "literature-search@example.com"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def pdf_candidates(work):
    candidates = []
    best = work.get("best_oa_location") or {}
    if best.get("pdf_url"):
        candidates.append(best["pdf_url"])
    for loc in work.get("locations") or []:
        url = (loc or {}).get("pdf_url")
        if url and url not in candidates:
            candidates.append(url)
    return candidates


def download_pdf(url, target, session):
    headers = {
        "User-Agent": "Mozilla/5.0 literature metadata downloader",
        "Accept": "application/pdf,*/*",
    }
    with session.get(url, headers=headers, timeout=60, stream=True, allow_redirects=True) as response:
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        chunks = []
        total = 0
        for chunk in response.iter_content(chunk_size=65536):
            if not chunk:
                continue
            chunks.append(chunk)
            total += len(chunk)
            if total > 200_000_000:
                raise RuntimeError("file_too_large")
        data = b"".join(chunks)
    if not data.startswith(b"%PDF") and "pdf" not in content_type:
        raise RuntimeError(f"not_pdf_content_type={content_type or 'unknown'}")
    target.write_bytes(data)
    return len(data)


def main():
    PDF_DIR.mkdir(exist_ok=True)
    rows = load_rows()
    session = requests.Session()
    manifest_rows = []

    for index, row in enumerate(rows, start=1):
        doi = row["doi"].lower().strip()
        filename = f"{row['paper_id']}_{safe_name(doi)}.pdf"
        target = PDF_DIR / filename
        result = {
            "paper_id": row["paper_id"],
            "doi": doi,
            "title": row["title"],
            "journal": row["journal"],
            "year": row["year"],
            "pdf_file": str(target.relative_to(ROOT)),
            "status": "",
            "pdf_url": "",
            "bytes": "",
            "reason": "",
        }
        if target.exists() and target.stat().st_size > 1024:
            result["status"] = "exists"
            result["bytes"] = str(target.stat().st_size)
            manifest_rows.append(result)
            print(f"[{index}/{len(rows)}] exists {row['paper_id']} {doi}")
            continue

        try:
            work = openalex_work(doi, session)
            candidates = pdf_candidates(work)
            if not candidates:
                result["status"] = "not_downloaded"
                result["reason"] = "no_open_pdf_url_in_openalex"
                manifest_rows.append(result)
                print(f"[{index}/{len(rows)}] no pdf {row['paper_id']} {doi}")
                time.sleep(0.2)
                continue

            last_error = ""
            for pdf_url in candidates:
                try:
                    size = download_pdf(pdf_url, target, session)
                    result["status"] = "downloaded"
                    result["pdf_url"] = pdf_url
                    result["bytes"] = str(size)
                    print(f"[{index}/{len(rows)}] downloaded {row['paper_id']} {doi}")
                    break
                except Exception as exc:
                    last_error = str(exc)
                    if target.exists() and target.stat().st_size == 0:
                        target.unlink()
            if not result["status"]:
                result["status"] = "not_downloaded"
                result["pdf_url"] = candidates[0]
                result["reason"] = last_error
                print(f"[{index}/{len(rows)}] failed {row['paper_id']} {doi}: {last_error}")
        except Exception as exc:
            result["status"] = "not_downloaded"
            result["reason"] = str(exc)
            print(f"[{index}/{len(rows)}] error {row['paper_id']} {doi}: {exc}")
        manifest_rows.append(result)
        time.sleep(0.2)

    with MANIFEST.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(manifest_rows[0].keys()))
        writer.writeheader()
        writer.writerows(manifest_rows)

    downloaded = sum(1 for r in manifest_rows if r["status"] in {"downloaded", "exists"})
    print(f"done: {downloaded}/{len(manifest_rows)} PDFs available")
    print(f"manifest: {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
