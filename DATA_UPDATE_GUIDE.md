# Data Update Guide

Step-by-step guide for updating JJIF competition data.

## Quick Reference

| Data Type | Script | CAPTCHA Required |
|-----------|--------|------------------|
| Athlete Profiles | `python scrape_all_asian_profiles.py` | Yes (once) |
| Event Brackets | `python robust_bracket_scraper.py --scrape {VERID}` | Yes (once per event) |
| Batch Events | `python batch_asian_scraper.py` | Yes (once) |
| Parse Brackets to JSON | `python parse_bracket_html.py --all` | No |
| Rebuild Cache | `python data_cache.py` | No |

---

## Step 1: Update Athlete Profiles

Scrapes athlete profiles for all Asian countries (28 countries in priority order).

```bash
cd "c:\Users\l.gallagher\OneDrive - Team Saudi\Documents\Performance Analysis\Sport Detailed Data\Jiu Jitsu"
python scrape_all_asian_profiles.py
```

**What it does:**
- Opens browser, requires ONE CAPTCHA solve
- Scrapes profiles for KSA, UAE, KAZ, UZB, THA, JOR, IRI, and 20+ more Asian countries
- Saves to `Profiles/` folder as `athlete_profiles_{COUNTRY}_{timestamp}.json`

**Output:** Individual country profile files + consolidated `Results/all_profiles.json`

---

## Step 2: Scrape Event Brackets

Scrapes bracket/match data for a specific event.

```bash
# Find event ID (verid) from event_mappings.json or the website URL
python robust_bracket_scraper.py --scrape {VERID} --force

# Example: 2025 World Championships
python robust_bracket_scraper.py --scrape 811 --force
```

**What it does:**
- Opens browser, requires ONE CAPTCHA solve
- Downloads all bracket HTML files for each category
- Saves HTML to `Brackets/` folder as `bracket_{verid}_{catid}.html`
- Saves metadata to `Results/brackets_{verid}_{timestamp}.json`

**Alternative - Batch scrape multiple Asian events:**
```bash
python batch_asian_scraper.py
```

---

## Step 3: Parse Brackets to JSON

Converts bracket HTML files into structured match data.

```bash
python parse_bracket_html.py --all
```

**What it does:**
- Reads all `Brackets/bracket_*.html` files
- Extracts matches with: athletes, countries, scores, winners, rounds
- Saves to `Results/all_matches.json`

**Output structure:**
```json
{
  "events": [
    {
      "verid": "811",
      "event_name": "2025 WORLD CHAMPIONSHIPS",
      "categories": [
        {
          "catid": "19271",
          "category": "ADULTS CONTACT HIF JU-JITSU FEMALE +70 KG",
          "rounds": ["Round 1", "Quarterfinals", "Semifinals", "Finals"],
          "matches": [
            {
              "round": "Round 1",
              "red_corner": {"name": "...", "country": "KAZ", "score": 10},
              "blue_corner": {"name": "...", "country": "UZB", "score": 5},
              "winner": "..."
            }
          ]
        }
      ]
    }
  ]
}
```

---

## Step 4: Rebuild Cache (Optional)

Pre-aggregates data for faster dashboard loading.

```bash
python data_cache.py
```

---

## Step 5: Run Dashboard

```bash
streamlit run dashboard.py
```

---

## Common Event IDs (verid)

| Event | verid |
|-------|-------|
| 2025 World Championships | 811 |
| 2024 Asian Championships | 720 |
| 2024 World Championships | 722 |
| 2023 Asian Championships | 618 |

Full list in `event_mappings.json`

---

## Troubleshooting

### CAPTCHA Won't Clear
- Make sure you click the checkbox in the browser window
- Wait for the page to fully load after solving
- The scraper waits up to 5 minutes for CAPTCHA

### Missing Bracket Data
1. Check `Brackets/` folder has HTML files
2. Run `python parse_bracket_html.py --all` to regenerate JSON
3. Verify `Results/all_matches.json` has the event data

### Dashboard Shows No Data
1. Check `Results/all_matches.json` exists and has content
2. Check `Results/all_profiles.json` exists
3. Restart dashboard: `streamlit run dashboard.py`

---

## File Locations

```
Jiu Jitsu/
├── dashboard.py                  # Main dashboard
├── parse_bracket_html.py         # HTML to JSON parser
├── robust_bracket_scraper.py     # Single event bracket scraper
├── batch_asian_scraper.py        # Batch Asian events scraper
├── scrape_all_asian_profiles.py  # Batch profile scraper
├── data_cache.py                 # Cache builder
├── loss_chain_analyzer.py        # Opponent analysis
├── Results/
│   ├── all_matches.json          # All parsed match data
│   ├── all_profiles.json         # All athlete profiles
│   └── brackets_*.json           # Bracket metadata
├── Brackets/
│   └── bracket_*.html            # Raw bracket HTML (gitignored)
├── Profiles/
│   └── athlete_profiles_*.json
└── Archive_Scrapers/             # Legacy/backup scrapers
```

---

## Full Data Refresh Workflow

```bash
# 1. Update profiles (solve CAPTCHA once)
python scrape_all_asian_profiles.py

# 2. Scrape new event brackets (solve CAPTCHA once per event)
python robust_bracket_scraper.py --scrape 811 --force

# OR batch scrape multiple events
python batch_asian_scraper.py

# 3. Parse all brackets to JSON
python parse_bracket_html.py --all

# 4. Rebuild cache
python data_cache.py

# 5. Launch dashboard
streamlit run dashboard.py
```
