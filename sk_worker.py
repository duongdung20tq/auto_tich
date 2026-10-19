"""Skilljar course worker: enroll + visit all lessons for a list of slugs.
Usage: python sk_worker.py <worker_id> <slug1,slug2,...>   (slug or slug@MOD@REM)"""
import sys, time, re, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
from playwright.sync_api import sync_playwright

CDP = os.environ.get("CDP_URL", "http://127.0.0.1:9222")
BASE = "https://anthropic.skilljar.com"
wid = sys.argv[1]
slugs = [s for s in sys.argv[2].split(",") if s]

def log(m): print(f"[W{wid}] {m}")

def click_text(page, names, timeout=4000):
    for nm in names:
        for role in ("button", "link"):
            try:
                el = page.get_by_role(role, name=nm, exact=False)
                if el.count(): el.first.click(timeout=timeout); return nm
            except Exception: pass
        try:
            el = page.get_by_text(nm, exact=False)
            if el.count(): el.first.click(timeout=timeout); return nm
        except Exception: pass
    return None

def lesson_links(page, slug):
    return page.evaluate("""(slug)=>{
      const out=[]; const seen=new Set();
      document.querySelectorAll('a[href]').forEach(a=>{
        const h=a.getAttribute('href')||'';
        const m=h.match(new RegExp('^/'+slug+'/(\\\\d+)'));
        if(!m) return; if(seen.has(h)) return; seen.add(h);
        const li=a.closest('li,div')||a;
        const cls=(a.className||'')+' '+(li.className||'');
        const complete=/complete/i.test(cls) || !!li.querySelector('.lesson-complete,.complete,[class*=complete]');
        out.push({href:h, txt:(a.innerText||'').replace(/\\s+/g,' ').trim().slice(0,60), complete});
      });
      return out;
    }""", slug)

def progress(page):
    body = " ".join(page.evaluate("()=>document.body.innerText").split())
    m = re.search(r"(\d+)\s+of\s+(\d+)\s+lessons completed\s*\((\d+)%\)", body)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(CDP)
    page = b.contexts[0].new_page()
    for token in slugs:
        parts = token.split("@")
        slug = parts[0]
        mod = int(parts[1]) if len(parts) > 2 else 1
        rem = int(parts[2]) if len(parts) > 2 else 0
        try:
            page.goto(f"{BASE}/{slug}", wait_until="domcontentloaded", timeout=45000); time.sleep(2.5)
            e = click_text(page, ["Enroll in Course", "Enroll", "Register | FREE", "Register"])
            if e: log(f"{slug}: enrolled ('{e}')"); time.sleep(3)
            elif rem != 0: time.sleep(4)
            page.goto(f"{BASE}/{slug}", wait_until="domcontentloaded", timeout=45000); time.sleep(2)
            links = lesson_links(page, slug)
            links = [L for i, L in enumerate(links) if i % mod == rem]
            log(f"{slug}[{rem}/{mod}]: {len(links)} lesson links; progress={progress(page)}")
            for idx, L in enumerate(links, 1):
                url = BASE + L["href"]
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=45000); time.sleep(1.5)
                except Exception:
                    try: page.goto(url, wait_until="domcontentloaded", timeout=45000); time.sleep(1.5)
                    except Exception: log(f"{slug}: FAIL {L['txt'][:35]}")
            page.goto(f"{BASE}/{slug}", wait_until="domcontentloaded", timeout=45000); time.sleep(2)
            log(f"{slug}: AFTER progress={progress(page)}")
        except Exception as ex:
            log(f"{slug}: ERROR {type(ex).__name__}: {ex}")
    log("WORKER DONE")
