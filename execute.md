# Competitive Analysis Feature - Execution Log

**Started**: 2026-03-10
**Plan Version**: 2.18

---

## Phase 0: Competitor Data Collection (Step 4 button) - COMPLETED

### Changes Made

#### 1. Import Addition (`techaudit_agent.py:17`)
- Added `from typing import Optional`
- Added `urlparse` to existing `from urllib.parse import quote, urlparse`

#### 2. Path Constants & COMPETITORS_BY_CATEGORY (`techaudit_agent.py:269-319`)
- `BASE_DIR`, `COMPETITORS_DATA_PATH`, `DEFAULT_COMPETITORS_PATH`, `COMPETITORS_SS_KEY`
- `COMPETITORS_BY_CATEGORY` dict with all 4 categories (5-6 competitors each)
- `_validate_competitor_config()` function — validates keys match `CATEGORIES`

#### 3. Session State Keys (`techaudit_agent.py:347-349`)
Added 3 keys to `_init()` defaults:
- `COMPETITORS_SS_KEY: None` — competitors data cache
- `"collection_in_progress": False` — prevent duplicate button clicks
- `"competitive_context": ""` — preserve context for re-run/QA retry

#### 4. Helper Functions (`techaudit_agent.py:546-770`)
New section "5b · COMPETITOR DATA" with:

| Function | Line | Purpose |
|----------|------|---------|
| `validate_url_format()` | 548 | URL format validation (urlparse only, no requests) |
| `dedup_articles()` | 559 | Remove duplicates by URL, sort by date desc |
| `validate_competitors_schema()` | 570 | Validate data structure (schema_version, competitors, articles) |
| `migrate_competitors_schema()` | 593 | Schema version migration (v1.0 passthrough) |
| `save_competitors_data()` | 600 | Dual storage: session_state 1st + file 2nd |
| `load_competitors_data()` | 609 | 3-layer fallback: session_state → file → default |
| `fetch_articles_for_competitor()` | 650 | Gemini + Google Search per competitor |
| `collect_competitor_articles()` | 691 | Orchestrator: collect all competitors for current category |

#### 5. Step 4 UI Button (`techaudit_agent.py:2175-2194`)
- "📥 Collect Competitor Articles" button inserted before Generate Article button
- Disabled during collection (`collection_in_progress` flag)
- try/except/finally pattern with spinner, success/info/warning messages
- Located after NotebookLM expander, before `st.markdown("---")`

#### 6. Default Data File (NEW)
- Created `data/default_competitors.json`
- Schema version 1.0, all 4 categories
- 22 competitors total, 32 sample articles
- Used as 3rd-layer fallback by `load_competitors_data()`

### Verification
- [x] Syntax OK
- [x] `data/default_competitors.json` — JSON valid, all 4 categories present
- [x] All `COMPETITORS_BY_CATEGORY` keys match `CATEGORIES` exactly

---

## Phase 1: Load & Display (Step 5 — 📊 Competitors tab) - COMPLETED

### Changes Made

#### 1. New Functions (`techaudit_agent.py:773-878`)

| Function | Line | Purpose |
|----------|------|---------|
| `load_competitors_for_category()` | 773 | Case-insensitive category match from loaded data |
| `build_competitive_context()` | 785 | Generate competitor context block for prompt injection |
| `render_competitors_dashboard()` | 817 | Full dashboard: competitors table + articles accordion |

#### 2. `generate_article()` Signature Modified (`techaudit_agent.py:1102`)
- Added `competitive_context: str = ""` parameter
- Appends context to prompt when non-empty: `prompt += f"\n\n{competitive_context}"`

#### 3. `generate_article_claude()` Signature Modified (`techaudit_agent.py:1166`)
- Added `competitive_context: str = ""` parameter
- Appends context to prompt when non-empty: `prompt += f"\n\n{competitive_context}"`

#### 4. `_do_generate()` Signature Modified (`techaudit_agent.py:2236`)
- Added `competitive_context: str = ""` parameter
- Passes to both `generate_article_claude()` and `generate_article()` calls

#### 5. All 4 Call Sites Updated

| Line | Location | How competitive_context is passed |
|------|----------|-----------------------------------|
| 2216 | step_4_research() Generate button | Calculated fresh via `build_competitive_context()`, saved to session_state |
| 2340 | step_5_article() Retry Generation | Reused from `st.session_state.get("competitive_context", "")` |
| 2351 | step_5_article() safety net | Reused from `st.session_state.get("competitive_context", "")` |
| 2427 | handle_rerun() QA re-run | Reused from `st.session_state.get("competitive_context", "")` |

#### 6. "📊 Competitors" Tab Added (`techaudit_agent.py:2410-2462`)
- 5th tab added to `st.tabs()` list
- Tab handler: loads data → matches category → renders dashboard or shows fallback selectbox
- No data: shows info message "Use Step 4 to collect"

### Dashboard UI Components
- **Competitors table**: `st.dataframe()` with Company, Tier, Blog columns
- **Articles accordion**: `st.expander()` per competitor (CLOSED by default)
  - Each article shows: title (linked), published date, relevance
- **Category mismatch**: `st.selectbox()` to pick available category

### Verification
- [x] Syntax OK (`py_compile` passes)
- [x] All 4 `_do_generate()` call sites include `competitive_context`
- [x] Both `generate_article()` and `generate_article_claude()` accept and inject context
- [x] Tab renders from session_state data (no redundant API calls)
- [x] Backward compatible — empty string default has no prompt effect

---

## Phase 2: Error Handling - COMPLETED

### Changes Made

#### 1. Logger Setup (`techaudit_agent.py:547-553`)
- `_comp_log = logging.getLogger("competitor_data")`
- StreamHandler with `HH:MM:SS [LEVEL] message` format
- INFO level — logs collection flow, file I/O, filtered URLs, API errors

#### 2. Custom Error Classes (`techaudit_agent.py:556-570`)

| Class | Parent | Usage |
|-------|--------|-------|
| `CompetitorDataError` | `Exception` | Base — category not found, config mismatch |
| `SchemaValidationError` | `CompetitorDataError` | Missing fields in JSON structure |
| `DataLoadingError` | `CompetitorDataError` | File load / migration failures |
| `GeminiAPIError` | `CompetitorDataError` | Gemini API call failures |

#### 3. Enhanced try-except in `load_competitors_data()`
- `FileNotFoundError` — logged info, silent fallthrough
- `json.JSONDecodeError` — logged error + user warning "invalid JSON"
- `SchemaValidationError` — logged error + user warning with field detail
- `DataLoadingError` — logged error + user warning
- `IOError` / `PermissionError` — logged error + user warning "unable to read"
- Default fallback path also has specific exception handlers

#### 4. Enhanced `fetch_articles_for_competitor()`
- `ValueError` / `json.JSONDecodeError` — parse errors logged, returns `[]`
- Other exceptions — wrapped and re-raised as `GeminiAPIError`
- Non-list responses detected and logged

#### 5. Enhanced `collect_competitor_articles()`
- `GeminiAPIError` per-competitor — logged, added to `failed_comps`, continues
- All competitors failed → `st.error()` + return None
- Partial failure → `st.warning()` showing skipped names
- `SchemaValidationError` after collection — logged + user error
- `CompetitorDataError` — logged + user error
- Filtered URL count logged per competitor
- Collection start/complete logged with counts

#### 6. `save_competitors_data()` — file save logged, IOError logged as warning

### User-Facing Messages
| Scenario | UI Element | Message |
|----------|-----------|---------|
| Invalid JSON file | `st.warning` | "Competitor data file has invalid JSON. Re-collect in Step 4." |
| Schema error | `st.warning` | "Competitor data format error: {field detail}" |
| All collections failed | `st.error` | "All competitor collections failed. Check API key and try again." |
| Partial collection | `st.warning` | "Partial collection — skipped: {names}" |
| API parse error | `st.warning` | "Could not parse articles for {name}. Skipping." |
| File unreadable | `st.warning` | "Unable to read competitor data file." |

### Verification
- [x] Syntax OK (`py_compile` passes)
- [x] 4 custom error classes defined and used (29 total references)
- [x] 28 log statements across collection/load/save/fetch functions
- [x] All error paths show user-friendly `st.warning`/`st.error` messages
- [x] No silent error swallowing — every except block logs or warns

---

## Phase 3: Performance Optimization - COMPLETED

### Changes Made

#### 1. Caching Strategy (session_state based) — Already Optimal
- `load_competitors_data()`: 1st session_state → 2nd file → 3rd default
- `save_competitors_data()`: immediately updates session_state + async file
- `@st.cache_data` forbidden (conflicts with session_state) — not used
- Subsequent calls within same session hit session_state cache (O(1))

#### 2. Dashboard UI Optimization (`render_competitors_dashboard`)
- **Sorted by tier**: Tier 1 competitors shown first, then Tier 2 (sorted by name within tier)
- **Summary stats**: Header shows competitor count + article count + collection timestamp
- **Articles column**: Added to table for at-a-glance article counts per competitor
- **Accordion CLOSED**: All `st.expander(expanded=False)` — lazy load on click
- **Defensive re-sort**: Articles re-sorted by date in render (handles file/default data)

#### 3. Memory Efficiency
- JSON loaded once per session via session_state cache
- No redundant copies — `load_competitors_for_category()` returns reference to existing dict
- `build_competitive_context()` limits to max 2 article titles per competitor (prompt size control)
- `dedup_articles()` processes in single pass with set-based URL tracking

### Verification
- [x] Syntax OK
- [x] Dashboard sorts by tier (1 → 2) then name
- [x] Table shows Articles count column
- [x] All expanders start closed
- [x] No `@st.cache_data` usage (session_state only)

---

## Phase 4: Integration & Testing - COMPLETED

### Test File
- `tests/test_competitors.py` — 50 tests, all passing (0.41s)
- Framework: pytest 9.0.2, Python 3.11.9
- Streamlit/genai/anthropic mocked at module level (no API calls)

### Test Coverage (10 test classes, 50 tests)

| Class | Tests | What it covers |
|-------|-------|---------------|
| `TestValidateUrlFormat` | 8 | https/http/ftp/empty/None/non-string/no-domain |
| `TestDedupArticles` | 5 | duplicates/sort/missing dates/empty/empty URL |
| `TestValidateCompetitorsSchema` | 5 | valid/missing version/missing competitors/field/article field |
| `TestMigrateCompetitorsSchema` | 3 | v1.0 passthrough/unknown version/missing version |
| `TestSaveLoadCompetitorsData` | 6 | session_state/file/fallback default/all fail |
| `TestLoadCompetitorsForCategory` | 5 | exact/case-insensitive/no match/None/no schema |
| `TestBuildCompetitiveContext` | 5 | content/None data/no match/2 title limit/empty articles |
| `TestValidateCompetitorConfig` | 2 | categories match/all covered |
| `TestEdgeCases` | 7 | **All 7 plan.md scenarios** (see below) |
| `TestDefaultCompetitorsFile` | 4 | exists/valid JSON/passes schema/all categories |

### 7 Edge Case Scenarios (from plan.md)

| # | Scenario | Test | Result |
|---|----------|------|--------|
| 1 | Missing API key | `test_missing_api_key` | Returns None, shows warning |
| 2 | Empty articles list | `test_empty_articles_from_gemini` | Dashboard renders, 0 articles |
| 3 | Invalid article URLs | `test_invalid_urls_filtered` | Only valid https kept |
| 4 | Duplicate articles | `test_duplicate_articles_deduped` | First occurrence kept |
| 5 | Schema version mismatch | `test_schema_version_mismatch` | Returns None via migration |
| 6 | Large JSON (100 comps × 50 arts) | `test_large_json_handles` | Loads without error |
| 7 | Category not found | `test_category_not_found` | Returns None |

### Verification
- [x] `pytest tests/test_competitors.py -v` — **50 passed in 0.41s**
- [x] All 7 edge cases from plan.md covered
- [x] Default competitors file validated (exists, valid JSON, passes schema, all 4 categories)
- [x] No API calls during tests (all mocked)

---

## Key Line References (post-Phase 1)

| Item | Line |
|------|------|
| `COMPETITORS_BY_CATEGORY` | 275 |
| `_validate_competitor_config()` | 318 |
| Session state keys | 347-349 |
| `validate_url_format()` | 548 |
| `dedup_articles()` | 559 |
| `validate_competitors_schema()` | 570 |
| `migrate_competitors_schema()` | 593 |
| `save_competitors_data()` | 600 |
| `load_competitors_data()` | 609 |
| `fetch_articles_for_competitor()` | 650 |
| `collect_competitor_articles()` | 691 |
| `load_competitors_for_category()` | 773 |
| `build_competitive_context()` | 785 |
| `render_competitors_dashboard()` | 817 |
| `generate_article()` | 1102 |
| `generate_article_claude()` | 1166 |
| Step 4 Collect button | 2175 |
| Step 4 Generate button | 2209 |
| `_do_generate()` | 2236 |
| `step_5_article()` | 2326 |
| `st.tabs()` (5 tabs) | 2410 |
| `handle_rerun()` | 2421 |
| `tab_competitors` handler | 2447 |
