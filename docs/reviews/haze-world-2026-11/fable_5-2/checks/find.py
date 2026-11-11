import json, sys, urllib.request, urllib.parse, time
for q in [l.strip() for l in open(sys.argv[1]) if l.strip()]:
    try:
        url = "https://api.crossref.org/works?rows=2&query.bibliographic=" + urllib.parse.quote(q)
        m = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "doi-check/1.0"}), timeout=40))["message"]["items"]
        print("Q:", q[:90])
        for it in m:
            au = it.get("author", [])
            names = ", ".join(a.get("family", a.get("name", "?")) for a in au[:3]) + (" et al." if len(au) > 3 else "")
            yr = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
            print(f"   {it['DOI']} | {names} | {yr} | {(it.get('title') or ['?'])[0][:100]} | {(it.get('container-title') or ['?'])[0][:40]} {it.get('volume','')}:{it.get('page','')}")
    except Exception as ex:
        print("ERR", q[:60], repr(ex)[:80])
    time.sleep(.4)
