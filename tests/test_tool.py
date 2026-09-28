import tool
import json
import urllib.parse


def test_maps_provider_evidence_to_regions_and_specialties():
    report = tool.map_coverage(tool.SAMPLE)
    assert report["provider_count"] == 3
    assert "DACH" in report["regions"]
    assert report["evidence"]


def test_no_people_contacts_in_output():
    assert "contacts" not in tool.map_coverage(tool.SAMPLE)

def test_serp_and_unlocker_requests_use_official_contracts(monkeypatch):
    calls=[]
    class Response:
        status=200
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self): return (json.dumps({"organic":[{"link":"https://agency.example/services","title":"Analytics partner for DACH agencies","description":"Agency analytics implementation. Contact person@example.org or +1 212 555 0199"}]}).encode() if len(calls)==1 else json.dumps({"status_code":200,"headers":{"content-type":"text/html"},"body":"<p>DACH analytics agency partner. Contact person@example.org at +1 212 555 0199</p>"}).encode())
    monkeypatch.setattr(tool.urllib.request,"urlopen",lambda req,timeout:(calls.append((req.full_url,json.loads(req.data),req.get_header("Authorization"))) or Response()))
    records=tool.find_partners("analytics","DACH","agency","key","serp-zone","unlock-zone")
    assert len(calls)==2
    assert calls[0][0]=="https://api.brightdata.com/request"
    assert calls[0][1]["zone"]=="serp-zone" and urllib.parse.parse_qs(urllib.parse.urlsplit(calls[0][1]["url"]).query)["q"]==["analytics DACH agency"]
    assert calls[0][1]["format"]=="raw" and calls[0][1]["data_format"]=="parsed_light"
    assert calls[0][2]==calls[1][2]=="Bearer key"
    assert calls[1][1]=={"zone":"unlock-zone","url":"https://agency.example/services","format":"raw"}
    assert records[0]["evidence_url"]=="https://agency.example/services"
    assert "fit_rationale" in records[0]
    assert records[0]["page_corroborates_requested_service"] is True
    assert "page_evidence_excerpt" not in records[0]
    assert "person@example.org" not in json.dumps(records)
    assert "212 555 0199" not in json.dumps(records)

def test_filters_search_results_against_all_requested_dimensions():
    results=[{"link":"https://a.example/","title":"Analytics agency DACH","description":"partner"},{"link":"https://b.example/","title":"Analytics agency","description":"North America"}]
    assert [r["link"] for r in tool.filter_results(results,"analytics","DACH","agency")] == ["https://a.example/"]
    assert [r["provider"] for r in tool.filter_providers(tool.SAMPLE,"analytics","DACH","agency")] == ["DataWorks GmbH"]

def test_caps_and_required_inputs_fail_before_network(monkeypatch):
    monkeypatch.setattr(tool.urllib.request,"urlopen",lambda *a,**k:(_ for _ in ()).throw(AssertionError("network called")))
    try: tool.find_partners("","DACH","agency","key","zone","unlock")
    except ValueError: pass
    else: assert False
    try: tool.find_partners("analytics","DACH","agency","key","zone","unlock",max_pages=6)
    except ValueError: pass
    else: assert False
