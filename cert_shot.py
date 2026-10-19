"""Screenshot Skilljar certificates for a set of completed courses.
Usage: python cert_shot.py <out_folder> <slug1,slug2,...>
For each slug: open course page -> follow 'View certificate' (verify.skilljar.com)
-> full-page screenshot into <out_folder>/<slug>.png. Falls back to the
'Certificate of completion' lesson page if no verify link is present."""
import sys, time, os, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
from playwright.sync_api import sync_playwright

CDP = os.environ.get("CDP_URL", "http://127.0.0.1:9222")
BASE = "https://anthropic.skilljar.com"
out = sys.argv[1]
slugs = [s for s in sys.argv[2].split(",") if s]
os.makedirs(out, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(CDP)
    pg = b.contexts[0].new_page()
    for slug in slugs:
        try:
            pg.goto(f"{BASE}/{slug}", wait_until="domcontentloaded", timeout=45000); time.sleep(2.2)
            info = pg.evaluate("""()=>{
              const a=[...document.querySelectorAll('a')].find(e=>/verify\\.skilljar\\.com/.test(e.getAttribute('href')||''));
              const cert=[...document.querySelectorAll('a')].find(e=>/certificate of completion/i.test(e.innerText||''));
              return {verify:a?a.getAttribute('href'):'', certhref:cert?cert.getAttribute('href'):''};
            }""")
            target = info["verify"] or (BASE + info["certhref"] if info["certhref"] else "")
            if not target:
                print(f"{slug}: NO CERT LINK"); continue
            pg.goto(target, wait_until="domcontentloaded", timeout=45000); time.sleep(3)
            path = os.path.join(out, f"{slug}.png")
            pg.screenshot(path=path, full_page=True)
            sz = os.path.getsize(path)
            print(f"{slug}: saved {path} ({sz} bytes) <- {target}")
        except Exception as e:
            print(f"{slug}: ERR {type(e).__name__}: {e}")
    pg.close()
