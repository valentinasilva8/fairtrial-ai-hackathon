"""Download every TrialWatch/CFJ report PDF listed in cfj.org's report sitemap.

Polite by design: cfj.org's robots.txt sets Crawl-delay 10, so we wait 10 s
between requests (about 30 minutes for all reports). Re-running skips PDFs
already downloaded. PDFs go to data/raw/trialwatch/ (git-ignored: they are
CFJ's copyrighted reports, so we don't republish them).

Run: python scripts/fetch_trialwatch_reports.py
"""

import csv
import re
import ssl
import sys
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

import certifi

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "trialwatch"
SITEMAP = "https://cfj.org/rb_report-sitemap.xml"
UA = "Mozilla/5.0 (compatible; paper-vs-practice/0.1; TrialWatch Fair Trial & AI Hackathon)"
DELAY = 10
CTX = ssl.create_default_context(cafile=certifi.where())


def get(url: str, retries: int = 2) -> bytes:
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
                return r.read()
        except Exception:
            if attempt == retries:
                raise
            time.sleep(DELAY * 2)


class ReportPage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.pdfs, self.title, self._in_title = [], "", False

    def handle_starttag(self, tag, attrs):
        href = dict(attrs).get("href", "")
        if tag == "a" and href.lower().endswith(".pdf"):
            self.pdfs.append(href)
        self._in_title = tag == "title"

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sitemap = get(SITEMAP).decode()
    urls = [u for u in re.findall(r"<loc>([^<]+)</loc>", sitemap) if u.rstrip("/") != "https://cfj.org/reports"]
    print(f"{len(urls)} report pages in sitemap", flush=True)

    rows = []
    for i, url in enumerate(urls, 1):
        row = {"url": url, "title": "", "pdf_url": "", "pdf_file": "", "status": ""}
        try:
            time.sleep(DELAY)
            page = ReportPage()
            page.feed(get(url).decode("utf-8", "replace"))
            row["title"] = page.title.split(" : ")[0].split("|")[0].strip()
            pdfs = list(dict.fromkeys(page.pdfs))
            if not pdfs:
                row["status"] = "no_pdf"
            else:
                row["pdf_url"] = pdfs[0]
                row["pdf_file"] = pdfs[0].rsplit("/", 1)[-1]
                dest = OUT / row["pdf_file"]
                if not dest.exists():
                    time.sleep(DELAY)
                    dest.write_bytes(get(pdfs[0]))
                row["status"] = "ok"
        except Exception as e:
            row["status"] = f"error: {type(e).__name__}"
        rows.append(row)
        print(f"[{i}/{len(urls)}] {row['status']:8s} {url}", flush=True)

    with open(OUT / "pages.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    failed = [r for r in rows if r["status"].startswith("error")]
    print(f"done: {sum(r['status'] == 'ok' for r in rows)} PDFs, {len(failed)} errors (re-run to retry)")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
