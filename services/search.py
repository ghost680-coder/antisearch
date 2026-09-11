"""
Search providers. Pure Python - no Rust, no compiled extensions.
Order: SerpAPI -> Brave -> DuckDuckGo HTML -> empty.
"""
import re
import requests
from config import Config

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _serpapi(query, max_results=10):
    if not Config.SERPAPI_KEY:
        return []
    try:
        r = requests.get("https://serpapi.com/search", params={
            "q": query, "api_key": Config.SERPAPI_KEY,
            "num": max_results, "engine": "google",
        }, timeout=8)
        r.raise_for_status()
        return [{
            "title": x.get("title", ""),
            "snippet": x.get("snippet", ""),
            "url": x.get("link", ""),
        } for x in r.json().get("organic_results", [])[:max_results]]
    except Exception as e:
        print(f"[search] SerpAPI failed: {e}")
        return []


def _brave(query, max_results=10):
    if not Config.BRAVE_API_KEY:
        return []
    try:
        r = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"X-Subscription-Token": Config.BRAVE_API_KEY,
                     "Accept": "application/json"},
            params={"q": query, "count": max_results},
            timeout=8,
        )
        r.raise_for_status()
        web = r.json().get("web", {}).get("results", [])
        return [{
            "title": x.get("title", ""),
            "snippet": x.get("description", ""),
            "url": x.get("url", ""),
        } for x in web[:max_results]]
    except Exception as e:
        print(f"[search] Brave failed: {e}")
        return []


def _ddg_html(query, max_results=10):
    """
    Scrape DuckDuckGo's HTML-only endpoint. No API key.
    Falls back gracefully if it fails.
    """
    try:
        r = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers={"User-Agent": USER_AGENT},
            timeout=8,
        )
        r.raise_for_status()
        html = r.text

        results = []
        # Each result has: <a class="result__a" href="...">Title</a>
        # and <a class="result__snippet">Snippet</a>
        link_re = re.compile(
            r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            re.DOTALL
        )
        snip_re = re.compile(
            r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
            re.DOTALL
        )

        links = link_re.findall(html)
        snippets = snip_re.findall(html)

        for i, (url, title) in enumerate(links[:max_results]):
            title_clean = _clean(title)
            snip_clean = _clean(snippets[i]) if i < len(snippets) else ""
            if title_clean:
                results.append({
                    "title": title_clean,
                    "snippet": snip_clean,
                    "url": url,
                })
        return results
    except Exception as e:
        print(f"[search] DDG html failed: {e}")
        return []


def _clean(s):
    """Strip HTML tags and decode common entities."""
    s = re.sub(r"<[^>]+>", "", s or "")
    s = (s.replace("&amp;", "&").replace("&quot;", '"')
           .replace("&#x27;", "'").replace("&lt;", "<")
           .replace("&gt;", ">").replace("&nbsp;", " "))
    return s.strip()


def search(query, max_results=10):
    for fn in (_serpapi, _brave, _ddg_html):
        results = fn(query, max_results)
        if results:
            return results
    return []
