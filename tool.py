"""Find organization-level service partner evidence using bounded Bright Data SERP + Web Unlocker calls."""
import argparse, html, ipaddress, json, os, re, sys, urllib.error, urllib.parse, urllib.request

SAMPLE=[{"provider":"Acme Analytics Studio","region":"North America","partner_type":"agency","specialties":["analytics","implementation"],"evidence_url":"https://example.com/acme/services"},{"provider":"DataWorks GmbH","region":"DACH","partner_type":"agency","specialties":["analytics","migration"],"evidence_url":"https://example.com/dataworks/capabilities"},{"provider":"Growth Partners","region":"North America","partner_type":"consultancy","specialties":["implementation","training"],"evidence_url":"https://example.com/growth/services"}]
API_URL="https://api.brightdata.com/request"
MAX_RESULTS=5

class BrightDataError(Exception):
    def __init__(self,code,message): self.code=code; super().__init__(message)

def request_json(payload,key,timeout=75):
    request=urllib.request.Request(API_URL,data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(request,timeout=timeout) as response:
            body=response.read().decode()
            if response.status<200 or response.status>=300: raise BrightDataError("http_error",f"Bright Data returned HTTP {response.status}")
    except urllib.error.HTTPError as e: raise BrightDataError("http_error",f"Bright Data returned HTTP {e.code}") from e
    try: return json.loads(body)
    except json.JSONDecodeError as e: raise BrightDataError("invalid_response","Bright Data response was not valid JSON") from e

def request_text(payload,key,timeout=75):
    request=urllib.request.Request(API_URL,data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(request,timeout=timeout) as response:
            if response.status<200 or response.status>=300: raise BrightDataError("http_error",f"Bright Data returned HTTP {response.status}")
            raw=response.read().decode(errors="replace")
    except urllib.error.HTTPError as e: raise BrightDataError("http_error",f"Bright Data returned HTTP {e.code}") from e
    try: result=json.loads(raw)
    except json.JSONDecodeError as e: raise BrightDataError("invalid_response","Web Unlocker response was not valid JSON") from e
    if not isinstance(result,dict) or not isinstance(result.get("status_code"),int) or not isinstance(result.get("body"),str): raise BrightDataError("invalid_response","Web Unlocker response lacked status_code/body")
    if not 200<=result["status_code"]<300: raise BrightDataError("target_error",f"Target page returned HTTP {result['status_code']}")
    return result["body"]

def filter_results(results,category,geography,partner_type):
    terms=[category,geography,partner_type]
    filtered=[]
    for row in results:
        if not isinstance(row,dict) or not all(term.casefold() in " ".join(str(row.get(k,"")) for k in ("title","description","link")).casefold() for term in terms): continue
        url=row.get("link")
        try: validate_public_url(url)
        except ValueError: continue
        filtered.append(row)
    return filtered

def validate_public_url(url):
    parts=urllib.parse.urlsplit(url) if isinstance(url,str) else None
    if not parts or parts.scheme!="https" or not parts.hostname or parts.username or parts.password: raise ValueError("Only credential-free public HTTPS provider URLs are allowed")
    host=parts.hostname.lower().rstrip(".")
    if host=="localhost" or host.endswith((".localhost",".local",".internal")): raise ValueError("Local/private provider URLs are not allowed")
    try:
        address=ipaddress.ip_address(host)
        if not address.is_global: raise ValueError("Private/reserved provider IPs are not allowed")
    except ValueError as e:
        if "not allowed" in str(e): raise
    return url

def search_serp(category,geography,partner_type,key,zone):
    query=urllib.parse.urlencode({"q":f"{category} {geography} {partner_type}","hl":"en"})
    target="https://www.google.com/search?"+query
    payload={"zone":zone,"url":target,"format":"raw","data_format":"parsed_light"}
    data=request_json(payload,key)
    results=data.get("organic") if isinstance(data,dict) else None
    if not isinstance(results,list): raise BrightDataError("invalid_response","SERP response lacked an organic result array")
    return results

def find_partners(category,geography,partner_type,key,serp_zone,unlocker_zone,max_pages=MAX_RESULTS):
    if not all(isinstance(v,str) and v.strip() for v in (category,geography,partner_type)): raise ValueError("Category, geography, and partner type are all required")
    if not 1<=max_pages<=MAX_RESULTS: raise ValueError(f"max_pages must be between 1 and {MAX_RESULTS}")
    if not key or not serp_zone or not unlocker_zone: raise ValueError("API key, SERP zone, and Web Unlocker zone are required")
    filtered=filter_results(search_serp(category.strip(),geography.strip(),partner_type.strip(),key,serp_zone),category.strip(),geography.strip(),partner_type.strip())[:max_pages]
    providers=[]
    for row in filtered:
        url=row["link"]
        validate_public_url(url)
        try: page=request_text({"zone":unlocker_zone,"url":url,"format":"raw"},key)
        except BrightDataError: raise
        page_text=html.unescape(re.sub(r"\s+"," ",re.sub(r"<[^>]*>"," ",page))).casefold()
        corroborated=category.casefold() in page_text and partner_type.casefold() in page_text
        if not corroborated: continue
        providers.append({"provider":urllib.parse.urlsplit(url).hostname,"region":geography.strip(),"specialties":[category.strip()],"partner_type":partner_type.strip(),"fit_rationale":f"SERP result matched all three requested terms; unlocked page text also contains {category} and {partner_type}.","evidence_url":url,"matched_search_dimensions":[category.strip(),geography.strip(),partner_type.strip()],"page_corroborates_requested_service":True,"provenance":{"provider":"source hostname; SERP titles and snippets are not retained","region":"operator query matched in SERP result","specialties":"operator query matched in SERP result and unlocked page","partner_type":"operator query matched in SERP result and unlocked page","evidence_url":"SERP organic result URL","page_corroboration":"Bright Data Web Unlocker raw public page response; response body itself is not retained in the report"}})
    return providers

def map_coverage(providers):
    regions={}; evidence=[]
    for p in providers:
        region=p.get("region","unspecified"); slot=regions.setdefault(region,{"providers":[],"specialties":{}}); slot["providers"].append(p.get("provider","unknown"))
        for s in p.get("specialties",[]): slot["specialties"][s]=slot["specialties"].get(s,0)+1
        evidence.append({"provider":p.get("provider"),"region":region,"specialties":p.get("specialties",[]),"partner_type":p.get("partner_type"),"fit_rationale":p.get("fit_rationale"),"matched_search_dimensions":p.get("matched_search_dimensions"),"page_corroborates_requested_service":p.get("page_corroborates_requested_service"),"source_url":p.get("evidence_url",""),"provenance":p.get("provenance","supplied evidence")})
    return {"provider_count":len(providers),"regions":regions,"evidence":evidence,"gaps":"Review requested regions or specialties with no sourced provider; absence from this bounded search is not evidence that no provider exists.","limits":["Only returned search/page evidence is represented; not an exhaustive directory.","No people or personal contact data are collected.","Provider claims and availability require direct verification."]}

def filter_providers(providers,category,geography,partner_type):
    if not all(isinstance(v,str) and v.strip() for v in (category,geography,partner_type)): raise ValueError("Filtering requires category, geography, and partner type together")
    return [r for r in providers if category.casefold() in " ".join(map(str,r.get("specialties",[]))).casefold() and geography.casefold() in str(r.get("region","")).casefold() and partner_type.casefold() in str(r.get("partner_type","")).casefold()]

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("input",nargs="?"); p.add_argument("output",nargs="?",default="coverage.json"); p.add_argument("--sample",action="store_true"); p.add_argument("--live",action="store_true"); p.add_argument("--dry-run",action="store_true"); p.add_argument("--category"); p.add_argument("--geography"); p.add_argument("--partner-type"); p.add_argument("--max-pages",type=int,default=MAX_RESULTS); a=p.parse_args(argv)
    try:
        if a.sample and a.live: raise ValueError("--sample is offline-only and cannot be combined with --live")
        if a.live:
            if not all(v and v.strip() for v in (a.category,a.geography,a.partner_type)): raise ValueError("--category, --geography, and --partner-type are required with --live")
            if not 1<=a.max_pages<=MAX_RESULTS: raise ValueError(f"--max-pages must be between 1 and {MAX_RESULTS}")
            if a.dry_run: print(json.dumps({"live":True,"requests_max":1+a.max_pages,"max_serp_results":a.max_pages,"category":a.category,"geography":a.geography,"partner_type":a.partner_type})); return 0
            key=os.environ.get("BRIGHT_DATA_API_KEY"); serp_zone=os.environ.get("BRIGHT_DATA_SERP_ZONE"); unlocker_zone=os.environ.get("BRIGHT_DATA_WEB_UNLOCKER_ZONE")
            if not all((key,serp_zone,unlocker_zone)): raise ValueError("Set BRIGHT_DATA_API_KEY, BRIGHT_DATA_SERP_ZONE, and BRIGHT_DATA_WEB_UNLOCKER_ZONE")
            providers=find_partners(a.category,a.geography,a.partner_type,key,serp_zone,unlocker_zone,a.max_pages)
        else:
            if a.sample: providers=SAMPLE
            elif a.input:
                providers=json.load(open(a.input,encoding="utf-8"))
                if not isinstance(providers,list) or any(not isinstance(r,dict) for r in providers): raise ValueError("Input must be a JSON array of provider records")
            else: p.error("Use --sample, a provider JSON input, or --live with all query dimensions")
            if a.category or a.geography or a.partner_type: providers=filter_providers(providers,a.category,a.geography,a.partner_type)
            if a.dry_run: print(json.dumps({"providers":len(providers),"live_calls":0})); return 0
        report=map_coverage(providers)
        report["query"]={"category":a.category,"geography":a.geography,"partner_type":a.partner_type} if any((a.category,a.geography,a.partner_type)) else None
        if report["query"]:
            report["requested_coverage"]={"region":a.geography,"specialty":a.category,"partner_type":a.partner_type,"status":"evidence_found" if providers else "no_provider_evidence_found","interpretation":"No result in this bounded sample is not proof of no provider coverage."}
        with open(a.output,"w",encoding="utf-8") as f: json.dump(report,f,indent=2)
        print(json.dumps({"output":a.output,"providers":len(providers)})); return 0
    except BrightDataError as e: print(json.dumps({"error":{"code":e.code,"message":str(e),"retryable":False}}),file=sys.stderr); return 1
    except urllib.error.URLError: print(json.dumps({"error":{"code":"transport_error","message":"Bright Data request failed at transport level","retryable":False}}),file=sys.stderr); return 1
    except (ValueError,OSError,KeyError,json.JSONDecodeError) as e: print(json.dumps({"error":{"code":"input_error","message":str(e),"retryable":False}}),file=sys.stderr); return 1
if __name__=="__main__": raise SystemExit(main())
