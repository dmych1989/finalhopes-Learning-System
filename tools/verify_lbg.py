# -*- coding: utf-8 -*-
"""灵龟八法整页端到端验证（无头 Edge）。"""
import sys
from playwright.sync_api import sync_playwright

EDGE = r"C:/Program Files (x86)/Microsoft/EdgeCore/150.0.4078.105/msedge.exe"
URL = "http://127.0.0.1:8000/renji"

errs = []
def on_console(m):
    if m.type == "error": errs.append("CONSOLE: " + m.text)
def on_page(e):
    errs.append("PAGE: " + str(e))

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=EDGE, args=["--no-sandbox"])
        pg = b.new_page()
        pg.on("console", on_console)
        pg.on("pageerror", on_page)
        pg.goto(URL, wait_until="networkidle")
        pg.wait_for_selector("#boardTabs .board-tab")
        # 点击 灵龟八法
        for t in pg.query_selector_all("#boardTabs .board-tab"):
            if "灵龟八法" in (t.inner_text() or ""):
                t.click(); break
        pg.wait_for_selector("#lbgDial svg", timeout=8000)
        pg.wait_for_selector("#lbgSizhu")
        pg.wait_for_selector("#lbgYq")
        pg.wait_for_selector("#lbgTable table")

        # 四柱块
        sz = pg.eval_on_selector("#lbgSizhu", "el => el.innerText")
        # 3 结果卡标题
        cards = pg.eval_on_selector_all(".lbg-card-ttl", "els => els.map(e=>e.textContent)")
        # 圆盘元素计数
        dial = pg.eval_on_selector("#lbgDial svg", """svg => {
            const texts = [...svg.querySelectorAll('text')].map(t=>t.textContent);
            const GUA = ['乾','坤','兑','艮','离','坎','巽','震'];
            const SYM = ['☰','☷','☱','☶','☲','☵','☴','☳'];
            return {
                hourNums: texts.filter(t=>/^\\d+$/.test(t)).length,
                shichen: texts.filter(t=>['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'].includes(t)).length,
                jing: texts.filter(t=>['胆','肝','肺','大肠','胃','脾','心','小肠','膀胱','肾','心包','三焦'].includes(t)).length,
                gua: texts.filter(t=>GUA.some(g=>t.includes(g))).length,
                guaSym: texts.filter(t=>SYM.some(s=>t.includes(s))).length,
                acs: texts.filter(t=>['公孙','内关','后溪','申脉','足临泣','外关','列缺','照海'].includes(t)).length,
                paths: svg.querySelectorAll('path').length,
                circles: svg.querySelectorAll('circle').length,
                lines: svg.querySelectorAll('line').length,
                hasKai: texts.some(t=>t.startsWith('开穴'))
            };
        }""")
        # 五运六气
        yq = pg.eval_on_selector_all("#lbgYq .lbg-v", "els => els.map(e=>e.textContent)")
        # 万年历
        calCells = pg.eval_on_selector_all("#lbgCal .lbg-cal-c", "els => els.length")
        calTerm = pg.eval_on_selector_all("#lbgCal .lbg-cal-c.term", "els => els.length")
        # 灵龟八法表
        tblRows = pg.eval_on_selector_all("#lbgTable tbody tr", "els => els.length")
        tblCols = pg.eval_on_selector_all("#lbgTable thead th", "els => els.length")

        # 改时间 -> 开穴刷新
        pg.select_option("#lbgH", "8")  # 申时 15-17
        pg.wait_for_timeout(400)
        kai1 = pg.eval_on_selector("#lbgDial svg", "svg => [...svg.querySelectorAll('text')].map(t=>t.textContent).find(t=>t.startsWith('开穴'))")
        pg.select_option("#lbgH", "20")  # 戌时 19-21
        pg.wait_for_timeout(400)
        kai2 = pg.eval_on_selector("#lbgDial svg", "svg => [...svg.querySelectorAll('text')].map(t=>t.textContent).find(t=>t.startsWith('开穴'))")

        print("== 四柱 ==")
        print(sz.replace("\n", " | "))
        print("== 结果卡 ==")
        print(cards)
        print("== 圆盘 ==")
        print(dial)
        print("== 五运六气 ==")
        print(yq)
        print("== 万年历 cells=%d term=%d ==" % (calCells, calTerm))
        print("== 灵龟八法表 rows=%d cols=%d ==" % (tblRows, tblCols))
        print("== 开穴刷新 ==", kai1, "->", kai2)

        ok = (all([sz, cards, dial["hourNums"]>=24, dial["shichen"]==12, dial["jing"]==12,
                   dial["gua"]==8, dial["guaSym"]==8, dial["acs"]==8, dial["paths"]==8, dial["circles"]>=10,
                   dial["lines"]>=1, dial["hasKai"], len(yq)==6, calCells>28, tblRows==60, tblCols==13])
             and kai1 != kai2 and not errs)
        print("== ERRORS ==", errs)
        print("VERIFY", "PASS" if ok else "FAIL")
        pg.screenshot(path="tools/lbg_verify.png", full_page=True)
        b.close()
        sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
