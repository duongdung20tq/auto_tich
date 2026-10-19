"""FPT eLearning (daotao.fpt.com) course automation via Chrome CDP.

Chrome must already be running with --remote-debugging-port=9222 and logged in,
with the course page open (Curriculum/User_ViewCourse?oid=...).

Commands:
  python fpt_course.py items          - list all curriculum items (id, type, title)
  python fpt_course.py video <id>     - load a video/audio lesson and mark it fully watched
  python fpt_course.py videos-all     - auto-complete every video/audio lesson in the course
  python fpt_course.py load <id>      - just load an item (for docs/quiz/survey) + save
  python fpt_course.py state          - dump progress percent + current lesson fields
"""
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

import os
CDP = os.environ.get("CDP_URL", "http://127.0.0.1:9222")


def get_page(b):
    dts = [pg for c in b.contexts for pg in c.pages if "daotao.fpt.com" in pg.url]
    if not dts:
        raise SystemExit("FPT course page not found in debug Chrome.")
    oid = os.environ.get("DAOTAO_OID")
    if oid:
        for pg in dts:
            if f"oid={oid}" in (pg.url or ""):
                return pg
    tab = int(os.environ.get("DAOTAO_TAB", "0"))
    return dts[tab] if tab < len(dts) else dts[0]


def list_items(pg):
    return pg.evaluate(
        """() => {
        const out = [];
        document.querySelectorAll('.li-sub-menu-el').forEach(e => {
            const oc = e.getAttribute('onclick') || '';
            const m = oc.match(/LoadViewCur\\((\\d+)\\)/);
            const id = m ? m[1] : (e.getAttribute('data-cur-id') || '');
            const txt = (e.innerText || '').replace(/\\s+/g, ' ').trim();
            if (id) out.push({ id: id, txt: txt.slice(0, 70) });
        });
        return out;
    }"""
    )


def load_item(pg, item_id):
    pg.evaluate(
        "(id) => { LoadViewCur(parseInt(id)); if(typeof loadProgessBar==='function') loadProgessBar(); }",
        str(item_id),
    )


def mark_video(pg, item_id):
    """Load a video/audio lesson, set watched time = full duration, save to server."""
    load_item(pg, item_id)
    # wait for the player + hidden fields to populate
    dur = 0
    for _ in range(20):
        time.sleep(0.5)
        dur = pg.evaluate(
            """() => {
            let d = 0;
            try { d = Math.round(videojs('myVideo').duration()); } catch(e){}
            if (!d || isNaN(d)) {
                const v = document.querySelector('video');
                if (v && v.duration && !isNaN(v.duration)) d = Math.round(v.duration);
            }
            if (!d || isNaN(d)) {
                const t = document.getElementById('totaltime');
                if (t && t.value) d = Math.round(parseFloat(t.value));
            }
            return d || 0;
        }"""
        )
        if dur and dur > 0:
            break
    ctype = pg.evaluate("() => (document.getElementById('currentType')||{}).value")
    res = pg.evaluate(
        """(dur) => {
        const tp = document.getElementById('timeplay');
        const tt = document.getElementById('totaltime');
        const ct = document.getElementById('cur_time');
        if (tt && (!tt.value || parseInt(tt.value)===0)) tt.value = dur;
        if (tp) tp.value = (tt && tt.value) ? tt.value : dur;
        if (ct) ct.value = (tt && tt.value) ? tt.value : dur;
        let msg = 'ok';
        try { Learn_LogTime(); } catch(e){ msg = 'LogTime:'+e; }
        try { Learn_LogSave(); } catch(e){ msg = 'LogSave:'+e; }
        return { msg, timeplay: tp?tp.value:null, totaltime: tt?tt.value:null };
    }""",
        dur,
    )
    print(f"[{item_id}] type={ctype} dur={dur} -> {res}")
    return res


def _find_frame(pg, needle, tries=25):
    for _ in range(tries):
        for f in pg.frames:
            if needle in (f.url or ""):
                return f
        time.sleep(1)
    return None


def exam_open(pg, item_id):
    """Load an exam item, click 'Vào thi'/'Thi lại', dump questions with input ids."""
    load_item(pg, item_id)
    info = None
    for _ in range(4):
        fr = _find_frame(pg, "ViewExam")
        if not fr:
            print("NO ViewExam frame"); return
        time.sleep(2)
        try:
            info = " ".join(fr.locator("body").inner_text().split())
            break
        except Exception:
            continue  # frame reloaded mid-read; find it again
    if info is None:
        print("could not read ViewExam frame"); return
    print("INFO:", info[:300])
    clicked = None
    for name in ("Tiếp tục thi", "Vào thi", "Thi lại"):
        btn = fr.get_by_text(name, exact=True)
        if btn.count():
            btn.first.click()
            clicked = name
            break
    print("clicked:", clicked)
    # a confirm modal (bootbox or plain OK button) may appear before the exam loads
    qf = _find_frame(pg, "questiontest", tries=8)
    if not qf:
        for scope in (fr, pg):
            try:
                ok = scope.get_by_role("button", name="OK")
                if ok.count():
                    ok.first.click()
                    print("confirmed OK modal")
                    break
            except Exception:
                continue
    qf = _find_frame(pg, "questiontest", tries=45)
    if not qf:
        print("NO questiontest frame"); return
    time.sleep(2)
    for _ in range(3):
        try:
            dump_questions(qf)
            return
        except Exception:
            time.sleep(2)
            qf = _find_frame(pg, "questiontest", tries=10)


def dump_questions(qf):
    body = " ".join(qf.locator("body").inner_text().split())
    print("BODY:", body[:3500])
    res = qf.evaluate(
        """() => {
        const out = [];
        document.querySelectorAll("input[type=radio],input[type=checkbox]").forEach(i => {
            if (!i.name || !i.name.startsWith('a_')) return;
            const lab = i.closest('label') || document.querySelector("label[for='"+i.id+"']");
            out.push({q: i.name, id: i.id, t: i.type[0],
                      txt: (lab ? lab.innerText : '').replace(/\\s+/g,' ').trim().slice(0,90)});
        });
        return out;
    }"""
    )
    for r in res:
        print(f"{r['q']} {r['t']} {r['id']} | {r['txt']}")


def exam_answer(pg, ids):
    qf = _find_frame(pg, "questiontest", tries=5)
    if not qf:
        print("NO questiontest frame"); return
    res = qf.evaluate(
        """(ids) => {
        let n = 0;
        ids.forEach(id => {
            const el = document.getElementById(id);
            if (el) { el.checked = true;
                el.dispatchEvent(new Event('click',{bubbles:true}));
                el.dispatchEvent(new Event('change',{bubbles:true})); n++; }
        });
        const total = new Set(Array.from(
            document.querySelectorAll("input[type=radio]:checked,input[type=checkbox]:checked"))
            .filter(i => i.name && i.name.startsWith('a_')).map(i => i.name)).size;
        return {checked: n, answeredQuestions: total};
    }""",
        ids,
    )
    print(res)


def exam_submit(pg):
    qf = _find_frame(pg, "questiontest", tries=5)
    if not qf:
        print("NO questiontest frame"); return
    pg.on("dialog", lambda d: d.accept())
    btn = qf.get_by_text("Kết thúc bài thi")
    if not btn.count():
        print("no submit button"); return
    btn.first.click()
    time.sleep(1.5)
    ok = qf.get_by_role("button", name="OK")
    if not ok.count():
        ok = pg.get_by_role("button", name="OK")
    if ok.count():
        ok.first.click()
        print("confirmed OK")
    # result appears in a ViewTest frame
    rf = _find_frame(pg, "ViewTest", tries=15)
    if rf:
        time.sleep(1.5)
        print("RESULT:", " ".join(rf.locator("body").inner_text().split())[:300])
    else:
        print("no ViewTest frame; frames:", [f.url for f in pg.frames])


def state(pg):
    info = pg.evaluate(
        """() => {
        const g = id => { const e=document.getElementById(id); return e? e.value : null; };
        const body = document.body.innerText;
        const status = (body.match(/Trạng thái học[^\\n]*/) || [''])[0];
        return {
            courseId: g('currentCourseId'), curId: g('currentCurriculumId'),
            type: g('currentType'), timeplay: g('timeplay'), totaltime: g('totaltime'),
            status
        };
    }"""
    )
    print(info)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "items"
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(CDP)
        pg = get_page(b)
        if cmd == "items":
            for it in list_items(pg):
                print(it["id"], it["txt"])
        elif cmd == "state":
            state(pg)
        elif cmd == "load":
            load_item(pg, sys.argv[2])
            time.sleep(3)
            state(pg)
        elif cmd == "video":
            mark_video(pg, sys.argv[2])
        elif cmd == "exam-open":
            exam_open(pg, sys.argv[2])
        elif cmd == "exam-questions":
            qf = _find_frame(pg, "questiontest", tries=10)
            if qf:
                dump_questions(qf)
            else:
                print("NO questiontest frame")
        elif cmd == "exam-answer":
            exam_answer(pg, sys.argv[2].split(","))
        elif cmd == "exam-submit":
            exam_submit(pg)
        elif cmd == "auto-all":
            # Load every item, detect type, complete non-interactive ones.
            items = list_items(pg)
            print(f"{len(items)} items total")
            interactive = []
            for it in items:
                iid = it["id"]
                load_item(pg, iid)
                time.sleep(2.2)
                ctype = pg.evaluate("() => (document.getElementById('currentType')||{}).value")
                if ctype in ("1", "2"):
                    mark_video(pg, iid)
                elif ctype in ("3", "4", "5", "7", "8"):
                    r = pg.evaluate("() => { try { Learn_Save(); return 'ok'; } catch(e){ return 'err '+e; } }")
                    print(f"[{iid}] type={ctype} doc/html -> {r}")
                elif ctype in ("6", "9", "11"):
                    interactive.append((iid, ctype, it["txt"]))
                    print(f"[{iid}] type={ctype} INTERACTIVE (needs answers): {it['txt']}")
                else:
                    print(f"[{iid}] type={ctype} UNKNOWN: {it['txt']}")
                time.sleep(0.6)
            print("--- interactive items to handle manually ---")
            for iid, ct, txt in interactive:
                print(iid, ct, txt)
        elif cmd == "videos-all":
            items = list_items(pg)
            print(f"{len(items)} items total")
            for it in items:
                low = it["txt"].lower()
                # skip documents (Tài liệu), quiz (Kiểm tra), survey (Khảo sát)
                if any(k in low for k in ("tài liệu", "kiểm tra", "khảo sát")):
                    print(f"[skip] {it['id']} {it['txt']}")
                    continue
                mark_video(pg, it["id"])
                time.sleep(1)
            print("DONE videos")
        else:
            print(__doc__)


if __name__ == "__main__":
    main()
