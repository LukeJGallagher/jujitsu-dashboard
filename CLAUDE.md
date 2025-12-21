# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JJIF (Ju-Jitsu International Federation) competition data scraping and analysis pipeline for Team Saudi. Scrapes athlete profiles, competition brackets, and results from sportdata.org with a focus on Asian competitions and Saudi athletes.

## Quick Start Commands

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium  # Required for bracket scraping

# Run Streamlit dashboard
streamlit run dashboard.py

# Scrape brackets for a specific event (uses verid from event_mappings.json)
python robust_bracket_scraper.py --scrape 714  # 2023 Asian Championship

# List available events
python robust_bracket_scraper.py --list
```

## Architecture

### Data Flow
```
sportdata.org (CAPTCHA protected)
        │
        ▼
robust_bracket_scraper.py  ──► Brackets/*.html (raw HTML)
        │                  ──► Results/brackets_{verid}_{timestamp}.json
        ▼
dashboard.py (Streamlit)  ◄── Profiles/*.json (athlete data)
                          ◄── Results/*.json (scraped data)
```

### Key Components

**Scrapers (Playwright-based)**
- `robust_bracket_scraper.py` - Main scraper with CAPTCHA handling. Opens browser, waits for manual CAPTCHA solve, extracts categories and competitors.
- `smart_bracket_scraper.py` - Earlier version, less robust with CAPTCHA redirects.
- `scrape_athlete_profiles.py` - Scrapes individual athlete profiles by country code.

**Dashboard**
- `dashboard.py` - 166KB Streamlit app with Team Saudi branding. Shows athlete profiles, competition results, head-to-head analysis, bracket visualization.

**Data Files**
- `event_mappings.json` - Maps event names to sportdata.org `verid` values (e.g., "ADULTS ASIAN CHAMPIONSHIP 2023": "714")
- `Profiles/{COUNTRY_CODE}{ID}.json` - Individual athlete profiles
- `Results/brackets_{verid}_{timestamp}.json` - Scraped bracket data with categories and competitors
- `Brackets/bracket_{verid}_{catid}.html` - Raw bracket HTML for parsing

## Claude Code Skills

Available skills in `.claude/skills/`:

| Skill | File | Use For |
|-------|------|---------|
| **Web Scraping Expert** | `web-scraping-expert.md` | Scraping competition results, rate limiting, anti-bot strategies |
| **Browser Automation** | `browser-automation-expert.md` | Playwright/Selenium, CAPTCHA handling, JavaScript rendering |
| **HTML Extraction** | `html-extraction-specialist.md` | BeautifulSoup, lxml, parsing brackets and tables |
| **API Gathering** | `api-gathering-expert.md` | REST APIs, OpenRouter AI extraction, rate limiting |
| **Python Specialist** | `python-data-specialist.md` | Async programming, data processing, file I/O |
| **Jiu Jitsu Analyst** | `jiu-jitsu-analyst.md` | Competition rules, weight categories, Team Saudi athletes |

Skills auto-invoke based on context.

## Environment Variables

Required in `.env`:
```bash
OPENROUTER_API_KEY=sk-or-v1-xxxx  # For AI-assisted extraction
```

Optional:
```bash
ANTHROPIC_API_KEY=sk-ant-xxxx     # Claude direct access
FIRECRAWL_API_KEY=fc-xxxx         # JavaScript rendering service
```

### OpenRouter Free Models (Best First)

| Model | Best For |
|-------|----------|
| `google/gemini-2.0-flash-exp:free` | HTML/JSON extraction (recommended) |
| `google/gemini-exp-1206:free` | Complex analysis |
| `meta-llama/llama-3.2-3b-instruct:free` | Quick simple tasks |
| `qwen/qwen-2-7b-instruct:free` | Arabic/multilingual |

## sportdata.org URL Structure

```
Base: https://www.sportdata.org/ju-jitsu/set-online/

Event categories list:
veranstaltung_info_main.php?vernr={verid}&ver_info_action=catauslist

Bracket/draw for category:
veranstaltung_info_main.php?vernr={verid}&catid={catid}&ver_info_action=catdraw

Athlete profile:
teilnehmer_info.php?id={athlete_id}
```

## CAPTCHA Handling

sportdata.org has reCAPTCHA protection. When scraping:
1. Browser opens automatically (non-headless)
2. CAPTCHA page appears - **solve manually in the browser**
3. Scraper waits up to 10 minutes, polling for content
4. After CAPTCHA solved, scraper continues automatically

## Team Saudi Focus

Country codes for filtering: `KSA`, `SAU`, `"Saudi Arabia"`, `السعودية`

Key Asian events (verid values):
- 714: ADULTS ASIAN CHAMPIONSHIP 2023
- 662: ADULTS ASIAN CHAMPIONSHIP 2022
- 621: ADULTS ASIAN CHAMPIONSHIP 2021
- 715: U16/U18/U21 ASIAN CHAMPIONSHIP 2023

## Weight Categories (JJIF)

**Male**: 56kg, 62kg, 69kg, 77kg, 85kg, 94kg, +94kg
**Female**: 48kg, 52kg, 57kg, 63kg, 70kg, +70kg

## Data Directories

```
Results/     - Scraped JSON data, timestamped
Brackets/    - Raw HTML bracket pages
Profiles/    - Individual athlete JSON profiles
Data/        - Aggregated/processed data
Archive/     - Historical data backups
```
