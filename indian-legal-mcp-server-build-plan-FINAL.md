# Build Plan: Indian Legal MCP Server — Final Specification

> **Version:** 3.0 (Stress-Tested & Corrected)
> **Date:** 2026-07-16
> **Status:** Ready for execution

**Hand this file to Claude Code as the working spec.** Follows the conventions of
`redhat-data-and-ai/template-mcp-server` (FastMCP + FastAPI, one file per tool, structured
dict returns, docstring metadata blocks, pytest per tool).

---

## Preamble: What This Plan Learned the Hard Way

This plan was stress-tested before a single line of code was written. The architecture
survived. The original execution plan did not. Here's what broke and what was fixed:

| What Broke | Root Cause | How It's Fixed Here |
|---|---|---|
| 33-day timeline for 16 tools | Confused *specifying* data schema with *populating* 1,850 sections | Realistic 12-14 week timeline with 4 milestones (v0.1 → v0.5 → v1.0 → v1.5) |
| 10 acts in Phase 1 | ~1,850 sections × 15 fields each = 200+ hours of data work | v0.1 starts with 3 acts, 5-field schema. Full schema earned in v0.5+ |
| "Source the bare acts" in one line | India Code portal is JS-rendered, rate-limited, inconsistently formatted | Explicit data sourcing strategy with existing open-source repos + semi-automated pipeline |
| No defined target user | Building for citizens, advocates, students, NRIs simultaneously → scope creep | Primary user: **junior/mid-level mofussil advocate**. Others expand from that base |
| 16 tools in v1 | RTI generator shares zero infrastructure with bail assessment | v1.0 ships 7 tools. Rest deferred to v1.5+ with clear gates |
| `cause_list_checker` via web scraping | 25 HCs with different formats, CAPTCHAs, PDFs, broken sites. A product, not a tool. | **Cut from v1 entirely.** Revisit via eCourts API provider in v2 only |
| EN + HI + MR as P0 | 3× data, 3× templates, 3× LLM prompt tuning, 3× test surface | EN output only through v0.5. Accept HI/MR *input* from day 1 (free — LLM understands it). HI output in v1.0. MR in v1.5 |
| No quality targets | `limitation_calculator` wrong 2% of the time → cases permanently dismissed | Zero-tolerance error budget for `limitation_calculator` + `bail_assessment`. Confidence scores on every tool |
| Citation validation via regex | Legal citations have 10+ formats across EN/HI/MR. Regex can't cover them all | Constrained LLM output: `[act_id.s.NUMBER]` bracket notation → post-processor expands to human-readable |
| No monitoring/feedback | No way to know if tools return wrong answers post-deployment | `submit_feedback` tool + anonymized usage telemetry |
| BM25 + FTS5 redundancy | SQLite FTS5 already has built-in BM25 ranking | Drop `rank_bm25` package. Use FTS5's native `bm25()` function |
| Aadhaar regex matched PAN format | Aadhaar = 12 digits, not alphanumeric | Fixed regex: `\d{4}[\s-]?\d{4}[\s-]?\d{4}` |
| State-specific law handwaved | Labor codes not notified in most states. Land law is 100% state-specific | `state_applicability` field on statute responses. Land law explicitly out-of-scope for v1 |

**What survived the stress test unchanged** (these are genuine strengths):

1. **Citations from indexed data only, never LLM memory** — architecturally enforced, not just a prompt instruction
2. **BM25 over embeddings for v1** — legal search is keyword-dominated; embeddings are premature optimization
3. **`draft_pending_review` status for all document-generating tools** — never `"success"` for notices/complaints
4. **Partial failure degradation in the orchestrator** — `explain_situation` continues with available data when sub-tools fail
5. **Template structure + LLM-generated content separation in notices** — Jinja skeleton for boilerplate, LLM only for fact paragraphs
6. **Privacy-by-design with PII hashing** — scenario inputs never logged verbatim, DPDP 2023 compliant
7. **Provider-agnostic abstraction** — swap LLM provider or eCourts provider without touching tool code

---

## Table of Contents

0. [Design Principles & Constraints](#0-design-principles--constraints)
1. [Project Setup](#1-project-setup)
2. [Target User & Prioritization](#2-target-user--prioritization)
3. [Architecture Overview](#3-architecture-overview)
4. [Data Layer — The Foundation (and the Hardest Part)](#4-data-layer--the-foundation)
5. [Quality Targets & Error Budgets](#5-quality-targets--error-budgets)
6. [v1 Tool Suite (7 Tools)](#6-v1-tool-suite-7-tools)
7. [v1.5+ Deferred Tools (9 Tools)](#7-v15-deferred-tools-9-tools)
8. [Orchestration & Intelligence Layer](#8-orchestration--intelligence-layer)
9. [LLM Integration Architecture](#9-llm-integration-architecture)
10. [Multi-Language Strategy](#10-multi-language-strategy)
11. [Production Hardening](#11-production-hardening)
12. [Monitoring, Observability & Feedback](#12-monitoring-observability--feedback)
13. [Build Order — Phased Execution (Realistic)](#13-build-order--phased-execution)
14. [Legal & Regulatory Compliance](#14-legal--regulatory-compliance)
15. [Non-Negotiables](#15-non-negotiables)
16. [Decisions Required Before Start](#16-decisions-required-before-start)
17. [Full Roadmap (v0.1 → v2.0)](#17-full-roadmap)
18. [Appendix A: Statute Coverage Matrix](#appendix-a-statute-coverage-matrix)
19. [Appendix B: Test Scenario Bank](#appendix-b-test-scenario-bank)
20. [Appendix C: Stress Test Record](#appendix-c-stress-test-record)

---

## 0. Design Principles & Constraints

These are not aspirations. They are hard constraints. If a decision conflicts with
any of these, the decision is wrong.

### Principles

1. **Accuracy over breadth.** 5 acts with zero-defect data beats 40 acts with gaps.
   Ship fewer tools that work perfectly rather than many tools that work "mostly."

2. **Indexed data over LLM memory.** Every statute citation, every limitation period,
   every bailable/non-bailable classification comes from the local data index. Never
   from the LLM's parametric knowledge. This is the #1 architectural rule.

3. **Graceful degradation over hard failure.** If an external API is down, the
   orchestrator continues with local data. The user gets 70% of the answer, not an
   error page.

4. **Draft over final.** Any tool that generates a document a human might sign, file,
   or serve returns `status: "draft_pending_review"`. Never `"success"`.

5. **Privacy by default.** Scenario inputs are hashed, not logged. PII is redacted.
   7-day log retention. No training data collection. DPDP 2023 compliant from day 1.

6. **Ship and learn.** v0.1 goes in front of 3 advocates in 2 weeks. Their usage
   patterns determine what gets built next, not a spec written months in advance.

### Constraints

- **Solo developer (you) + LLM assistance.** No dedicated legal research team.
  Data curation speed is the bottleneck, not code speed.
- **Budget-conscious.** External APIs (eCourts, Indian Kanoon, Claude) are metered.
  Every `explain_situation` call costs real money. Design to minimize API calls.
- **No venture funding.** This is a practitioner tool, not a startup pitch.
  Over-engineering is a bigger risk than under-building.

---

## 1. Project Setup

```bash
git clone https://github.com/redhat-data-and-ai/template-mcp-server.git indian-legal-mcp-server
cd indian-legal-mcp-server
rm -rf .git && git init
```

**Rename** per the template's checklist (`template-mcp-server` → `indian-legal-mcp-server`,
`template_mcp_server` → `indian_legal_mcp_server`) in:
`pyproject.toml`, `Makefile`, `Containerfile`, `compose.yaml`, `deployment/openshift/*`,
`.github/workflows/*`, `README.md`, `.env.example`.

Verify with:
```bash
grep -rn "template.mcp" --include="*.py" --include="*.yaml" --include="*.yml" --include="*.toml" --include="*.md" .
```

Then:
```bash
make install   # venv + deps + pre-commit
cp .env.example .env
make local     # confirm http://localhost:5001/health works before adding anything
```

---

## 2. Target User & Prioritization

### Primary User: Junior/Mid-Level Mofussil Advocate (1-10 years practice)

**Why this user:**
- Most underserved by existing legal tech (CaseMine/SCC Online target metro Big Law)
- Handles the highest variety of case types (criminal, family, civil, consumer all in one practice)
- Willing to adopt new tools (₹500-2000/mo price sensitivity)
- Their needs naturally build the foundation for all other user segments
- Your own practice context — you know their workflow first-hand

**Their daily pain points (mapped to tools):**

| Pain Point | How Often | Tool That Solves It | Priority |
|---|---|---|---|
| "Is this offence bailable? What BNSS section replaced the old CrPC one?" | Multiple times daily | `statute_search` | **v0.1** |
| Client walks in with a complex situation, needs quick triage | Daily | `explain_situation` | **v0.1** |
| "Client arrested at 2 AM — is anticipatory bail possible? What are grounds?" | Weekly (urgent) | `bail_assessment` | **v0.5** |
| "Has limitation expired for this cheque bounce complaint?" | Weekly | `limitation_calculator` | **v0.5** |
| Need to check case status / next hearing date | Daily | `ecourts_lookup` | **v0.5** |
| "What is res judicata? Client is asking me to explain in simple terms" | Daily | `legal_concepts` | **v0.5** |
| Need to draft a s.138 NI Act demand notice | Weekly | `draft_legal_notice` | **v1.0** |
| Need to search for supporting case law | Weekly | `indiankanoon_search` | **v1.0** |

**Deferred users (v1.5+):**
- Citizens (need Hindi/Marathi UI, WhatsApp integration — different product)
- Senior advocates (need cause lists, case analytics — niche features)
- Law students (need concept explanations — `legal_concepts` covers this as a side-effect)
- NRIs (need cross-border jurisdiction — specialized module)

---

## 3. Architecture Overview

### 3.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        MCP CLIENT (Claude, etc.)                     │
└──────────────────────────┬───────────────────────────────────────────┘
                           │ MCP Protocol (SSE/stdio)
┌──────────────────────────▼───────────────────────────────────────────┐
│                    INDIAN LEGAL MCP SERVER                           │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  API Gateway Layer (FastAPI)                                  │    │
│  │  • Auth (OAuth2/API Key) • Rate Limiting • Request Logging   │    │
│  └──────────────────────────┬───────────────────────────────────┘    │
│  ┌──────────────────────────▼───────────────────────────────────┐    │
│  │  Orchestration Layer                                          │    │
│  │  • explain_situation (v0.1)                                  │    │
│  └───────┬──────────────────┬────────────────────┬──────────────┘    │
│  ┌───────▼───────┐ ┌───────▼──────────┐ ┌───────▼──────────────┐    │
│  │ Knowledge     │ │ External API     │ │ Computation          │    │
│  │ Tools         │ │ Tools            │ │ Tools                │    │
│  │               │ │                  │ │                      │    │
│  │• statute      │ │• ecourts_lookup  │ │• limitation          │    │
│  │  _search      │ │  (v0.5)         │ │  _calculator (v0.5) │    │
│  │  (v0.1)      │ │• indiankanoon    │ │                      │    │
│  │• legal_       │ │  _search (v1.0) │ │                      │    │
│  │  concepts     │ │                  │ │                      │    │
│  │  (v0.5)      │ │                  │ │                      │    │
│  └───────┬───────┘ └───────┬──────────┘ └───────┬──────────────┘    │
│  ┌───────▼─────────────────▼────────────────────▼──────────────┐    │
│  │  Data Layer                                                   │    │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────────┐               │    │
│  │  │ SQLite   │ │ FTS5     │ │ Statute JSON   │               │    │
│  │  │ Statute  │ │ Index    │ │ Files          │               │    │
│  │  │ Store    │ │ (BM25)   │ │ (source data)  │               │    │
│  │  └──────────┘ └──────────┘ └────────────────┘               │    │
│  └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.2 Directory Structure

```
indian_legal_mcp_server/
├── src/
│   ├── mcp.py                          # FastMCP tool registration
│   ├── config.py                       # Pydantic settings (all env vars)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── # ── v0.1 Tools ──
│   │   ├── statute_search.py           # Local statute/section lookup
│   │   ├── explain_situation.py        # Scenario → plain-language + steps
│   │   ├── # ── v0.5 Tools ──
│   │   ├── legal_concepts.py           # Legal term/concept explainer
│   │   ├── bail_assessment.py          # Bail eligibility & grounds
│   │   ├── limitation_calculator.py    # Limitation period computation
│   │   ├── ecourts_lookup.py           # eCourts case status/hearings
│   │   ├── # ── v1.0 Tools ──
│   │   ├── draft_legal_notice.py       # Legal notice generation
│   │   ├── indiankanoon_search.py      # Judgment/precedent search
│   │   ├── submit_feedback.py          # User error reporting (privacy-safe)
│   │   ├── # ── v1.5+ Tools (deferred, not built yet) ──
│   │   ├── # precedent_digest.py
│   │   ├── # analyze_case_strength.py
│   │   ├── # draft_complaint.py
│   │   ├── # rti_application.py
│   │   ├── # legal_checklist.py
│   │   ├── # jurisdiction_finder.py
│   │   ├── # court_fee_calculator.py
│   │   ├── # cause_list_checker.py     # DEFERRED — v2+ only, via API not scraping
│   │   └── # section_mapper_tool.py    # Expose old↔new mapping as standalone tool
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── system_instructions.py      # Shared system prompt (disclaimer, tone, citation format)
│   │   ├── explain_situation_prompt.py
│   │   └── notice_generation_prompt.py
│   ├── templates/
│   │   ├── __init__.py
│   │   └── notice_templates/
│   │       ├── base_notice.py          # Shared Jinja skeleton
│   │       ├── cheque_bounce_138.py
│   │       ├── eviction_notice.py
│   │       ├── restitution_s9_hma.py
│   │       ├── maintenance_demand.py
│   │       └── general_civil.py
│   ├── data/
│   │   ├── statutes/                   # Raw act JSON files
│   │   │   ├── bns_2023.json           # v0.1
│   │   │   ├── bnss_2023.json          # v0.1
│   │   │   ├── hma_1955.json           # v0.1
│   │   │   ├── dv_act_2005.json        # v0.5
│   │   │   ├── ni_act_1881.json        # v0.5 (s.138-142 focus)
│   │   │   ├── limitation_act_1963.json # v0.5
│   │   │   ├── special_marriage_1954.json # v0.5
│   │   │   ├── constitution_part3.json  # v1.0
│   │   │   ├── cpc_1908.json           # v1.0
│   │   │   ├── contract_act_1872.json  # v1.0
│   │   │   ├── consumer_protection_2019.json # v1.0
│   │   │   ├── hindu_succession_1956.json # v1.0
│   │   │   ├── bnsa_2023.json          # v1.0
│   │   │   ├── rera_2016.json          # v1.0
│   │   │   └── it_act_2000.json        # v1.0
│   │   ├── precedents/
│   │   │   └── landmark_cases.json     # v0.5: 30 cases. v1.0: 100.
│   │   ├── old_to_new_mapping.json     # v0.5: IPC↔BNS, CrPC↔BNSS only
│   │   ├── limitation_periods.json     # v0.5: Top 50 cause types
│   │   ├── legal_concepts.json         # v0.5: 50 terms EN only. v1.0: 200 terms.
│   │   ├── court_hierarchy.json
│   │   └── standard_phrases/
│   │       ├── marathi.json            # v1.0
│   │       ├── hindi.json              # v1.0
│   │       └── english.json            # v0.1
│   ├── services/
│   │   ├── __init__.py
│   │   ├── search_engine.py            # SQLite FTS5 search (built-in BM25)
│   │   ├── statute_index.py            # Statute indexing & retrieval
│   │   ├── llm_client.py               # LLM call abstraction (provider-agnostic)
│   │   ├── cache_manager.py            # In-memory caching layer (v0.5)
│   │   ├── section_mapper.py           # Old law ↔ New law section mapper (v0.5)
│   │   ├── citation_validator.py       # Validates LLM citations against index (v0.1)
│   │   └── document_generator.py       # DOCX generation service (v1.0)
│   └── utils/
│       ├── __init__.py
│       ├── validators.py               # Input validation (CNR format, dates, injection)
│       ├── formatters.py               # Output formatting helpers
│       ├── privacy.py                  # PII redaction for logs
│       ├── rate_limiter.py             # Per-user/per-key rate limiting
│       └── metrics.py                  # Anonymized usage telemetry
├── scripts/
│   ├── build_statute_index.py          # Chunk acts → SQLite FTS5
│   ├── validate_statute_data.py        # CI: validate all JSON files
│   ├── build_precedent_index.py        # Index landmark cases
│   ├── build_limitation_table.py       # Build limitation schedule
│   └── old_new_section_mapper.py       # Generate IPC→BNS mapping
├── tests/
│   ├── conftest.py
│   ├── test_statute_search.py
│   ├── test_explain_situation.py
│   ├── test_bail_assessment.py
│   ├── test_limitation_calculator.py
│   ├── test_ecourts_lookup.py
│   ├── test_indiankanoon_search.py
│   ├── test_legal_concepts.py
│   ├── test_draft_legal_notice.py
│   ├── test_citation_validator.py
│   ├── test_section_mapper.py
│   ├── test_privacy_redaction.py
│   ├── test_orchestrator_partial_failure.py
│   ├── test_data_integrity.py          # All JSON valid, cross-refs resolve
│   ├── test_limitation_zero_tolerance.py # Every Article of Limitation Act verified
│   └── fixtures/
│       ├── sample_scenarios.json
│       ├── mock_ecourts_responses.json
│       ├── mock_indiankanoon_responses.json
│       └── expected_outputs/
└── docs/
    ├── API_REFERENCE.md
    ├── STATUTE_COVERAGE.md
    ├── DATA_SOURCES.md
    └── ETHICAL_GUIDELINES.md
```

---

## 4. Data Layer — The Foundation (and the Hardest Part)

> **Hard truth:** Data curation is the bottleneck of this entire project.
> Writing code takes days. Populating 1,850 sections with verified legal data
> takes weeks. This plan accounts for that reality.

### 4.1 Data Sourcing Strategy (Not Handwaved)

The raw text of Indian statutes is government-published and copyright-free (s.52(1)(q)
Copyright Act). But getting it into structured, machine-readable JSON is non-trivial:

**Source 1 — India Code portal (indiacode.nic.in):**
- Contains all central acts, updated
- BUT: JS-rendered pages, inconsistent HTML, rate-limited, no API
- Use for: verification and gap-filling, NOT as primary ingestion source

**Source 2 — Existing open-source projects:**
- `india-code-api` on GitHub — pre-scraped structured data for many acts
- Various legal-tech open-source projects have already parsed common acts
- Use for: starting point for `text` field, then validate against India Code

**Source 3 — LLM-assisted data entry (the realistic approach):**
- Feed raw act text (from gazette PDF / India Code HTML) to Claude
- Ask it to extract into the JSON schema section by section
- **Human validates every output** — the LLM does the formatting, you verify the content
- This is ~3× faster than manual entry but still requires human review time

**Source 4 — For old↔new mapping specifically:**
- MHA published partial IPC→BNS mapping (PDF)
- Several legal publishers (EBC, Taxmann) have published mapping tables
- Cross-reference against the acts themselves for split/merged sections
- This is a legal research task, not an automation task

**Source 5 — For bailable/cognizable/compoundable classification:**
- BNSS First Schedule contains the complete classification
- Available in structured format from legal publishers
- Can be cross-referenced against the act text itself

### 4.2 Tiered Data Schema (Start Simple, Earn Complexity)

**v0.1 Schema (5 fields — the minimum viable statute entry):**

```json
{
  "act_id": "bns_2023",
  "full_title": "Bharatiya Nyaya Sanhita, 2023",
  "short_title": "BNS 2023",
  "year": 2023,
  "category": "criminal",
  "enforcement_date": "2024-07-01",
  "is_active": true,
  "source_url": "https://indiacode.nic.in/...",
  "last_verified": "2026-07-01",
  "sections": [
    {
      "section_number": "103",
      "section_title": "Punishment for murder",
      "text": "...(full verbatim text)...",
      "keywords": ["murder", "punishment", "death", "imprisonment", "life"],
      "chapter": "VI — Of Offences Affecting the Human Body"
    }
  ]
}
```

That's it. 5 fields per section. No `plain_summary`, no `cross_references`, no
`penalties` structure, no `bailable/cognizable`. Those come later when the core
search actually works.

**v0.5 Schema (adds 6 more fields):**

```json
{
  "section_number": "103",
  "section_title": "Punishment for murder",
  "text": "...",
  "keywords": ["murder", "punishment", "death"],
  "chapter": "VI",
  "plain_summary": "Whoever commits murder shall be punished with death or life imprisonment, and shall also be liable to fine.",
  "old_section": {"act": "ipc_1860", "section": "302", "changes": "Substantially same."},
  "penalties": {"imprisonment_max": "death/life", "fine_max": "unlimited"},
  "is_bailable": false,
  "is_cognizable": true,
  "is_compoundable": false,
  "court_triable_by": "Court of Session"
}
```

**v1.0 Schema (full — adds remaining fields):**

```json
{
  "section_number": "103",
  "section_title": "Punishment for murder",
  "text": "...",
  "keywords": ["murder", "punishment", "death"],
  "chapter": "VI",
  "plain_summary": "...",
  "old_section": {...},
  "penalties": {...},
  "is_bailable": false,
  "is_cognizable": true,
  "is_compoundable": false,
  "court_triable_by": "Court of Session",
  "cross_references": ["bns_2023.s101", "bns_2023.s104", "bnss_2023.s193"],
  "sub_sections": [...],
  "explanations": [...],
  "provisos": [...],
  "illustrations": [...],
  "landmark_cases": ["sc_machhi_singh_1983", "sc_bachan_singh_1980"],
  "state_applicability": {
    "uniform_central": true,
    "state_specific_note": null
  }
}
```

### 4.3 v0.1 Data Scope (Realistic — 3 acts, ~420 sections)

| Act | Sections | Schema Level | Est. Hours | Rationale |
|---|---|---|---|---|
| BNS 2023 | ~358 | v0.1 (5-field) | 12-15h | Core criminal law, most referenced |
| BNSS 2023 | ~531 (index critical chapters only: arrest, bail, maintenance, search, trial) | v0.1 (5-field) | 10-12h | Procedure — bail, arrest, maintenance chapters most needed |
| HMA 1955 | ~30 | v0.1 (5-field) | 2h | Family law — small act, high use |

**Total: ~420 sections at 5 fields each = ~25-30 hours of data work.**
At 6 hours/day of focused data curation = ~5 working days. Realistic for Phase 1.

The remaining acts (DV Act, NI Act, Limitation Act, etc.) come in v0.5 when the
search engine is working and you can validate data quality against real queries.

### 4.4 Precedent Data Format

```json
{
  "case_id": "sc_arnesh_kumar_2014",
  "case_name": "Arnesh Kumar v. State of Bihar",
  "citation": "(2014) 8 SCC 273",
  "court": "Supreme Court of India",
  "bench": ["Chandramauli Kr. Prasad, J.", "Pinaki Chandra Ghose, J."],
  "date": "2014-07-02",
  "category": ["criminal", "arrest", "s.498A"],
  "acts_interpreted": ["ipc_1860.s498A", "crpc_1973.s41", "crpc_1973.s41A"],
  "current_relevance_new_law": ["bns_2023.s85", "bnss_2023.s35", "bnss_2023.s36"],
  "ratio_decidendi": "Arrest under s.498A IPC should not be automatic. Magistrates must verify compliance with s.41 CrPC checklist before authorizing detention.",
  "key_directions": [
    "Police must follow s.41(1)(b) checklist before arrest in s.498A cases",
    "Magistrate must record reasons for authorizing detention",
    "Non-compliance may lead to departmental action and contempt"
  ],
  "current_status": "good_law",
  "overruled_by": null,
  "practical_impact": "Police must fill checklist before arrest in matrimonial cases. Magistrate cannot mechanically authorize remand."
}
```

**v0.5 target: 30 cases.** Focus on cases that directly support `bail_assessment` and
`explain_situation` for criminal + family law scenarios:

Arnesh Kumar, D.K. Basu, Lalita Kumari, Satender Kumar Antil, Sushila Aggarwal
(anticipatory bail), Arnab Goswami (bail principles), Rajesh Sharma v. State of UP
(498A safeguards), Shayara Bano (triple talaq), V. Bhagat v. D. Bhagat (cruelty),
Rupali Devi (maintenance), Vineeta Sharma (coparcenary), Dashrath Rupsingh Rathod
(NI Act jurisdiction), Kesavananda Bharati (basic structure), Maneka Gandhi (Art.21),
Puttaswamy (privacy), Navtej Singh Johar (s.377), Shreya Singhal (s.66A), D.K. Basu
(arrest guidelines), Vishaka (sexual harassment), Bikramjit Singh (default bail),
Gurbaksh Singh Sibbia (AB principles), Hussainara Khatoon (speedy trial), Nilabati
Behera (custodial death compensation), Joginder Kumar (arrest safeguards), Sunil Batra
(prisoner rights), Laxmi v. UOI (acid attack), Sakshi v. UOI (child witnesses),
Mohd. Ahmed Khan v. Shah Bano (maintenance), Shabnam v. State of UP (women death
sentence), Dattatraya v. State (medical negligence), Lily Thomas (conviction
disqualification).

### 4.5 Old Law → New Law Section Mapping

**Deferred to v0.5.** Not needed for v0.1 — the BNS/BNSS text itself is searchable.
The mapping adds value when practitioners search using old IPC/CrPC terms.

**v0.5 scope:** IPC↔BNS (criminal) and CrPC↔BNSS (procedure) only. ~500 mappings.
IEA↔BNSA deferred to v1.0.

**Mapping types to handle:**

| Type | Example | Handling |
|---|---|---|
| `direct` | IPC 302 → BNS 103 (identical) | 1:1 map |
| `modified` | CrPC 125 → BNSS 144 (added timelines) | 1:1 map + `changes` field |
| `split` | IPC 376 → BNS 63, 64, 65, 66, 67, 68, 69, 70 (rape provisions expanded) | 1:N map |
| `merged` | IPC 463+464+465 → BNS 336 (forgery consolidated) | N:1 map |
| `new` | No IPC equivalent → BNS 111 (organized crime) | New section, no old equivalent |
| `repealed` | IPC 497 (adultery — struck down 2018) → No BNS equivalent | Old section, no new equivalent |

```json
{
  "old_act": "ipc_1860",
  "new_act": "bns_2023",
  "old_section": "376",
  "new_sections": ["63", "64", "65", "66", "67", "68", "69", "70"],
  "mapping_type": "split",
  "old_title": "Punishment for rape",
  "new_title": "Various rape provisions (split by context)",
  "changes": "Single section split into 8 sections covering different scenarios: rape, rape by person in authority, gang rape, rape on minor, etc.",
  "notes": "Section numbers not directly interchangeable. Check specific scenario."
}
```

### 4.6 Search Index Architecture

**Use SQLite FTS5 only. Drop `rank_bm25` package.**

SQLite FTS5 has built-in BM25 ranking. Using a separate Python BM25 library is
redundant infrastructure for the same job.

```python
# services/search_engine.py

import sqlite3

class StatuteSearchEngine:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self._ensure_fts_table()

    def _ensure_fts_table(self):
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS statute_fts USING fts5(
                act_id,
                section_number,
                section_title,
                text,
                keywords,
                chapter,
                tokenize='porter unicode61'
            )
        """)

    def search(self, query: str, act_filter: str = None, max_results: int = 10) -> list:
        """
        Search statutes. Uses FTS5 built-in BM25 ranking.
        Handles both exact section lookups ("section 302") and
        natural language queries ("maintenance husband wife").
        """
        # Exact section lookup (regex detect: "section 302", "s.498A", "BNS 103")
        exact_match = self._try_exact_section_lookup(query)
        if exact_match:
            return exact_match

        # BM25 full-text search
        sql = """
            SELECT *, rank FROM statute_fts
            WHERE statute_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """
        params = [query, max_results]

        if act_filter:
            sql = """
                SELECT *, rank FROM statute_fts
                WHERE statute_fts MATCH ? AND act_id = ?
                ORDER BY rank
                LIMIT ?
            """
            params = [query, act_filter, max_results]

        return self.conn.execute(sql, params).fetchall()
```

**v1.0 upgrade path (only if FTS5 retrieval quality is insufficient):**
- Add `sentence-transformers` embeddings
- Use LanceDB (local, zero-config) alongside FTS5
- Hybrid: FTS5 candidates → rerank with embeddings

### 4.7 Data Currency & Freshness

| Data Type | Update Frequency | Update Method |
|---|---|---|
| Central Acts (text) | On amendment (Parliament session check) | Semi-automated: diff against India Code portal |
| Landmark judgments | Monthly | Manual curation |
| Old↔New mapping | Stable (corrections only) | User-reported error correction via `submit_feedback` |
| Limitation periods | On statute amendment | Tied to statute update cycle |
| Legal concepts | Quarterly | Based on query patterns from telemetry |

Every tool response includes `data_freshness`:
```json
{
  "data_freshness": {
    "statute_index_built": "2026-07-01T00:00:00Z",
    "act_last_verified": "2026-07-01"
  }
}
```

### 4.8 Data Integrity Validation (Runs in CI)

```python
# scripts/validate_statute_data.py — runs on every commit

def validate():
    """
    1. Every JSON file in data/statutes/ is valid JSON
    2. Every act has: act_id, full_title, year, category, sections[]
    3. Every section has: section_number, section_title, text (non-empty)
    4. No duplicate section numbers within an act
    5. All cross_references (when present) resolve to real sections
    6. All old_section references (when present) point to indexed acts
    7. All act_ids are unique across the corpus
    8. All dates are valid ISO format
    """
```

---

## 5. Quality Targets & Error Budgets

> For a legal tool, a wrong answer is worse than no answer. A missed limitation
> period means a case is dismissed forever. A wrong bailable/non-bailable
> classification affects someone's liberty. Define what "correct" means.

### 5.1 Per-Tool Quality Targets

| Tool | Accuracy Target | Failure Mode | Error Budget | Enforcement |
|---|---|---|---|---|
| `statute_search` | Top-3 results contain the most relevant section | Wrong or missing results | < 5% miss rate | Golden test set: 100 queries with expected top-3 results |
| `limitation_calculator` | Correct period to the exact day | Wrong date | **0% (zero tolerance)** | Every Limitation Act article + 50 special statutes verified in CI test |
| `bail_assessment` | Correct bailable/non-bailable/cognizable | Wrong classification | **0% (zero tolerance)** | Full BNSS First Schedule verified in CI test |
| `legal_concepts` | Accurate definition, correct governing section | Wrong definition or section | < 2% | Spot-check against standard legal dictionaries |
| `explain_situation` | Relevant explanation, no misleading statements | Misleading advice | < 5% | 50-scenario test bank with human-reviewed expected outputs |
| `ecourts_lookup` | Returns correct case data from API | Wrong data | N/A (passthrough from provider) | Schema validation on API response |
| `draft_legal_notice` | Correct statute citations, proper format | Wrong citations, bad format | < 2% (citations); 0% (format) | Citation validation against index; template rendering tests |
| `indiankanoon_search` | Returns relevant judgments | Irrelevant results | N/A (passthrough from API) | Attribution string always present |

### 5.2 Confidence Scores

Every tool response includes a `confidence` field:

```json
{
  "status": "success",
  "confidence": {
    "score": 0.95,
    "level": "high",          // "high" (>0.9), "medium" (0.7-0.9), "low" (<0.7)
    "factors": [
      "Exact section match found",
      "Single applicable act identified"
    ],
    "warnings": []            // Populated when confidence < 0.9
  }
}
```

**Zero-tolerance tools** (`limitation_calculator`, `bail_assessment`):
- If confidence < 0.95, append a prominent warning:
  ```json
  "warnings": [
    "⚠ This computation may be affected by factors not captured (state-specific rules, disabilities under s.6 Limitation Act, or pending amendments). Verify with an advocate before relying on this date."
  ]
  ```
- If confidence < 0.7, return `status: "uncertain"` instead of `"success"`:
  ```json
  {
    "status": "uncertain",
    "message": "Cannot determine limitation period with sufficient confidence. Multiple cause types may apply. Consult an advocate.",
    "possible_results": [...]
  }
  ```

### 5.3 Scope Boundaries — What the Server Explicitly Does NOT Do

| Out of Scope | Why | What Users See Instead |
|---|---|---|
| Land law (tenancy, revenue, ceiling) | 100% state-specific, 28 different regimes | "Land law varies entirely by state. This server covers central laws only. Consult a local advocate." |
| Tax advisory (GST/IT return filing) | Requires chartered accountant expertise, not legal | "For tax computation and filing, consult a Chartered Accountant." |
| Immigration/visa law | Central but specialized, not covered in v1 | "Immigration law is not covered in this version." |
| Legal outcome prediction | Ethically prohibited, practically unreliable | "This tool provides information about the legal framework, not predictions about your specific case outcome." |
| Automated filing/serving | BCI rules prohibit unauthorized practice | Tool status is always `draft_pending_review`. No auto-submit. |

---

## 6. v1 Tool Suite (7 Tools)

Each tool = one file in `indian_legal_mcp_server/src/tools/`, registered in
`indian_legal_mcp_server/src/mcp.py`. Follow the template's pattern exactly:
docstring metadata block, `try/except` returning `{"status": "error", ...}`,
structured logging via `get_python_logger()`.

---

### 6.1 `statute_search.py` — Statute & Section Lookup [v0.1]

**Purpose:** The backbone tool. Every other tool depends on it for citation accuracy.

```python
# Input
{
    "query": str,                    # "maintenance husband wife" or "section 125 CrPC"
                                     # or "BNS 103" or "murder punishment"
    "act_filter": Optional[str],     # "bns_2023", "hma_1955"
    "category_filter": Optional[str],# "criminal", "family", "civil"
    "include_old_new_mapping": bool,  # Default True (from v0.5 onwards; no-op in v0.1)
    "max_results": int,               # Default 10
}

# Output
{
    "status": "success",
    "query": "maintenance husband wife",
    "total_results": 8,
    "confidence": {"score": 0.92, "level": "high"},
    "sections": [
        {
            "act": "Bharatiya Nagarik Suraksha Sanhita, 2023",
            "act_id": "bnss_2023",
            "section": "144",
            "section_title": "Order for maintenance of wives, children and parents",
            "text": "...(verbatim)...",
            "relevance_score": 0.92,
            "is_active": true,
            // v0.5+ fields (absent in v0.1 output):
            "old_equivalent": {...},
            "plain_summary": "...",
            "bailable": null,
            "cognizable": null,
            "state_applicability": {"uniform_central": true}
        }
    ],
    "data_freshness": {"statute_index_built": "2026-07-01"}
}
```

---

### 6.2 `explain_situation.py` — Scenario → Plain-Language Explanation [v0.1]

**Purpose:** The flagship UX tool. Takes a free-text scenario (in any language — EN, HI,
MR input all accepted) and returns an English explanation with applicable law, rights,
and next steps.

```python
# Input
{
    "scenario": str,                  # Free text, any language accepted
    "detail_level": str,              # "brief" | "standard" (default) | "detailed"
    "include_checklist": bool,        # Default True
}

# Output
{
    "status": "success",
    "classification": {
        "primary_domain": "criminal",
        "sub_domain": "arrest_and_bail",
        "related_domains": ["family_law_498a"],
        "confidence": 0.91
    },
    "explanation": "...(plain-language explanation)...",
    "applicable_law": [
        {"provision": "BNS s.85 (formerly IPC s.498A)", "relevance": "..."}
    ],
    "your_rights": ["..."],
    "immediate_steps": ["..."],
    "checklist": ["..."],
    "caution_points": [
        "⚠ The law on electronic service of notice under BNSS s.94 is currently evolving — some High Courts have questioned its validity."
    ],
    "sources_used": ["statute_search"],
    "sources_failed": [],
    "disclaimer": "This is general legal information. It is NOT legal advice for your specific situation. Consult a qualified advocate.",
    "data_freshness": {...},
    "confidence": {"score": 0.88, "level": "medium"}
}
```

**Orchestration flow (v0.1 — minimal):**
```
scenario → [1] Classify (rules engine) → [2] statute_search → [3] LLM synthesis → [4] Citation validation → [5] Disclaimer → Return
```

**Orchestration flow (v0.5+ — enriched):**
```
scenario → [1] Classify → [2] statute_search → [3] bail_assessment (if criminal)
         → [4] limitation_calculator (if dates present)
         → [5] ecourts_lookup (if CNR present)
         → [6] LLM synthesis → [7] Citation validation → [8] Disclaimer → Return
```

**Timeout & degradation:**
- Each sub-tool: 10s timeout
- If any sub-tool fails, continue with available data
- `sources_used` and `sources_failed` always populated
- Minimum viable response: statute_search results + disclaimer (even if everything else fails)

---

### 6.3 `bail_assessment.py` — Bail Eligibility & Grounds [v0.5]

**Purpose:** Given offence sections and circumstances, determines bail type applicable,
grounds available, and relevant precedents. The most common emergency need in criminal
practice.

**Quality: ZERO TOLERANCE for bailable/non-bailable classification.**

```python
# Input
{
    "offence_sections": [str],        # ["bns_2023.s103"] or ["ipc.302"] (auto-maps)
    "stage": str,                     # "pre_arrest", "post_arrest_police", "post_chargesheet"
    "custody_days": Optional[int],
    "is_first_offence": bool,
    "special_act": Optional[str],     # "ndps", "pmla", "uapa"
}

# Output
{
    "status": "success",
    "confidence": {"score": 0.98, "level": "high"},
    "bail_analysis": {
        "offences_analyzed": [...],
        "bail_type_applicable": "anticipatory_bail",
        "bailable_or_not": {
            "s103_bns": {"bailable": false, "max_punishment": "death/life imprisonment"}
        },
        "bail_provisions": [
            {"provision": "BNSS s.482", "type": "Anticipatory Bail", "forum": "Sessions Court / High Court"}
        ],
        "default_bail_eligibility": {
            "applicable": true,
            "provision": "BNSS s.187(2)",
            "trigger": "Chargesheet not filed within 90 days",
            "days_remaining_for_default_bail": 45,
            "key_case": "Bikramjit Singh v. State of Punjab (2020) 10 SCC 616"
        },
        "grounds_to_argue": ["No flight risk", "Cooperation with investigation", "Parity"],
        "restrictive_provisions": [],
        "key_precedents": [
            {"case": "Satender Kumar Antil v. CBI (2022) 10 SCC 51", "relevance": "Bail is rule, jail is exception"}
        ],
        "checklist_for_application": [...]
    },
    "disclaimer": "This is a general bail eligibility assessment. Bail outcomes depend on specific facts, evidence, and judicial discretion. Consult a criminal lawyer immediately."
}
```

---

### 6.4 `limitation_calculator.py` — Limitation Period Computation [v0.5]

**Quality: ZERO TOLERANCE. Every period verified in CI tests.**

```python
# Input
{
    "cause_type": str,                # "cheque_bounce_138", "consumer_complaint",
                                      # "suit_for_money", "divorce_petition"
    "cause_of_action_date": str,      # "2024-06-15"
    "is_government_party": bool,      # Default False
    "disability": Optional[str],      # "minority", "unsoundness_of_mind"
    "include_covid_extension": bool,  # Default True
}

# Output
{
    "status": "success",     // or "uncertain" if confidence < 0.7
    "confidence": {"score": 0.99, "level": "high"},
    "limitation_analysis": {
        "cause_type": "cheque_bounce_138",
        "governing_provision": "Negotiable Instruments Act, 1881, Section 142(b)",
        "standard_limitation": "30 days from date of cause of action",
        "cause_of_action_date": "2024-06-15",
        "limitation_starts": "2024-06-15",
        "limitation_expires": "2024-07-15",
        "current_status": "EXPIRED",
        "days_remaining": -731,
        "condonation_possible": true,
        "condonation_provision": "Section 142(b) NI Act read with Section 5 Limitation Act",
        "special_notes": [
            "30-day period starts from expiry of 15-day notice period under s.138",
            "If cheque returned for second time, fresh cause of action arises"
        ]
    },
    "disclaimer": "Limitation computation is general guidance. Counting rules for holidays, postal delays, and disabilities may alter the date. Verify with an advocate."
}
```

---

### 6.5 `legal_concepts.py` — Legal Term Explainer [v0.5]

```python
# Input
{
    "term": str,                     # "anticipatory bail", "FIR", "cognizable offence"
    "context": Optional[str],        # "criminal" | "civil" | "family"
}

# Output
{
    "status": "success",
    "concept": {
        "term": "Anticipatory Bail",
        "definition": "A direction by a court to release a person on bail even before arrest...",
        "plain_explanation": "If you fear you might be arrested...",
        "governing_provisions": ["bnss_2023.s482"],
        "old_provisions": ["crpc_1973.s438"],
        "key_case": "Sushila Aggarwal v. State (NCT of Delhi) (2020) 5 SCC 1",
        "procedure": ["File application before Sessions Court or HC", ...],
        "related_concepts": ["bail", "regular_bail", "default_bail"],
        "common_misconceptions": [...]
    }
}
```

**v0.5: 50 terms (English only).** v1.0: 200 terms. Hindi/Marathi translations added in v1.5.

---

### 6.6 `ecourts_lookup.py` — Live Case Status [v0.5]

```python
# Input
{
    "cnr_number": Optional[str],
    "case_type": Optional[str],
    "case_number": Optional[str],
    "case_year": Optional[int],
    "court_code": Optional[str],
}

# Output
{
    "status": "success",
    "case_details": {
        "cnr_number": "MHNA01-123456-2024",
        "case_type": "Criminal Misc Application",
        "court": "Court of Additional Sessions Judge, Nashik",
        "case_status": "Pending",
        "next_hearing": "2026-08-15",
    },
    "parties": {...},
    "hearings": [...],
    "orders": [...]
}
```

**Auth:** `ECOURTS_API_KEY` env var. Provider-agnostic interface.
**Cache:** 30 minutes. **Timeout:** 10s. **Fallback:** `"status": "provider_unavailable"`.

---

### 6.7 `draft_legal_notice.py` — Legal Notice Generation [v1.0]

**Status is ALWAYS `draft_pending_review`.** Never `success`.

**v1.0 notice types (5):**

| `notice_type` | Governing Law | Use |
|---|---|---|
| `cheque_bounce_138` | NI Act s.138 | Demand notice before criminal complaint |
| `eviction_notice` | TPA s.106 | Landlord → Tenant |
| `restitution_s9_hma` | HMA s.9 | Restitution of conjugal rights |
| `maintenance_demand` | BNSS s.144 | Maintenance demand |
| `general_civil` | CPC, Contract Act | Money recovery, breach of contract |

```python
# Input
{
    "notice_type": str,
    "advocates": [{"name": str, "mobile": str, "enrollment": str}],
    "office_address": str,
    "recipient": {"name": str, "address": str},
    "client": {"name": str, "address": str, "role": str},
    "facts": [str],
    "relief_sought": str,
    "compliance_deadline_days": int,
    "governing_sections": Optional[list],
    "language": str,                  # v1.0: "mr" only. v1.5: "hi", "en"
    "output_format": str,             # v1.0: "markdown" only. v1.5: "docx"
}

# Output
{
    "status": "draft_pending_review",
    "notice_draft": {
        "content": "...(full formatted notice)...",
        "format": "markdown"
    },
    "citations_used": [...],
    "review_notes": [
        "⚠ Verify client's full legal name matches ID documents",
        "⚠ Review fact paragraphs for factual accuracy"
    ],
    "disclaimer": "This is a DRAFT for advocate review. Do NOT serve without thorough review by a licensed advocate."
}
```

**Template architecture (preserved from original — this design survived the stress test):**
- `templates/notice_templates/base_notice.py` — Jinja skeleton (letterhead, relational
  markers, closing boilerplate)
- Each notice type extends base with type-specific paragraph patterns
- LLM generates ONLY the numbered fact paragraphs
- Standard connector phrases from `data/standard_phrases/{language}.json`
- **Statute citations MUST come from `statute_search`, not LLM memory**

---

### 6.8 `indiankanoon_search.py` — Judgment Search [v1.0]

```python
# Input
{
    "query": str,
    "court": Optional[str],
    "date_from": Optional[str],
    "date_to": Optional[str],
    "fetch_full_text": bool,          # Default False
    "max_results": int,               # Default 10
}

# Output
{
    "status": "success",
    "judgments": [...],
    "total_results": 1247,
    "attribution": "Powered by Indian Kanoon — https://indiankanoon.org",
    "disclaimer": "Search results are for research purposes. Verify citations from official sources."
}
```

**Attribution is MANDATORY and non-removable.** Indian Kanoon ToS requirement.

---

### 6.9 `submit_feedback.py` — Error Reporting [v1.0]

```python
# Input
{
    "tool_name": str,          # Which tool produced wrong output
    "issue_type": str,         # "wrong_section", "wrong_limitation", "missing_info",
                                # "wrong_bail_classification", "other"
    "description": str,        # What was wrong
    "expected_result": Optional[str],
    # NO scenario text — privacy. User describes the error, not the scenario.
}

# Output
{
    "status": "received",
    "feedback_id": "fb_20260716_001",
    "message": "Thank you. Feedback logged for review. If this is a bail/limitation classification error, it will be prioritized."
}
```

Feedback stored in append-only SQLite table. Zero-tolerance tool errors
(`limitation_calculator`, `bail_assessment`) trigger alerts for immediate review.

---

## 7. v1.5+ Deferred Tools (9 Tools)

These are fully specified in the architecture but NOT built until v1.0 is stable and
user feedback validates the need. Listed here so the architecture accommodates them.

| Tool | Target Release | Why Deferred |
|---|---|---|
| `precedent_digest` | v1.0 | 30 cases embedded in `bail_assessment` already. Standalone tool useful but not critical for v1.0 |
| `jurisdiction_finder` | v1.5 | Useful but pecuniary limits rarely queried by advocates (they know their local court) |
| `court_fee_calculator` | v1.5 | State-specific data curation burden is high. 6 states = weeks of research |
| `analyze_case_strength` | v1.5 | LLM-heavy, needs careful prompt engineering. Build after `explain_situation` prompt is battle-tested |
| `draft_complaint` (FIR/consumer/writ) | v1.5 | FIR drafts are simple (low-template); writs are complex (high-risk). Do notices first, learn, then complaints |
| `rti_application` | v1.5 | Different user segment (citizen, not advocate). Low infrastructure overlap with core tools |
| `legal_checklist` | v1.5 | Nice-to-have, not must-have. `explain_situation` already includes a checklist |
| `section_mapper_tool` | v1.5 | Section mapper service exists from v0.5. Exposing as standalone MCP tool is trivial when needed |
| `cause_list_checker` | **v2+ only** | Requires web scraping of 25+ unreliable court websites OR paid API. Not worth the maintenance burden for v1. If built, use eCourts API provider, NOT custom scrapers |

---

## 8. Orchestration & Intelligence Layer

### 8.1 Scenario Classification Engine

Two-tier system:

**Tier 1: Rules/Keyword Engine (fast, no API call, handles 70% of scenarios):**

```python
CLASSIFICATION_RULES = {
    "arrest_and_bail": {
        "keywords": ["arrested", "FIR", "police station", "bail", "custody", "remand",
                      "गिरफ्तार", "अटक", "जामीन", "कोठडी", "पोलीस"],
        "section_patterns": [r"bns.*s\.\d+", r"bnss.*s\.35", r"bnss.*s\.480", r"bnss.*s\.482"],
        "domain": "criminal",
    },
    "maintenance": {
        "keywords": ["maintenance", "alimony", "wife maintenance", "child support",
                      "पोटगी", "निर्वाहखर्च", "भरण-पोषण"],
        "section_patterns": [r"bnss.*s\.144", r"hma.*s\.24", r"hma.*s\.25"],
        "domain": "family",
    },
    "cheque_bounce": {
        "keywords": ["cheque bounce", "dishonour", "138", "NI Act",
                      "चेक बाउन्स", "धनादेश"],
        "section_patterns": [r"ni.*s\.138", r"ni.*s\.141"],
        "domain": "commercial",
    },
    "domestic_violence": {
        "keywords": ["domestic violence", "DV act", "protection order", "dowry",
                      "घरगुती हिंसा", "दहेज", "कौटुंबिक हिंसाचार"],
        "section_patterns": [r"dv.*s\.\d+", r"bns.*s\.85"],
        "domain": "family",
    },
    "divorce": {
        "keywords": ["divorce", "mutual consent", "contested divorce", "cruelty",
                      "तलाक", "घटस्फोट", "विवाहभंग"],
        "section_patterns": [r"hma.*s\.13"],
        "domain": "family",
    },
    # ... 20+ more categories
}
```

**Tier 2: LLM Classification (fallback for ambiguous/multi-domain scenarios):**
- Only invoked if Tier 1 confidence < 0.6 or scenario spans multiple domains
- Uses a cheap, fast model call (Claude Haiku or similar)
- Returns primary + secondary domains + confidence

### 8.2 Citation Validation (Constrained Format)

**Problem:** LLMs cite sections in unpredictable formats. Regex-based extraction across
10+ citation formats (including Hindi/Marathi) is fragile and will miss cases.

**Solution: Constrain the LLM output, not the parser.**

The synthesis prompt instructs the LLM to cite sections in a specific bracket notation:

```
When citing a statute section, use this exact format: [act_id.s.NUMBER]
Examples: [bnss_2023.s144], [bns_2023.s85], [hma_1955.s13]
Never cite a section that is not in the provided context.
```

The citation validator then:

```python
# services/citation_validator.py

import re

CITATION_PATTERN = re.compile(r'\[([a-z_0-9]+)\.s\.([0-9A-Za-z()]+)\]')

def validate_citations(generated_text: str, indexed_sections: set) -> dict:
    """
    1. Extract all [act_id.s.NUMBER] citations from LLM output
    2. Check each against the set of sections actually retrieved by statute_search
    3. Strip any citation NOT in the retrieved set (hallucination)
    4. Return cleaned text + validation report
    """
    found = CITATION_PATTERN.findall(generated_text)
    valid = []
    hallucinated = []

    for act_id, section in found:
        key = f"{act_id}.s.{section}"
        if key in indexed_sections:
            valid.append(key)
        else:
            hallucinated.append(key)

    cleaned_text = generated_text
    for h in hallucinated:
        # Strip the hallucinated citation
        cleaned_text = cleaned_text.replace(f"[{h}]", "[citation removed — not verified]")

    return {
        "cleaned_text": cleaned_text,
        "valid_citations": valid,
        "hallucinated_citations": hallucinated,
        "warning": "Some citations were removed as they could not be verified." if hallucinated else None
    }
```

**Post-processing** then expands bracket citations to human-readable form:

```python
def expand_citations(text: str, section_mapper) -> str:
    """
    [bnss_2023.s144] → "Section 144 BNSS (formerly Section 125 CrPC)"
    [bns_2023.s85]   → "Section 85 BNS (formerly Section 498A IPC)"
    """
    ...
```

This solves three problems at once:
1. Citation validation is trivial (just parse brackets)
2. Old↔new bridging is automatic (post-processor appends old equivalent)
3. No need for multi-format regex covering Hindi/Marathi citation styles

---

## 9. LLM Integration Architecture

### 9.1 Provider-Agnostic Client

```python
# services/llm_client.py

class LLMClient:
    """
    Provider-agnostic LLM client. Supports:
    - Anthropic Claude (primary, recommended)
    - OpenAI GPT (fallback)
    - Ollama local models (development, no API cost)
    """

    def __init__(self, config: Settings):
        self.provider = config.LLM_PROVIDER
        self.model = config.LLM_MODEL
        self.fallback = config.LLM_FALLBACK_PROVIDER

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.2,   # Low for legal accuracy
    ) -> LLMResponse:
        ...

    async def classify(
        self,
        text: str,
        categories: list,
    ) -> ClassificationResult:
        ...
```

### 9.2 Config Settings

```python
class Settings(BaseSettings):
    # LLM Configuration
    LLM_PROVIDER: str = "anthropic"               # "anthropic" | "openai" | "ollama"
    LLM_MODEL: str = "claude-sonnet-4-20250514"
    LLM_FALLBACK_PROVIDER: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # External API Keys
    ECOURTS_API_KEY: Optional[str] = None
    ECOURTS_PROVIDER: str = "ecourts_india"
    INDIANKANOON_API_TOKEN: Optional[str] = None

    # Feature Flags
    ENABLE_LLM_TOOLS: bool = True
    ENABLE_EXTERNAL_APIS: bool = True
    DEFAULT_LANGUAGE: str = "en"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 30
    RATE_LIMIT_LLM_PER_MINUTE: int = 10
    RATE_LIMIT_EXTERNAL_API_PER_MINUTE: int = 20

    # Privacy
    LOG_PII: bool = False                          # NEVER True in production
    REDACT_SCENARIO_INPUT: bool = True

    # Data
    STATUTE_INDEX_PATH: str = "indian_legal_mcp_server/data/statute_index.db"
    DATA_DIR: str = "indian_legal_mcp_server/data"

    # Timeouts (seconds)
    EXTERNAL_API_TIMEOUT: int = 10
    LLM_CALL_TIMEOUT: int = 30
    TOTAL_ORCHESTRATION_TIMEOUT: int = 60
```

### 9.3 Prompt Architecture

```python
# prompts/system_instructions.py

LEGAL_SYSTEM_PROMPT = """
You are a legal information assistant for Indian law. You operate inside an MCP server
that supplies verified statute data. Follow these rules absolutely:

CITATION RULES:
1. ONLY cite sections provided in the context below. NEVER from your own memory.
2. Use bracket notation for all citations: [act_id.s.NUMBER]
   Examples: [bnss_2023.s144], [bns_2023.s85], [hma_1955.s13]
3. If no relevant section is in the context, say "the relevant provision could not be
   identified from the current index" — do NOT guess.

CONTENT RULES:
4. NEVER predict case outcomes. Say "courts have typically held..." not "you will win."
5. Distinguish settled law from evolving/contested positions. Flag with ⚠ when uncertain.
6. Use plain language. Define legal jargon on first use.
7. Specify WHICH court/forum has jurisdiction. Never just "go to court."
8. For criminal matters: always state bailable/non-bailable and cognizable/non-cognizable.
9. Flag when law differs by state.
10. End every response with the disclaimer provided.

OUTPUT FORMAT:
- Structured sections: Explanation → Applicable Law → Rights → Steps → Checklist
- Each applicable law entry cites one [act_id.s.NUMBER]
- Checklist items are concrete, actionable, and time-bound where applicable
"""
```

---

## 10. Multi-Language Strategy

### 10.1 Phased Rollout (Not All-at-Once)

| Phase | Input Languages | Output Language | Scope |
|---|---|---|---|
| v0.1 | EN, HI, MR (LLM understands natively — free) | EN only | All tools |
| v0.5 | EN, HI, MR | EN only | All tools |
| v1.0 | EN, HI, MR | EN + HI (for `explain_situation` only) | Targeted |
| v1.5 | EN, HI, MR | EN + HI + MR (all output tools) | Full |

**Key insight:** Accepting Hindi/Marathi INPUT costs nothing — Claude already understands
Devanagari. The expensive part is generating correct Hindi/Marathi OUTPUT (requires
verified legal term translations, not machine translation). So accept input in any
language from day 1, but output in English only until the phrase library is ready.

### 10.2 Legal Term Translation (Not Machine Translation)

```python
# data/standard_phrases/hindi.json (v1.0 — 200 verified terms)
{
    "bail": "जमानत",
    "anticipatory_bail": "अग्रिम जमानत",
    "FIR": "प्रथम सूचना रिपोर्ट (एफ.आई.आर.)",
    "cognizable_offence": "संज्ञेय अपराध",
    "maintenance": "भरण-पोषण",
    "writ_of_habeas_corpus": "बंदी प्रत्यक्षीकरण"
}

# data/standard_phrases/marathi.json (v1.5 — 200 verified terms)
{
    "bail": "जामीन",
    "anticipatory_bail": "अटकपूर्व जामीन",
    "FIR": "प्रथम खबर अहवाल (एफ.आय.आर.)",
    "cognizable_offence": "दखलपात्र गुन्हा",
    "maintenance": "पोटगी / निर्वाहखर्च"
}
```

**Note the differences:** Hindi "अग्रिम जमानत" vs Marathi "अटकपूर्व जामीन" for the
same legal concept. This is why machine translation fails for legal terms.

---

## 11. Production Hardening

### 11.1 Privacy & PII Redaction

```python
# utils/privacy.py

import hashlib
import re

PII_PATTERNS = [
    # Aadhaar: 12 digits, possibly space/dash separated (FIXED — was wrong in v2.0)
    (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[AADHAAR_MASKED]'),
    # PAN: ABCDE1234F
    (r'\b[A-Z]{5}\d{4}[A-Z]\b', '[PAN_MASKED]'),
    # Phone: 10 digits, possibly with +91 prefix
    (r'(?:\+91[\s-]?)?\b[6-9]\d{9}\b', '[PHONE_MASKED]'),
    # FIR numbers
    (r'\bFIR\s*No\.?\s*\d+/\d{4}\b', '[FIR_MASKED]'),
    # Email
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_MASKED]'),
    # CNR number
    (r'\b[A-Z]{4}\d{2}-\d{6}-\d{4}\b', '[CNR_MASKED]'),
]

def redact_pii(text: str) -> str:
    for pattern, replacement in PII_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text

def hash_scenario(scenario: str) -> str:
    return hashlib.sha256(scenario.encode()).hexdigest()[:12]
```

**Logging rules:**
- `INFO`: tool name, status, duration, confidence score — NEVER raw input
- `DEBUG`: redacted input, sub-tool call sequence
- `ERROR`: error type, tool name, redacted context
- All scenario inputs hashed, not logged verbatim
- 7-day log retention max

### 11.2 Timeouts & Circuit Breaker

```python
TIMEOUT_CONFIG = {
    "statute_search": 2,        # Local — must be fast
    "legal_concepts": 1,        # Local dictionary
    "bail_assessment": 3,       # Local + lookup
    "limitation_calculator": 1, # Pure computation
    "ecourts_lookup": 10,       # External API
    "indiankanoon_search": 10,  # External API
    "llm_call": 30,             # LLM generation
    "total_orchestration": 60,  # Total for explain_situation
}

CIRCUIT_BREAKER = {
    "failure_threshold": 3,     # 3 failures in window → trip
    "window_seconds": 300,      # 5-minute window
    "cooldown_seconds": 120,    # Skip for 2 minutes after trip
}
```

### 11.3 Caching

```python
CACHE_CONFIG = {
    "statute_search":       {"ttl": 86400},   # 24h — text doesn't change
    "ecourts_lookup":       {"ttl": 1800},    # 30min — case status changes
    "indiankanoon_search":  {"ttl": 3600},    # 1h — corpus changes slowly
    "limitation_calculator": {"ttl": 0},      # NEVER cache — depends on current date
    "legal_concepts":       {"ttl": 86400},   # 24h — dictionary
    "bail_assessment":      {"ttl": 0},       # NEVER cache — inputs vary
}
```

### 11.4 Input Validation

```python
# utils/validators.py

import re
from pydantic import BaseModel, field_validator

class ScenarioInput(BaseModel):
    scenario: str

    @field_validator('scenario')
    def validate_scenario(cls, v):
        if len(v) < 20:
            raise ValueError("Scenario too short — provide more detail for accurate analysis")
        if len(v) > 10000:
            raise ValueError("Scenario too long — maximum 10,000 characters")
        injection_patterns = [
            r'ignore\s+(previous|above|all)\s+instructions',
            r'you\s+are\s+now\s+a',
            r'disregard\s+(the\s+)?system\s+prompt',
        ]
        for pattern in injection_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Invalid input detected")
        return v

CNR_PATTERN = re.compile(r'^[A-Z]{4}\d{2}-\d{6}-\d{4}$')

class CNRInput(BaseModel):
    cnr_number: str

    @field_validator('cnr_number')
    def validate_cnr(cls, v):
        v = v.strip().upper()
        if not CNR_PATTERN.match(v):
            raise ValueError(f"Invalid CNR format. Expected: XXHC01-123456-2024")
        return v
```

---

## 12. Monitoring, Observability & Feedback

> The original plan had zero monitoring. For a legal tool, wrong answers are worse
> than no answers. You MUST be able to detect errors after deployment.

### 12.1 Usage Telemetry (Anonymized)

```python
# utils/metrics.py

class ToolMetrics:
    """
    Tracks anonymized, non-PII usage metrics per tool.
    Stored in local SQLite, NOT sent externally.
    """

    def record_call(self, tool_name: str, status: str, duration_ms: int,
                    confidence_score: float, classification: str = None):
        """
        Records: tool_name, status (success/error/uncertain), duration,
        confidence score, classification (for explain_situation).
        Does NOT record: scenario text, user identity, case details.
        """
        ...

    def get_daily_summary(self) -> dict:
        """
        Returns: calls per tool, avg response time, error rate,
        confidence distribution, most common classifications.
        """
        ...
```

### 12.2 Error Detection

| Signal | Detection Method | Action |
|---|---|---|
| `limitation_calculator` feedback with `issue_type: "wrong_limitation"` | `submit_feedback` tool | **IMMEDIATE**: verify data, fix, redeploy within 24h |
| `bail_assessment` feedback with `issue_type: "wrong_bail_classification"` | `submit_feedback` tool | **IMMEDIATE**: verify BNSS First Schedule data |
| `statute_search` returning 0 results for common queries | Telemetry: zero-result rate > 5% | Review index coverage, add missing keywords |
| `explain_situation` confidence consistently < 0.7 for a domain | Telemetry: classification distribution | Add more keywords to classification rules, expand training scenarios |
| External API error rate > 20% | Circuit breaker trips logged | Check provider status, consider switching provider |
| Data freshness > 90 days | Scheduled check against `data_freshness` timestamps | Trigger statute data update cycle |

### 12.3 Stale Data Alert

```python
# Runs as a scheduled check (weekly)
def check_data_freshness():
    """
    Alerts if any statute data hasn't been verified in > 90 days.
    Critical for BNS/BNSS/BNSA which are still being amended.
    """
    for act in all_acts:
        days_since_verified = (today - act.last_verified).days
        if days_since_verified > 90:
            log.warning(f"STALE DATA: {act.act_id} last verified {days_since_verified} days ago")
```

---

## 13. Build Order — Phased Execution (Realistic)

### v0.1 — "Does it even work?" (Weeks 1-2)

**Goal:** Get working `statute_search` + `explain_situation` in front of 3 advocates.

| # | Deliverable | Est. Hours | Verification |
|---|---|---|---|
| 0.1 | Rename template, `make local` works | 2h | `/health` returns 200 |
| 0.2 | `config.py` with all env vars | 2h | Settings load |
| 0.3 | Directory structure + `__init__.py` files | 1h | Imports work |
| 0.4 | `services/llm_client.py` scaffold | 4h | Mock LLM call works |
| 0.5 | `utils/validators.py`, `utils/privacy.py` | 3h | Unit tests pass |
| 1.1 | Curate BNS 2023 as JSON (v0.1 schema, 5 fields) | 15h | `validate_statute_data.py` passes |
| 1.2 | Curate BNSS 2023 (key chapters only) as JSON | 12h | Validates |
| 1.3 | Curate HMA 1955 as JSON | 2h | Validates |
| 1.4 | `services/search_engine.py` (SQLite FTS5) | 6h | Search returns results |
| 1.5 | `scripts/build_statute_index.py` | 4h | Index builds clean |
| 1.6 | `statute_search.py` + tests (15 cases) | 8h | Tests pass |
| 1.7 | `services/citation_validator.py` | 4h | Validation tests pass |
| 1.8 | `prompts/system_instructions.py` + `explain_situation_prompt.py` | 4h | Prompt produces structured output |
| 1.9 | `explain_situation.py` (v0.1: classify → statute_search → LLM) + tests | 10h | 10 scenario tests pass |
| 1.10 | Manual test with 3 real scenarios from practice | 2h | Advocates find output useful |

**Total: ~79 hours. At 6h/day = ~13 working days. Rounds to 2.5-3 weeks.**

**Gate:** 3 advocates have used it and provided feedback before v0.5 starts.

### v0.5 — "It's actually useful" (Weeks 4-7)

**Goal:** Add the 5 most-requested tools based on v0.1 feedback.

| # | Deliverable | Est. Hours | Verification |
|---|---|---|---|
| 2.1 | Curate DV Act, NI Act (s.138-142), Limitation Act, SMA 1954 as JSON | 20h | Validates |
| 2.2 | Upgrade BNS/BNSS to v0.5 schema (add plain_summary, old_section, bailable/cognizable) | 25h | Validates |
| 2.3 | `services/section_mapper.py` (IPC↔BNS, CrPC↔BNSS) | 8h | Mapper tests pass |
| 2.4 | `old_to_new_mapping.json` (criminal laws only) | 15h | All mappings verified |
| 2.5 | Curate 30 landmark precedent digests | 12h | JSON validates |
| 2.6 | Build `limitation_periods.json` (top 50 cause types) | 10h | Validates |
| 2.7 | Build `legal_concepts.json` (50 terms, EN only) | 8h | Validates |
| 2.8 | `bail_assessment.py` + tests (15 cases, zero-tolerance) | 12h | All BNSS First Schedule classifications verified |
| 2.9 | `limitation_calculator.py` + tests (20 cases, zero-tolerance) | 10h | All 50 cause types verified |
| 2.10 | `legal_concepts.py` + tests | 6h | 10 term lookups correct |
| 2.11 | `ecourts_lookup.py` + tests (mocked HTTP) | 8h | Mock tests pass |
| 2.12 | Upgrade `explain_situation` to call bail/limitation/ecourts | 8h | Enriched scenario tests pass |
| 2.13 | `test_orchestrator_partial_failure.py` | 4h | Degradation works |
| 2.14 | `services/cache_manager.py` | 4h | Cache tests pass |
| 2.15 | Manual test with 20 advocates | 4h | Feedback collected |

**Total: ~154 hours. At 6h/day = ~26 working days. Rounds to 5-6 weeks.**

**Gate:** 20 advocates have used it. `limitation_calculator` and `bail_assessment`
have zero reported errors before v1.0 starts.

### v1.0 — "Practitioners rely on it" (Weeks 8-12)

**Goal:** Add document generation, judgment search, production hardening. Ship publicly.

| # | Deliverable | Est. Hours |
|---|---|---|
| 3.1 | Curate 5 more acts (Constitution Part III, CPC, Contract Act, CPA 2019, Hindu Succession) | 25h |
| 3.2 | Expand precedent digests to 100 cases | 20h |
| 3.3 | Expand legal concepts to 200 terms | 15h |
| 3.4 | Notice templates (5 types, Marathi) | 15h |
| 3.5 | `draft_legal_notice.py` + tests | 12h |
| 3.6 | `indiankanoon_search.py` + tests (mocked HTTP) | 8h |
| 3.7 | `submit_feedback.py` | 4h |
| 3.8 | `utils/metrics.py` (telemetry) | 4h |
| 3.9 | `utils/rate_limiter.py` | 3h |
| 3.10 | Hindi input → English output (prompt tuning) | 6h |
| 3.11 | Privacy audit (PII redaction verified) | 4h |
| 3.12 | `make lint && make test && make pre-commit` | 2h |
| 3.13 | End-to-end test suite (50 scenarios) | 10h |
| 3.14 | Documentation (API_REFERENCE.md, STATUTE_COVERAGE.md) | 6h |
| 3.15 | Containerfile + compose.yaml | 3h |

**Total: ~137 hours. At 6h/day = ~23 working days. Rounds to 4-5 weeks.**

### v1.5 — "Comprehensive" (Ongoing after v1.0)

- Hindi + Marathi output for all tools
- 40+ acts with full schema
- 500 precedent digests
- DOCX/PDF generation for notices
- `jurisdiction_finder`, `court_fee_calculator` (6 states)
- `analyze_case_strength`, `draft_complaint`, `rti_application`
- `legal_checklist`

### Summary Timeline

| Milestone | Elapsed | Status |
|---|---|---|
| v0.1 | Week 3 | 2 tools, 3 acts, tested with 3 advocates |
| v0.5 | Week 7 | 6 tools, 7 acts, tested with 20 advocates |
| v1.0 | Week 12 | 8 tools, 15 acts, public release |
| v1.5 | Week 20+ | 16 tools, 40+ acts, full language support |

**Total to v1.0: ~12 weeks (3 months). Not 33 days.**

---

## 14. Legal & Regulatory Compliance

### 14.1 DPDP Act, 2023
- Data minimization: no storage of scenario input beyond request lifecycle
- No training data collection from user inputs
- Consent mechanism for deployed service

### 14.2 Bar Council of India Guidelines
- Not a replacement for advocate — every output states this
- All document tools produce "drafts for review" only
- No auto-filing, auto-serving, auto-signing

### 14.3 Attribution & Licensing
- Indian Kanoon: "Powered by Indian Kanoon" mandatory on all search results
- India Code: government data, copyright-free under s.52(1)(q) Copyright Act
- eCourts: check provider-specific terms

---

## 15. Non-Negotiables

1. **Disclaimer on all legal-content responses.**
2. **No outcome predictions.** Never "you will win/lose."
3. **Citations from indexed data only.** Bracket notation, validated, hallucinations stripped.
4. **Old ↔ New law bridging** (from v0.5). Every IPC citation includes BNS equivalent.
5. **Evolving law flagged with ⚠.** (e.g., BNSS s.94 electronic service validity)
6. **Indian Kanoon attribution.** Non-removable.
7. **Draft documents are drafts.** `status: "draft_pending_review"` always.
8. **No auto-filing/serving/signing.**
9. **Privacy by design.** Scenario inputs never logged verbatim, never stored, never trained on.
10. **State-specific flagging.** When law differs by state, say which state and warn about others.
11. **Zero-tolerance tools declare confidence.** `limitation_calculator` and `bail_assessment` return `"uncertain"` when confidence < 0.7 rather than guessing.
12. **Land law is out of scope.** Explicitly flagged. "Land law varies entirely by state. Consult a local advocate."

---

## 16. Decisions Required Before Start

### Must-decide (blocks v0.1):
- [ ] **eCourts API provider** (for v0.5): eCourtsIndia.com / Surepass / Vakeel360
- [ ] **LLM provider:** Anthropic Claude (recommended) / OpenAI / Ollama for dev
- [ ] **Deployment target:** Local only / Docker / cloud VM

### Should-decide (blocks v1.0):
- [ ] **Auth:** Enable OAuth for anything beyond local dev?
- [ ] **DOCX library (v1.5):** `python-docx` / `docxtpl` / `pandoc`
- [ ] **Indian Kanoon API access:** Apply for API token (not instant)

### Can-decide-later:
- [ ] Additional API integrations (SCC Online, Manupatra)
- [ ] Voice input for regional languages
- [ ] Analytics dashboard

---

## 17. Full Roadmap

| Version | Tools | Acts | Precedents | Languages (Output) | Key Addition |
|---|---|---|---|---|---|
| v0.1 | 2 | 3 | 0 | EN | Prove the concept works |
| v0.5 | 6 | 7 | 30 | EN | Bail + limitation + eCourts |
| v1.0 | 8 | 15 | 100 | EN + HI (limited) | Notices + IK search + public release |
| v1.5 | 13 | 25 | 300 | EN + HI + MR | Full language + DOCX + deferred tools |
| v2.0 | 16+ | 40+ | 500 | EN + HI + MR + regional | Cause list (via API), OCR, voice input |

---

## Appendix A: Statute Coverage Matrix

### v0.1 (3 acts)
| Act | Sections | Priority |
|---|---|---|
| BNS 2023 | ~358 | Criminal law backbone |
| BNSS 2023 | ~200 (key chapters) | Procedure: arrest, bail, maintenance |
| HMA 1955 | ~30 | Family law backbone |

### v0.5 (adds 4 acts = 7 total)
| Act | Sections | Priority |
|---|---|---|
| DV Act 2005 | ~37 | Domestic violence protection |
| NI Act 1881 | ~20 (s.138-142 focus) | Cheque bounce (volume offence) |
| Limitation Act 1963 | ~31 + 137 articles | Limitation periods |
| Special Marriage Act 1954 | ~50 | Inter-faith marriage |

### v1.0 (adds 8 acts = 15 total)
| Act | Sections |
|---|---|
| Constitution Part III | ~24 articles |
| CPC 1908 | ~158 |
| Contract Act 1872 | ~238 |
| Consumer Protection Act 2019 | ~107 |
| Hindu Succession Act 1956 | ~30 |
| BNSA 2023 | ~170 |
| RERA 2016 | ~92 |
| IT Act 2000 | ~90 |

### v1.5+ (adds 25 acts = 40 total)
Arbitration Act 1996, Companies Act 2013, IBC 2016, POSH Act 2013, MV Act 1988,
NDPS 1985, POCSO 2012, SC/ST Act 1989, DPDP Act 2023, Mediation Act 2023,
Telecom Act 2023, Land Acquisition 2013, RTI Act 2005, LSAA 1987, JJ Act 2015,
Code on Wages 2019, Code on Social Security 2020, Occupational Safety 2020,
Industrial Relations 2020, Gratuity Act 1972, Specific Relief 1963,
Registration Act 1908, Stamp Act 1899, Benami Act 1988, Income Tax 1961 (key provisions).

---

## Appendix B: Test Scenario Bank (20 core + 30 extended)

### Core Scenarios (must pass in v0.1)

```json
[
  {"id": "S001", "scenario": "My husband has been harassing me for dowry. He beats me. What are my options?",
   "domain": "family", "sub_domain": "domestic_violence",
   "expected_acts": ["bns_2023.s85", "dv_act_2005"]},

  {"id": "S002", "scenario": "I received a cheque of Rs.5 lakh which bounced. What can I do?",
   "domain": "commercial", "sub_domain": "cheque_bounce",
   "expected_acts": ["ni_1881.s138"]},

  {"id": "S003", "scenario": "Police came at 2 AM and took my brother without FIR or warrant.",
   "domain": "criminal", "sub_domain": "illegal_detention",
   "expected_acts": ["bnss_2023.s35", "bnss_2023.s36", "constitution.art22"]},

  {"id": "S004", "scenario": "मला माझ्या पत्नीकडून तलाक हवा आहे. आम्ही 5 वर्षे विवाहित आहोत.",
   "domain": "family", "sub_domain": "divorce",
   "expected_acts": ["hma_1955.s13"]},

  {"id": "S005", "scenario": "My wife has filed a false 498A case. I want anticipatory bail.",
   "domain": "criminal", "sub_domain": "arrest_and_bail",
   "expected_acts": ["bns_2023.s85", "bnss_2023.s482"]}
]
```

(15 more core + 30 extended scenarios covering: bail varieties, property, consumer,
RERA, labor, cyber, NRI issues, cheque bounce notice timeline, maintenance quantum,
custody, guardianship, medical negligence, motor accident, criminal appeal, revision.)

---

## Appendix C: Stress Test Record

This plan was stress-tested before execution. The full stress test analysis is preserved
at `/Users/bsahane/Downloads/indian-legal-mcp-server-STRESS-TEST.md` and covers:

**5 critical breaks found and fixed:**
1. Timeline fantasy (33 days → 12 weeks)
2. Data sourcing handwaved (now explicit pipeline)
3. No target user (now: junior mofussil advocate)
4. `cause_list_checker` is a trap (cut from v1)
5. Multi-language premature (EN-first, languages phased)

**6 significant weaknesses found and fixed:**
1. No error budgets (now: zero-tolerance for bail/limitation)
2. Citation validation regex (now: constrained LLM bracket format)
3. Aadhaar regex wrong (now: correct 12-digit pattern)
4. State-specific variations deeper than acknowledged (now: `state_applicability` field + explicit out-of-scope declarations)
5. No monitoring (now: telemetry + feedback tool + stale data alerts)
6. BM25 + FTS5 redundancy (now: FTS5 only with built-in BM25)

**7 design decisions that survived unchanged** — see Preamble.

---

## Appendix D: Cost Estimation

| Component | Per 1,000 calls | Notes |
|---|---|---|
| `statute_search` | ₹0 | Local, no API |
| `legal_concepts` | ₹0 | Local |
| `bail_assessment` | ₹0 | Local |
| `limitation_calculator` | ₹0 | Local |
| `ecourts_lookup` | ₹400-1,600 | Provider-dependent |
| `indiankanoon_search` | ₹400-800 | Per-query pricing |
| `explain_situation` (LLM call) | ₹1,200-2,400 | Claude Sonnet ~$15-30 |
| `draft_legal_notice` (LLM call) | ₹1,200-2,400 | Claude Sonnet |

**Typical usage for a solo advocate (50 queries/day, 22 days/month):**
- ~1,100 queries/month
- ~30% hit LLM (`explain_situation`, `draft_legal_notice`) = 330 LLM calls = ~₹500/month
- ~10% hit external API = 110 API calls = ~₹100/month
- **Total: ~₹600/month** (under $8/month)

This is viable as a self-hosted tool. No venture funding required.

---

*This plan has been stress-tested, scope-cut, and timeline-corrected. It knows what it
doesn't know (land law, state-specific labor codes, cause list scraping) and says so
explicitly. Execute v0.1 first. Ship it. Learn. Then decide what v0.5 actually needs
based on what 3 advocates told you, not what this spec imagines.*
