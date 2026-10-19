"""Reliable daotao survey: reload + sidebar-click open, fill iframe#myFrame last-radio, submit.
Usage: python dsurvey.py <oid> <item>  (selects the daotao tab whose URL has oid)"""
import sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.sync_api import sync_playwright

oid, item = sys.argv[1], sys.argv[2]
TAB = int(sys.argv[3]) if len(sys.argv) > 3 else 0

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    dts = [q for c in b.contexts for q in c.pages if "daotao" in q.url]
    pg = next((q for q in dts if f"oid={oid}" in (q.url or "")), None) or (dts[TAB] if TAB < len(dts) else dts[0])
    pg.on("dialog", lambda d: d.accept())
    if f"oid={oid}" not in (pg.url or ""):
        pg.goto(f"https://daotao.fpt.com/Curriculum/User_ViewCourse?oid={oid}&mlid=1", wait_until="domcontentloaded"); time.sleep(6)
    opened = False
    for attempt in range(6):
        pg.reload(wait_until="domcontentloaded"); time.sleep(7)
        try:
            pg.wait_for_selector(f'.li-sub-menu-el[data-cur-id="{item}"]', timeout=10000)
            pg.evaluate("(id)=>{const el=[...document.querySelectorAll('.li-sub-menu-el')].find(e=>(e.getAttribute('data-cur-id')||'')===id);if(el)el.click();}", str(item))
        except Exception as e:
            print("click err", str(e)[:40]); continue
        time.sleep(7)
        fl = pg.frame_locator("iframe#myFrame")
        try:
            cnt = fl.locator("input[type=radio], input[type=checkbox], textarea").count()
        except Exception:
            cnt = 0
        if cnt > 0:
            opened = True; break
        print(f"  attempt {attempt+1}: survey inputs={cnt}")
    if not opened:
        print(f"{item}: FAILED open survey"); sys.exit(1)
    fl = pg.frame_locator("iframe#myFrame")
    fl.locator("body").evaluate(r"""(body)=>{const d=body.ownerDocument;
       const groups={}; d.querySelectorAll('input[type=radio]').forEach(i=>{(groups[i.name]=groups[i.name]||[]).push(i);});
       Object.values(groups).forEach(g=>{const pick=g[g.length-1]; pick.checked=true; pick.dispatchEvent(new Event('click',{bubbles:true})); pick.dispatchEvent(new Event('change',{bubbles:true}));});
       d.querySelectorAll('.check-answer').forEach(div=>{ const cbs=div.querySelectorAll('input[type=checkbox]'); if(cbs.length && ![...cbs].some(c=>c.checked)){ cbs[0].checked=true; cbs[0].dispatchEvent(new Event('click',{bubbles:true})); cbs[0].dispatchEvent(new Event('change',{bubbles:true})); } });
       d.querySelectorAll('textarea').forEach(t=>{t.value='Khóa học rất hữu ích và thực tế.'; t.dispatchEvent(new Event('change',{bubbles:true}));});
    }""")
    valid = fl.locator("body").evaluate("(body)=>{try{return body.ownerDocument.defaultView.AnswerSurveyValidate();}catch(e){return 'err '+e;}}")
    print("validate:", valid)
    fl.locator("body").evaluate("(body)=>{try{body.ownerDocument.defaultView.AnswerSurvey('SurveyDo');}catch(e){}}")
    time.sleep(2)
    r = fl.locator("body").evaluate(r"""(body)=>{const btn=[...body.ownerDocument.querySelectorAll('.bootbox .btn-primary')].find(e=>e.offsetParent!==null) || [...body.ownerDocument.querySelectorAll('.bootbox .btn')].pop(); if(btn){btn.click(); return 'clicked '+(btn.innerText||'').trim();} return 'no btn';}""")
    print("confirm:", r)
    time.sleep(3)
    pg.reload(wait_until="domcontentloaded"); time.sleep(3)
    res = pg.evaluate(r"""()=>{let d=0,t=0;document.querySelectorAll('.li-sub-menu-el').forEach(e=>{t++;const img=e.querySelector('.img-status-el img');if(img&&img.src.includes('dahoc'))d++;});return d+'/'+t;}""")
    print(f"oid {oid}: {res} done")
