# Agency / Partner Coverage Finder

Build a coverage map from provider capability evidence gathered for an explicitly selected product/service category, geography, and partner type. It helps a channel or partnerships lead see which region/specialty gaps need research and which candidate providers merit human qualification.

## Who, why, decision

For partner/channel teams, not sales lead-generation teams. The offline tool consumes provider records with provider name, region, specialties, and evidence URL. A live SERP + Web Unlocker workflow is intended to collect public capability evidence for explicit search inputs; it does not scrape personal contacts, infer provider availability, or create an account territory plan.

## Workflow and synthetic example -> decision

The synthetic sample has three fictitious providers: two in North America and one in DACH, with analytics, implementation, migration, and training capability tags. Run `python3 tool.py --sample --category analytics --geography DACH --partner-type agency`. The output shows sourced entries by region; a human can identify regions/specialties to research further. It is not proof that the map is complete.

## Quick start

```bash
python3 tool.py --sample
python3 tool.py provider_evidence.json coverage.json
python3 -m pytest -q
```

Live collection is explicitly disabled because the official Web Unlocker request reference could not be verified during this build; `--live` fails closed and makes no request. The existing account-tested SERP CLI documents `POST https://api.brightdata.com/request` with `zone`, target URL, `brd_json=1`; see [official SERP request guide](https://docs.brightdata.com/scraping-automation/serp-api/send-your-first-request) and the sibling `bright-data-google-search-scraper`. Do not infer the Web Unlocker contract from SERP. Once enabled, bound query counts and page fetches, require operator opt-in, and check the current [pricing](https://brightdata.com/pricing).

## Outputs and caveats

Coverage JSON reports region/provider counts, observed specialty labels, and source URLs. Search results and publicly visible site claims may be incomplete, stale, or self-reported. Provider existence, capabilities, geography, willingness, and availability require direct validation. No completeness percentage or market census is implied.

## Differentiation

Unlike `bright-data-territory-planner`, this maps potential service partners by geography and specialty, not company/account counts or territory capacity. Unlike local presence audits, it is not a listing audit. Unlike `bright-data-serp-market-map` or generic SERP exports, the decision is partner coverage gaps, and unlike lead harvesters it does not seek individual contacts.

## Safety and FAQ

Only explicit public provider/category/geography inputs are in scope. No personal contact scraping or private pages. Offline sample/tests make no calls. Never commit credentials; `.env` is ignored.

**Is the coverage exhaustive?** No. It represents evidence supplied or returned for the requested search scope.

**Does it find a person to contact?** No. The output is organization capability evidence only.

MIT License. Independent demonstration; not affiliated with or endorsed by Bright Data.
