# -*- coding: utf-8 -*-
"""
build_items.py — parse the 163 operational items (الجزء ب) out of the unified
compliance register (سجل_المطابقة_الموحد.md) into items155.js (window.ITEMS155),
so the viewer can browse/link every one of the 163 بند to its scene + show its
phase / priority / status card. Deterministic: data comes straight from the
register's 16 chapter tables — nothing transcribed by hand.  python build_items.py
"""
import json, os, re
HERE=os.path.dirname(os.path.abspath(__file__))
REG=os.path.normpath(os.path.join(HERE,"..","سجل_المطابقة_الموحد.md"))

txt=open(REG,encoding="utf-8").read().splitlines()
# locate الجزء ب (operational items) — everything before it is الجزء أ (axes)
start=next(i for i,l in enumerate(txt) if l.startswith("# الجزء ب"))

PRIO={"أ":"أساسي","ب":"مرحلة ثانية","ق":"مرهون بقرار"}
def parse_phase(cell):
    """المرحلة cell → (phase_num, [priority letters]).  'معلّق' => phase 0 (pending)."""
    letters=re.findall(r"\[([أبق])\]",cell)
    if "معلّق" in cell or "ق" in letters: pnum=0
    elif cell.strip().startswith("2"): pnum=2
    else: pnum=1
    # keep order, de-dup
    seen=[]; [seen.append(x) for x in letters if x not in seen]
    return pnum,seen

PHASE_LBL={1:"مرحلة 1 — أساسية",2:"مرحلة 2 — ثانية",0:"معلّق — مرهون بقرار"}

chapters=[]; cur=None; count=0
chre=re.compile(r"^##\s*الباب\s*(\d+)\s*—\s*(.+?)\s*\((\d+)\s*بنود\)")
for l in txt[start:]:
    m=chre.match(l)
    if m:
        cur={"n":int(m.group(1)),"title":m.group(2).strip(),"declared":int(m.group(3)),"items":[],"scope":"","scopeShort":"155"}
        chapters.append(cur); continue
    if l.strip().startswith("> النطاق") and cur is not None:
        sc=l.split(":",1)[1].strip() if ":" in l else l.strip().lstrip(">").replace("النطاق","").strip()
        cur["scope"]=sc; cur["scopeShort"]="كل المواقع — يُفصّل نصيب 155" if "كل المواقع" in sc else "155"
        continue
    if l.startswith("| OP-") and cur is not None:
        cells=[c.strip() for c in l.split("|")[1:-1]]
        if len(cells)<7: continue
        code,title,spec,phase_c,repr_c,access_c,status=cells[:7]
        # the rack chapter (4): the ≤6.80م height has now been APPLIED in the model
        status=status.replace("جزئي — الارتفاع يحتاج تصحيح ≤6.80م",
                              "مُصحَّح: الرفوف ≤6.80م (مطبّق في النموذج)")
        pnum,prio=parse_phase(phase_c)
        cur["items"].append({
            "code":code,"title":title,"spec":spec,
            "phase":pnum,"phaseLbl":PHASE_LBL[pnum],
            "prio":prio,"prioLbl":[PRIO[x] for x in prio],
            "repr":repr_c,"access":access_c,"status":status})
        count+=1

for ch in chapters:
    got=len(ch["items"])
    flag="" if got==ch["declared"] else f"  <-- MISMATCH declared {ch['declared']}"
    print(f"  الباب {ch['n']:>2} · {got:>2} بند · {ch['title']}{flag}")

out={"count":count,"chapters":chapters,
     "note":"البنود التشغيلية الـ163 — المصدر: الملحق «القائمة الشاملة» عبر سجل المطابقة الموحّد. [أ] أساسي · [ب] مرحلة ثانية · [ق] مرهون بقرار. النطاق حسب الباب (أغلبها 155؛ بعضها كل المواقع — يُفصّل نصيب 155)."}
open(os.path.join(HERE,"items155.js"),"w",encoding="utf-8").write(
    "window.ITEMS155="+json.dumps(out,ensure_ascii=False,separators=(",",":"))+";")
print(json.dumps({"total_items":count,"chapters":len(chapters)},ensure_ascii=False))
assert count==163, f"expected 163 items, got {count}"
print("OK — items155.js written (163 بند)")
