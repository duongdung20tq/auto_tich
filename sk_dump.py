"""Dump all questions+options of a Skilljar quiz, reusing sk_solve's proven
flush+restart+advance machinery. Usage: python sk_dump.py <slug> <lesson_url>"""
import sys, time, re, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
from playwright.sync_api import sync_playwright

CDP = os.environ.get("CDP_URL", "http://127.0.0.1:9222")
slug = sys.argv[1]; url = sys.argv[2]

def click_exact(page, name, timeout=5000):
    for role in ("button", "link"):
        try:
            el = page.get_by_role(role, name=name, exact=True)
            if el.count(): el.first.click(timeout=timeout); return True
        except Exception: pass
    try:
        el = page.get_by_text(name, exact=True)
        if el.count(): el.first.click(timeout=timeout); return True
    except Exception: pass
    return False

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(CDP)
    page = [q for c in b.contexts for q in c.pages if "skilljar" in q.url][0]
    page.goto(url, wait_until="domcontentloaded", timeout=45000); time.sleep(3)
    page.bring_to_front()
    for _ in range(18):
        bt = " ".join(page.evaluate("()=>document.body?document.body.innerText:''").split())
        if re.search(r"Your score|have passed|did not pass", bt): break
        nr = page.locator("input[type=radio]").count()
        if nr > 0:
            try: page.locator("input[type=radio]").last.check(timeout=3000)
            except Exception: pass
            time.sleep(0.4)
            if not (click_exact(page, "Next Question", 3000) or click_exact(page, "Submit", 3000) or click_exact(page, "Complete", 3000)): break
        else:
            try: page.evaluate("()=>document.querySelectorAll('textarea').forEach(t=>{if(!t.value){t.value='Great!';t.dispatchEvent(new Event('input',{bubbles:true}));t.dispatchEvent(new Event('change',{bubbles:true}));}})")
            except Exception: pass
            if not (click_exact(page, "Submit", 3000) or click_exact(page, "Complete", 3000) or click_exact(page, "Next Question", 3000)): break
        time.sleep(1.2)
    click_exact(page, "Take this again"); time.sleep(2.5)
    for _ in range(6):
        if click_exact(page, "Start"): break
        time.sleep(1.5)
    time.sleep(2)
    for _ in range(12):
        if page.locator("input[type=radio]").count() > 0: break
        time.sleep(1)
    seen = -1
    for step in range(45):
        nr = page.evaluate("()=>document.querySelectorAll('input[type=radio]').length")
        if nr == 0:
            body = " ".join(page.evaluate("()=>document.body.innerText").split())
            if re.search(r"Your score|have passed|did not pass", body): break
            click_exact(page, "Start"); time.sleep(1.2); continue
        data = page.evaluate("""()=>{
          const t=(document.body.innerText||'').replace(/\\s+/g,' ');
          const m=t.match(/Question (\\d+) of (\\d+)/);
          const q=(t.match(/Question \\d+ of \\d+(.*?)(Previous|Next)/)||[])[1]||'';
          const labs=[...document.querySelectorAll('label')].filter(l=>l.querySelector('input[type=radio]'))
            .map(l=>(l.innerText||'').replace(/\\s+/g,' ').trim());
          return {n:m?+m[1]:-1, q:q.trim().slice(0,240), labs};
        }""")
        if data["n"] == seen:
            if not (click_exact(page, "Next Question") or click_exact(page, "Next") or click_exact(page, "Submit")): break
            time.sleep(1.1); continue
        seen = data["n"]
        print(f"Q{data['n']}: {data['q']}")
        for j, L in enumerate(data["labs"]):
            print(f"   {chr(65+j)}. {L}")
        # advance by selecting first option
        try: page.locator("input[type=radio]").first.check(timeout=3000)
        except Exception: pass
        time.sleep(0.4)
        if not (click_exact(page, "Next Question") or click_exact(page, "Submit") or click_exact(page, "Complete") or click_exact(page, "Next")): break
        time.sleep(1.1)
    print("DUMP DONE")
