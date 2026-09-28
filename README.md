# Agency / Partner Coverage Finder

Build a coverage map from provider capability evidence gathered for an explicitly selected product/service category, geography, and partner type. It helps a channel or partnerships lead see which region/specialty gaps need research and which candidate providers merit human qualification.

## Who, why, decision

For partner/channel teams, not sales lead-generation teams. Category, geography, and partner type are required live search inputs and are included in the Google query. Only results whose title/snippet/link contain all three requested terms are fetched for corroborating public-page evidence. Returned records are tagged with source/provenance; they do not scrape personal contacts, infer provider availability, or create an account territory plan.

## Workflow and synthetic example -> decision

The synthetic sample has three fictitious providers: two in North America and one in DACH, with analytics, implementation, migration, and training capability tags. Run `python3 tool.py --sample --category analytics --geography DACH --partner-type agency`. The output shows sourced entries by region; a human can identify regions/specialties to research further. It is not proof that the map is complete.

## Quick start

```bash
python3 tool.py --sample
python3 tool.py provider_evidence.json coverage.json
python3 -m pytest -q
```

Live use requires explicit opt-in, query inputs, `BRIGHT_DATA_API_KEY`, `BRIGHT_DATA_SERP_ZONE`, and `BRIGHT_DATA_WEB_UNLOCKER_ZONE`. It performs one SERP request and at most five Web Unlocker fetches, with no automatic retries:

```bash
python3 tool.py --live --dry-run --category analytics --geography DACH --partner-type agency
BRIGHT_DATA_API_KEY="..." BRIGHT_DATA_SERP_ZONE="..." BRIGHT_DATA_WEB_UNLOCKER_ZONE="..." \
  python3 tool.py --live --category analytics --geography DACH --partner-type agency --max-pages 5
```

Both requests are grounded in current official references: [SERP API introduction](https://docs.brightdata.com/scraping-automation/serp-api/introduction) documents `POST https://api.brightdata.com/request`, bearer auth, JSON `zone`, target `url`, `format: raw`, and `data_format: parsed_light`; the [SERP first-request guide](https://docs.brightdata.com/products/serp-api/send-your-first-request) gives the direct request structure. The [Web Unlocker API reference](https://docs.brightdata.com/api-reference/rest-api/unlocker/unlock-website) documents the direct endpoint, auth, `zone`, `url`, and `format: raw`, and returns JSON with `status_code`, `headers`, and `body`. The CLI checks both provider and target statuses and extracts only the returned page body. Check current [pricing](https://brightdata.com/pricing/serp) and Web Unlocker account access first. CI and dry-runs make no calls.

## Outputs and caveats

Coverage JSON reports providers found, an explicit requested-region/specialty status (including `no_provider_evidence_found`), matched search dimensions, rationale, and source URLs. Provider identity is represented by the source hostname; SERP titles/snippets and unlocked page bodies are not retained, avoiding accidental contact-detail output. Search results and public site claims may be incomplete, stale, or self-reported. Provider existence, capabilities, geography, willingness, and availability require direct validation. No result in a bounded query does not prove a regional or specialty gap in reality; no completeness percentage or market census is implied.

## Differentiation

Unlike `bright-data-territory-planner`, this maps potential service partners by geography and specialty, not company/account counts or territory capacity. Unlike local presence audits, it is not a listing audit. Unlike `bright-data-serp-market-map` or generic SERP exports, the decision is partner coverage gaps, and unlike lead harvesters it does not seek individual contacts.

## Safety and FAQ

Only explicit public provider/category/geography inputs are in scope. No personal contact scraping or private/local targets. All query inputs, credentials, and page caps are validated before requests. Structured errors omit tokens; requests are not retried. Offline sample/tests and `--dry-run` make no calls. Never commit credentials; `.env` is ignored.

**Is the coverage exhaustive?** No. It represents evidence supplied or returned for the requested search scope.

**Does it find a person to contact?** No. The output is organization capability evidence only.

MIT License. Independent demonstration; not affiliated with or endorsed by Bright Data.
