import json, os, sys, urllib.request

USER = os.environ.get("GH_USER", "arzaanxeng")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUT = os.environ.get("OUT_FILE", "dist/koi-contribution.svg")

QUERY = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{
        weeks{ contributionDays{ contributionLevel } }
      }
    }
  }
}"""

LEVELS = {"NONE":0,"FIRST_QUARTILE":1,"SECOND_QUARTILE":2,"THIRD_QUARTILE":3,"FOURTH_QUARTILE":4}

# ---- glow settings (the only new part) ----
GLOW_COLOR = "#ff9a3c"   # color the blocks turn when the koi swims near
GLOW_RADIUS = 42         # how far (pixels) the glow reaches around the koi
FADE_SPEED = 0.93        # closer to 1 = glow fades back slower

def fetch_weeks():
    if os.environ.get("FAKE_DATA"):          # only for offline testing
        import random; random.seed(1)
        return [[random.choices(range(5),[40,20,18,14,8])[0] for _ in range(7)] for _ in range(53)]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query":QUERY,"variables":{"login":USER}}).encode(),
        headers={"Authorization":f"bearer {TOKEN}","Content-Type":"application/json"})
    data = json.load(urllib.request.urlopen(req))
    if "errors" in data: sys.exit(f"GitHub error: {data['errors']}")
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [[LEVELS[d["contributionLevel"]] for d in w["contributionDays"]] for w in weeks]

# ---- glow helpers: work out where the koi is at every moment of its lap ----
PATH_START = (90,75)
PATH_SEGS = [((90,30),(250,25),(380,65)),((510,105),(670,120),(670,75)),
             ((670,30),(520,25),(380,85)),((240,145),(90,120),(90,75))]

def sample_path(per=80):
    pts=[PATH_START]; cur=PATH_START
    for a,b,e in PATH_SEGS:
        for k in range(1,per+1):
            t=k/per; u=1-t
            pts.append((u**3*cur[0]+3*u*u*t*a[0]+3*u*t*t*b[0]+t**3*e[0],
                        u**3*cur[1]+3*u*u*t*a[1]+3*u*t*t*b[1]+t**3*e[1]))
        cur=e
    cum=[0.0]
    for i in range(1,len(pts)):
        cum.append(cum[-1]+((pts[i][0]-pts[i-1][0])**2+(pts[i][1]-pts[i-1][1])**2)**.5)
    return pts,cum

def point_at(pts,cum,frac):
    target=frac*cum[-1]
    for i in range(1,len(cum)):
        if cum[i]>=target:
            t=(target-cum[i-1])/max(cum[i]-cum[i-1],1e-9)
            return (pts[i-1][0]+t*(pts[i][0]-pts[i-1][0]), pts[i-1][1]+t*(pts[i][1]-pts[i-1][1]))
    return pts[-1]

def rdp(points, eps):
    """keeps only the points needed to draw the curve (keeps the file small)"""
    if len(points) < 3: return points
    (x1,y1),(x2,y2) = points[0], points[-1]
    worst, idx = 0, 0
    for i in range(1,len(points)-1):
        x,y = points[i]
        d = abs(y - (y1 + (y2-y1)*(x-x1)/max(x2-x1,1e-9)))
        if d > worst: worst, idx = d, i
    if worst > eps:
        return rdp(points[:idx+1],eps)[:-1] + rdp(points[idx:],eps)
    return [points[0], points[-1]]

def glow_layer(centers, dur):
    pts,cum = sample_path()
    N = 240
    head = [point_at(pts,cum,k/N) for k in range(N)]
    rects=[]
    for (x,y,cx,cy) in centers:
        prox=[]
        for hx,hy in head:
            d=((hx-cx)**2+(hy-cy)**2)**.5
            prox.append(max(0.0, min(1.0, (GLOW_RADIUS-d)/(GLOW_RADIUS*0.6))))
        if max(prox) < 0.05: continue
        o=[0.0]*N
        for _ in range(2):                      # two laps so the fade wraps around
            prev=o[-1]
            for k in range(N):
                prev=max(prox[k], prev*FADE_SPEED)
                o[k]=prev
        keep=rdp([(k/N, o[k]) for k in range(N)] + [(1.0, o[0])], 0.03)
        times=";".join(f"{t:.4f}" for t,_ in keep)
        vals=";".join(f"{v*0.9:.2f}" for _,v in keep)
        rects.append(f'<rect x="{x}" y="{y}" width="10" height="10" rx="2" fill="{GLOW_COLOR}" opacity="0">'
                     f'<animate attributeName="opacity" values="{vals}" keyTimes="{times}" dur="{dur}s" repeatCount="indefinite"/></rect>')
    return "\n".join(rects)

def build(weeks):
    W,H = 760,160
    cols = ["#16213a","#0e4429","#006d32","#26a641","#39d353"]
    x0,y0,pitch = 35,34,13
    cells=[]; centers=[]
    for c,week in enumerate(weeks):
        for r,lvl in enumerate(week):
            cells.append(f'<rect x="{x0+c*pitch}" y="{y0+r*pitch}" width="10" height="10" rx="2" fill="{cols[lvl]}"/>')
            centers.append((x0+c*pitch, y0+r*pitch, x0+c*pitch+5, y0+r*pitch+5))

    PATH="M90,75 C90,30 250,25 380,65 C510,105 670,120 670,75 C670,30 520,25 380,85 C240,145 90,120 90,75 Z"
    DUR=24; STEP=0.2
    radii=[7,7.6,7.2,6.4,5.5,4.6,3.7,2.9,2.1]
    colors=["#ff7a1a","#fff4e6","#ff7a1a","#e53935","#ff7a1a","#fff4e6","#ff7a1a","#ff9a3c","#ffb066"]
    def motion(i):
        b = 0 if i==0 else -(DUR-i*STEP)
        return f'<animateMotion dur="{DUR}s" begin="{b:.2f}s" repeatCount="indefinite" rotate="auto" path="{PATH}"/>'
    n=len(radii)-1
    parts=[f'''<g>{motion(n)}<g><path d="M0,0 C-8,-6 -14,-9 -22,-10 C-17,0 -17,0 -22,10 C-14,9 -8,6 0,0Z" fill="#ffb066" opacity=".85"/><animateTransform attributeName="transform" type="rotate" values="-14;14;-14" dur="0.9s" repeatCount="indefinite"/></g></g>''']
    for i in range(n,0,-1):
        extra=""
        if i==2:
            extra='''<ellipse cx="-2" cy="-8" rx="6" ry="2.5" fill="#ffb066" opacity=".8"><animateTransform attributeName="transform" type="rotate" values="-15 0 -6;15 0 -6;-15 0 -6" dur="1.6s" repeatCount="indefinite"/></ellipse><ellipse cx="-2" cy="8" rx="6" ry="2.5" fill="#ffb066" opacity=".8"><animateTransform attributeName="transform" type="rotate" values="15 0 6;-15 0 6;15 0 6" dur="1.6s" repeatCount="indefinite"/></ellipse>'''
        parts.append(f'<g>{motion(i)}{extra}<circle r="{radii[i]}" fill="{colors[i]}"/></g>')
    parts.append(f'''<g>{motion(0)}<ellipse rx="10" ry="6.5" fill="#ff7a1a"/><ellipse cx="-1" rx="4" ry="3" fill="#e53935"/><circle cx="5" cy="-3.2" r="1.3" fill="#111"/><circle cx="5" cy="3.2" r="1.3" fill="#111"/></g>''')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<title>Koi swimming over {USER}'s contribution graph</title>
<defs><linearGradient id="w" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b1020"/><stop offset="1" stop-color="#0d1b2e"/></linearGradient></defs>
<rect width="{W}" height="{H}" rx="12" fill="url(#w)"/>
{chr(10).join(cells)}
{glow_layer(centers, DUR)}
{chr(10).join(parts)}
</svg>'''

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    open(OUT,"w").write(build(fetch_weeks()))
    print("wrote", OUT)
