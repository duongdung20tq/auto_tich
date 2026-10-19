"""Check completion % for a list of course slugs. Usage: python sweep.py <slug1,slug2,...>"""
import sys, time, re, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
from playwright.sync_api import sync_playwright
CDP = os.environ.get("CDP_URL", "http://127.0.0.1:9222")
slugs = sys.argv[1].split(",")
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(CDP)
    pg = b.contexts[0].new_page()
    for slug in slugs:
        try:
            pg.goto(f"https://anthropic.skilljar.com/{slug}", wait_until="domcontentloaded", timeout=45000); time.sleep(2.2)
            body = " ".join((pg.evaluate("()=>document.body?document.body.innerText:''") or "").split())
            m = re.search(r"(\d+) of (\d+) lessons completed \((\d+)%\)", body)
            cert = "CERT" if re.search(r"verify\.skilljar\.com|Download as PDF|Certificate", body) else ""
            flag = "" if (m and m.group(3) == "100") else "  <<<"
            print(f"{slug}: {m.group(0) if m else 'NO-PROGRESS'} {cert}{flag}")
        except Exception as e:
            print(f"{slug}: ERR {type(e).__name__}")
    pg.close()
