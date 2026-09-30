# IROPO Business Plan

**International Registry of Pet Offenders (IROPO)**

> This document is a living plan for turning IROPO from a research/prototype repository into a sustainably funded, publicly useful registry. It should be revisited and updated as the project matures — treat it as a companion to the roadmap in [`README.md`](README.md), not a replacement for it.

## 1. Executive summary

IROPO is a nonprofit-oriented animal-welfare project that aggregates public and official records into a single, verifiable source of truth documenting people who have harmed animals, and publishes that information at `iropo.org` for advocates, shelters, rescues, adoption agencies, and the public. Its geographic scope is the United States and beyond: the US first, then only the countries with more people than the US, China and India (Section 3.3).

The project is currently a data-collection and research effort with no revenue, no formal legal entity, and no dedicated funding. This plan defines what IROPO will offer, how it will be built and operated, and — most centrally — how it will be funded, since funding is the current blocker called out in the README's "Mission and goals" and "Roadmap" sections.

## 2. Mission and vision

- **Mission:** Give the public and animal-welfare community a reliable, well-sourced registry of animal-cruelty offenders to support accountability, safer adoptions, and informed advocacy.
- **Vision:** Become the standard reference that shelters, rescues, journalists, and policymakers check before making decisions related to animal welfare and animal-cruelty offenders.
- **Values:** accuracy and provenance over speed; public/official sourcing only; a clear correction and dispute process; privacy- and legal-risk awareness (see README "Legal & ethical considerations").

## 3. What the business will offer

### 3.1 Core offering (free, public good)
- A searchable public registry at `iropo.org` of animal-cruelty offender records, each with source citations, verification status, and a correction/removal path.
- Coverage of the United States (aggregate statistics already span all 50 states and DC), expanding beyond the US only to China and India (Section 3.3).

### 3.2 Supporting offerings (to help fund the core mission)
- **Verified data access / API tier** — a rate-limited or licensed API for shelters, rescues, background-check vendors, and researchers who want structured, machine-readable access beyond the public search UI.
- **Institutional partnerships** — data-sharing or referral agreements with animal-welfare organizations, humane societies, and adoption platforms that want to screen applicants against the registry.
- **Grants-funded research reports** — periodic public reports/dashboards on animal-cruelty trends by state, useful to press and policymakers, tied to grant deliverables.
- **Merchandise / branded donations page** — low-effort, low-priority revenue support (stickers, apparel) tied to the mission, mainly for community engagement rather than material funding.

The core registry must remain free and public; paid tiers apply only to bulk/API/institutional access, not to basic public search.

### 3.3 Geographic scope: the United States and beyond

IROPO is an international registry, but covering every country is not realistic: laws on animal cruelty, court records, and personal data differ from country to country, and many are much stricter than in the US. The scope is therefore limited to countries at least the size of the United States by population:

- **United States** — covered today.
- **China** and **India** — the only countries with more people than the US; planned for Phase 4.

Together these are the world's three most populous countries. Each new country requires its own legal review (Section 5) and source evaluation before any of its data is published. Other countries are out of scope unless this plan is revised.

## 4. Market and users

- **Primary users:** individual members of the public, animal-welfare advocates.
- **Institutional users:** animal shelters, rescues, and adoption agencies performing applicant screening; journalists and researchers; policymakers evaluating animal-cruelty enforcement.
- **Why now:** data already exists (FBI NIBRS, state/local agency records) but is fragmented across incompatible formats and systems; no consolidated, provenance-tracked public registry currently exists.

## 5. Legal and organizational structure

Before any funding or public launch, IROPO needs a formal legal footing:

- Evaluate forming a **501(c)(3) nonprofit** (or fiscal sponsorship under an existing nonprofit) to enable tax-deductible donations and grant eligibility. Fiscal sponsorship is the faster near-term path while full nonprofit status is pursued.
- Obtain legal review specific to publishing personally identifying information about individuals (defamation, privacy, and jurisdiction-specific risk), as flagged in the README's legal & ethical considerations.
- Before expanding beyond the US, obtain a separate legal review for China and India covering animal cruelty law, access to and reuse of court records, and data protection law (China's Personal Information Protection Law; India's Digital Personal Data Protection Act, 2023).
- Define governance: who has authority to add/remove/correct records, and an appeals process for disputed entries.
- Confirm licensing terms for any third-party data sources (e.g., FBI Crime Data API terms of use).

## 6. Implementation plan

This maps directly onto the existing README roadmap, sequenced into phases with funding gates.

> **Status (September 2026):** the canonical record schema and draft publication, correction and dispute policies are done (Phase 0). The automated FBI importer covers all 50 states and DC with provenance and a coverage matrix (Phase 1). The framework decision is made and the public site, search and open-data downloads are live at `iropo.org` on free GitHub Pages hosting (Phase 2). Legal structure, legal review, court-record sources and the individual-record verification workflow remain open. Expansion beyond the United States is limited to China and India (Phase 4). See the [roadmap](https://iropo.org/roadmap/).

### Phase 0 — Foundation (pre-funding)
- Formalize legal structure (fiscal sponsorship or nonprofit filing).
- Define the canonical offender/case record schema (fields, identifiers, source references, dates).
- Draft data governance, verification, and correction/dispute policies.

### Phase 1 — Data aggregation (current focus)
- Catalog and evaluate data sources (FBI NIBRS, state/local agency records, public court records).
- Build a US city/state coverage matrix.
- Build scrapers/importers for the states already represented (NC, ND, NY), then expand.
- Stand up a verification workflow and a single source-of-truth datastore with provenance tracking.

### Phase 2 — Platform and interface
- Choose the framework/deployment model (static/GitHub Pages vs. database-backed application) based on data volume and query needs identified in Phase 1.
- Build the ingestion pipeline, storage model, and update cadence.
- Build the public browse/search interface with citations, verification status, and correction affordances.
- Add accessibility, responsive design, and basic SEO.

### Phase 3 — Launch and growth
- Set up analytics, contact paths, and feedback mechanisms.
- Launch institutional/API access tier for shelters, rescues, and partners.
- Promote across social media and animal-welfare communities.
- Establish an ongoing maintenance plan (updates, reviews, corrections, archival).

### Phase 4 — Beyond the United States
- Obtain a legal review for China and India covering animal cruelty, court record, and personal data law.
- Catalog and evaluate official animal cruelty data and court record sources in each country.
- Recruit volunteers and partners with legal and language expertise in each country.
- Extend the schemas, pipeline, and site to jurisdictions outside the US.
- Publish a country's data only after its legal review is complete.

Each phase should only begin once the funding needed to staff and run it (Section 7) is secured or credibly committed — avoid scaling data collection or publishing faster than verification and legal review can keep up.

## 7. Funding plan

### 7.1 What funding is needed for
- **Hosting and infrastructure:** database hosting, storage for source documents, API infrastructure.
- **Tooling:** scraping/automation tooling, monitoring, backup.
- **Legal review:** attorney time for privacy/defamation review and nonprofit filing, plus a separate review for each country before expanding to China and India.
- **People:** part-time or contract help for data verification, engineering, and design once volunteer capacity is insufficient.
- **Promotion:** basic outreach/design costs for launch materials.

### 7.2 How to raise it
- **Grants:** apply to animal-welfare foundations and philanthropic grant programs (e.g., ASPCA, Petco Love, Bissell Pet Foundation, and similar organizations that fund animal-welfare data/advocacy work) once fiscal sponsorship or nonprofit status is in place.
- **Individual donations:** a donation page on `iropo.org` (via a payment processor or the fiscal sponsor's donation infrastructure) once the site has a public presence worth donating to.
- **Crowdfunding campaign:** a time-boxed campaign (e.g., GoFundMe, Kickstarter-style for nonprofits) to fund a specific milestone, such as "launch the public beta for three states."
- **Corporate/partner sponsorship:** pet-industry companies, shelters, and rescues that benefit from the registry may sponsor hosting or API costs in exchange for recognition or early access.
- **In-kind support:** apply for nonprofit hosting credits/grants (e.g., cloud provider nonprofit programs) and pro-bono legal clinics to reduce cash funding needs before cash funding exists.
- **Volunteer labor:** treat contributor time as the primary "funding" source during Phase 0–1, reserving cash fundraising for Phase 2–3 costs that cannot be met by volunteers (hosting, legal, verification review).

### 7.3 Sequencing
1. Secure fiscal sponsorship or file nonprofit paperwork (unlocks donation/grant eligibility).
2. Launch a simple donation page and a small crowdfunding campaign tied to a concrete milestone (e.g., "complete verified NC/ND/NY data" or "launch public beta").
3. Use early funding to cover hosting/legal costs and any contract help needed for Phase 2.
4. Apply for larger foundation grants once there is a working public beta to point to as evidence of traction.
5. Pursue institutional/API partnerships as a recurring revenue stream once the registry has enough verified coverage to be useful to shelters and rescues.

## 8. Operating budget (illustrative, to be refined)

| Category | Phase 0–1 (pre-launch) | Phase 2–3 (post-launch, annual) |
| --- | --- | --- |
| Hosting/infrastructure | Low (static/GitHub Pages, free tiers) | Moderate (database hosting, API) |
| Legal review | One-time (nonprofit filing + privacy review) | Occasional (dispute/removal cases) |
| Contract/part-time help | Minimal, volunteer-driven | As funding allows, for verification and engineering |
| Promotion | Minimal | Modest (launch campaign, ongoing outreach) |

Exact figures depend on hosting choices and legal counsel quotes; this table should be replaced with real numbers once those quotes are obtained.

## 9. Risks

- **Legal/reputational risk:** publishing information about identifiable individuals carries defamation and privacy risk if sourcing or verification is weak — mitigate with strict public/official sourcing, provenance tracking, and a working correction/removal process before any public launch.
- **Jurisdictional risk:** privacy, records, and defamation laws differ by country and are often stricter than in the US — mitigate by limiting the scope to the US, China, and India and requiring a separate legal review before publishing data from each country.
- **Funding risk:** without a legal entity, donations and grants are not readily available — prioritize Section 5 and 7.3 step 1 early.
- **Volunteer sustainability risk:** as a volunteer-driven project, progress depends on contributor availability — track this openly in `CONTRIBUTING.md` and roadmap issues.
- **Data quality risk:** inconsistent or incomplete source data could undermine trust — verification workflow (Phase 1) must be in place before Phase 2 launch.

## 10. Next steps

- [ ] Decide between fiscal sponsorship and direct nonprofit filing, and start that process.
- [ ] Get a legal review scoped and quoted for privacy/defamation risk.
- [ ] Set up a donation page placeholder and identify 2–3 target grants to apply for once the entity is formed.
- [ ] Continue Phase 1 data-aggregation work in parallel, since it does not require funding to start.
