"""List all lesson ids+titles for a course. Usage: python lessons.py <slug> [enterLessonId]"""
import sys, time, re, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
from playwright.sync_api import sync_playwright
CDP = os.environ.get("CDP_URL", "http://127.0.0.1:9222")
slug = sys.argv[1]
enter = sys.argv[2] if len(sys.argv) > 2 else None
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(CDP)
    pg = b.contexts[0].new_page()
    target = f"https://anthropic.skilljar.com/{slug}/{enter}" if enter else f"https://anthropic.skilljar.com/{slug}"
    pg.goto(target, wait_until="domcontentloaded", timeout=45000); time.sleep(3)
    items = pg.evaluate(
        "(slug)=>{const o=[];const seen=new Set();"
        "document.querySelectorAll('a[href]').forEach(a=>{"
        "const h=a.getAttribute('href')||'';"
        "const m=h.match(new RegExp('/'+slug+'/([0-9]+)'));"
        "if(!m)return; if(seen.has(m[1]))return; seen.add(m[1]);"
        "let t=(a.innerText||'').replace(/\\s+/g,' ').trim();"
        "if(!t){const li=a.closest('li,div'); t=li?(li.innerText||'').replace(/\\s+/g,' ').trim():'';}"
        "o.push(m[1]+' | '+t.slice(0,60));});return o;}", slug)
    print("TOTAL", len(items))
    for it in items:
        print(it)
    pg.close()
