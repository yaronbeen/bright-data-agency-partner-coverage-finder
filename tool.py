"""Map explicit provider evidence into a partner coverage matrix."""
import argparse, json, sys
SAMPLE=[{"provider":"Acme Analytics Studio","region":"North America","specialties":["analytics","implementation"],"evidence_url":"https://example.com/acme/services"},{"provider":"DataWorks GmbH","region":"DACH","specialties":["analytics","migration"],"evidence_url":"https://example.com/dataworks/capabilities"},{"provider":"Growth Partners","region":"North America","specialties":["implementation","training"],"evidence_url":"https://example.com/growth/services"}]
def map_coverage(providers):
    regions={}; evidence=[]
    for p in providers:
        region=p.get("region","unspecified"); slot=regions.setdefault(region,{"providers":[],"specialties":{}}); slot["providers"].append(p.get("provider","unknown"))
        for s in p.get("specialties",[]): slot["specialties"][s]=slot["specialties"].get(s,0)+1
        evidence.append({"provider":p.get("provider"),"region":region,"specialties":p.get("specialties",[]),"source_url":p.get("evidence_url","")})
    return {"provider_count":len(providers),"regions":regions,"evidence":evidence,"gaps":"Review regions or specialties with no sourced provider; sample completeness is unknown.","limits":["Only returned search/web page evidence is represented; not an exhaustive directory.","No people or personal contact data are collected.","Provider claims and availability require direct verification."]}
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("input",nargs="?"); p.add_argument("output",nargs="?",default="coverage.json"); p.add_argument("--sample",action="store_true"); p.add_argument("--live",action="store_true"); p.add_argument("--dry-run",action="store_true"); p.add_argument("--category"); p.add_argument("--geography"); p.add_argument("--partner-type"); a=p.parse_args()
    try:
        if a.live: raise ValueError("Live Web Unlocker collection is disabled until its current official request contract is verified; no request made. SERP endpoint docs are at https://docs.brightdata.com/scraping-automation/serp-api/send-your-first-request")
        data=SAMPLE if a.sample else json.load(open(a.input,encoding="utf-8"))
        if a.dry_run: print(json.dumps({"providers":len(data),"live_calls":0,"category":a.category,"geography":a.geography,"partner_type":a.partner_type})); return 0
        json.dump(map_coverage(data),open(a.output,"w",encoding="utf-8"),indent=2); print(json.dumps({"output":a.output,"providers":len(data)})); return 0
    except (ValueError,OSError,KeyError) as e: print(str(e),file=sys.stderr); return 1
if __name__=="__main__": raise SystemExit(main())
