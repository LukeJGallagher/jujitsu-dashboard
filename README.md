# 🥋 Team Saudi Jiu Jitsu - Web Scraping Pipeline

A comprehensive web scraping and performance analysis system for Jiu Jitsu competitions, designed for Team Saudi performance analysts.

## Features

- **Multi-Source Scraping**: AJP Tour, IBJJF, JJIF, UAEJJF
- **AI-Powered Extraction**: Uses free LLM models for intelligent data extraction
- **Athlete Profiling**: Comprehensive athlete profiles with performance analysis
- **Team Saudi Focus**: Automatic filtering and prioritization of Saudi athletes
- **Interactive Dashboard**: Streamlit dashboard with Team Saudi branding
- **Automated Scheduling**: Configurable auto-scraping with email notifications
- **Claude Code Integration**: Skills and agents for AI-assisted development

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.template` to `.env` and add your API keys:

```bash
cp .env.template .env
# Edit .env with your keys
```

### 3. Run Dashboard

```bash
streamlit run dashboard.py
```

### 4. Scrape Data

```bash
# Scrape a competition URL
python scraper.py --url "https://ajptour.com/events/123/results"

# Add a Saudi athlete
python athlete_scraper.py add "Athlete Name" --weight 77kg --belt Brown

# Build athlete profile
python athlete_scraper.py build "Athlete Name"
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    JIU JITSU SCRAPING PIPELINE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  AJP Tour   │  │   IBJJF     │  │    JJIF     │  Data       │
│  │  Scraper    │  │   Scraper   │  │   Scraper   │  Sources    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                     │
│         └────────────────┼────────────────┘                     │
│                          │                                      │
│                          ▼                                      │
│              ┌───────────────────────┐                         │
│              │   AI Extraction       │  OpenRouter              │
│              │   Agents              │  Free Models             │
│              └───────────┬───────────┘                         │
│                          │                                      │
│         ┌────────────────┼────────────────┐                    │
│         │                │                │                     │
│         ▼                ▼                ▼                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Results    │  │  Athlete    │  │  Rankings   │  Data       │
│  │  CSV/JSON   │  │  Profiles   │  │  Tracker    │  Storage    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                │                │                     │
│         └────────────────┼────────────────┘                    │
│                          │                                      │
│                          ▼                                      │
│              ┌───────────────────────┐                         │
│              │   Streamlit           │  Team Saudi              │
│              │   Dashboard           │  Theme                   │
│              └───────────────────────┘                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## AI Agents

The system includes specialized AI agents:

| Agent | Purpose | Model |
|-------|---------|-------|
| ResultsExtraction | Extract results from HTML | gemini-2.0-flash |
| AthleteProfile | Build athlete profiles | llama-3.2-3b |
| ScheduleParsing | Parse event schedules | mistral-7b |
| BracketAnalysis | Analyze tournament brackets | gemini-2.0-flash |
| PerformanceAnalysis | Analyze athlete performance | gemini-2.0-flash |
| CompetitorScouting | Scout opponents | gemini-2.0-flash |

## Data Sources

### Primary Sources

1. **AJP Tour** (Abu Dhabi Jiu Jitsu Pro)
   - Professional BJJ circuit
   - API available
   - Priority: High

2. **JJIF** (Jiu-Jitsu International Federation)
   - Olympic pathway federation
   - World Championships, Asian Games
   - Priority: High

3. **IBJJF** (International Brazilian Jiu-Jitsu Federation)
   - World's largest BJJ federation
   - JavaScript-heavy site (needs Selenium)
   - Priority: Medium

### Competition Formats

- **Gi** (Traditional with uniform)
- **No-Gi** (Submission wrestling style)
- **Fighting** (JJIF Olympic format)

## Team Saudi Configuration

Saudi athletes are automatically identified by:
- Country codes: KSA, SAU
- Full names: Saudi Arabia
- Arabic: السعودية

### Priority Tracking

Add priority athletes in `.env`:
```
PRIORITY_ATHLETES=Athlete1,Athlete2,Athlete3
```

## Dashboard Features

- **Overview Tab**: Medal counts, charts, recent results
- **Competition Results**: Filterable results table
- **Athlete Profiles**: Saudi athlete management
- **Analytics**: Performance trends and statistics
- **Scraping Tools**: Quick access to scraping commands

## Automation

### Scheduled Scraping

```bash
# Start scheduler (runs in background)
python auto_scraper.py --mode scheduler
```

Default intervals:
- Full scrape: Every 6 hours
- Quick check: Every 1 hour
- Daily report: 8:00 AM

### Email Notifications

Configure in `.env`:
```
SENDER_EMAIL=your@email.com
SENDER_PASSWORD=app_specific_password
RECIPIENT_EMAILS=analyst1@team.com,analyst2@team.com
```

## Weight Categories

### Male
| Category | Weight |
|----------|--------|
| Rooster | 56kg |
| Light Feather | 62kg |
| Feather | 69kg |
| Light | 77kg |
| Middle | 85kg |
| Medium Heavy | 94kg |
| Heavy | +94kg |

### Female
| Category | Weight |
|----------|--------|
| Light Rooster | 48kg |
| Rooster | 52kg |
| Light Feather | 57kg |
| Feather | 63kg |
| Light | 70kg |
| Heavy | +70kg |

## Development

### Adding New Data Source

1. Create scraper class in `scraper.py`:
```python
class NewSourceScraper(BaseScraper):
    def __init__(self):
        super().__init__("NewSource")
        # Configure source

    async def scrape_results(self, url):
        # Implement scraping logic
        pass
```

2. Register in pipeline:
```python
self.scrapers["newsource"] = NewSourceScraper()
```

### Adding New Agent

1. Create agent class in `agents.py`:
```python
class NewAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="NewAgent",
            description="Description",
            task_type="task_type"
        )

    async def execute(self, *args, **kwargs):
        # Implement agent logic
        pass
```

## File Structure

```
Jiu Jitsu/
├── .claude/                # Claude Code configuration
│   ├── settings.local.json
│   └── skills/
├── .streamlit/             # Streamlit configuration
│   └── config.toml
├── Results/                # Output: scraped results
├── Athletes/               # Output: athlete profiles
├── Archive/                # Historical data
├── config.py              # Configuration
├── models.py              # Data models
├── agents.py              # AI agents
├── scraper.py             # Main scraper
├── athlete_scraper.py     # Athlete tools
├── dashboard.py           # Streamlit UI
├── auto_scraper.py        # Automation
├── requirements.txt       # Dependencies
├── .env.template          # Environment template
├── CLAUDE.md              # Claude Code guide
└── README.md              # This file
```

## Support

For issues or questions:
1. Check `scraping.log` for error details
2. Review `CLAUDE.md` for quick reference
3. Check Claude skills for domain knowledge

---

**Team Saudi Performance Analysis**
🇸🇦 Excellence in Sport
