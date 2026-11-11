import json, sys, urllib.request, urllib.parse, time
dois = [l.strip() for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]
for d in dois:
    try:
        req = urllib.request.Request("https://api.crossref.org/works/" + urllib.parse.quote(d), headers={"User-Agent": "doi-check/1.0"})
        m = json.load(urllib.request.urlopen(req, timeout=30))["message"]
        au = m.get("author", [])
        names = ", ".join(a.get("family", a.get("name", "?")) for a in au[:4]) + (" et al." if len(au) > 4 else "")
        yr = (m.get("issued", {}).get("date-parts") or [[None]])[0][0]
        print(f"OK  {d} | {names} | {yr} | {(m.get('title') or ['?'])[0][:110]} | {(m.get('container-title') or ['?'])[0]} {m.get('volume','')}:{m.get('page','')}")
    except Exception as ex:
        print(f"ERR {d} | {repr(ex)[:80]}")
    time.sleep(.3)
