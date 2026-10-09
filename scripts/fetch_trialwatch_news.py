"""Download CFJ news posts (cfj.org/news/...) so outcomes after a report can be traced.

Same rules as fetch_trialwatch_reports.py: 10 s between requests (robots.txt
Crawl-delay), already-fetched posts are skipped. Saves one JSON per post
(url, title, published date, plain body text) to data/raw/trialwatch/news/,
which is git-ignored.

Run: python scripts/fetch_trialwatch_news.py
"""

import json
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from fetch_trialwatch_reports import DELAY, get  # noqa: E402

OUT = ROOT / "data" / "raw" / "trialwatch" / "news"
SITEMAP = "https://cfj.org/post-sitemap.xml"


class PostPage(HTMLParser):
    """Collects the page title, publish date and the text inside <main>."""

    SKIP = {"script", "style", "nav", "footer", "form", "noscript"}

    def __init__(self):
        super().__init__()
        self.title, self.date, self.parts = "", "", []
        self._in_title = self._in_main = False
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta" and a.get("property") == "article:published_time":
            self.date = a.get("content", "")[:10]
        elif tag == "main":
            self._in_main = True
        elif tag in self.SKIP:
            self._skip += 1
        elif tag in ("p", "li", "h1", "h2", "h3", "br"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "main":
            self._in_main = False
        elif tag in self.SKIP and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif self._in_main and not self._skip:
            self.parts.append(data)

    def text(self):
        return re.sub(r"\n\s*\n+", "\n\n", re.sub(r"[ \t]+", " ", "".join(self.parts))).strip()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    urls = [u for u in re.findall(r"<loc>([^<]+)</loc>", get(SITEMAP).decode()) if u.rstrip("/") != "https://cfj.org/news"]
    print(f"{len(urls)} news posts in sitemap", flush=True)
    errors = 0
    for i, url in enumerate(urls, 1):
        dest = OUT / (url.rstrip("/").rsplit("/", 1)[-1][:120] + ".json")
        if dest.exists():
            continue
        time.sleep(DELAY)
        try:
            page = PostPage()
            page.feed(get(url).decode("utf-8", "replace"))
            title = page.title.split(" : ")[0].split("|")[0].strip()
            dest.write_text(json.dumps({"url": url, "title": title, "date": page.date, "text": page.text()}, ensure_ascii=False))
            status = "ok"
        except Exception as e:
            errors += 1
            status = f"error: {type(e).__name__}"
        print(f"[{i}/{len(urls)}] {status} {url}", flush=True)
    print(f"done, {errors} errors (re-run to retry)")


if __name__ == "__main__":
    main()
