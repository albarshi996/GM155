# -*- coding: utf-8 -*-
"""
build_site.py — Abuhadi 155 CONCEPT model, re-laid out to MATCH the actual engineering
site plan NAS-8155-ARC (doc BFP-SCM-ENG-2026-001, §1.2): the site is split into FIVE
operational zones in an irregular plot, NOT a rectangular grid:
  Z1 الإدارة والخدمات  — NW corner (admin + service/housing + courtyard, on the main road)
  Z2 المواقف والبوابة  — west, south of Z1 (parking + truck waiting + SW gate)
  Z3 الثلاجات          — east of Z1 (cold complex 80×65, 12 rooms, 8 docks)
  Z4 المستودعات الرئيسية — centre & north: E-5 (100×35) on top + 3 small (50×20, west col)
                          + 3 long (110×20, east col)                       = 13,450 m²
  Z5 المستودعات الجنوبية — south strip along the length: 2 long (110×20) + 1 small = 5,400 m²
As-built from the drawings: ground-level doors + internal 5.50 m drive-through aisle (E-W).
Requirements shown as a distinct "proposed" layer (racking, Dock-Leveler ramps). HR families
+ team sizes per store. Heights: dry 6.80 m, cold 5.0 m. North = +Y, East = +X, up = +Z.
Sources (nothing dropped): NAS-8155-ARC site plan (5 zones), BFP-SCM-ENG-2026-001 (22 axes),
D3 cold racking (12 rooms, 4,632 pallets), HR-STF-001 (families + teams).  python build_site.py
"""
import json, os, math
HERE=os.path.dirname(os.path.abspath(__file__))

C={
 "asphalt":(0.30,0.31,0.33),"road":(0.22,0.23,0.25),"yard":(0.34,0.35,0.37),"apron":(0.74,0.74,0.72),
 "wall":(0.93,0.94,0.95),"wall2":(0.86,0.88,0.91),"roof":(0.29,0.41,0.60),"roof2":(0.23,0.33,0.50),
 "glass":(0.42,0.60,0.78),"upright":(0.11,0.28,0.60),"beam":(0.90,0.44,0.06),"pallet":(0.52,0.37,0.22),
 "load":(0.76,0.58,0.38),"load2":(0.80,0.64,0.45),"lane":(0.95,0.78,0.10),"cold":(0.86,0.91,0.96),
 "door":(0.25,0.70,0.45),"dockdoor":(0.90,0.55,0.12),"fork":(0.95,0.63,0.10),"forkdark":(0.15,0.15,0.17),
 "tank":(0.72,0.22,0.18),"gen":(0.40,0.42,0.45),"fuel":(0.25,0.45,0.35),"fence":(0.58,0.60,0.63),
 "cctv":(0.20,0.21,0.23),"canopy":(0.90,0.72,0.30),"office":(0.84,0.80,0.74),"gate":(0.75,0.55,0.20),
 "person":(0.20,0.35,0.55),"col":(0.80,0.80,0.82),"guard":(0.95,0.78,0.10),"truck":(0.94,0.95,0.97),
}
FAM={"غذائي جاف":(0.92,0.87,0.73),"مشروبات":(0.78,0.88,0.90),"ملابس":(0.87,0.80,0.90),
     "تغليف ومساند":(0.85,0.85,0.83),"غير غذائي":(0.89,0.82,0.73),"ألعاب ومدينة الألعاب":(0.80,0.90,0.86)}
# vivid sector/family colours for the facade sign bands (storage families serving HR sectors — تقرير التوظيف)
FAMV={"غذائي جاف":(0.90,0.64,0.18),"مشروبات":(0.18,0.54,0.82),"ملابس":(0.56,0.34,0.72),
      "تغليف ومساند":(0.42,0.46,0.52),"غير غذائي":(0.82,0.44,0.22),"ألعاب ومدينة الألعاب":(0.12,0.68,0.55)}
# zone accent colours (match the plan's zone key)
ZC={"Z1":(0.85,0.22,0.22),"Z2":(0.12,0.70,0.86),"Z3":(0.95,0.72,0.12),"Z4":(0.20,0.68,0.35),"Z5":(0.22,0.38,0.82)}

CONFIG={
 "site":[380.0,290.0],
 "wall_h":6.8,            # ارتفاع المخازن الجافة (فعلي)
 "aisle":5.5,             # ممر الشاحنات الداخلي (فعلي، أبواب أرضية)
 "cold":{"w":80.0,"l":65.0,"x":100.0,"y":68.0,"h":5.0},      # Z3 — شرق Z1 مباشرة
 # dry stores E-1..E-10 placed by the 5-zone site plan. ramp = proposed Dock-Leveler face (S/N).
 "wh":[
  # Z4 — long east column (110×20), stacked south→north
  {"id":"E-7","x":258,"y":64,"LX":110,"DY":20,"a":2200,"fam":"مشروبات","team":"5–7","det":False,"ramp":"S","zone":"Z4"},
  {"id":"E-6","x":258,"y":92,"LX":110,"DY":20,"a":2200,"fam":"غذائي جاف","team":"5–7","det":False,"ramp":"S","zone":"Z4"},
  {"id":"E-1","x":258,"y":120,"LX":110,"DY":20,"a":2200,"fam":"غذائي جاف","team":"5–7","det":False,"ramp":"S","zone":"Z4"},
  # Z4 — small west column (50×20), stacked south→north
  {"id":"E-4","x":196,"y":64,"LX":50,"DY":20,"a":1000,"fam":"تغليف ومساند","team":"3–4","det":False,"ramp":"S","zone":"Z4"},
  {"id":"E-3","x":196,"y":92,"LX":50,"DY":20,"a":1000,"fam":"ملابس","team":"3–4","det":False,"ramp":"S","zone":"Z4"},
  {"id":"E-2","x":196,"y":120,"LX":50,"DY":20,"a":1000,"fam":"مشروبات","team":"3–4","det":False,"ramp":"S","zone":"Z4"},
  # Z4 — E-5 the biggest, on top (north)
  {"id":"E-5","x":212,"y":150,"LX":100,"DY":35,"a":3500,"fam":"غذائي جاف","team":"7–9","det":True,"ramp":"S","zone":"Z4"},
  # Z5 — southern strip (110×20 ×2 + 50×20), ramp faces north toward the spine road
  {"id":"E-8","x":26,"y":22,"LX":110,"DY":20,"a":2200,"fam":"غذائي جاف","team":"5–7","det":False,"ramp":"N","zone":"Z5"},
  {"id":"E-9","x":150,"y":22,"LX":110,"DY":20,"a":2200,"fam":"ألعاب ومدينة الألعاب","team":"5–7","det":False,"ramp":"N","zone":"Z5"},
  {"id":"E-10","x":276,"y":22,"LX":50,"DY":20,"a":1000,"fam":"تغليف ومساند","team":"3–4","det":False,"ramp":"N","zone":"Z5"},
 ],
}

boxes=[]; WH_LIST=[]
def add(id,group,type,pos,size,color,label="",system="",state="concept",rot=0,meta=None):
    boxes.append({"id":id,"group":group,"type":type,
        "position_m":[round(pos[0],3),round(pos[1],3),round(pos[2],3)],
        "dimensions_m":[round(size[0],3),round(size[1],3),round(size[2],3)],
        "rotation":rot,"color":list(color),"label":label,"system":system,"state":state,
        **({} if not meta else {"meta":meta})})
def box(id,group,type,x,y,z,sx,sy,sz,color,**kw): add(id,group,type,[x,y,z],[sx,sy,sz],color,**kw)
def seg(idp,group,typ,A,B,thick,h,color,z=0.0,**kw):
    # an angled box running from point A to point B (rotation about its centre, around the up axis)
    dx,dy=B[0]-A[0],B[1]-A[1]; L=math.hypot(dx,dy); ang=math.degrees(math.atan2(dy,dx))
    mx,my=(A[0]+B[0])/2.0,(A[1]+B[1])/2.0
    box(idp,group,typ,mx-L/2.0,my-thick/2.0,z,L,thick,h,color,rot=round(ang,3),**kw)
def cyl(tag,group,cx,cy,z,dia,h,color,**kw):
    box(tag,group,"cylinder",cx-dia/2.0,cy-dia/2.0,z,dia,dia,h,color,meta={"cyl":True},**kw)

# ---- Brandzo workwear palette (BFP-SCM-UNI-2026-001) — role-differentiated ----
UNI={"charcoal":(0.239,0.255,0.282),"white":(0.95,0.95,0.95),"red":(0.882,0.106,0.133),
     "orange":(0.851,0.376,0.059),"lime":(0.843,0.871,0.157),"green":(0.184,0.655,0.341),
     "navy":(0.071,0.243,0.459),"blue":(0.118,0.353,0.659),"ctrlred":(0.769,0.063,0.090),
     "trouser":(0.22,0.23,0.26),"skin":(0.80,0.66,0.52),
     "hat_red":(0.882,0.106,0.133),"hat_yel":(0.957,0.761,0.051),"hat_grn":(0.184,0.655,0.341),
     "hat_blu":(0.118,0.353,0.659),"hat_wht":(0.93,0.93,0.95)}
# ---- realistic figures: articulated worker (role-coded) + forklift ----
def person(tag,x,y,body=None,accent=None,helmet=None,grp="ops"):
    body=UNI["charcoal"] if body is None else body
    helmet=UNI["hat_yel"] if helmet is None else helmet
    box(f"{tag}_ll",grp,"person",x+0.06,y,0,0.15,0.2,0.82,UNI["trouser"])            # legs
    box(f"{tag}_rl",grp,"person",x+0.28,y,0,0.15,0.2,0.82,UNI["trouser"])
    box(f"{tag}_to",grp,"person",x+0.02,y-0.02,0.82,0.47,0.26,0.52,body)             # body (charcoal field / white office)
    if accent: box(f"{tag}_ac",grp,"person",x+0.0,y-0.04,1.16,0.51,0.30,0.18,accent)  # ~20% functional colour (shoulders/back)
    box(f"{tag}_rm",grp,"person",x+0.30,y-0.03,1.0,0.1,0.06,0.09,UNI["red"])          # ~10% Brandzo red mark
    box(f"{tag}_hd",grp,"person",x+0.12,y+0.03,1.36,0.26,0.22,0.24,UNI["skin"])        # head
    box(f"{tag}_ht",grp,"person",x+0.11,y+0.02,1.58,0.28,0.24,0.11,helmet)            # helmet (movement permission)
def forklift(tag,x,y,load=False,grp="ops",z0=0.0):
    box(f"{tag}_bd",grp,"fork",x,y,0.12+z0,1.2,2.0,0.95,C["fork"])                    # chassis
    box(f"{tag}_cw",grp,"forkdark",x+0.05,y+1.55,0.12+z0,1.1,0.5,1.25,(0.20,0.21,0.24)) # counterweight
    box(f"{tag}_g1",grp,"col",x+0.12,y+0.35,1.05+z0,0.1,0.1,1.9,(0.22,0.22,0.24)); box(f"{tag}_g2",grp,"col",x+1.0,y+0.35,1.05+z0,0.1,0.1,1.9,(0.22,0.22,0.24))
    box(f"{tag}_gt",grp,"forkdark",x+0.08,y+0.28,2.9+z0,1.14,1.35,0.1,(0.22,0.22,0.24))  # overhead guard
    box(f"{tag}_m1",grp,"col",x+0.32,y-0.12,0+z0,0.12,0.14,3.0,(0.30,0.30,0.33)); box(f"{tag}_m2",grp,"col",x+0.78,y-0.12,0+z0,0.12,0.14,3.0,(0.30,0.30,0.33))  # mast
    box(f"{tag}_fk",grp,"forkdark",x+0.22,y-0.95,0.12+z0,0.72,0.95,0.1,(0.12,0.12,0.14))  # forks
    box(f"{tag}_st",grp,"forkdark",x+0.3,y+0.8,0.95+z0,0.6,0.5,0.45,(0.15,0.15,0.17))     # seat
    box(f"{tag}_dt",grp,"person",x+0.4,y+0.88,1.35+z0,0.4,0.35,0.5,UNI["lime"])           # operator — lime (equipment family)
    box(f"{tag}_dh",grp,"person",x+0.47,y+0.93,1.82+z0,0.24,0.22,0.22,UNI["skin"])
    box(f"{tag}_dhat",grp,"person",x+0.46,y+0.92,2.0+z0,0.26,0.24,0.1,UNI["hat_yel"])     # yellow helmet (equipment ops)
    if load: box(f"{tag}_ld",grp,"load",x+0.1,y-1.05,0.22+z0,1.0,1.0,1.1,C["load2"])

S=CONFIG["site"]; H=CONFIG["wall_h"]
# ---------------- GROUND / PERIMETER ----------------
# desert context plane + plot-shaped asphalt yard (bbox of the real plot)
box("desert","site","sand",-700,-700,-0.16,1600,1600,0.1,(0.62,0.58,0.49))
box("ground","site","ground",-6,0,-0.1,398,242,0.1,C["asphalt"],
    label="مخازن أبوهادي 155 — ~7 هكتار · 5 مناطق تشغيلية · 10 مخازن جافة (18,850م²) + مبرّد E-F (3,850م²)")
# real irregular plot boundary (NAS-8155): vertical west edge · triangular north apex over E-5 · angled east road
PLOT=[(4,6),(4,170),(14,212),(250,236),(360,176),(384,92),(360,6)]
for i in range(len(PLOT)):
    A=PLOT[i]; Bv=PLOT[(i+1)%len(PLOT)]
    if A==(360,6) and Bv==(4,6):   # leave a gate gap (x4–28) at the SW for the main entrance
        seg("fence_s","site","fence",A,(28,6),0.4,3.0,C["fence"],system="08 السور الفعلي + البوابة الجنوبية الغربية")
    else:
        seg(f"fence{i}","site","fence",A,Bv,0.4,3.0,C["fence"])
for vx,vy in PLOT:   # precast posts at the polygon corners
    box(f"post_{int(vx)}_{int(vy)}","site","col",vx-0.25,vy-0.25,0,0.5,0.5,3.4,(0.70,0.71,0.73))

# ---------------- ZONE MARKERS (match plan §1.2) ----------------
def zone_mark(z,x,y,w,d,label):
    col=ZC[z]; tt=0.6
    box(f"zb_{z}s","zone","lane",x,y,0.05,w,tt,0.03,col); box(f"zb_{z}n","zone","lane",x,y+d-tt,0.05,w,tt,0.03,col)
    box(f"zb_{z}w","zone","lane",x,y,0.05,tt,d,0.03,col); box(f"zb_{z}e","zone","lane",x+w-tt,y,0.05,tt,d,0.03,col)
    box(f"zf_{z}","zone","col",x+2.5,y+d-2.5,0,0.5,0.5,12.5,col,label=label)   # tall labeled zone pole (rises above buildings)
zone_mark("Z1",14,146,66,56,"Z1 · الإدارة والخدمات")
zone_mark("Z2",14,20,78,104,"Z2 · المواقف والبوابة")
zone_mark("Z3",96,62,92,78,"Z3 · الثلاجات E-F")
zone_mark("Z4",190,60,184,130,"Z4 · المستودعات الرئيسية")
zone_mark("Z5",20,18,314,30,"Z5 · المستودعات الجنوبية")

# ---------------- ROADS / CIRCULATION ----------------
box("road_w","site","road",10,18,0.03,10,186,0.04,C["road"],label="طريق المحيط الغربي")
box("road_spine","site","road",92,48,0.03,262,12,0.04,C["road"],label="الطريق الداخلي الرئيسي")
for i,ry in enumerate((84,112,140)):
    box(f"road_r{i}","site","road",188,ry,0.03,186,8,0.04,C["road"])   # E-W aisles between Z4 rows
box("road_c1","site","road",182,60,0.03,8,130,0.04,C["road"])          # N-S between Z3 and Z4
box("road_c2","site","road",248,60,0.03,10,132,0.04,C["road"])         # N-S between Z4 columns

# ---------------- Z2 — GATE · PARKING · TRUCK WAITING (SW / west) ----------------
box("z2_yard","site","yard",22,28,0.02,66,92,0.04,C["yard"],
    label="ساحة مواقف وانتظار الشاحنات — 73.46م",system="09 حركة المرور")
# SW site entrance + guard + scale + boom + ANPR
box("gate_road","site","road",6,0,0.02,16,26,0.04,C["road"])
box("gate_house","site","building",26,24,0,5,4,3.2,(0.82,0.78,0.70),label="البوابة الرئيسية — ميزان 60ط + ANPR",system="08 بوابة الأمن")
box("gate_boom","site","gate",14,20,1.0,0.3,6,0.3,C["gate"])
box("gate_cctv","site","cctv",24,20,0,0.25,0.25,6,C["cctv"],label="ANPR + PTZ",system="05 CCTV")
box("truckscale","site","concrete",10,28,0.05,12,4,0.2,C["apron"],label="ميزان البوابة 60ط + ANPR",system="08 ميزان البوابة")
box("driver","support","canopy",30,8,3.2,30,9,0.3,C["canopy"],label="انتظار السائقين المبرد",system="20 انتظار السائقين")

# ---------------- AS-BUILT DRY WAREHOUSE (ground doors + internal 5.5 m aisle) ----------------
def dry_warehouse(w):
    x,yy,LX,DY=w["x"],w["y"],w["LX"],w["DY"]; pre="WH"+w["id"]; det=w["det"]; tw=0.3
    fam=w["fam"]; fl=FAM.get(fam,(0.80,0.81,0.83)); rs=w.get("ramp","S")
    box(f"{pre}_floor",pre,"floor",x,yy,0,LX,DY,0.08,fl,
        label=f"{w['id']} · {LX}×{DY}م · {w['a']}م² · {fam} · فريق {w['team']}",system="10 تخزين جاف")
    box(f"{pre}_ws",pre,"wall",x,yy,0,LX,tw,H,C["wall"])
    box(f"{pre}_wn",pre,"wall",x,yy+DY-tw,0,LX,tw,H,C["wall"])
    dgap=5.0; dy0=yy+(DY-dgap)/2
    for wx,nm in [(x,"ww"),(x+LX-tw,"we")]:
        box(f"{pre}_{nm}a",pre,"wall",wx,yy,0,tw,(dy0-yy),H,C["wall"])
        box(f"{pre}_{nm}b",pre,"wall",wx,dy0+dgap,0,tw,(yy+DY-(dy0+dgap)),H,C["wall"])
    box(f"{pre}_dw",pre,"door",x-0.1,dy0,0,0.3,dgap,4.2,C["door"],system="04 باب أرضي (قائم)")
    box(f"{pre}_de",pre,"door",x+LX-0.2,dy0,0,0.3,dgap,4.2,C["door"])
    box(f"{pre}_roof1",pre,"roof",x,yy,H,LX,DY/2+0.2,0.3,C["roof"],meta={"hideable":True})
    box(f"{pre}_roof2",pre,"roof",x,yy+DY/2,H,LX,DY/2,0.3,C["roof2"],meta={"hideable":True})
    box(f"{pre}_ridge",pre,"roof",x,yy+DY/2-0.3,H+0.7,LX,0.6,0.3,C["roof2"],meta={"hideable":True})
    for sl in range(5):
        sxk=x+9+sl*((LX-18)/4)
        box(f"{pre}_sky{sl}",pre,"roof",sxk,yy+2.0,H+0.31,3.2,DY-4,0.06,(0.62,0.70,0.79),meta={"hideable":True})
    for v in range(max(1,int(LX//26))):
        box(f"{pre}_vnt{v}",pre,"roof",x+13+v*26,yy+DY/2-0.45,H+0.82,0.9,0.9,0.5,(0.68,0.70,0.74),meta={"hideable":True})
    al=CONFIG["aisle"]; ay=yy+(DY-al)/2
    box(f"{pre}_aisle",pre,"zonefloor",x+0.3,ay,0.05,LX-0.6,al,0.04,(0.80,0.80,0.82),
        label=("ممر شاحنات داخلي 5.50م — أبواب أرضية (قائم)" if det else ""),system="04 ممر داخلي قائم")
    box(f"{pre}_laneL",pre,"lane",x+0.3,ay+0.1,0.07,LX-0.6,0.18,0.02,C["lane"])
    box(f"{pre}_laneR",pre,"lane",x+0.3,ay+al-0.28,0.07,LX-0.6,0.18,0.02,C["lane"])
    for cxn in range(max(2,int(LX//22))):
        cx2=x+12+cxn*22
        box(f"{pre}_colA{cxn}",pre,"col",cx2,ay-0.5,0,0.4,0.4,H,C["col"])
        box(f"{pre}_colB{cxn}",pre,"col",cx2,ay+al+0.1,0,0.4,0.4,H,C["col"])
        box(f"{pre}_hbx{cxn}",pre,"light",cx2,ay+al/2,H-0.5,1.0,0.55,0.18,(1.0,0.95,0.80))
        box(f"{pre}_hbz{cxn}",pre,"light",cx2+11,ay+al/2,H-0.5,1.0,0.55,0.18,(1.0,0.95,0.80))   # intermediate high-bay (denser → brighter, even interior)
    def rackband(y0,depth):
        nb=int((LX-6)//2.8)
        for p in range(nb+1):
            box(f"{pre}_u{int(y0)}_{p}","proposed","rack_up",x+3+p*2.8,y0,0,0.1,0.1,6.0,C["upright"],state="proposed")
            box(f"{pre}_u{int(y0)}_{p}b","proposed","rack_up",x+3+p*2.8,y0+depth-0.1,0,0.1,0.1,6.0,C["upright"],state="proposed")
        for Lv in range(3):
            box(f"{pre}_bm{int(y0)}_{Lv}","proposed","rack_bm",x+3,y0,0.2+Lv*2.0,LX-6,depth,0.08,C["beam"],state="proposed")
        pals=[C["load"],C["load2"],(0.72,0.74,0.80),(0.86,0.85,0.80)]
        for p in range(nb):
            for Lv in range(3):                              # 3 full levels — stores معبأة بالبليت
                hv=(p*7+Lv*5+int(y0))%10
                if hv<1: continue                            # ~10% empty slots (realistic, not a solid wall)
                hz=1.4 if hv<7 else 0.95
                ld=pals[(p+Lv)%4]
                bx=x+3.1+p*2.8; bz=0.3+Lv*2.0
                box(f"{pre}_wb{int(y0)}_{p}_{Lv}","proposed","tree",bx,y0+0.12,bz,2.3,depth-0.24,0.13,(0.44,0.32,0.19),state="proposed")        # wood pallet base
                box(f"{pre}_pl{int(y0)}_{p}_{Lv}","proposed","load",bx+0.07,y0+0.18,bz+0.13,2.16,depth-0.36,hz-0.13,ld,state="proposed")         # wrapped cartons
    side=(DY-al)/2-0.6
    rackband(yy+0.4,side); rackband(ay+al+0.2,side)
    if det:
        box(f"{pre}_prop","proposed","label",x+LX/2,yy+1,6.5,8,6,0.1,fl,label="رفوف انتقائية مقترحة — المتطلبات (غير قائمة)")
        box(f"{pre}_wmo",pre,"building",x+1,yy+DY-7,2.4,10,6,0.3,(0.82,0.83,0.86),label="مكتب WMS")
        box(f"{pre}_wmg",pre,"glass",x+1,yy+DY-7,2.7,10,0.2,2.0,C["glass"])
        for k in range(3): box(f"{pre}_hb{k}",pre,"light",x+10+k*30,yy+DY/2,H-0.6,1.0,0.5,0.22,(1.0,0.96,0.72))
    # --- PROPOSED loading DOCK (المتطلبات §04 — الرامب الخارجي ومناطق التحميل): منصّة 1.20م · باب سريع 4×4.5م ·
    #     Dock Leveler ±300مم · 4 صدّامات/بوابة · Dock Shelter · كانوبي بوليكربونات · رامب وصول أرضي (ميلان ≤8%) · إشارة مرور ---
    rN=(rs=="N"); yf=(yy+DY) if rN else yy; Dp=5.0
    def yo(d1,d2): return ((yf+d1) if rN else (yf-d2)),(d2-d1)   # (ymin,size) for a box d1..d2 m outward from the face
    _m,_s=yo(0,Dp)
    box(f"{pre}_dock","proposed","concrete",x,_m,0,LX,_s,1.2,C["apron"],
        label=("منصّة التحميل المقترحة — ارتفاع 1.20م · باب سريع 4×4.5م · Dock Leveler ±300مم · أرضية R12 تتحمّل 8ط/م² (المتطلبات §04)" if det else ""),
        state="proposed",system="04 منصّة التحميل (مقترح)")
    _m,_s=yo(Dp-0.3,Dp); box(f"{pre}_edge","proposed","lane",x,_m,1.2,LX,_s,0.05,(0.95,0.78,0.10),state="proposed")   # edge safety stripe
    ndk=max(3,int(LX/22))
    for d in range(ndk):
        dx=x+5+d*((LX-10)/max(1,ndk-1))
        _m,_=yo(-0.16,0.16); box(f"{pre}_hd{d}","proposed","dockdoor",dx,_m,1.2,4.0,0.32,4.5,C["dockdoor"],state="proposed")   # high-speed door 4.0×4.5
        _m,_s=yo(0.0,0.4)
        box(f"{pre}_shl{d}","proposed","forkdark",dx-0.42,_m,1.2,0.42,_s,4.85,(0.12,0.12,0.14),state="proposed")   # dock shelter jamb L
        box(f"{pre}_shr{d}","proposed","forkdark",dx+4.0,_m,1.2,0.42,_s,4.85,(0.12,0.12,0.14),state="proposed")    # dock shelter jamb R
        box(f"{pre}_sht{d}","proposed","forkdark",dx-0.42,_m,5.75,4.84,_s,0.4,(0.12,0.12,0.14),state="proposed")   # dock shelter head
        _m,_s=yo(Dp-0.2,Dp+1.3); box(f"{pre}_lv{d}","proposed","dockdoor",dx+0.5,_m,1.12,3.0,_s,0.12,(0.56,0.57,0.60),state="proposed")  # Dock Leveler at the OUTER edge (bridges truck↔platform)
        for bi,bx in enumerate((dx+0.1,dx+1.35,dx+2.6,dx+3.85)):   # 4 Dock Bumpers / door (outer edge where the truck docks)
            _m,_s=yo(Dp-0.05,Dp+0.3); box(f"{pre}_bp{d}_{bi}","proposed","forkdark",bx,_m,0.35,0.3,_s,0.95,(0.07,0.07,0.08),state="proposed")
    _m,_s=yo(-0.6,Dp+0.6); box(f"{pre}_dcan","proposed","canopy",x-0.6,_m,4.95,LX+1.2,_s,0.28,C["canopy"],state="proposed")   # canopy ≥3×4 م
    for stp in range(5):   # ground-access ramp (slope ~8% for forklifts, OSHA) at the west end
        _m,_s=yo(Dp-0.5,Dp+2.3); box(f"{pre}_grp{stp}","proposed","concrete",x-7.5+stp*1.5,_m,stp*0.24,1.5,_s,0.26,(0.80,0.80,0.82),state="proposed")
    _m,_=yo(1.0,1.3); box(f"{pre}_tl","proposed","cctv",x+LX+0.6,_m,0,0.3,0.3,3.6,(0.80,0.15,0.13),state="proposed")   # dock traffic light
    # --- ENTRY FLOW on the 1.20 m platform: staged inbound pallets → a laden forklift carries one toward the door ---
    _m,_s=yo(1.5,2.3)
    for k in range(3): box(f"{pre}_pin{k}","proposed","load",x+6.5+k*1.35,_m,1.2,1.2,_s,1.0,(C["load"] if k%2 else C["load2"]),state="proposed")
    _fy,_=yo(0.3,2.3); forklift(f"{pre}_dkfk",x+LX*0.5-0.6,_fy,load=True,grp="proposed",z0=1.2)   # forklift on the platform (inbound)
    if det:   # 3-step flow callouts on the biggest store (E-5)
        box(f"{pre}_f1","proposed","label",x+2,yo(3.4,3.6)[0],3.8,1,1,0.1,(0.95,0.78,0.10),label="① الشاحنة ترجع للمنصّة وتُفرَّغ عبر Dock Leveler",state="proposed",system="04 تسلسل الدخول")
        box(f"{pre}_f2","proposed","label",x+LX*0.42,yo(1.8,2.0)[0],2.9,1,1,0.1,(0.95,0.78,0.10),label="② على المنصّة 1.20م: فرز ومطابقة الوارد",state="proposed",system="04 تسلسل الدخول")
        box(f"{pre}_f3","proposed","label",x+LX*0.6,yo(-0.2,0.0)[0],5.2,1,1,0.1,(0.95,0.78,0.10),label="③ الفوركلفت يُدخل البليت عبر الباب السريع إلى المستودع",state="proposed",system="04 تسلسل الدخول")
    WH_LIST.append({"name":w["id"],"x":x,"y":yy,"w":LX,"l":DY,"zone":w.get("zone","")})
    # family/sector sign band on the ramp-facing facade (vivid sector colour)
    sc=FAMV.get(fam,(0.5,0.5,0.55)); sy_=(yy-0.33) if rs=="S" else (yy+DY)
    box(f"{pre}_sign",pre,"building",x+LX/2-6,sy_,H-1.7,12,0.33,1.3,sc)
    # team of articulated workers (hi-vis) along the aisle — عدد الفريق وفق تقرير التوظيف
    pcy=ay+al/2
    for s in range(3): person(f"{pre}_p{s}",x+7+s*int((LX-14)/2),pcy,body=UNI["charcoal"],accent=UNI["orange"],helmet=UNI["hat_wht"])

for w in CONFIG["wh"]: dry_warehouse(w)

# ---------------- Z3 — COLD / FREEZER COMPLEX E-F (detailed per D3) ----------------
def build_cold():
    cb=CONFIG["cold"]; x0,y0,BW,BL,Hc=cb["x"],cb["y"],cb["w"],cb["l"],cb["h"]; tt=0.3
    box("Z3_floor","cold","floor",x0,y0,0,BW,BL,0.1,(0.84,0.88,0.93),
        label="المجمّع المبرّد E-F — 80×65م · 5م · 3,850م² · 12 غرفة · 4,632 موقع · فريق 8–12",system="22 التبريد")
    box("Z3_ws","cold","wall",x0,y0,0,BW,tt,Hc,(0.90,0.93,0.97)); box("Z3_wn","cold","wall",x0,y0+BL-tt,0,BW,tt,Hc,(0.90,0.93,0.97))
    box("Z3_ww","cold","wall",x0,y0,0,tt,BL,Hc,(0.90,0.93,0.97)); box("Z3_we","cold","wall",x0+BW-tt,y0,0,tt,BL,Hc,(0.90,0.93,0.97))
    box("Z3_roof","cold","roof",x0,y0,Hc,BW,BL,0.3,C["roof"],meta={"hideable":True})
    box("Z3_office","cold","building",x0+BW+0.5,y0+1,0,10,13,5.5,(0.84,0.80,0.74),label="مكاتب الثلاجات (26)",system="26 مكاتب الثلاجات")
    box("Z3_officeg","cold","glass",x0+BW+0.5,y0+1,1.2,10,0.2,2.6,C["glass"])
    dhw=40.0; dhx=x0+(BW-dhw)/2; dhd=9.85
    box("Z3_dockhall","cold","zonefloor",dhx,y0+tt,0.06,dhw,dhd,0.05,(0.90,0.90,0.84),
        label="صالة الأرصفة +10°م · 39.20×9.85م · فرز وفحص الوارد",system="22 صالة الأرصفة")
    for d in range(8):
        ddx=dhx+2+d*((dhw-4)/7)
        box(f"Z3_dock{d}","cold","dockdoor",ddx,y0-0.15,0,3.0,0.3,3.4,C["dockdoor"],system="04 رصيف Dock Leveler (مقترح)")
        box(f"Z3_lvl{d}","cold","dockdoor",ddx,y0+0.2,0.0,3.0,1.2,0.12,(0.56,0.57,0.60))
    for ri,rx in enumerate([dhx+7,dhx+26]):
        box(f"Z3_reef{ri}t","cold","truck",rx,y0-9,0,2.6,8,3.2,(0.91,0.93,0.97)); box(f"Z3_reef{ri}c","cold","truck",rx,y0-11.6,0,2.6,2.6,2.9,(0.16,0.28,0.50))
    box("Z3_reeflbl","cold","label",dhx+16,y0-6,2,1,1,0.1,(0.9,0.9,0.95),label="حاويات مبرّدة 40ft Reefer")
    ay=y0+dhd
    box("Z3_aisle","cold","zonefloor",x0+tt,ay,0.04,BW-2*tt,6.0,0.04,(0.90,0.90,0.84),label="ممر الرافعات 6م +10°م · حلقة أحادية",system="09 حلقة الحركة")
    ROOMS={"CS-1":(20,18,"−20°م",420),"CS-2":(22.6,14.7,"−20°م",432),"CS-3":(22.6,14.75,"−20°م",432),
     "CS-4":(25.65,16.5,"−20°م",504),"CS-5":(13.75,16.5,"−20°م",288),"CS-6":(13.75,16.5,"−20°م",288),
     "CS-7":(25.7,16.5,"−20°م",504),"CS-8":(22.6,14.75,"−20°م",432),"CS-9":(22.6,14.7,"−20°م",432),
     "CS-10":(20,18,"−20°م",420),"CS-11":(21.5,11.65,"+2°م",240),"CS-12":(21.5,11.65,"+2°م",240)}
    rowA=["CS-10","CS-1","CS-11","CS-12","CS-2","CS-3"]; rowB=["CS-9","CS-8","CS-7","CS-4","CS-5","CS-6"]
    inner=BW-2*tt-0.6
    def layrow(order,ry,rd):
        sw=sum(ROOMS[r][0] for r in order); sc=inner/sw; cx=x0+tt+0.3
        for rid in order:
            d0,d1,temp,cap=ROOMS[rid]; rw=d0*sc; frz=temp.startswith("−"); flc=(0.80,0.86,0.95) if frz else (0.86,0.93,0.97)
            box(f"{rid}_fl","cold","zonefloor",cx,ry,0.06,rw-0.3,rd,0.05,flc,label=f"{rid} · {temp} · {cap} طبلية · {d0}×{d1}م",system="22 غرفة تبريد")
            box(f"{rid}_wl","cold","wall",cx,ry,0,0.16,rd,Hc-0.25,(0.90,0.93,0.97)); box(f"{rid}_wb","cold","wall",cx,ry+rd-0.16,0,rw-0.3,0.16,Hc-0.25,(0.90,0.93,0.97))
            box(f"{rid}_dr","cold","door",cx+rw/2-1.2,ry-0.1,0,2.1,0.2,3.0,C["door"])
            rx=cx+0.7
            while rx+1.0<=cx+rw-0.9:
                box(f"{rid}_bmA{int(rx*10)}","cold","rack_bm",rx,ry+2.6,1.0,1.0,rd-4.5,0.08,C["beam"]); box(f"{rid}_bmB{int(rx*10)}","cold","rack_bm",rx,ry+2.6,2.55,1.0,rd-4.5,0.08,C["beam"])
                for p in range(int((rd-4.5)//2.8)):
                    yyp=ry+2.8+p*2.8
                    box(f"{rid}_u{int(rx*10)}_{p}","cold","rack_up",rx,yyp,0,0.1,0.1,4.4,C["upright"]); box(f"{rid}_u{int(rx*10)}_{p}b","cold","rack_up",rx+0.9,yyp,0,0.1,0.1,4.4,C["upright"])
                    cols=[(0.78,0.60,0.40),(0.80,0.64,0.45),(0.74,0.76,0.82),(0.86,0.88,0.90)]
                    for Lv in range(3):
                        hv=(p*5+Lv*7+int(rx*10))%10
                        if hv<1: continue
                        ld=cols[(p+Lv)%4]
                        box(f"{rid}_pl{int(rx*10)}_{p}_{Lv}","cold","load",rx+0.03,yyp+0.1,0.25+Lv*1.55,0.9,2.3,1.15 if hv<8 else 0.8,ld)
                rx+=1.0+3.0
            cx+=rw
    layrow(rowA,ay+6.2,20); layrow(rowB,ay+6.2+20+3,20)
    for u in range(6): box(f"Z3_cond{u}","cold","gen",x0+8+u*11.5,y0+BL-3,Hc+0.3,3.5,2,1.4,C["gen"],system="22 وحدات تكثيف")
    WH_LIST.append({"name":"E-F","x":x0,"y":y0,"w":BW,"l":BL,"zone":"Z3"})
build_cold()

# ---------------- Z1 — ADMIN · SERVICES / HOUSING (NW) + SUPPORT SYSTEMS ----------------
# Z1 is drawn in the NAS-8155 site plan as a landscaped CLUSTER — angled office/residence blocks in a
# chevron, a bent central admin building and a fountain — not two large bars. Modelled to match the plan.
STONE=(0.80,0.74,0.60); CH=(0.22,0.23,0.27)
box("z1_green","admin","zonefloor",14,150,0,64,58,0.09,(0.36,0.57,0.33),label="Z1 · الإدارة والخدمات — عنقود فلل مكتبية/سكنية + نافورة")
def villa(tag,cx,cy,w,d,h,rot,lbl="",sys=""):
    box(tag,"admin","building",cx-w/2,cy-d/2,0.09,w,d,h,C["office"],rot=rot,label=lbl,system=sys)
    box(f"{tag}_bs","admin","building",cx-w/2-0.1,cy-d/2-0.1,0.09,w+0.2,d+0.2,0.7,CH,rot=rot)                 # charcoal base
    box(f"{tag}_rf","admin","roof2",cx-(w+0.5)/2,cy-(d+0.5)/2,h+0.09,w+0.5,d+0.5,0.45,(0.66,0.36,0.28),rot=rot) # tiled hip roof
for i in range(5): villa(f"vL{i}",22+i*5.2,184+i*2.6,8.0,5.4,6.6,-38)      # upper-left arm (angled blocks rising to centre)
for i in range(5): villa(f"vR{i}",72-i*5.2,184+i*2.6,8.0,5.4,6.6,38)       # upper-right arm (mirror)
villa("admin",39,168,17,9.5,9.15,22,lbl="المبنى الإداري — 1,200م² · طابقان (+10.05م)",sys="06 الإداري")        # bent admin — W wing
villa("admin2",55,168,17,9.5,9.15,-22)                                     # bent admin — E wing
box("admin_entry","admin","glass",45.5,171.3,0.1,9,0.25,8.4,C["glass"])    # double-height glazed entrance (vertex)
villa("housing",25,159,16,10,7.95,0,lbl="المبنى الخدمي/السكني — 580م² · طابقان · 22 سريرًا",sys="07 السكن")
cyl("z1_fnt_b","admin",45,203,0,7.0,0.55,(0.74,0.78,0.80),label="النافورة")  # basin (open green pocket, top-centre)
cyl("z1_fnt_w","admin",45,203,0.34,5.3,0.46,(0.36,0.60,0.84))              # water surface
cyl("z1_fnt_r","admin",45,203,0.8,1.3,2.3,(0.82,0.84,0.86))                # central jet column
cyl("z1_fnt_j","admin",45,203,3.1,0.9,1.2,(0.72,0.87,0.97))                # water plume
for i,(tx,ty) in enumerate([(17,207),(77,207),(16,153),(78,153),(62,205)]):  # palms around the green
    box(f"z1pt{i}","ops","tree",tx,ty,0,0.5,0.5,2.2,(0.42,0.30,0.18)); box(f"z1pc{i}","ops","tree",tx-1.1,ty-1.1,2.2,2.6,2.6,2.6,(0.24,0.5,0.28))
# support systems — placed in free pockets, clear of the five zones
box("fire_tank","support","cylinder",320,156,0,12,12,12,C["tank"],label="خزان حريق 500م³ · رشاشات ESFR · NFPA 13",system="02 الحماية",meta={"cyl":True})
box("pump","support","building",306,156,0,6,5,3.5,C["wall2"],label="محطة الضخ 750GPM")
box("gen_room","support","building",336,150,0,10,8,4.0,C["gen"],label="مولدات ≥500kVA · ATS ≤15ث · ISO 8528",system="21 المولدات")
box("workshop","support","building",332,24,0,16,12,5.0,C["wall2"],label="ورشة الصيانة",system="14 الصيانة")
box("fuel_canopy","support","canopy",96,24,4.0,10,8,0.3,C["canopy"],label="محطة الوقود",system="19 الوقود")
box("charging","support","building",186,25,0,9,8,3.5,C["wall2"],label="شحن الرافعات",system="15 شحن الرافعات")
for (px,py) in [(10,10),(356,10),(16,206),(352,172)]:   # perimeter CCTV at the real plot corners
    box(f"cctv_{int(px)}_{int(py)}","support","cctv",px,py,0,0.2,0.2,5,C["cctv"],system="05 CCTV")
# requirements clarification callouts (anchored near the relevant zone)
REQ=[("req_rack",300,120,7.2,"رفوف انتقائية ≤6.5م صافٍ ضمن مبنى 6.80م (أرضية-سقف) · 3–4 مستويات بالته · خلوص رشاشات ESFR · باليه 800×1200 · ممر ≥3.5م · EN 15512"),
     ("req_epoxy",230,66,0.3,"إيبوكسي 3مم · R12 · خطوط ملوّنة ISO 7010"),
     ("req_cctv",30,22,6.5,"CCTV ≥144TB · ANPR · غرفة مراقبة · EN 62676"),
     ("req_hvac",140,100,5.5,"تكييف VRF · تبريد +2..+8°م · تجميد ≤-18°م · AHRI 1100"),
     ("req_elec",80,150,5.5,"الغرف الكهربائية · MDB 4000A · UPS ≥2س · IEC 61439"),
     ("req_dock",200,50,4.5,"رامب 1.20م · Dock Leveler ±300مم · باب سريع 4×4.5م (مقترح)"),
     ("req_fire2",320,170,10,"خزان 500م³ · مضخة 750GPM · هيدرنت كل 60م")]
for rid,rx,ry,rz,lbl in REQ:
    box(rid,"requirements","label",rx,ry,rz,1,1,0.1,(0.95,0.78,0.10),label=lbl,system="المتطلبات")

# ---------------- OPERATIONS: trucks · forklifts · cars · trees ----------------
def truck(tag,x,y,cab_north=True,trailer=(0.94,0.95,0.97),cab=(0.16,0.28,0.50)):
    box(f"{tag}_tr","ops","truck",x,y,0.95,2.6,8.0,2.55,trailer)
    box(f"{tag}_ch","ops","forkdark",x+0.2,y-0.1,0.35,2.2,8.2,0.35,(0.12,0.12,0.14))
    cy=y+8.0 if cab_north else y-2.6
    box(f"{tag}_cab","ops","truck",x,cy,0.55,2.6,2.6,2.45,cab)
    box(f"{tag}_cabg","ops","glass",x+0.15,(cy+2.45 if cab_north else cy),1.6,2.3,0.12,1.0,C["glass"])
    for wy in (y+1.0,y+6.5,cy+1.2):
        box(f"{tag}_wL{int(wy*10)}","ops","forkdark",x-0.12,wy,0,0.28,1.3,0.9,(0.07,0.07,0.08))
        box(f"{tag}_wR{int(wy*10)}","ops","forkdark",x+2.44,wy,0,0.28,1.3,0.9,(0.07,0.07,0.08))
def car(tag,x,y,col): box(f"{tag}_b","ops","car",x,y,0,1.8,4.2,1.05,col); box(f"{tag}_c","ops","car",x+0.1,y+1,1.05,1.6,2,0.6,col)
def fork2(tag,x,y): forklift(tag,x,y,load=False)
def tree(tag,x,y): box(f"{tag}_t","ops","tree",x,y,0,0.35,0.35,1.6,(0.42,0.30,0.18)); box(f"{tag}_c","ops","tree",x-0.9,y-0.9,1.6,2.1,2.1,2.3,(0.26,0.52,0.28))
# trucks waiting in Z2 + moving on the spine + reefers already at cold
for i,ty in enumerate([34,52,70,88]): truck(f"tkw{i}",34+(i%2)*16,ty,cab_north=True)
truck("tks1",120,50,cab_north=True); truck("tks2",210,50,cab_north=True,cab=(0.55,0.18,0.16))
truck("tkin",12,30);
# forklifts on the spine/roads near docks
for i,(fx,fy) in enumerate([(120,62),(205,62),(300,62),(150,46)]): fork2(f"fk{i}",fx,fy)
# staff car park in Z2 + near admin
pal=[(0.28,0.31,0.38),(0.62,0.62,0.64),(0.42,0.16,0.15),(0.20,0.30,0.46),(0.75,0.74,0.70)]
for r in range(5):
    for cc in range(7): car(f"car{r}_{cc}",26+cc*2.7,34+r*5.2,pal[(r+cc)%5])
for cc in range(6): car(f"carA_{cc}",20+cc*2.7,168,pal[cc%5])
# landscaping
for i,(tx,ty) in enumerate([(6,30),(6,70),(6,110),(6,150),(6,190),(6,230),(6,270),(S[0]-8,40),(S[0]-8,120),(S[0]-8,210),(S[0]-8,270),(90,10),(200,10),(300,10)]):
    tree(f"tr{i}",tx,ty)

# ---------------- ACTIVITY & FINER DETAILS ----------------
longwh=[w for w in CONFIG["wh"] if w["DY"]==20]
def lfork(tag,x,y,load=True): forklift(tag,x,y,load=load)
for i,w in enumerate(longwh):
    ay=w["y"]+(w["DY"]-CONFIG["aisle"])/2; lfork(f"lfk{i}",w["x"]+14+(i%3)*10,ay+1.4)
for i,(fx,fy) in enumerate([(130,52),(230,52),(300,52),(60,100)]): lfork(f"yfk{i}",fx,fy)
# staged pallet stacks + live loading/unloading — pallets IN and OUT at every store ramp (معبأ بليت تدخل وتخرج)
def stack(tag,x,y,nx=3,ny=2,c0=None):
    for a in range(nx):
        for b in range(ny): box(f"{tag}_{a}_{b}","ops","load",x+a*1.3,y+b*0.9,0,1.2,0.8,1.0,(c0 or (C["load"] if (a+b)%2==0 else C["load2"])))
stack("stg1",120,52); stack("stg2",230,52); stack("stg3",300,52)
# articulated trucks backed to the loading platforms (rear to the dock, bridged by the Dock Leveler)
_tkcab={"E-5":(0.55,0.18,0.16),"E-6":None,"E-1":None,"E-8":None,"E-9":None}
for w in CONFIG["wh"]:
    if w["id"] not in _tkcab: continue
    rN=w.get("ramp")=="N"; xd=w["x"]+w["LX"]*0.5-1.3; cc=_tkcab[w["id"]]
    ty,cn=((w["y"]+w["DY"]+6.0),True) if rN else ((w["y"]-14.0),False)
    truck(f"tkd_{w['id']}",xd,ty,cab_north=cn,**({} if cc is None else {"cab":cc}))
# workers — role-coded by zone (Brandzo workwear identity BFP-SCM-UNI-2026-001)
wpos=[(130,54),(230,54),(300,54)]
for w in longwh: wpos.append((w["x"]+16,w["y"]+(w["DY"]-5.5)/2+1.0))
for i,(px,py) in enumerate(wpos): person(f"wk{i}",px,py,body=UNI["charcoal"],accent=UNI["orange"],helmet=UNI["hat_wht"])  # warehouse handling
person("role_gate1",30,30,body=UNI["ctrlred"],helmet=UNI["hat_red"])        # Z2 gate/audit officer (control red)
person("role_gate2",34,27,body=UNI["blue"],helmet=UNI["hat_blu"])           # Z2 delivery driver (movement blue)
person("role_qc1",126,63,body=UNI["green"],accent=UNI["green"],helmet=UNI["hat_grn"])  # Z3 QC / cold-chain inspector
person("role_rf1",150,63,body=UNI["navy"],helmet=UNI["hat_blu"])            # Z3 refrigeration / electrical tech
person("role_adm1",52,146,body=UNI["white"],helmet=UNI["hat_grn"])          # Z1 office staff (green helmet when crossing)
person("role_adm2",58,146,body=UNI["white"],helmet=UNI["hat_grn"])
# floor markings: green pedestrian walkway in front of each store (ramp side) + crosswalks on the spine
for w in longwh:
    pwy=(w["y"]+w["DY"]+0.3) if w.get("ramp")=="N" else (w["y"]-0.7)
    box(f"pw_{w['id']}","site","lane",w["x"],pwy,0.06,w["LX"],0.4,0.02,(0.24,0.58,0.30))
for i,cx in enumerate((150,250,320)):
    for z in range(6): box(f"cw{i}_{z}","site","lane",cx-5+z*2,48,0.06,1.0,12,0.02,(0.93,0.93,0.93))
# column guards + bollards at road intersections
for w in CONFIG["wh"]:
    box(f"cg_{w['id']}a","site","guard",w["x"]-0.35,w["y"]-0.35,0,0.6,0.6,0.85,C["guard"])
    box(f"cg_{w['id']}b","site","guard",w["x"]+w["LX"]-0.25,w["y"]-0.35,0,0.6,0.6,0.85,C["guard"])
for (bx,by) in [(184,60),(246,60),(184,140),(246,140),(92,54),(352,54)]:
    box(f"boll{int(bx)}_{int(by)}","site","guard",bx,by,0,0.3,0.3,1.0,C["guard"])
# BRANDZO branding on admin + perimeter light poles
box("brand","admin","label",42,158,8.2,12,1,0.1,(0.95,0.78,0.10),label="BRANDZO — مخازن 155")
for i,(px,py) in enumerate([(22,40),(22,110),(22,180),(22,255),(360,40),(360,110),(360,180),(360,255),(130,12),(290,12)]):
    box(f"pole{i}","support","cctv",px,py,0,0.2,0.2,8,C["cctv"]); box(f"poleL{i}","support","light",px-0.4,py-0.3,7.8,1.2,0.6,0.3,(1.0,0.95,0.7))

# ---------------- REALISM DETAILS ----------------
WHH=CONFIG["wall_h"]
for w in CONFIG["wh"]:
  for j,yy in enumerate((w["y"]-0.12,w["y"]+w["DY"]-0.12)):
    box(f"fas_{w['id']}_{j}","wall","building",w["x"],yy,WHH-0.5,w["LX"],0.24,0.5,C["wall2"])
    box(f"pl_{w['id']}_{j}","wall","building",w["x"],yy-0.05,0,w["LX"],0.32,0.4,(0.34,0.36,0.40))
# spine road markings: dashed centerline + solid edge lines
for i,xx in enumerate(range(96,350,8)):
  box(f"rdc{i}","site","lane",xx,53.7,0.05,4,0.4,0.02,(0.95,0.95,0.95))
box("rde1","site","lane",96,49.0,0.05,252,0.28,0.02,(0.88,0.88,0.88))
box("rde2","site","lane",96,58.8,0.05,252,0.28,0.02,(0.88,0.88,0.88))
# Z2 parking bay guide lines
for i in range(6):
  yy=30+i*5.2
  for k in range(7):
    box(f"pk{i}_{k}","site","lane",25+k*2.7,yy,0.05,0.2,2.0,0.02,(0.95,0.95,0.95))

# ---------------- REALISM-2: building facades · perimeter wall · masts · flagpoles ----------------
GP=(0.80,0.81,0.84)
def facade(tag,x,y,sx,sy,sz,floors=2,grp="admin",canopy=True):
    g=C["glass"]; bandN=max(1,floors)
    for f in range(bandN):
        z=0.9+f*(sz-0.9)/bandN; bh=(sz-0.9)/bandN-0.35
        if bh<0.4: continue
        box(f"{tag}_gS{f}",grp,"glass",x+0.6,y-0.06,z,sx-1.2,0.1,bh,g)
        box(f"{tag}_gN{f}",grp,"glass",x+0.6,y+sy-0.04,z,sx-1.2,0.1,bh,g)
        box(f"{tag}_gE{f}",grp,"glass",x+sx-0.04,y+0.6,z,0.1,sy-1.2,bh,g)
        box(f"{tag}_gW{f}",grp,"glass",x-0.06,y+0.6,z,0.1,sy-1.2,bh,g)
    for m in range(1,int(sx//3)):
        box(f"{tag}_mu{m}",grp,"col",x+m*3,y-0.11,0.9,0.14,0.14,sz-1.1,GP)
    box(f"{tag}_par",grp,"building",x-0.15,y-0.15,sz,sx+0.3,sy+0.3,0.35,GP)
    if canopy:
        cxm=x+sx/2
        box(f"{tag}_can",grp,"canopy",cxm-3,y-2.2,2.6,6,2.4,0.18,(0.88,0.89,0.92))
        box(f"{tag}_cc1",grp,"col",cxm-2.8,y-2.0,0,0.15,0.15,2.6,GP); box(f"{tag}_cc2",grp,"col",cxm+2.65,y-2.0,0,0.15,0.15,2.6,GP)
        box(f"{tag}_door",grp,"glass",cxm-1.6,y-0.12,0,3.2,0.12,2.4,(0.28,0.42,0.58))
for a in [("fac_wshop",332,24,16,12,5,1),("fac_charge",186,25,9,8,3.5,1),("fac_gen",338,196,10,8,4,1),
          ("fac_pump",306,156,6,5,3.5,1),("fac_coff",180.5,69,10,13,5.5,2)]:
    facade(*a)
# perimeter precast posts distributed along the real plot polygon edges (~22 m spacing)
for i in range(len(PLOT)):
    A=PLOT[i]; Bv=PLOT[(i+1)%len(PLOT)]
    L=math.hypot(Bv[0]-A[0],Bv[1]-A[1]); n=max(1,int(L//22))
    for k in range(1,n):
        fx=A[0]+(Bv[0]-A[0])*k/n; fy=A[1]+(Bv[1]-A[1])*k/n
        box(f"ppost_{i}_{k}","site","col",fx-0.25,fy-0.25,0,0.5,0.5,3.3,(0.70,0.71,0.73))
# SW gate pillars + sliding leaf
box("gp_a","site","col",6,22,0,0.8,0.8,4.2,(0.62,0.50,0.22)); box("gp_b","site","col",22,22,0,0.8,0.8,4.2,(0.62,0.50,0.22))
box("gl_x","site","fence",7,22.4,0,14,0.2,2.6,(0.74,0.76,0.80))
# flood-light masts at the Z2 yard corners + Z4/Z5 corners
for i,(mx,my) in enumerate([(24,26),(88,26),(24,118),(360,20),(360,60),(190,188)]):
    box(f"mast{i}","support","col",mx,my,0,0.4,0.4,16,(0.72,0.73,0.75)); box(f"masth{i}","support","light",mx-1.2,my-0.3,15.4,2.6,1.2,0.4,(1.0,0.96,0.74))
# flagpoles at the admin frontage (south of admin)
for i,fx in enumerate([24,29,34]):
    box(f"fp{i}","support","col",fx,147,0,0.16,0.16,10,(0.86,0.87,0.89))
    box(f"fpf{i}","support","canopy",fx-1.5,147,8.6,1.5,0.1,0.95,[(0.85,0.18,0.18),(0.12,0.45,0.22),(0.12,0.12,0.12)][i])

# ---------------- 22 ENGINEERING AXES — physical systems (BFP-SCM-ENG-2026-001, Part 2) ----------------
def bld(tag,x,y,sx,sy,sz,col,label="",sysn=""): box(tag,"support","building",x,y,0,sx,sy,sz,col,label=label,system=sysn)
# 03 الغرف الكهربائية — electrical room + transformer + MDB
bld("elec_room",348,170,9,7,4.2,(0.80,0.80,0.74),"الغرفة الكهربائية · MDB 4000A · IEC 61439","03 الكهرباء")
box("elec_tx","support","gen",342,172,0,3,3,2.6,(0.45,0.46,0.49)); box("elec_mdb","support","gen",349,170.6,0,1.2,0.8,2.0,(0.30,0.32,0.36))
facade("fac_elec",348,170,9,7,4.2,1)
# 25 الشبكات والإنترنت — IT/server room + comms mast + dish (east of admin)
bld("it_room",80,152,8,6,3.6,(0.82,0.82,0.86),"غرفة الشبكات والخوادم · UPS ≥2س","25 الشبكات")
box("it_mast","support","col",85,150,0,0.25,0.25,15,(0.72,0.73,0.75),label="برج الاتصالات",system="25 الشبكات")
box("it_dish","support","truck",83.3,149.2,12,1.8,1.8,1.1,(0.90,0.91,0.93)); facade("fac_it",80,152,8,6,3.6,1)
# 16 إدارة النفايات — waste / recycling compound (colour-coded skips + carton baler), fenced
box("waste_pad","site","concrete",108,8,0.04,18,11,0.1,C["apron"],label="إدارة النفايات · حاويات فرز + مكبس كرتون",system="16 النفايات")
for i,c in enumerate([(0.20,0.45,0.75),(0.25,0.60,0.35),(0.70,0.55,0.15)]): box(f"skip{i}","support","gen",110+i*5,10,0,3.6,2.4,1.8,c)
box("baler","support","gen",122,16,0,3,2.2,2.6,(0.55,0.22,0.20))
for s,(fx,fy,fw,fd) in enumerate([(107,7,19,0.2),(107,19,19,0.2),(107,7,0.2,12.2),(125.8,7,0.2,12.2)]): box(f"wf{s}","site","fence",fx,fy,0,fw,fd,2.0,C["fence"])
# 18 الصحة والسلامة المهنية — assembly point + first-aid / safety station
box("assembly","site","zonefloor",60,8,0.05,11,11,0.03,(0.20,0.62,0.30),label="نقطة التجمّع عند الطوارئ · EN ISO 7010",system="18 السلامة")
box("firstaid",'support',"building",74,9,0,4,4,3.0,(0.92,0.92,0.94),label="إسعافات أولية + السلامة المهنية",system="18 السلامة")
box("firstaid_c","support","dockdoor",75.5,8.9,1.2,1.0,0.1,1.0,(0.80,0.20,0.20))
# 02 الحماية من الحرائق — hydrants (~ every 40–60 m on roads) + hose-reel cabinets + fire-pump house
for i,(hx,hy) in enumerate([(110,54),(160,54),(210,54),(260,54),(310,54),(24,62),(24,122),(24,182),(188,120),(248,120),(150,46),(300,46)]):
    box(f"hyd{i}","support","gen",hx,hy,0,0.35,0.35,1.1,(0.80,0.15,0.12),system="02 هيدرنت")
for i,w in enumerate(longwh[:6]):
    hy=(w["y"]+w["DY"]+0.25) if w.get("ramp")=="N" else (w["y"]-0.95)
    box(f"hose{i}","support","dockdoor",w["x"]+2,hy,0.3,0.9,0.5,0.9,(0.80,0.18,0.14))
box("firepump_lbl","support","label",310,150,9.2,1,1,0.1,(0.95,0.78,0.10),label="غرفة مضخات الحريق 750GPM · هيدرنت كل 60م")
# 22 التكييف والتبريد — VRF condensers on admin / housing roofs (dry side; cold side already has condensers)
for i in range(4): box(f"hvac_a{i}","support","gen",24+i*9,155,9.15,2.4,1.6,1.0,(0.78,0.79,0.82))
for i in range(3): box(f"hvac_h{i}","support","gen",21+i*7,183,7.95,2.4,1.6,1.0,(0.78,0.79,0.82))
# 11 الاستلام والفرز · 12 الصرف والشحن — marked staging bays on the spine apron (floor patches)
box("recv_zone","site","zonefloor",96,61,0.05,70,3,0.03,(0.30,0.55,0.80),label="منطقة الاستلام والفرز (11) — GRN / PUTAWAY",system="11 الاستلام")
box("disp_zone","site","zonefloor",196,61,0.05,120,3,0.03,(0.82,0.46,0.30),label="منطقة الصرف والشحن (12) — PICK / DN / POD",system="12 الصرف")
# Axis 23 — internal platform scales 2.0×2.0م ±500غ at receiving + each store
box("scale_recv","support","concrete",130,62,0.05,2,2,0.28,(0.30,0.32,0.36),label="ميزان أرضي 2×2م ±500غ (23)",system="23 الميزان الداخلي")
for w in CONFIG["wh"]:
    sxp=w["x"]+w["LX"]-3; syp=(w["y"]+w["DY"]+0.6) if w.get("ramp")=="N" else (w["y"]-2.1)
    box(f"ps_{w['id']}","support","concrete",sxp,syp,0.05,2,2,0.24,(0.30,0.32,0.36),system="23 ميزان أرضي")
# Axis 05 — CCTV control / monitoring room (≤12م²) by the admin
box("control_room","support","building",70,154,0,6,5,3.6,(0.82,0.82,0.86),label="غرفة المراقبة CCTV ≤12م² (05)",system="05 CCTV")
box("control_g","support","glass",70,154,1.2,6,0.2,2.0,C["glass"])

# ---------------- REALISM-3: kerbs · landscaping ----------------
def kerb(tag,x,y,sx,sy): box(tag,"site","col",x,y,0,sx,sy,0.16,(0.85,0.85,0.83))
kerb("kb_sp1",92,47.3,262,0.3); kerb("kb_sp2",92,60.4,262,0.3)                 # spine road kerbs
kerb("kb_w1",9.4,18,0.3,186); kerb("kb_w2",20.3,18,0.3,186)                    # west road kerbs
for i,ry in enumerate((83.7,91.3,111.7,119.3,139.7,147.3)): kerb(f"kb_r{i}",188,ry,186,0.3)
HED=(0.24,0.50,0.28); LAWN=(0.38,0.60,0.33)
for i,(hx,hy,hw,hd) in enumerate([(16,148,58,1.2),(14,200,66,1.2),(94,22,1.2,100)]):
    box(f"hedge{i}","site","tree",hx,hy,0,hw,hd,1.0,HED)                        # hedges
box("isl_gate","site","zonefloor",36,18,0.05,14,5,0.03,LAWN)                   # entrance planted island
for i in range(4): box(f"islt{i}","ops","tree",39+i*3,20,0,0.3,0.3,1.3,(0.30,0.52,0.30))
for i,(tx,ty,sz) in enumerate([(8,40,2.6),(8,90,2.0),(10,150,2.8),(22,205,2.2),(120,220,2.6),(340,120,2.4),(355,60,2.2),(300,14,2.0),(200,14,2.4),(60,14,2.2)]):
    box(f"tv{i}_t","ops","tree",tx,ty,0,0.4,0.4,1.8,(0.42,0.30,0.18)); box(f"tv{i}_c","ops","tree",tx-sz/2,ty-sz/2,1.8,sz,sz,sz*1.1,(0.23,0.50+(i%3)*0.03,0.27))

# ---------------- GEOGRAPHIC CONTEXT (real surroundings · Benghazi 32.204°N 20.219°E, from the satellite) ----------------
box("ctx_road_w","site","road",-26,-60,-0.05,18,360,0.06,(0.26,0.27,0.30),label="الطريق العام الغربي — محور رئيسي")
for i in range(16):
    box(f"ctx_rwl{i}","site","lane",-17.5,-40+i*22,0.0,0.5,9,0.02,(0.92,0.86,0.3))
seg("ctx_road_e","site","road",(372,96),(468,-36),20,0.06,(0.26,0.27,0.30),z=-0.05)   # east angled road continues outward
box("ctx_food","site","building",-96,96,0,44,26,7.0,(0.80,0.82,0.86),label="شركة النعم لتسويق المواد الغذائية (جار)")
box("ctx_foodr","site","roof2",-96.3,95.7,7.0,44.6,26.6,0.4,C["roof2"])
box("ctx_fuelcan","site","canopy",66,266,4.2,24,12,0.3,C["canopy"],label="محطة وقود المسماري")
for i in range(3): box(f"ctx_fp{i}","site","col",72+i*8,272,0,0.6,0.6,4.2,(0.7,0.71,0.73))
box("ctx_school","site","building",252,288,0,34,20,8.0,(0.84,0.82,0.80),label="مدرسة مدينتي (جوار شمالي)")
box("ctx_neigh","site","building",428,118,0,30,44,6.0,(0.82,0.83,0.85),label="منشآت صناعية مجاورة")
box("ctx_nshaft","site","col",356,205,0,0.7,10,2.2,(0.80,0.15,0.13))                   # north marker (North = +Y)
box("ctx_geolbl","site","label",356,216,3,1,1,0.1,(0.95,0.78,0.10),label="شمال ↑ N · الموقع 32.204°ش 20.219°شرقًا — بنغازي")

# ---------------- MOVEMENT PATHS (conceptual circulation overlay · §09/§04) ----------------
# Conceptual operating paths (state=concept) — NOT execution paint lines. Rendered in the viewer
# only, as coloured tubes + arrowheads (not added to boxes or to the OBJ). Coords in metres (X=east,
# Y=north); each path inherits colour/z/width from LAYERDEF so the legend and the drawing share one
# colour source. Derived from the same road constants + warehouse docks already in this model.
LAYERDEF={
 "trucks":{"color":[0.122,0.435,0.922],"z":0.60,"width":0.70,"label":"الشاحنات"},
 "fork":  {"color":[1.0,0.541,0.0],    "z":0.40,"width":0.45,"label":"الرافعات الشوكية"},
 "ped":   {"color":[0.129,0.651,0.353],"z":0.22,"width":0.35,"label":"المشاة"},
 "goods": {"color":[0.753,0.149,0.827],"z":1.10,"width":0.60,"label":"تدفّق البضائع"},
}
ZONES_META=[
 {"z":"Z1","x":14,"y":146,"w":66,"d":56,"color":[0.85,0.22,0.22]},
 {"z":"Z2","x":14,"y":20,"w":78,"d":104,"color":[0.12,0.70,0.86]},
 {"z":"Z3","x":96,"y":62,"w":92,"d":78,"color":[0.95,0.72,0.12]},
 {"z":"Z4","x":190,"y":60,"w":184,"d":130,"color":[0.20,0.68,0.35]},
 {"z":"Z5","x":20,"y":18,"w":314,"d":30,"color":[0.22,0.38,0.82]},
]
def P(pid,layer,label,pts,drn=False,ae=0):
    d={"id":pid,"layer":layer,"label":label,"state":"concept","dir":bool(drn),"pts":pts}
    if drn: d["arrow_every"]=ae
    return d
PATHS=[
 # الشاحنات (trucks)
 P("trk_in","trucks","دخول الشاحنات من البوابة الجنوبية-الغربية",[[14,-2],[14,20],[16,30],[26,40],[50,48],[80,52],[96,54]],True,18),
 P("trk_spine","trucks","الشريان الرئيسي (حلقة اتجاه واحد 12م)",[[96,54],[150,54],[205,54],[253,54],[320,54],[352,54]],True,22),
 P("trk_c2","trucks","المحور الشمالي c2",[[253,54],[253,88],[253,116],[253,144],[253,188]],True,22),
 P("trk_c1","trucks","المحور الشمالي c1",[[186,60],[186,88],[186,116],[186,144],[186,186]],True,22),
 P("trk_r0","trucks","ممر عرضي (أرصفة E-7/E-6)",[[190,88],[374,88]]),
 P("trk_r1","trucks","ممر عرضي (أرصفة E-1)",[[190,116],[374,116]]),
 P("trk_r2","trucks","ممر عرضي (رصيف E-5)",[[190,144],[374,144]]),
 P("trk_dock_E7","trucks","رجوع إلى رصيف E-7",[[313,54],[313,59],[313,62]],True,6),
 P("trk_dock_E6","trucks","رجوع إلى رصيف E-6",[[253,88],[300,88],[313,90]],True,10),
 P("trk_dock_E5","trucks","رجوع إلى رصيف E-5",[[253,144],[270,146],[279,148]],True,8),
 P("trk_dock_E9","trucks","رجوع إلى رصيف E-9 (Z5 يواجه الشمال)",[[207,54],[207,49],[207,45]],True,6),
 P("trk_dock_cold","trucks","رجوع الحاويات المبرّدة إلى أرصفة Z3",[[140,54],[140,60],[140,64]],True,6),
 # الرافعات الشوكية (fork)
 P("fk_E5","fork","رافعة E-5: رصيف ← الممر الأوسط ← الرفوف غربًا",[[279,148],[279,167.5],[218,167.5]],True,8),
 P("fk_E5b","fork","رافعة E-5 شرقًا",[[279,167.5],[306,167.5]],True,8),
 P("fk_E6","fork","رافعة E-6: رصيف ← الممر ← الرفوف",[[313,90],[313,102],[262,102]],True,10),
 P("fk_E6b","fork","رافعة E-6 شرقًا",[[313,102],[364,102]],True,10),
 P("fk_cold_feed","fork","رافعة الثلاجات: الرصيف ← الصالة ← الحلقة",[[140,67],[140,73],[140,80.8]],True,4),
 P("fk_cold_ring","fork","حلقة رافعات الثلاجات (اتجاه واحد)",[[105,80.8],[175,80.8]],True,14),
 P("fk_cold_room","fork","دخول غرفة تبريد (ممثّل × كل غرفة)",[[124,80.8],[124,85]],True,4),
 # المشاة (ped)
 P("ped_admin","ped","ممشى الإدارة Z1 ← العمليات",[[52,148],[55,130],[70,100],[88,70],[110,63],[131,63],[150,63],[150,54]],True,16),
 P("ped_front_E4","ped","ممشى واجهة E-4/E-3/E-2",[[196,63.3],[246,63.3]]),
 P("ped_front_E7","ped","ممشى واجهة E-7",[[258,63.3],[368,63.3]]),
 P("ped_front_Z5a","ped","ممشى واجهة E-8",[[26,42.3],[136,42.3]]),
 P("ped_front_Z5b","ped","ممشى واجهة E-9",[[150,42.3],[260,42.3]]),
 P("ped_front_Z5c","ped","ممشى واجهة E-10",[[276,42.3],[326,42.3]]),
 P("ped_cross150","ped","معبر مشاة محمي (§18)",[[150,63],[150,45]]),
 P("ped_cross250","ped","معبر مشاة محمي (§18)",[[250,63],[250,45]]),
 P("ped_cross320","ped","معبر مشاة محمي (§18)",[[320,63],[320,45]]),
 # تدفّق البضائع (goods)
 P("goods_1","goods","① استلام ← تخزين (GRN/Putaway §11)",[[131,62.5],[150,75],[230,92],[313,102]],True,14),
 P("goods_2","goods","② تخزين ← تجهيز (Pick/Stage §12)",[[313,102],[300,82],[270,66],[256,62.5]],True,14),
 P("goods_3","goods","③ تجهيز ← شحن (التحميل عند الصرف)",[[256,62.5],[240,56],[207,50],[207,45]],True,10),
 P("goods_4","goods","④ شحن ← خروج (الشاحنة إلى البوابة)",[[207,45],[205,54],[150,54],[96,54],[40,46],[16,30],[14,4]],True,20),
]

# ---------------- WRITE ----------------
meta={"project":"Abuhadi 155 — site plan (5 zones) + requirements (combined)","units":"metre",
      "axes":"X=east,Y=north,Z=up","note":"المواقع وفق المخطط الفعلي NAS-8155 (5 مناطق): Z1 الإدارة شمال-غرب · Z2 المواقف والبوابة غرب · Z3 الثلاجات · Z4 المستودعات الرئيسية وسط/شمال · Z5 المستودعات الجنوبية. القائم: أبواب أرضية + ممر 5.50م؛ الرفوف/الأرصفة مقترح. ارتفاعات: جاف 6.80م، مبرّد 5م.",
      "warehouses":WH_LIST,"cold":{"x":CONFIG["cold"]["x"],"y":CONFIG["cold"]["y"],"w":CONFIG["cold"]["w"],"l":CONFIG["cold"]["l"]},
      "plot":[list(p) for p in PLOT],"zones":ZONES_META}
scene={"meta":meta,"palette":C,"boxes":boxes,"paths":PATHS,"pathLayers":LAYERDEF}
json.dump(scene,open(os.path.join(HERE,"site_scene.json"),"w",encoding="utf-8"),ensure_ascii=False,separators=(",",":"))
open(os.path.join(HERE,"site_scene.js"),"w",encoding="utf-8").write("window.SCENE="+json.dumps(scene,ensure_ascii=False,separators=(",",":"))+";")
# OBJ
verts=[]; faces=[]; mats={}
def mtl_for(col):
    k="m_%02x%02x%02x"%(int(col[0]*255),int(col[1]*255),int(col[2]*255)); mats[k]=col; return k
def cuboid(p,s,m):
    x,yq,z=p; sx,sy,sz=s
    pts=[(x,z,yq),(x+sx,z,yq),(x+sx,z,yq+sy),(x,z,yq+sy),(x,z+sz,yq),(x+sx,z+sz,yq),(x+sx,z+sz,yq+sy),(x,z+sz,yq+sy)]
    b=len(verts); verts.extend(pts)
    for q in [(0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]: faces.append((m,[b+i+1 for i in q]))
for bx in boxes: cuboid(bx["position_m"],bx["dimensions_m"],mtl_for(bx["color"]))
open(os.path.join(HERE,"warehouse155_site.mtl"),"w",encoding="utf-8").write("".join(f"newmtl {n}\nKd {c[0]:.3f} {c[1]:.3f} {c[2]:.3f}\nKa 0.08 0.08 0.08\nd 1\nillum 1\n\n" for n,c in mats.items()))
with open(os.path.join(HERE,"warehouse155_site.obj"),"w",encoding="utf-8") as o:
    o.write("# Abuhadi155 5-zone site plan + requirements\nmtllib warehouse155_site.mtl\n")
    for v in verts: o.write("v %.3f %.3f %.3f\n"%v)
    cur=None
    for m,f in faces:
        if m!=cur: o.write("usemtl %s\n"%m); cur=m
        o.write("f "+" ".join(map(str,f))+"\n")
print(json.dumps({"boxes":len(boxes),"verts":len(verts),"warehouses":[w["name"] for w in WH_LIST]},ensure_ascii=False))
