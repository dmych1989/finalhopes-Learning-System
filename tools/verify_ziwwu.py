import sys
from playwright.sync_api import sync_playwright

EDGE = r"C:/Program Files (x86)/Microsoft/EdgeCore/150.0.4078.105/msedge.exe"
URL = "http://127.0.0.1:8000/renji"

errs = []
def on_console(msg):
    if msg.type == "error": errs.append("CONSOLE: " + msg.text)
def on_pageerror(e):
    errs.append("PAGE: " + str(e))

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EDGE, args=["--no-sandbox"])
    pg = b.new_page()
    pg.on("console", on_console)
    pg.on("pageerror", on_pageerror)
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_selector("#boardTabs .board-tab")

    # click 子午流注 board tab (no dropdown expected)
    clicked = False
    for t in pg.query_selector_all("#boardTabs .board-tab"):
        if "子午流注" in (t.inner_text() or ""):
            t.click(); clicked = True; break
    assert clicked, "子午流注 tab not found"
    pg.wait_for_selector("#zwNajia table", timeout=8000)

    # no sub dropdown: there should be no sub menu for this board
    has_submenu = pg.eval_on_selector_all("#subTabs .sub-tab, .sub-list .sub-tab", "els => els.length")
    print("submenu tabs:", has_submenu)

    # tables row counts
    n_najia = pg.eval_on_selector("#zwNajia table tbody", "tb => tb.querySelectorAll('tr').length")
    n_nazi = pg.eval_on_selector("#zwNazi table tbody", "tb => tb.querySelectorAll('tr').length")
    print("najia rows:", n_najia, "nazi rows:", n_nazi)

    # 干支 hint + sizhu + current result
    gz = pg.eval_on_selector("#zwGZ", "e => e.textContent")
    sizhu = pg.eval_on_selector("#zwSizhu", "e => e.innerText.replace(/\\n/g,' ')")
    cur = pg.eval_on_selector("#zwCurBd", "e => e.innerText.replace(/\\n/g,' ')")
    print("GZ:", gz)
    print("SIZHU:", sizhu)
    print("CUR:", cur)

    # current highlighted rows (should be exactly 1 in each table)
    cur_najia = pg.eval_on_selector_all("#zwNajia table tr.cur", "els => els.map(e=>e.getAttribute('data-h'))")
    cur_nazi_key = pg.eval_on_selector_all("#zwNazi table tr.cur", "els => els.map(e=>e.getAttribute('data-k'))")
    print("cur najia h:", cur_najia, "cur nazi key:", cur_nazi_key)

    # change hour to 20 (戌时) -> assert highlight + result changes
    pg.eval_on_selector("#zwH", "s => { s.value='20'; s.dispatchEvent(new Event('change',{bubbles:true})); }")
    pg.wait_for_timeout(400)
    gz2 = pg.eval_on_selector("#zwGZ", "e => e.textContent")
    cur2 = pg.eval_on_selector("#zwCurBd", "e => e.innerText.replace(/\\n/g,' ')")
    cur_nazi_key2 = pg.eval_on_selector_all("#zwNazi table tr.cur", "els => els.map(e=>e.getAttribute('data-k'))")
    print("GZ2:", gz2)
    print("CUR2:", cur2)
    print("cur nazi key2:", cur_nazi_key2)

    pg.screenshot(path="tools/ziwwu_verify.png", full_page=True)

    # assertions
    ok = (has_submenu == 0 and n_najia == 12 and n_nazi == 120
          and gz and "日" in gz and "时" in gz
          and len(cur_najia) == 1 and len(cur_nazi_key) == 1
          and cur_nazi_key and cur_nazi_key2 and cur_nazi_key != cur_nazi_key2
          and cur != cur2 and not errs)
    print("ERRORS:", errs)
    print("RESULT:", "PASS" if ok else "FAIL")
    b.close()
    sys.exit(0 if ok else 1)
