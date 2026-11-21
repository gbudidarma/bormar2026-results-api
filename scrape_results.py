import asyncio
import csv
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from bs4 import BeautifulSoup
import nodriver as uc
from nodriver.core import util

DEFAULT_URL = "https://results.scorenow.co.id/Results.aspx?CId=19723&RId=340"
CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def slugify(name: str) -> str:
    """Convert an event name like 'Marathon' into 'marathon'."""
    s = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return s or "event"


def discover_events(html: str, cid: int, rid: int) -> list[tuple[int, str]]:
    """Discover all (EId, EventName) pairs from the race results page."""
    soup = BeautifulSoup(html, "lxml")
    events = []
    seen_eids = set()
    pattern = re.compile(
        rf"results\.aspx\?CId={cid}&RId={rid}&EId=(\d+)$", re.IGNORECASE
    )
    for a in soup.find_all("a"):
        href = (a.get("href") or "").strip()
        m = pattern.search(href)
        if m:
            eid = int(m.group(1))
            name = a.get_text(" ", strip=True)
            if eid not in seen_eids and name:
                seen_eids.add(eid)
                events.append((eid, name))
    if not events:
        events.append((1, f"race_{cid}_{rid}_eid1"))
    return events


async def fetch_and_parse_batch_in_browser(page, urls: list[str]) -> list[dict]:
    """Fetch a batch of URLs inside the browser and parse table rows + athlete AId in JS."""
    js_code = f"""
    (async () => {{
        const urls = {json.dumps(urls)};
        const parseHtml = (html) => {{
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const table = doc.getElementById('ctl00_Content_Main_tblResults');
            if (!table) return {{ headers: [], rows: [], maxPage: 1 }};
            const trs = Array.from(table.querySelectorAll('tr'));
            if (!trs.length) return {{ headers: [], rows: [], maxPage: 1 }};

            const headerCells = Array.from(trs[0].querySelectorAll('th, td'));
            const keepIndices = [];
            const headers = [];
            headerCells.forEach((cell, idx) => {{
                const text = cell.textContent.replace(/\\s+/g, ' ').trim();
                if (text === 'Fav' || cell.classList.contains('d-sm-none')) return;
                keepIndices.push(idx);
                headers.push(text);
            }});
            headers.push('AId');

            const rows = [];
            for (let i = 1; i < trs.length; i++) {{
                const tr = trs[i];
                const cells = Array.from(tr.querySelectorAll('th, td'));
                if (cells.length < headerCells.length) continue;

                let aid = '';
                const dataHref = tr.getAttribute('data-href') || '';
                const mUid = dataHref.match(/uid=\\d+-\\d+-\\d+-(\\d+)/i);
                if (mUid) {{
                    aid = mUid[1];
                }} else {{
                    const nameLink = tr.querySelector('a.grid-name');
                    if (nameLink) {{
                        const href = nameLink.getAttribute('href') || '';
                        const mHref = href.match(/uid=\\d+-\\d+-\\d+-(\\d+)/i) || href.match(/AId=(\\d+)/i);
                        if (mHref) aid = mHref[1];
                    }}
                }}

                const rowVals = keepIndices.map(idx => {{
                    const c = cells[idx];
                    const nameLink = c.querySelector('a.grid-name');
                    if (nameLink) {{
                        return nameLink.textContent.replace(/\\s+/g, ' ').trim();
                    }}
                    return c.textContent.replace(/\\s+/g, ' ').trim();
                }});
                if (!rowVals[0]) {{
                    const rawNameCell = cells[keepIndices[2]].textContent.replace(/\\s+/g, ' ').trim();
                    const m = rawNameCell.match(/^(CUT|DNS|DNF|DSQ|QRY|DQ)\\b/i) || rawNameCell.match(/^(CUT|DNS|DNF|DSQ|QRY|DQ)/i);
                    if (m) {{
                        rowVals[0] = m[1].toUpperCase();
                        if (rowVals[2] === rawNameCell) {{
                            rowVals[2] = rawNameCell.slice(m[1].length).trim();
                        }}
                    }}
                }}
                rowVals.push(aid);
                rows.push(rowVals);
            }}

            let maxPage = 1;
            const pager = doc.getElementById('ctl00_Content_Main_grdBottomPager');
            if (pager) {{
                pager.querySelectorAll('a').forEach(a => {{
                    const href = a.getAttribute('href') || '';
                    const m = href.match(/PageNo=(\\d+)/i);
                    if (m) maxPage = Math.max(maxPage, parseInt(m[1], 10));
                }});
                pager.querySelectorAll('span').forEach(s => {{
                    const t = s.textContent.trim();
                    if (/^\\d+$/.test(t)) maxPage = Math.max(maxPage, parseInt(t, 10));
                }});
            }}
            return {{ headers, rows, maxPage }};
        }};

        const results = await Promise.all(
            urls.map(async (u) => {{
                for (let attempt = 0; attempt < 3; attempt++) {{
                    try {{
                        const resp = await fetch(u, {{ credentials: 'include' }});
                        if (resp.ok) {{
                            const html = await resp.text();
                            return parseHtml(html);
                        }}
                    }} catch (e) {{}}
                    await new Promise(r => setTimeout(r, 1000));
                }}
                return {{ headers: [], rows: [], maxPage: 1 }};
            }})
        );
        return JSON.stringify(results);
    }})()
    """
    raw = await page.evaluate(js_code, await_promise=True, return_by_value=True)
    if not raw or not isinstance(raw, str):
        return [{"headers": [], "rows": [], "maxPage": 1} for _ in urls]
    return json.loads(raw)


async def scrape_event(page, cid: int, rid: int, eid: int, event_name: str, output_csv: Path, batch_size: int = 12):
    """Scrape all pages for a given event (EId) and write to CSV."""
    first_url = f"https://results.scorenow.co.id/Results.aspx?CId={cid}&RId={rid}&EId={eid}&dt=0&PageNo=1"
    print(f"\nFetching Page 1 for '{event_name}' (EId={eid}): {first_url}", flush=True)
    batch = await fetch_and_parse_batch_in_browser(page, [first_url])
    first_res = batch[0]

    headers = first_res["headers"]
    all_rows = list(first_res["rows"])
    max_page = first_res["maxPage"]
    if not headers:
        print(f"Warning: No table found for EId={eid} ({event_name})", flush=True)
        return 0, []

    print(f"Found {len(all_rows)} rows on Page 1. Total pages detected: {max_page}", flush=True)
    print(f"Columns ({len(headers)}): {headers}", flush=True)

    current_page = 2
    while current_page <= max_page:
        end_page = min(current_page + batch_size - 1, max_page)
        urls = [
            f"https://results.scorenow.co.id/Results.aspx?CId={cid}&RId={rid}&EId={eid}&dt=0&PageNo={p}"
            for p in range(current_page, end_page + 1)
        ]
        parsed_list = await fetch_and_parse_batch_in_browser(page, urls)
        for res in parsed_list:
            all_rows.extend(res["rows"])
            if res["maxPage"] > max_page:
                max_page = res["maxPage"]
        print(f"  Scraped pages {current_page}..{end_page} / {max_page} (total rows so far: {len(all_rows)})", flush=True)
        current_page = end_page + 1

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(all_rows)

    print(f"Saved {len(all_rows)} rows to {output_csv}", flush=True)
    return len(all_rows), headers


async def start_browser_reliably():
    """Start Chrome with a generous startup timeout before attaching nodriver."""
    port = util.free_port()
    user_data_dir = tempfile.mkdtemp(prefix="scorenow_chrome_")
    cfg = uc.Config(
        headless=False,
        browser_executable_path=CHROME_PATH if Path(CHROME_PATH).exists() else None,
        user_data_dir=user_data_dir,
        host="127.0.0.1",
        port=port,
    )
    exe = cfg.browser_executable_path
    params = cfg()
    proc = subprocess.Popen(
        [exe, *params],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    version_url = f"http://127.0.0.1:{port}/json/version"
    for _ in range(12):
        await asyncio.sleep(0.5)
        try:
            with urllib.request.urlopen(version_url, timeout=1) as resp:
                if resp.status == 200:
                    break
        except Exception:
            pass
    else:
        proc.terminate()
        raise RuntimeError("Chrome failed to open remote debugging port within 6s")

    browser = await uc.start(host="127.0.0.1", port=port)
    return browser, proc


async def main():
    target_url = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].startswith("http") else DEFAULT_URL
    m_cid = re.search(r"CId=(\d+)", target_url, re.IGNORECASE)
    m_rid = re.search(r"RId=(\d+)", target_url, re.IGNORECASE)
    cid = int(m_cid.group(1)) if m_cid else 19723
    rid = int(m_rid.group(1)) if m_rid else 340

    print(f"Starting browser and navigating to {target_url} ...", flush=True)
    browser, proc = await start_browser_reliably()
    try:
        page = await browser.get(target_url)
        content = ""
        for i in range(25):
            await asyncio.sleep(2)
            content = await page.get_content()
            if "ctl00_Content_Main_tblResults" in content:
                print(f"Cloudflare challenge passed! (step {i})", flush=True)
                break
            print(f"Waiting for Cloudflare challenge... (step {i})", flush=True)
        else:
            raise RuntimeError("Timed out waiting for results table to load.")

        events = [(eid, name) for eid, name in discover_events(content, cid=cid, rid=rid) if eid in (1, 2, 3)]
        print(f"Scraping {len(events)} event(s) on CId={cid}&RId={rid}: {events}", flush=True)

        out_dir = Path(__file__).resolve().parent
        for eid, event_name in events:
            csv_name = f"{slugify(event_name)}_results.csv"
            await scrape_event(
                page,
                cid=cid,
                rid=rid,
                eid=eid,
                event_name=event_name,
                output_csv=out_dir / csv_name,
            )
    finally:
        try:
            browser.stop()
        except Exception:
            pass
        try:
            proc.terminate()
        except Exception:
            pass


if __name__ == "__main__":
    uc.loop().run_until_complete(main())
