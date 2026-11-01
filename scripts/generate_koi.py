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

LEVELS = {"NONE":0,"FIRST_QUARTER":1,"SECOND_QUARTER":2,"THIRD_QUARTER":3,"FOURTH_QUARTER":4}

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

def build(weeks):
    W,H = 760,160
    cols = ["#16213a","#0e4429","#006d32","#26a641","#39d353"]
    x0,y0,pitch = 35,34,13
    cells=[]
    for c,week in enumerate(weeks):
        for r,lvl in enumerate(week):
            cells.append(f'<rect x="{x0+c*pitch}" y="{y0+r*pitch}" width="10" height="10" rx="2" fill="{cols[lvl]}"/>')

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
{chr(10).join(parts)}
</svg>'''

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    open(OUT,"w").write(build(fetch_weeks()))
    print("wrote", OUT)
