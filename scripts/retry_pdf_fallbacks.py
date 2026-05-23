import csv
import time
from pathlib import Path
from urllib.parse import quote

import requests


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "outputs" / "pdf_download_manifest.csv"


def download_pdf(url, target, session):
    headers = {
        "User-Agent": "Mozilla/5.0 literature metadata downloader; contact=literature-search@example.com",
        "Accept": "application/pdf,application/octet-stream,*/*",
        "Referer": "https://doi.org/",
    }
    with session.get(url, headers=headers, timeout=60, stream=True, allow_redirects=True) as response:
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        data = b"".join(chunk for chunk in response.iter_content(65536) if chunk)
    if not data.startswith(b"%PDF") and "pdf" not in content_type:
        raise RuntimeError(f"not_pdf_content_type={content_type or 'unknown'}")
    target.write_bytes(data)
    return len(data)


def semantic_scholar_pdf(doi, session):
    url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
    response = session.get(url, params={"fields": "openAccessPdf,isOpenAccess,title"}, timeout=30)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    data = response.json()
    pdf = data.get("openAccessPdf") or {}
    return pdf.get("url")


def unpaywall_pdf(doi, session):
    url = "https://api.unpaywall.org/v2/" + quote(doi, safe="")
    response = session.get(url, params={"email": "literature-search@example.com"}, timeout=30)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    data = response.json()
    best = data.get("best_oa_location") or {}
    if best.get("url_for_pdf"):
        return best["url_for_pdf"]
    for loc in data.get("oa_locations") or []:
        if loc.get("url_for_pdf"):
            return loc["url_for_pdf"]
    return None


def main():
    with MANIFEST.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    session = requests.Session()
    fixed = 0

    for row in rows:
        if row["status"] != "not_downloaded":
            continue
        target = ROOT / row["pdf_file"]
        candidates = []
        for finder_name, finder in [
            ("semantic_scholar", semantic_scholar_pdf),
            ("unpaywall", unpaywall_pdf),
        ]:
            try:
                url = finder(row["doi"], session)
            except Exception as exc:
                row["reason"] = f"{row['reason']}; {finder_name}_lookup={exc}"
                url = None
            if url and url not in candidates:
                candidates.append(url)
            time.sleep(0.2)

        last_error = ""
        for url in candidates:
            try:
                size = download_pdf(url, target, session)
                row["status"] = "downloaded_fallback"
                row["pdf_url"] = url
                row["bytes"] = str(size)
                row["reason"] = ""
                fixed += 1
                print(f"downloaded_fallback {row['paper_id']} {row['doi']}")
                break
            except Exception as exc:
                last_error = str(exc)
                if target.exists() and target.stat().st_size == 0:
                    target.unlink()
        if row["status"] == "not_downloaded" and candidates:
            row["reason"] = f"{row['reason']}; fallback_failed={last_error}"

    with MANIFEST.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    available = sum(1 for r in rows if r["status"] in {"downloaded", "downloaded_fallback", "exists"})
    print(f"fallback fixed: {fixed}")
    print(f"available: {available}/{len(rows)}")


if __name__ == "__main__":
    main()
