"""
Team Saudi Jiu Jitsu Analysis Dashboard
=======================================
Streamlit dashboard for analyzing JJIF athlete data with focus on Team Saudi.
"""
import streamlit as st
import pandas as pd
import json
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Configuration
BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "Results"
PROFILES_DIR = BASE_DIR / "Profiles"
FLAG_URL_BASE = "https://flagcdn.com/48x36/"
PHOTO_URL_BASE = ""

# Event codes for bracket access
EVENT_CODES = {
    # 2025 Events
    "2025 ADULTS WORLD CHAMPIONSHIPS (THA)": "897",
    "2025 WORLD CHAMPIONSHIPS - U16-U18-U21 (THA)": "813",
    "2025 ASIAN CHAMPIONSHIPS ADULTS (JOR)": None,
    "2025 ASIAN CHAMPIONSHIPS U21 (JOR)": None,
    "U16/U18 ASIAN CHAMPIONSHIP 2025 (THA)": None,
    # 2024 Events
    "ADULTS WORLD CHAMPIONSHIPS 2024 (GRE)": "811",
    "2024 WORLD CHAMPIONSHIPS - U16-U18-U21 (GRE)": None,
    "ADULTS ASIAN CHAMPIONSHIP 2024 (UAE)": None,
    "U16/U18/U21 ASIAN CHAMPIONSHIP 2024 (UAE)": None,
    # 2023 Events
    "WORLD COMBAT GAMES 2023 (KSA)": None,
    "ADULTS WORLD CHAMPIONSHIPS 2023 (MGL)": None,
    "U16/U18/U21 WORLD CHAMPIONSHIPS 2023 (KAZ)": None,
    # 2022 Events
    "ADULTS WORLD CHAMPIONSHIPS 2022 (UAE)": None,
    "U16/U18/U21 WORLD CHAMPIONSHIPS 2022 (UAE)": None,
}


def get_event_bracket_url(event_name):
    """Get bracket URL for an event if we have the event ID."""
    # Return None - bracket links removed for deployment
    return None

# Page config
st.set_page_config(
    page_title="Team Saudi Jiu Jitsu Analysis",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# TEAM SAUDI THEME CSS
# =============================================================================
TEAM_SAUDI_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Tajawal:wght@300;400;500;700;800&display=swap');

:root {
    --saudi-green: #006C35;
    --saudi-green-dark: #004d26;
    --saudi-green-light: #2A8F5C;
    --saudi-gold: #A08E66;
    --saudi-white: #ffffff;
}

.stApp {
    font-family: 'Poppins', 'Tajawal', sans-serif;
    background: #f8f9fa;
}

.main-header {
    background: linear-gradient(135deg, var(--saudi-green) 0%, var(--saudi-green-dark) 100%);
    color: white;
    padding: 2rem 2.5rem;
    border-radius: 12px;
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
    border-top: 4px solid var(--saudi-gold);
}

.main-header h1 {
    font-weight: 700;
    font-size: 2.2rem;
    margin: 0;
}

.main-header p {
    color: var(--saudi-gold);
    margin: 0.5rem 0 0 0;
    font-size: 1rem;
}

.sub-header {
    font-size: 1.5rem;
    color: var(--saudi-green);
    border-bottom: 2px solid var(--saudi-green);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}

.metric-card {
    background: linear-gradient(145deg, #ffffff 0%, #f9f9f9 100%);
    border-radius: 12px;
    padding: 1.5rem;
    margin: 0.5rem 0;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
    border-left: 5px solid var(--saudi-green);
    transition: all 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0, 108, 53, 0.2);
    border-left-color: var(--saudi-gold);
}

.metric-value {
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--saudi-green);
}

.metric-label {
    font-size: 0.9rem;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.saudi-highlight {
    background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
    padding: 1.5rem;
    border-left: 4px solid var(--saudi-green);
    border-radius: 8px;
    margin: 1rem 0;
}

.competitor-card {
    background-color: #f5f5f5;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 3px solid #ccc;
}

.flag-img {
    width: 32px;
    height: auto;
    vertical-align: middle;
    margin-right: 8px;
    border-radius: 2px;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--saudi-green) 0%, var(--saudi-green-dark) 100%);
}

[data-testid="stSidebar"] * {
    color: white !important;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--saudi-gold) !important;
}

.stButton > button[kind="primary"] {
    background-color: var(--saudi-green);
    color: white;
}

.stButton > button[kind="primary"]:hover {
    background-color: var(--saudi-gold);
}

.footer {
    text-align: center;
    padding: 1.5rem;
    margin-top: 2rem;
    background: linear-gradient(135deg, var(--saudi-green) 0%, var(--saudi-green-dark) 100%);
    color: white;
    border-radius: 10px;
    border-top: 3px solid var(--saudi-gold);
}
</style>
"""

st.markdown(TEAM_SAUDI_CSS, unsafe_allow_html=True)


# =============================================================================
# DATA FUNCTIONS
# =============================================================================
@st.cache_data(ttl=60)
def load_latest_data():
    """Load the most recent JJIF scrape data combining matches and profiles."""
    data = {
        'athletes': [],
        'athletes_by_country': {},
        'country_rankings': [],
        'events': [],
        'all_matches': [],
        '_file': 'combined'
    }

    # Load matches data
    all_matches_file = RESULTS_DIR / "all_matches.json"
    if all_matches_file.exists():
        try:
            with open(all_matches_file, 'r', encoding='utf-8') as f:
                matches_data = json.load(f)
            data['events'] = matches_data.get('events', [])
            data['all_matches'] = matches_data.get('all_matches', [])
            data['total_matches'] = matches_data.get('total_matches', 0)
            data['_file'] = all_matches_file.name
        except Exception:
            pass

    # Load profiles data and convert to athletes format
    all_profiles_file = RESULTS_DIR / "all_profiles.json"
    if all_profiles_file.exists():
        try:
            with open(all_profiles_file, 'r', encoding='utf-8') as f:
                profiles_data = json.load(f)
            profiles = profiles_data.get('profiles', []) if isinstance(profiles_data, dict) else profiles_data

            # Convert profiles to athletes format for overview
            athletes = []
            athletes_by_country = {}
            for p in profiles:
                country = p.get('country_code', 'UNK')
                athletes.append({
                    'name': p.get('name', ''),
                    'country': p.get('country', ''),
                    'country_code': country,
                    'profile_id': p.get('profile_id', ''),
                    'categories': p.get('categories', []),
                    'medal_summary': p.get('medal_summary', {}),
                    'overall_stats': p.get('overall_stats', {})
                })
                athletes_by_country[country] = athletes_by_country.get(country, 0) + 1

            data['athletes'] = athletes
            data['athletes_by_country'] = athletes_by_country
            data['countries_scraped'] = len(athletes_by_country)
            data['timestamp'] = profiles_data.get('scraped_at', '') if isinstance(profiles_data, dict) else ''
        except Exception:
            pass

    # Fallback to legacy jjif_*.json files if no data loaded
    if not data['athletes']:
        json_files = list(RESULTS_DIR.glob("jjif_full_scrape_*.json"))
        if not json_files:
            json_files = list(RESULTS_DIR.glob("jjif_*.json"))

        if json_files:
            latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    legacy_data = json.load(f)
                data.update(legacy_data)
                data['_file'] = latest_file.name
            except Exception:
                pass

    return data if (data['athletes'] or data['events']) else None


def parse_country_rankings(raw_rankings):
    """Fix the country rankings data (handles column misalignment)."""
    fixed = []
    for r in raw_rankings:
        country_text = r.get('continent', '') or r.get('country', '')
        if not country_text:
            continue

        code_match = re.search(r'\(([A-Z]{2,4})\)$', country_text)
        if code_match:
            code = code_match.group(1)
            name = country_text.replace(f'({code})', '').strip()
            fixed.append({
                'rank': r.get('rank'),
                'country': name,
                'country_code': code,
                'flag_url': f"{FLAG_URL_BASE}{code}.png"
            })
    return fixed


@st.cache_data(ttl=300)
def load_athlete_profiles():
    """Load all athlete profiles - tries multiple sources for speed."""
    # 1. Try all_profiles.json first (consolidated file - fastest for cloud)
    all_profiles_file = RESULTS_DIR / "all_profiles.json"
    if all_profiles_file.exists():
        try:
            with open(all_profiles_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            profiles = data.get('profiles', []) if isinstance(data, dict) else data
            if profiles:
                return profiles
        except Exception as e:
            st.error(f"Error loading all_profiles.json: {e}")

    # 2. Try pickle cache (fast for local)
    cache_file = BASE_DIR / "Cache" / "profiles_cache.pkl"
    if cache_file.exists():
        try:
            import pickle
            with open(cache_file, 'rb') as f:
                cache = pickle.load(f)
            return cache.get('profiles', [])
        except Exception:
            pass

    # 3. Fallback to loading individual JSON files from Profiles/
    profiles = []
    if PROFILES_DIR.exists():
        for profile_file in PROFILES_DIR.glob("*.json"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                    # Handle both single profile and list of profiles
                    if isinstance(profile, list):
                        profiles.extend(profile)
                    else:
                        profiles.append(profile)
            except Exception:
                continue

    # 4. Try country-level profile files (athlete_profiles_*.json)
    if not profiles and PROFILES_DIR.exists():
        for profile_file in PROFILES_DIR.glob("athlete_profiles_*.json"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        profiles.extend(data)
                    elif isinstance(data, dict) and 'profiles' in data:
                        profiles.extend(data['profiles'])
            except Exception:
                continue

    return profiles


def fuzzy_name_match(name1, name2, country1=None, country2=None):
    """
    Match athlete names accounting for different name formats.
    Handles: FIRSTNAME SURNAME vs SURNAME FIRSTNAME
    Returns True if names likely match the same person.
    """
    if not name1 or not name2:
        return False

    n1 = name1.upper().strip()
    n2 = name2.upper().strip()

    # Exact match
    if n1 == n2:
        return True

    # If countries don't match, not the same person
    if country1 and country2 and country1 != country2:
        return False

    # Split into name parts
    parts1 = set(n1.replace('-', ' ').replace("'", '').split())
    parts2 = set(n2.replace('-', ' ').replace("'", '').split())

    # Remove common short words that might differ
    skip_words = {'AL', 'EL', 'BIN', 'IBN', 'ABU', 'ABDUL', 'MOHAMMED', 'MOHAMMAD', 'AHMED', 'MUHAMMAD'}

    # Check if at least 2 significant name parts match
    # or all parts of shorter name are in longer name
    common = parts1 & parts2

    # For short names (2 parts), require both to match
    if len(parts1) <= 2 and len(parts2) <= 2:
        return len(common) >= 2

    # For longer names, require at least 2 matches excluding common prefixes
    significant_common = common - skip_words

    if len(significant_common) >= 2:
        return True

    # Check if one name is substring of other (for partial matches)
    if n1 in n2 or n2 in n1:
        return True

    return False


@st.cache_data(ttl=300)
def load_bracket_data():
    """Load parsed bracket/match data."""
    all_matches_file = RESULTS_DIR / "all_matches.json"
    saudi_matches_file = RESULTS_DIR / "saudi_matches.json"

    data = {
        'all_matches': None,
        'saudi_matches': None,
        'events': [],
        'total_matches': 0
    }

    if all_matches_file.exists():
        try:
            with open(all_matches_file, 'r', encoding='utf-8') as f:
                data['all_matches'] = json.load(f)
                data['events'] = data['all_matches'].get('events', [])
                data['total_matches'] = data['all_matches'].get('total_matches', 0)
        except Exception:
            pass

    if saudi_matches_file.exists():
        try:
            with open(saudi_matches_file, 'r', encoding='utf-8') as f:
                data['saudi_matches'] = json.load(f)
        except Exception:
            pass

    return data


def load_enriched_opponents():
    """Load the enriched Asia Top 10 opponent data."""
    # Find most recent enriched file
    enriched_files = sorted(RESULTS_DIR.glob("asia_top10_enriched_*.json"), reverse=True)

    if not enriched_files:
        return None

    try:
        with open(enriched_files[0], 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def get_inferred_opponents(athlete_name, athlete_country, category_name, enriched_data):
    """Get inferred opponents for an athlete from enriched data."""
    if not enriched_data:
        return []

    for cat in enriched_data.get('categories', []):
        if cat.get('category', '').upper() == category_name.upper():
            for ath in cat.get('athletes', []):
                if (ath.get('name', '').upper() == athlete_name.upper() and
                    ath.get('country_code', '') == athlete_country):
                    return ath.get('inferred_opponents', [])

    return []


def get_athlete_match_history(athlete_name, country='KSA'):
    """Get match history for a specific athlete from bracket data.

    Uses fuzzy name matching to handle reversed name formats
    (FIRSTNAME SURNAME vs SURNAME FIRSTNAME).
    """
    bracket_data = load_bracket_data()
    matches = []

    if not bracket_data['all_matches']:
        return matches

    for event in bracket_data.get('events', []):
        event_name = event.get('event_name', '')

        for category in event.get('categories', []):
            cat_name = category.get('category', '')

            for match in category.get('matches', []):
                red = match.get('red_corner') or {}
                blue = match.get('blue_corner') or {}

                red_name = red.get('name', '') or ''
                blue_name = blue.get('name', '') or ''
                red_country = red.get('country', '')
                blue_country = blue.get('country', '')

                # Use fuzzy matching for name comparison
                in_red = fuzzy_name_match(athlete_name, red_name, country, red_country)
                in_blue = fuzzy_name_match(athlete_name, blue_name, country, blue_country)

                if in_red or in_blue:
                    winner = match.get('winner', '')
                    winner_country = match.get('winner_country', '')

                    if in_red:
                        athlete_info = red
                        opponent_info = blue
                        won = fuzzy_name_match(athlete_name, winner, country, winner_country)
                    else:
                        athlete_info = blue
                        opponent_info = red
                        won = fuzzy_name_match(athlete_name, winner, country, winner_country)

                    matches.append({
                        'event': event_name,
                        'category': cat_name,
                        'round': match.get('round', ''),
                        'opponent_name': opponent_info.get('name', 'Unknown') if opponent_info else 'BYE',
                        'opponent_country': opponent_info.get('country', '') if opponent_info else '',
                        'won': won,
                        'athlete_score': athlete_info.get('score', 0) if athlete_info else 0,
                        'opponent_score': opponent_info.get('score', 0) if opponent_info else 0
                    })

    return matches


def get_bracket_matches_by_category(event_name, category_name, country=None):
    """
    Get all matches from a specific event/category.
    Used for matching athletes by competition context when names don't match directly.
    """
    bracket_data = load_bracket_data()
    matches = []

    if not bracket_data['all_matches']:
        return matches

    event_upper = event_name.upper() if event_name else ''

    for event in bracket_data.get('events', []):
        ev_name = event.get('event_name', '').upper()

        # Match event by keyword presence
        if event_upper and not any(word in ev_name for word in event_upper.split()):
            continue

        for category in event.get('categories', []):
            cat_name = category.get('category', '')

            # Match category (weight class)
            if category_name and category_name.upper() not in cat_name.upper():
                continue

            for match in category.get('matches', []):
                red = match.get('red_corner') or {}
                blue = match.get('blue_corner') or {}

                # Filter by country if specified
                if country:
                    if red.get('country') != country and blue.get('country') != country:
                        continue

                matches.append({
                    'event': event.get('event_name', ''),
                    'category': cat_name,
                    'round': match.get('round', ''),
                    'red': red,
                    'blue': blue,
                    'winner': match.get('winner'),
                    'winner_country': match.get('winner_country')
                })

    return matches


def get_athlete_match_history_by_profile(profile):
    """
    Get match history for an athlete using their profile's competition data.
    Matches by event + category + country rather than just name.

    Returns matches with source indicator (bracket=confirmed, inferred=estimated).
    """
    if not profile:
        return []

    bracket_data = load_bracket_data()
    if not bracket_data['all_matches']:
        return []

    country = profile.get('country_code', '')
    athlete_name = profile.get('name', '')
    all_matches = []

    # Get competitions from profile
    for cat_data in profile.get('categories', []):
        category = cat_data.get('category', '')

        for comp in cat_data.get('competitions', []):
            event_name = comp.get('event', '')
            rank = comp.get('rank', 0)
            wins = comp.get('wins', 0)

            # Find matching brackets
            bracket_matches = get_bracket_matches_by_category(event_name, category, country)

            if bracket_matches:
                # Found bracket data for this competition
                for m in bracket_matches:
                    red = m.get('red') or {}
                    blue = m.get('blue') or {}

                    # Check if this athlete is in this match
                    is_red = red.get('country') == country
                    is_blue = blue.get('country') == country

                    if is_red or is_blue:
                        athlete_info = red if is_red else blue
                        opponent_info = blue if is_red else red
                        won = m.get('winner_country') == country

                        all_matches.append({
                            'event': event_name,
                            'category': category,
                            'round': m.get('round', ''),
                            'opponent_name': opponent_info.get('name', 'Unknown') if opponent_info else 'Unknown',
                            'opponent_country': opponent_info.get('country', '') if opponent_info else '',
                            'won': won,
                            'athlete_score': athlete_info.get('score', 0) if athlete_info else 0,
                            'opponent_score': opponent_info.get('score', 0) if opponent_info else 0,
                            'source': 'bracket',  # Confirmed from bracket data
                            'rank_in_event': rank,
                            'wins_in_event': wins
                        })
            else:
                # No bracket data - create inferred record from profile
                all_matches.append({
                    'event': event_name,
                    'category': category,
                    'round': '',
                    'opponent_name': '',  # Unknown
                    'opponent_country': '',
                    'won': None,  # Unknown per-match
                    'athlete_score': 0,
                    'opponent_score': 0,
                    'source': 'profile',  # From profile, no opponent details
                    'rank_in_event': rank,
                    'wins_in_event': wins,
                    'medal': comp.get('medal', '')
                })

    return all_matches


def refresh_data():
    """Run the scraper to refresh rankings and profile data."""
    scraper_path = Path(__file__).parent / "scrape_jjif_full.py"
    profile_scraper = Path(__file__).parent / "scrape_all_opponents.py"

    if scraper_path.exists():
        with st.spinner("🔄 Fetching latest JJIF rankings... This may take 2-3 minutes."):
            try:
                result = subprocess.run(
                    [sys.executable, str(scraper_path)],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=300,
                    cwd=str(Path(__file__).parent)
                )
                if result.returncode == 0:
                    st.success("✅ Rankings data refreshed!")
                else:
                    st.error(f"Error refreshing rankings: {result.stderr[:300]}")
            except subprocess.TimeoutExpired:
                st.error("Rankings scrape timed out.")
            except Exception as e:
                st.error(f"Rankings error: {e}")

    # Also refresh athlete profiles if they exist
    if profile_scraper.exists() and PROFILES_DIR.exists() and any(PROFILES_DIR.glob("*.json")):
        with st.spinner("🔄 Refreshing athlete profiles... This may take a few minutes."):
            try:
                result = subprocess.run(
                    [sys.executable, str(profile_scraper), "--refresh"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=600,
                    cwd=str(Path(__file__).parent)
                )
                if result.returncode == 0:
                    st.success("✅ Profiles refreshed!")
                else:
                    st.warning(f"Profile refresh issue: {result.stderr[:200]}")
            except subprocess.TimeoutExpired:
                st.warning("Profile refresh timed out - some profiles may not be updated.")
            except Exception as e:
                st.warning(f"Profile refresh: {e}")

    st.cache_data.clear()
    st.rerun()


# =============================================================================
# MAIN DASHBOARD
# =============================================================================
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🥋 Team Saudi Jiu Jitsu Analysis</h1>
        <p>JJIF Rankings & Competitor Intelligence</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        # Use local Saudi logo
        logo_path = Path(__file__).parent / "Saudilogo.png"
        if logo_path.exists():
            st.image(str(logo_path), width=120)
        else:
            st.image(f"{FLAG_URL_BASE}KSA.png", width=60)
        st.title("Navigation")

        # Refresh Data Button
        st.markdown("---")
        if st.button("🔄 REFRESH DATA", type="primary", use_container_width=True):
            refresh_data()

        st.markdown("---")

        page = st.radio(
            "Select View",
            ["🏠 Overview", "🇸🇦 Saudi Athletes", "🌏 Asian Top 20", "🌍 World Top 20", "📋 Event Brackets", "👤 Athlete Profiles", "🎯 Opponent Scouting", "⚔️ Head-to-Head", "🌍 Country Rankings", "📊 Statistics"],
            label_visibility="collapsed"
        )

        st.markdown("---")

    # Load data
    data = load_latest_data()

    if data is None:
        st.warning("⚠️ No data found. Click 'REFRESH DATA' to fetch the latest JJIF rankings.")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Fetch Data Now", type="primary", use_container_width=True):
                refresh_data()
        return

    # Parse data
    athletes = data.get('athletes', [])
    athletes_by_country = data.get('athletes_by_country', {})
    raw_rankings = data.get('country_rankings', [])
    country_rankings = parse_country_rankings(raw_rankings)

    df_athletes = pd.DataFrame(athletes)
    df_rankings = pd.DataFrame(country_rankings) if country_rankings else pd.DataFrame()

    saudi_athletes = [a for a in athletes if a.get('country_code') == 'KSA']
    df_saudi = pd.DataFrame(saudi_athletes)

    # Data info in sidebar
    with st.sidebar:
        st.markdown("### 📊 Data Info")
        st.write(f"**File:** {data.get('_file', 'N/A')}")
        timestamp = data.get('timestamp', '')[:16].replace('T', ' ')
        st.write(f"**Updated:** {timestamp}")
        st.write(f"**Total Athletes:** {len(athletes):,}")
        st.markdown(f"**🇸🇦 Saudi Athletes:** `{len(saudi_athletes)}`")

    # Page content
    if page == "🏠 Overview":
        render_overview(data, df_athletes, df_saudi, df_rankings, athletes_by_country)
    elif page == "🇸🇦 Saudi Athletes":
        render_saudi_athletes(df_saudi, athletes)
    elif page == "🌏 Asian Top 20":
        render_asian_top_20_page()
    elif page == "🌍 World Top 20":
        render_world_top_20_page()
    elif page == "📋 Event Brackets":
        render_event_brackets()
    elif page == "👤 Athlete Profiles":
        render_athlete_profiles()
    elif page == "🎯 Opponent Scouting":
        render_opponent_scouting()
    elif page == "⚔️ Head-to-Head":
        render_head_to_head()
    elif page == "🌍 Country Rankings":
        render_country_rankings(df_rankings, athletes_by_country)
    elif page == "📊 Statistics":
        render_statistics(df_athletes, athletes_by_country)

    # Footer
    st.markdown(f"""
    <div class="footer">
        <p><strong>Team Saudi Jiu Jitsu Dashboard</strong></p>
        <p>Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
    </div>
    """, unsafe_allow_html=True)


def render_overview(data, df_athletes, df_saudi, df_rankings, athletes_by_country):
    """Render the overview page."""
    st.markdown('<p class="sub-header">Dashboard Overview</p>', unsafe_allow_html=True)

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">🇸🇦 {len(df_saudi)}</div>
            <div class="metric-label">Saudi Athletes</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">🌍 {data.get('countries_scraped', 0)}</div>
            <div class="metric-label">Countries Tracked</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">👥 {len(df_athletes):,}</div>
            <div class="metric-label">Total Athletes</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        # Find Saudi rank
        saudi_rank = "N/A"
        for r in df_rankings.to_dict('records') if len(df_rankings) > 0 else []:
            if r.get('country_code') == 'KSA':
                saudi_rank = f"#{r.get('rank', 'N/A')}"
                break
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">🏆 {saudi_rank}</div>
            <div class="metric-label">Saudi JJIF Rank</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Two columns
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<p class="sub-header">🇸🇦 Team Saudi Spotlight</p>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="saudi-highlight">
            <h3 style="margin-top: 0; color: #006C35;">Saudi Arabia (KSA)</h3>
            <p style="font-size: 1.2rem;"><strong>{len(df_saudi)}</strong> registered JJIF athletes</p>
            <img src="{FLAG_URL_BASE}KSA.png" style="width: 64px; margin-top: 10px; border-radius: 4px;">
        </div>
        """, unsafe_allow_html=True)

        if len(df_saudi) > 0:
            st.markdown("**Sample Saudi Athletes:**")
            for athlete in df_saudi.head(8).to_dict('records'):
                st.write(f"• {athlete.get('name', 'Unknown')}")

    with col2:
        st.markdown('<p class="sub-header">🌍 Athletes by Country</p>', unsafe_allow_html=True)

        if athletes_by_country:
            df_country_counts = pd.DataFrame([
                {'Country': k, 'Athletes': v}
                for k, v in sorted(athletes_by_country.items(), key=lambda x: -x[1])
            ])

            # Highlight Saudi
            colors = ['#006C35' if c == 'KSA' else '#1f77b4' for c in df_country_counts['Country']]

            fig = px.bar(
                df_country_counts,
                x='Country',
                y='Athletes',
                title='Athletes per Country (Tracked Nations)',
                color='Country',
                color_discrete_map={'KSA': '#006C35'}
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)


def render_saudi_athletes(df_saudi, all_athletes):
    """Render Saudi athletes page with profile cards and detailed analysis."""
    st.markdown('<p class="sub-header">🇸🇦 Saudi Arabia Athletes</p>', unsafe_allow_html=True)

    # Load detailed profiles
    profiles = load_athlete_profiles()
    saudi_profiles = [p for p in profiles if p.get('country_code') == 'KSA' and p.get('categories')]

    if not saudi_profiles:
        st.warning("No Saudi athlete profiles found. Run the scraper to fetch detailed Saudi team data.")
        return

    # Team Summary Stats
    col1, col2, col3, col4 = st.columns(4)

    total_saudi_medals = sum(p.get('medal_summary', {}).get('total', 0) for p in saudi_profiles)
    total_saudi_gold = sum(p.get('medal_summary', {}).get('gold', 0) for p in saudi_profiles)
    total_saudi_silver = sum(p.get('medal_summary', {}).get('silver', 0) for p in saudi_profiles)
    total_saudi_bronze = sum(p.get('medal_summary', {}).get('bronze', 0) for p in saudi_profiles)

    # Calculate average win rate
    win_rates = []
    for p in saudi_profiles:
        wr = p.get('overall_stats', {}).get('win_rate', '0%')
        try:
            win_rates.append(float(wr.replace('%', '')))
        except:
            pass
    avg_win_rate = sum(win_rates) / len(win_rates) if win_rates else 0

    with col1:
        st.metric("Total Athletes", len(saudi_profiles))
    with col2:
        st.metric("Total Medals", total_saudi_medals, f"🥇{total_saudi_gold} 🥈{total_saudi_silver} 🥉{total_saudi_bronze}")
    with col3:
        st.metric("Avg Win Rate", f"{avg_win_rate:.1f}%")
    with col4:
        medalists = len([p for p in saudi_profiles if p.get('medal_summary', {}).get('total', 0) > 0])
        st.metric("Medalists", medalists, f"{medalists/len(saudi_profiles)*100:.0f}% of team" if saudi_profiles else "")

    # Create tabs for Saudi section
    sa_tab1, sa_tab2, sa_tab3 = st.tabs(["📊 Overview", "🔍 Browse Athletes", "⚠️ Attention Needed"])

    # TAB 1: Overview
    with sa_tab1:
        # Saudi Top Performers Table
        st.markdown("#### 🏆 Top Saudi Performers (by Medals)")
        top_saudi = sorted(
            saudi_profiles,
            key=lambda x: (x.get('medal_summary', {}).get('gold', 0),
                           x.get('medal_summary', {}).get('silver', 0),
                           x.get('medal_summary', {}).get('bronze', 0)),
            reverse=True
        )[:10]

        if top_saudi:
            top_data = []
            for p in top_saudi:
                medals = p.get('medal_summary', {})
                stats = p.get('overall_stats', {})

                # Get primary category
                categories = p.get('categories', [])
                primary_cat = categories[0].get('category', 'N/A') if categories else 'N/A'
                primary_cat_short = primary_cat.replace('ADULTS JIU-JITSU ', '').replace('MALE ', 'M ').replace('FEMALE ', 'F ')

                # Get form score
                form_score, form_trend, _ = calculate_form_score(p)

                top_data.append({
                    'Athlete': p.get('name', 'Unknown'),
                    'Category': primary_cat_short,
                    '🥇': medals.get('gold', 0),
                    '🥈': medals.get('silver', 0),
                    '🥉': medals.get('bronze', 0),
                    'Win Rate': stats.get('win_rate', 'N/A'),
                    'Form': f"{form_score:.0f}" if form_score else 'N/A',
                    'Events': stats.get('total_events', 0)
                })

            df_top = pd.DataFrame(top_data)
            st.dataframe(df_top, use_container_width=True, hide_index=True)

        # Saudi Athletes by Weight Class Distribution
        st.markdown("#### 📊 Saudi Team Distribution")
        col1, col2 = st.columns(2)

        with col1:
            # By gender
            male_count = len([p for p in saudi_profiles if extract_gender_from_categories(p) == 'Male'])
            female_count = len([p for p in saudi_profiles if extract_gender_from_categories(p) == 'Female'])

            gender_data = pd.DataFrame({
                'Gender': ['Male', 'Female'],
                'Count': [male_count, female_count]
            })
            fig_gender = px.pie(gender_data, values='Count', names='Gender',
                                title='By Gender', color_discrete_sequence=['#2E86AB', '#E94F37'])
            fig_gender.update_layout(height=300)
            st.plotly_chart(fig_gender, use_container_width=True)

        with col2:
            # By discipline
            discipline_counts = {}
            for p in saudi_profiles:
                for disc in get_disciplines_competed(p):
                    discipline_counts[disc] = discipline_counts.get(disc, 0) + 1

            if discipline_counts:
                disc_data = pd.DataFrame({
                    'Discipline': list(discipline_counts.keys()),
                    'Count': list(discipline_counts.values())
                })
                fig_disc = px.pie(disc_data, values='Count', names='Discipline',
                                  title='By Discipline', color_discrete_sequence=px.colors.qualitative.Set2)
                fig_disc.update_layout(height=300)
                st.plotly_chart(fig_disc, use_container_width=True)

    # TAB 2: Browse Saudi Athletes with Profile Cards
    with sa_tab2:
        # Saudi-specific filters
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            saudi_search = st.text_input("🔎 Search by Name", placeholder="Enter athlete name...", key="sa_search")

        with col2:
            saudi_gender_options = ['All', 'Male', 'Female']
            saudi_gender_filter = st.selectbox("👤 Gender", options=saudi_gender_options, index=0, key="sa_gender")

        with col3:
            saudi_weight_options = ['All Weights', 'Lightweight (-62kg)', 'Middleweight (62-77kg)',
                                    'Light Heavy (77-94kg)', 'Heavyweight (+94kg)']
            saudi_weight_filter = st.selectbox("⚖️ Weight", options=saudi_weight_options, index=0, key="sa_weight")

        with col4:
            saudi_sort_options = ['Medals (Most)', 'Win Rate', 'Form Score', 'Events', 'Name (A-Z)']
            saudi_sort_by = st.selectbox("📊 Sort By", options=saudi_sort_options, index=0, key="sa_sort")

        # Apply filters
        filtered_saudi = saudi_profiles.copy()

        if saudi_search:
            filtered_saudi = [p for p in filtered_saudi if saudi_search.lower() in p.get('name', '').lower()]

        if saudi_gender_filter != 'All':
            filtered_saudi = [p for p in filtered_saudi if extract_gender_from_categories(p) == saudi_gender_filter]

        if saudi_weight_filter != 'All Weights':
            def matches_weight(profile):
                for cat in profile.get('categories', []):
                    cat_name = cat.get('category', '').upper()
                    if saudi_weight_filter == 'Lightweight (-62kg)' and any(w in cat_name for w in ['-56', '-62', '-48', '-52', '-57']):
                        return True
                    elif saudi_weight_filter == 'Middleweight (62-77kg)' and any(w in cat_name for w in ['-69', '-77', '-63', '-70']):
                        return True
                    elif saudi_weight_filter == 'Light Heavy (77-94kg)' and any(w in cat_name for w in ['-85', '-94']):
                        return True
                    elif saudi_weight_filter == 'Heavyweight (+94kg)' and '+94' in cat_name:
                        return True
                return False
            filtered_saudi = [p for p in filtered_saudi if matches_weight(p)]

        # Sort
        if saudi_sort_by == 'Medals (Most)':
            filtered_saudi = sorted(filtered_saudi,
                key=lambda x: (x.get('medal_summary', {}).get('gold', 0),
                               x.get('medal_summary', {}).get('silver', 0),
                               x.get('medal_summary', {}).get('bronze', 0)), reverse=True)
        elif saudi_sort_by == 'Win Rate':
            def get_win_rate(p):
                wr = p.get('overall_stats', {}).get('win_rate', '0%')
                try:
                    return float(wr.replace('%', ''))
                except:
                    return 0
            filtered_saudi = sorted(filtered_saudi, key=get_win_rate, reverse=True)
        elif saudi_sort_by == 'Form Score':
            def get_form(p):
                fs, _, _ = calculate_form_score(p)
                return fs if fs else 0
            filtered_saudi = sorted(filtered_saudi, key=get_form, reverse=True)
        elif saudi_sort_by == 'Events':
            filtered_saudi = sorted(filtered_saudi,
                key=lambda x: x.get('overall_stats', {}).get('total_events', 0), reverse=True)
        elif saudi_sort_by == 'Name (A-Z)':
            filtered_saudi = sorted(filtered_saudi, key=lambda x: x.get('name', ''))

        st.caption(f"Showing **{len(filtered_saudi)}** of {len(saudi_profiles)} Saudi athletes")

        # Display Saudi athletes as profile cards
        if filtered_saudi:
            cards_per_row = 4
            for row_start in range(0, len(filtered_saudi), cards_per_row):
                row_athletes = filtered_saudi[row_start:row_start + cards_per_row]
                cols = st.columns(cards_per_row)

                for idx, athlete in enumerate(row_athletes):
                    with cols[idx]:
                        medals = athlete.get('medal_summary', {})
                        stats = athlete.get('overall_stats', {})
                        gender = extract_gender_from_categories(athlete)

                        # Get primary category
                        categories = athlete.get('categories', [])
                        primary_cat = categories[0].get('category', 'N/A') if categories else 'N/A'
                        primary_cat_short = primary_cat.replace('ADULTS JIU-JITSU ', '').replace('MALE ', 'M ').replace('FEMALE ', 'F ')

                        # Get form score
                        form_score, form_trend, _ = calculate_form_score(athlete)
                        form_display = f"{form_score:.0f}" if form_score else '-'
                        trend_arrow = ''
                        trend_color = '#666'
                        if form_trend == 'improving':
                            trend_arrow = '↑'
                            trend_color = '#28a745'
                        elif form_trend == 'declining':
                            trend_arrow = '↓'
                            trend_color = '#dc3545'

                        # Medal display
                        gold = medals.get('gold', 0)
                        silver = medals.get('silver', 0)
                        bronze = medals.get('bronze', 0)

                        # Card background color
                        card_bg = '#f8f9fa'
                        if gold > 0:
                            card_bg = '#fff9e6'
                        elif silver > 0:
                            card_bg = '#f5f5f5'
                        elif bronze > 0:
                            card_bg = '#fff5ee'

                        # Photo URL
                        photo_url = athlete.get('photo_url', '')
                        photo_html = f'<img src="{photo_url}" style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover; border: 2px solid #006c35;">' if photo_url else '<div style="width: 60px; height: 60px; border-radius: 50%; background: #006c35; display: flex; align-items: center; justify-content: center; color: white; font-size: 24px;">🥋</div>'

                        card_html = f'''
                        <div style="background: {card_bg}; border: 1px solid #ddd; border-radius: 12px; padding: 12px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                {photo_html}
                                <div style="margin-left: 10px; flex: 1;">
                                    <div style="font-weight: bold; font-size: 14px; color: #006c35;">{athlete.get('name', 'Unknown')}</div>
                                    <div style="font-size: 11px; color: #666;">{primary_cat_short}</div>
                                </div>
                            </div>
                            <div style="display: flex; justify-content: space-around; margin: 8px 0; padding: 6px; background: white; border-radius: 8px;">
                                <span title="Gold">🥇 {gold}</span>
                                <span title="Silver">🥈 {silver}</span>
                                <span title="Bronze">🥉 {bronze}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 11px; color: #444;">
                                <div><strong>Win Rate:</strong> {stats.get('win_rate', 'N/A')}</div>
                                <div style="color: {trend_color};"><strong>Form:</strong> {form_display} {trend_arrow}</div>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 10px; color: #888; margin-top: 4px;">
                                <span>{gender} | Age: {athlete.get('age', 'N/A')}</span>
                                <span>{stats.get('total_events', 0)} events</span>
                            </div>
                        </div>
                        '''
                        st.markdown(card_html, unsafe_allow_html=True)

            # Detailed view expander
            st.markdown("---")
            st.markdown("##### 📋 Detailed Athlete View")
            saudi_names_for_view = {p.get('profile_id'): p.get('name', 'Unknown') for p in filtered_saudi}
            selected_saudi_id = st.selectbox(
                "Select athlete for detailed view",
                options=list(saudi_names_for_view.keys()),
                format_func=lambda x: saudi_names_for_view.get(x, x),
                key="sa_quick_view"
            )

            selected_saudi = next((p for p in filtered_saudi if p.get('profile_id') == selected_saudi_id), None)
            if selected_saudi:
                with st.expander(f"📊 {selected_saudi.get('name', 'Unknown')} - Full Profile", expanded=True):
                    detail_col1, detail_col2, detail_col3 = st.columns([1, 2, 1])

                    with detail_col1:
                        photo_url = selected_saudi.get('photo_url')
                        if photo_url:
                            st.image(photo_url, width=150)
                        st.markdown(f"**ID:** {selected_saudi.get('profile_id')}")
                        st.markdown(f"**Age:** {selected_saudi.get('age', 'N/A')}")

                    with detail_col2:
                        st.markdown(f"### {selected_saudi.get('name', 'Unknown')}")
                        stats = selected_saudi.get('overall_stats', {})

                        stat_col1, stat_col2, stat_col3 = st.columns(3)
                        with stat_col1:
                            st.metric("Events", stats.get('total_events', 0))
                        with stat_col2:
                            st.metric("Wins", stats.get('total_wins', 0))
                        with stat_col3:
                            st.metric("Win Rate", stats.get('win_rate', 'N/A'))

                        cats = selected_saudi.get('categories', [])
                        if cats:
                            st.markdown("**Categories:**")
                            for cat in cats[:3]:
                                cat_name = cat.get('category', '').replace('ADULTS JIU-JITSU ', '')
                                rank = cat.get('rank', 'N/A')
                                points = cat.get('points')
                                points_str = f"{points:.0f}" if points else "0"
                                st.markdown(f"- {cat_name} (Rank #{rank}, {points_str} pts)")

                    with detail_col3:
                        medals = selected_saudi.get('medal_summary', {})
                        st.markdown("### Medals")
                        st.markdown(f"""
                        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #006c35 0%, #00a651 100%); border-radius: 12px; color: white;">
                            <div style="font-size: 2rem;">🥇 {medals.get('gold', 0)}</div>
                            <div style="font-size: 1.5rem;">🥈 {medals.get('silver', 0)} | 🥉 {medals.get('bronze', 0)}</div>
                            <div style="margin-top: 8px; font-size: 0.9rem;">Total: {medals.get('total', 0)}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        form_score, form_trend, _ = calculate_form_score(selected_saudi)
                        if form_score:
                            trend_icon = '↑' if form_trend == 'improving' else ('↓' if form_trend == 'declining' else '→')
                            st.metric("Form Score", f"{form_score:.0f}", trend_icon)
        else:
            st.info("No Saudi athletes match the selected filters.")

    # TAB 3: Athletes Needing Attention
    with sa_tab3:
        st.markdown("#### ⚠️ Athletes Needing Attention")
        attention_needed = []
        for p in saudi_profiles:
            form_score, form_trend, _ = calculate_form_score(p)
            if form_score is not None and (form_score < 50 or form_trend == 'declining'):
                attention_needed.append({
                    'Athlete': p.get('name', 'Unknown'),
                    'Form Score': f"{form_score:.0f}",
                    'Trend': form_trend,
                    'Win Rate': p.get('overall_stats', {}).get('win_rate', 'N/A'),
                    'Issue': 'Low form' if form_score < 50 else 'Declining performance'
                })

        if attention_needed:
            df_attention = pd.DataFrame(attention_needed)
            st.dataframe(df_attention, use_container_width=True, hide_index=True)
        else:
            st.success("✅ All Saudi athletes are performing well!")

    # Download button at the bottom
    st.markdown("---")
    if saudi_profiles:
        csv_data = pd.DataFrame([{
            'Name': p.get('name'),
            'Age': p.get('age'),
            'Gold': p.get('medal_summary', {}).get('gold', 0),
            'Silver': p.get('medal_summary', {}).get('silver', 0),
            'Bronze': p.get('medal_summary', {}).get('bronze', 0),
            'Win Rate': p.get('overall_stats', {}).get('win_rate', 'N/A'),
            'Events': p.get('overall_stats', {}).get('total_events', 0)
        } for p in saudi_profiles]).to_csv(index=False)

        st.download_button(
            label="📥 Download Saudi Athletes (CSV)",
            data=csv_data,
            file_name=f"saudi_jjif_athletes_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )


def render_country_rankings(df_rankings, athletes_by_country):
    """Render country rankings page."""
    st.markdown('<p class="sub-header">🌍 JJIF Country Rankings</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Top Countries")

        if len(df_rankings) > 0:
            for row in df_rankings.head(30).to_dict('records'):
                rank = row.get('rank', '?')
                country = row.get('country', 'Unknown')
                code = row.get('country_code', '')
                flag_url = row.get('flag_url', '')
                athlete_count = athletes_by_country.get(code, 0)

                highlight = "saudi-highlight" if code == 'KSA' else "competitor-card"

                st.markdown(f"""
                <div class="{highlight}">
                    <img src="{flag_url}" class="flag-img">
                    <strong>#{rank}</strong> {country} ({code})
                    <span style="float: right; color: #666;">{athlete_count} athletes tracked</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Show athlete counts if rankings not available
            st.markdown("### Athletes by Country")
            for code, count in sorted(athletes_by_country.items(), key=lambda x: -x[1]):
                flag_url = f"{FLAG_URL_BASE}{code}.png"
                highlight = "saudi-highlight" if code == 'KSA' else "competitor-card"
                st.markdown(f"""
                <div class="{highlight}">
                    <img src="{flag_url}" class="flag-img">
                    <strong>{code}</strong>
                    <span style="float: right;">{count} athletes</span>
                </div>
                """, unsafe_allow_html=True)

    with col2:
        st.markdown("### Distribution")

        if athletes_by_country:
            top_10 = dict(sorted(athletes_by_country.items(), key=lambda x: -x[1])[:10])

            fig = px.pie(
                values=list(top_10.values()),
                names=list(top_10.keys()),
                title="Top 10 Countries by Athletes",
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Greens_r
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)


def render_competitor_analysis(df_athletes, df_saudi, country_rankings):
    """Render competitor analysis page."""
    st.markdown('<p class="sub-header">⚔️ Competitor Analysis</p>', unsafe_allow_html=True)

    st.markdown("Analyze athletes from competing nations to identify key competitors for Team Saudi.")

    # Select competitor country
    available_countries = df_athletes['country_code'].unique().tolist()
    competitor_countries = [c for c in available_countries if c != 'KSA']

    col1, col2 = st.columns([1, 2])

    with col1:
        selected_country = st.selectbox(
            "Select Competitor Country",
            options=sorted(competitor_countries),
            format_func=lambda x: f"{x} ({len(df_athletes[df_athletes['country_code'] == x])} athletes)"
        )

    if selected_country:
        competitor_athletes = df_athletes[df_athletes['country_code'] == selected_country]

        with col2:
            st.markdown(f"""
            <div style="background: #f0f0f0; padding: 1rem; border-radius: 8px;">
                <img src="{FLAG_URL_BASE}{selected_country}.png" style="width: 48px; vertical-align: middle;">
                <span style="font-size: 1.5rem; margin-left: 10px;"><strong>{selected_country}</strong></span>
                <br><br>
                <strong>{len(competitor_athletes)}</strong> registered athletes
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Side by side comparison
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"### 🇸🇦 Saudi Arabia ({len(df_saudi)} athletes)")
            if len(df_saudi) > 0:
                st.dataframe(
                    df_saudi[['name', 'profile_id']].head(20).rename(columns={
                        'name': 'Athlete',
                        'profile_id': 'ID'
                    }),
                    use_container_width=True,
                    height=400
                )

        with col2:
            st.markdown(f"### {selected_country} ({len(competitor_athletes)} athletes)")
            if len(competitor_athletes) > 0:
                st.dataframe(
                    competitor_athletes[['name', 'profile_id']].head(20).rename(columns={
                        'name': 'Athlete',
                        'profile_id': 'ID'
                    }),
                    use_container_width=True,
                    height=400
                )

        # Download competitor data
        csv = competitor_athletes.to_csv(index=False)
        st.download_button(
            label=f"📥 Download {selected_country} Athletes (CSV)",
            data=csv,
            file_name=f"{selected_country}_jjif_athletes_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )


def render_athlete_profiles():
    """Render detailed athlete profiles page - ALL athletes with filters."""
    st.markdown('<p class="sub-header">👤 Athlete Profiles Database</p>', unsafe_allow_html=True)

    profiles = load_athlete_profiles()

    if not profiles:
        st.warning("⚠️ No athlete profiles found. Run the profile scraper to fetch athlete data.")
        st.code("python scrape_all_opponents.py --top16", language="bash")
        return

    # Filter to profiles with actual competition data
    profiles_with_data = [p for p in profiles if p.get('categories') and len(p.get('categories', [])) > 0]

    # Get unique countries from profiles
    countries_in_db = sorted(set(p.get('country_code', 'UNK') for p in profiles if p.get('country_code')))
    country_names = {p.get('country_code'): p.get('country', p.get('country_code')) for p in profiles}

    # Summary stats
    total_countries = len(countries_in_db)
    saudi_count = len([p for p in profiles if p.get('country_code') == 'KSA'])

    st.info(f"📊 **{len(profiles)}** athletes from **{total_countries}** countries | **{len(profiles_with_data)}** with competition history | **{saudi_count}** Saudi athletes")

    # FILTERS SECTION
    st.markdown("### 🔍 Filter Athletes")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Country filter
        country_options = ['All Countries'] + [f"{code} - {country_names.get(code, code)}" for code in countries_in_db]
        selected_country = st.selectbox("🌍 Country", options=country_options, index=0)
        selected_country_code = None if selected_country == 'All Countries' else selected_country.split(' - ')[0]

    with col2:
        # Gender filter - default to Male
        gender_options = ['Male', 'Female', 'All']
        selected_gender = st.selectbox("👤 Gender", options=gender_options, index=0)

    with col3:
        # Weight class filter
        weight_options = ['All Weights', 'Lightweight (-62kg)', 'Middleweight (62-77kg)',
                          'Light Heavy (77-94kg)', 'Heavyweight (+94kg)']
        selected_weight = st.selectbox("⚖️ Weight Class", options=weight_options, index=0)

    with col4:
        # Discipline filter
        discipline_options = ['All Disciplines', 'Fighting', 'Ne-Waza', 'Duo', 'Contact']
        selected_discipline = st.selectbox("🥋 Discipline", options=discipline_options, index=0)

    # Second row of filters
    col5, col6, col7, col8 = st.columns(4)

    with col5:
        # Event type filter
        event_type_options = ['All Events', 'World Championship', 'Continental Championship (Asian)',
                              'World Games / Combat Games', 'A Class Tournament']
        selected_event_type = st.selectbox("🏆 Event Type", options=event_type_options, index=0)

    with col6:
        # Minimum events filter
        min_events_options = ['Any', '1+', '3+', '5+', '10+']
        selected_min_events = st.selectbox("📊 Min Events", options=min_events_options, index=0)

    with col7:
        # Medal filter
        medal_options = ['Any', 'Has Medals', 'Has Gold', 'Has Silver', 'Has Bronze']
        selected_medal_filter = st.selectbox("🏅 Medals", options=medal_options, index=0)

    with col8:
        # Sort by
        sort_options = ['Win Rate (High)', 'Total Events', 'Total Medals', 'Name (A-Z)']
        selected_sort = st.selectbox("📈 Sort By", options=sort_options, index=0)

    # Apply filters
    filtered_profiles = profiles_with_data.copy()

    # Country filter
    if selected_country_code:
        filtered_profiles = [p for p in filtered_profiles if p.get('country_code') == selected_country_code]

    # Gender filter
    if selected_gender != 'All':
        filtered_profiles = [p for p in filtered_profiles if extract_gender_from_categories(p) == selected_gender]

    # Weight class filter
    if selected_weight != 'All Weights':
        def matches_weight(profile):
            for cat in profile.get('categories', []):
                cat_name = cat.get('category', '').upper()
                if selected_weight == 'Lightweight (-62kg)' and any(w in cat_name for w in ['-56', '-62', '-48', '-52', '-57']):
                    return True
                elif selected_weight == 'Middleweight (62-77kg)' and any(w in cat_name for w in ['-69', '-77', '-63', '-70']):
                    return True
                elif selected_weight == 'Light Heavy (77-94kg)' and any(w in cat_name for w in ['-85', '-94']):
                    return True
                elif selected_weight == 'Heavyweight (+94kg)' and '+94' in cat_name:
                    return True
            return False
        filtered_profiles = [p for p in filtered_profiles if matches_weight(p)]

    # Discipline filter
    if selected_discipline != 'All Disciplines':
        def matches_discipline(profile):
            disciplines = get_disciplines_competed(profile)
            return selected_discipline in disciplines
        filtered_profiles = [p for p in filtered_profiles if matches_discipline(p)]

    # Event type filter - filter athletes who have competed in selected event type
    if selected_event_type != 'All Events':
        event_type_map = {
            'World Championship': 'WORLD CHAMPIONSHIP',
            'Continental Championship (Asian)': 'CONTINENTAL CHAMPIONSHIP',
            'World Games / Combat Games': 'WORLD GAMES',
            'A Class Tournament': 'A CLASS TOURNAMENT'
        }
        target_type = event_type_map.get(selected_event_type, '')
        def has_competed_in_event_type(profile):
            for cat in profile.get('categories', []):
                for comp in cat.get('competitions', []):
                    if target_type in comp.get('event_type', '').upper():
                        return True
            return False
        filtered_profiles = [p for p in filtered_profiles if has_competed_in_event_type(p)]

    # Minimum events filter
    if selected_min_events != 'Any':
        min_val = int(selected_min_events.replace('+', ''))
        filtered_profiles = [p for p in filtered_profiles
                             if p.get('overall_stats', {}).get('total_events', 0) >= min_val]

    # Medal filter
    if selected_medal_filter != 'Any':
        def matches_medal_filter(profile):
            medals = profile.get('medal_summary', {})
            if selected_medal_filter == 'Has Medals':
                return medals.get('total', 0) > 0
            elif selected_medal_filter == 'Has Gold':
                return medals.get('gold', 0) > 0
            elif selected_medal_filter == 'Has Silver':
                return medals.get('silver', 0) > 0
            elif selected_medal_filter == 'Has Bronze':
                return medals.get('bronze', 0) > 0
            return True
        filtered_profiles = [p for p in filtered_profiles if matches_medal_filter(p)]

    # Sort
    if selected_sort == 'Win Rate (High)':
        filtered_profiles.sort(
            key=lambda p: float(p.get('overall_stats', {}).get('win_rate', '0%').replace('%', '') or 0),
            reverse=True
        )
    elif selected_sort == 'Total Events':
        filtered_profiles.sort(
            key=lambda p: p.get('overall_stats', {}).get('total_events', 0) or 0,
            reverse=True
        )
    elif selected_sort == 'Total Medals':
        filtered_profiles.sort(
            key=lambda p: p.get('medal_summary', {}).get('total', 0),
            reverse=True
        )
    elif selected_sort == 'Name (A-Z)':
        filtered_profiles.sort(key=lambda p: p.get('name', 'ZZZ'))

    st.markdown(f"**{len(filtered_profiles)}** athletes match your filters")

    if selected_gender == 'All':
        st.warning("⚠️ Showing both Male and Female athletes. For accurate analysis, select a specific gender.")

    st.markdown("---")

    # Athlete selector from filtered list
    profile_names = {p.get('profile_id'): f"{p.get('name', 'Unknown')} ({p.get('country_code', 'UNK')}) - {p.get('profile_id')}"
                     for p in filtered_profiles if p.get('name') and p.get('name') != 'Unknown'}

    if not profile_names:
        st.warning("No athletes match the selected filters. Try adjusting your filter criteria.")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        selected_id = st.selectbox(
            "Select Athlete to View",
            options=list(profile_names.keys()),
            format_func=lambda x: profile_names.get(x, x)
        )

    # Get selected profile
    selected_profile = next((p for p in profiles if p.get('profile_id') == selected_id), None)

    if selected_profile:
        # Profile header
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            # Photo
            photo_url = selected_profile.get('photo_url')
            if photo_url:
                st.image(photo_url, width=150)
            else:
                st.image(f"{FLAG_URL_BASE}KSA.png", width=100)

        with col2:
            st.markdown(f"""
            ### {selected_profile.get('name', 'Unknown')}
            <img src="{FLAG_URL_BASE}{selected_profile.get('country_code', 'KSA')}.png" style="width: 32px; vertical-align: middle;">
            **{selected_profile.get('country', 'Saudi Arabia')}**

            **Age:** {selected_profile.get('age', 'N/A')} | **ID:** {selected_profile.get('profile_id')}
            """, unsafe_allow_html=True)

        with col3:
            # Medal summary
            medals = selected_profile.get('medal_summary', {})
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: #f9f9f9; border-radius: 10px;">
                <span style="font-size: 2rem;">🥇</span> <strong>{medals.get('gold', 0)}</strong><br>
                <span style="font-size: 2rem;">🥈</span> <strong>{medals.get('silver', 0)}</strong><br>
                <span style="font-size: 2rem;">🥉</span> <strong>{medals.get('bronze', 0)}</strong>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Overall stats
        stats = selected_profile.get('overall_stats', {})
        if stats:
            st.markdown("### 📊 Career Statistics")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Events", stats.get('total_events', 'N/A'))
            with col2:
                st.metric("Total Wins", stats.get('total_wins', 'N/A'))
            with col3:
                st.metric("Total Losses", stats.get('total_losses', 'N/A'))
            with col4:
                st.metric("Win Rate", stats.get('win_rate', 'N/A'))

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Points Scored / Against", stats.get('points_scored_against', 'N/A'))
            with col2:
                st.metric("Avg Scores per Bout", stats.get('avg_scores_per_bout', 'N/A'))

        # Categories
        categories = selected_profile.get('categories', [])
        if categories:
            st.markdown("---")
            st.markdown("### 🏆 Competition Categories")

            for cat in categories:
                with st.expander(f"**{cat.get('category', 'Unknown')}** - Rank #{cat.get('rank', 'N/A')} ({cat.get('points', 0):.0f} pts)" if cat.get('rank') else f"**{cat.get('category', 'Unknown')}**"):
                    competitions = cat.get('competitions', [])

                    if competitions:
                        # Create dataframe
                        df_comp = pd.DataFrame(competitions)

                        # Add medal emoji column
                        def medal_emoji(m):
                            if m == 'gold': return '🥇'
                            elif m == 'silver': return '🥈'
                            elif m == 'bronze': return '🥉'
                            return ''

                        df_comp['Medal'] = df_comp['medal'].apply(medal_emoji)

                        # Select and rename columns
                        display_cols = ['date', 'event', 'event_type', 'rank', 'Medal', 'wins', 'points']
                        df_display = df_comp[display_cols].rename(columns={
                            'date': 'Date',
                            'event': 'Event',
                            'event_type': 'Type',
                            'rank': 'Rank',
                            'wins': 'Wins',
                            'points': 'Points'
                        })

                        st.dataframe(df_display, use_container_width=True, hide_index=True)

                        # Quick stats
                        medals_in_cat = len([c for c in competitions if c.get('medal')])
                        total_wins = sum(c.get('wins', 0) for c in competitions)
                        total_points = sum(c.get('points', 0) for c in competitions)

                        st.caption(f"📈 **{len(competitions)}** competitions | **{medals_in_cat}** medals | **{total_wins}** total wins | **{total_points:.0f}** total points")

        # Performance timeline chart
        all_competitions = []
        for cat in categories:
            for comp in cat.get('competitions', []):
                comp_copy = comp.copy()
                comp_copy['category_name'] = cat.get('category', 'Unknown')
                all_competitions.append(comp_copy)

        if all_competitions:
            st.markdown("---")
            st.markdown("### 📈 Performance Timeline")

            df_timeline = pd.DataFrame(all_competitions)
            df_timeline['date'] = pd.to_datetime(df_timeline['date'])
            df_timeline = df_timeline.sort_values('date')

            fig = px.scatter(
                df_timeline,
                x='date',
                y='rank',
                color='event_type',
                size='points',
                hover_data=['event', 'wins', 'medal'],
                title='Competition Results Over Time',
                labels={'date': 'Date', 'rank': 'Placement', 'event_type': 'Event Type'}
            )
            fig.update_yaxes(autorange='reversed')  # Lower rank is better
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)


# Key competitor countries for Jiu Jitsu
COMPETITOR_COUNTRIES = {
    'UAE': 'United Arab Emirates',
    'KAZ': 'Kazakhstan',
    'THA': 'Thailand',
    'ITA': 'Italy',
    'GRE': 'Greece',
    'FRA': 'France',
    'GER': 'Germany',
    'JPN': 'Japan',
    'KOR': 'South Korea',
    'IRI': 'Iran',
    'BRA': 'Brazil',
    'USA': 'United States',
    'RUS': 'Russia',
    'UZB': 'Uzbekistan',
    'JOR': 'Jordan',
}


def scrape_opponent_profile(country_code, profile_id):
    """Look up opponent profile from cached data."""
    profile_file = PROFILES_DIR / f"{profile_id}.json"

    # Check if already in cache
    if profile_file.exists():
        with open(profile_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    # Profile not available
    return None


def extract_gender_from_categories(profile):
    """Extract gender from athlete's competition categories."""
    categories = profile.get('categories', [])
    for cat in categories:
        cat_name = cat.get('category', '').upper()
        if 'FEMALE' in cat_name:
            return 'Female'
        elif 'MALE' in cat_name:
            return 'Male'
    return 'Unknown'


def extract_weight_classes(profile):
    """Extract unique weight classes from athlete's categories."""
    weights = set()
    categories = profile.get('categories', [])
    for cat in categories:
        cat_name = cat.get('category', '')
        # Extract weight like "-62 KG", "+94 KG", "-85 KG"
        weight_match = re.search(r'([+-]?\d+\s*KG)', cat_name, re.IGNORECASE)
        if weight_match:
            weights.add(weight_match.group(1).upper())
    return list(weights)


def get_all_weight_classes(profiles):
    """Get all unique weight classes from profiles."""
    all_weights = set()
    for p in profiles:
        weights = extract_weight_classes(p)
        all_weights.update(weights)
    # Sort weights numerically
    def weight_sort_key(w):
        num = re.search(r'(\d+)', w)
        return int(num.group(1)) if num else 0
    return sorted(all_weights, key=weight_sort_key)


# =============================================================================
# JIU JITSU EXPERT ANALYSIS FUNCTIONS
# =============================================================================

def extract_discipline(category_name):
    """Extract Jiu Jitsu discipline from category name.

    JJIF disciplines:
    - Fighting (traditional gi competition)
    - Ne-Waza (ground fighting only)
    - Duo (choreographed pairs)
    - Contact Ju-Jitsu (full contact striking + grappling)
    """
    cat_upper = category_name.upper()
    if 'NE-WAZA' in cat_upper or 'NEWAZA' in cat_upper or 'NE WAZA' in cat_upper:
        return 'Ne-Waza'
    elif 'DUO' in cat_upper or 'SHOW' in cat_upper:
        return 'Duo'
    elif 'CONTACT' in cat_upper:
        return 'Contact'
    else:
        return 'Fighting'


def extract_age_category(category_name):
    """Extract age category from category name.

    JJIF age categories:
    - U16 (Under 16)
    - U18 (Under 18) / Cadets
    - U21 (Under 21) / Juniors
    - Adults / Seniors
    - Masters (30+)
    """
    cat_upper = category_name.upper()
    if 'U16' in cat_upper or 'UNDER 16' in cat_upper or 'U-16' in cat_upper:
        return 'U16'
    elif 'U18' in cat_upper or 'UNDER 18' in cat_upper or 'U-18' in cat_upper or 'CADET' in cat_upper:
        return 'U18'
    elif 'U21' in cat_upper or 'UNDER 21' in cat_upper or 'U-21' in cat_upper or 'JUNIOR' in cat_upper:
        return 'U21'
    elif 'MASTER' in cat_upper or 'VETERAN' in cat_upper:
        return 'Masters'
    elif 'ADULT' in cat_upper or 'SENIOR' in cat_upper:
        return 'Adults'
    else:
        return 'Adults'  # Default


def extract_event_tier(event_type):
    """Extract event tier from event type string.

    JJIF event tiers (in order of prestige):
    1. World Championship - highest prestige
    2. World Games / Combat Games - multi-sport prestige
    3. Continental Championship - regional championship
    4. A Class Tournament - Grand Prix level
    5. B Class Tournament - regional events
    6. National Championship - country level
    """
    if not event_type:
        return 'Unknown', 5

    event_upper = event_type.upper()

    if 'WORLD CHAMPIONSHIP' in event_upper:
        return 'World Championship', 1
    elif 'WORLD GAMES' in event_upper or 'COMBAT GAMES' in event_upper:
        return 'World Games', 2
    elif 'CONTINENTAL' in event_upper or 'ASIAN' in event_upper or 'EUROPEAN' in event_upper or 'AFRICAN' in event_upper or 'PAN-AMERICAN' in event_upper:
        return 'Continental Championship', 3
    elif 'A CLASS' in event_upper or 'GRAND PRIX' in event_upper:
        return 'A Class Tournament', 4
    elif 'B CLASS' in event_upper:
        return 'B Class Tournament', 5
    elif 'NATIONAL' in event_upper:
        return 'National Championship', 6
    else:
        return event_type, 5


def calculate_form_score(profile, months=12):
    """Calculate recent form score based on last N months of competition.

    Form score considers:
    - Medal finishes (weighted by event tier)
    - Win rate in recent competitions
    - Consistency of competition activity

    Returns: score 0-100, trend ('improving', 'stable', 'declining'), recent_results
    """
    from datetime import datetime, timedelta

    cutoff_date = datetime.now() - timedelta(days=months * 30)

    all_competitions = []
    for cat in profile.get('categories', []):
        for comp in cat.get('competitions', []):
            try:
                comp_date = datetime.strptime(comp.get('date', ''), '%Y-%m-%d')
                comp_copy = comp.copy()
                comp_copy['parsed_date'] = comp_date
                comp_copy['category'] = cat.get('category', '')
                all_competitions.append(comp_copy)
            except:
                continue

    # Filter to recent
    recent = [c for c in all_competitions if c.get('parsed_date', datetime.min) >= cutoff_date]
    recent = sorted(recent, key=lambda x: x.get('parsed_date', datetime.min), reverse=True)

    if not recent:
        return 0, 'inactive', []

    # Calculate form score
    total_score = 0
    for comp in recent:
        _, tier_weight = extract_event_tier(comp.get('event_type', ''))
        tier_multiplier = (7 - tier_weight) / 6  # Higher tier = higher multiplier

        rank = comp.get('rank', 99)
        medal = comp.get('medal')

        # Base score from placement
        if medal == 'gold':
            base_score = 100
        elif medal == 'silver':
            base_score = 80
        elif medal == 'bronze':
            base_score = 60
        elif rank and rank <= 5:
            base_score = 40
        elif rank and rank <= 8:
            base_score = 25
        else:
            base_score = 10

        # Add wins bonus
        wins = comp.get('wins', 0)
        base_score += wins * 5

        total_score += base_score * tier_multiplier

    # Normalize score (0-100)
    avg_score = min(100, total_score / len(recent))

    # Calculate trend (compare first half to second half)
    if len(recent) >= 4:
        mid = len(recent) // 2
        recent_half = sum(1 for c in recent[:mid] if c.get('medal'))
        older_half = sum(1 for c in recent[mid:] if c.get('medal'))

        if recent_half > older_half:
            trend = 'improving'
        elif recent_half < older_half:
            trend = 'declining'
        else:
            trend = 'stable'
    else:
        trend = 'stable'

    return round(avg_score, 1), trend, recent[:5]  # Return top 5 recent


def analyze_competition_frequency(profile):
    """Analyze how often athlete competes.

    Returns: competitions per year, consistency rating, gaps analysis
    """
    from datetime import datetime
    from collections import defaultdict

    all_dates = []
    for cat in profile.get('categories', []):
        for comp in cat.get('competitions', []):
            try:
                comp_date = datetime.strptime(comp.get('date', ''), '%Y-%m-%d')
                all_dates.append(comp_date)
            except:
                continue

    if not all_dates:
        return 0, 'Unknown', []

    all_dates = sorted(all_dates)

    # Group by year
    by_year = defaultdict(int)
    for d in all_dates:
        by_year[d.year] += 1

    # Calculate average per year
    if len(by_year) > 0:
        avg_per_year = sum(by_year.values()) / len(by_year)
    else:
        avg_per_year = 0

    # Consistency rating
    if avg_per_year >= 4:
        consistency = 'Very Active'
    elif avg_per_year >= 2:
        consistency = 'Active'
    elif avg_per_year >= 1:
        consistency = 'Moderate'
    else:
        consistency = 'Low Activity'

    # Find longest gap
    gaps = []
    for i in range(1, len(all_dates)):
        gap_days = (all_dates[i] - all_dates[i-1]).days
        if gap_days > 180:  # More than 6 months
            gaps.append({
                'from': all_dates[i-1].strftime('%Y-%m'),
                'to': all_dates[i].strftime('%Y-%m'),
                'days': gap_days
            })

    return round(avg_per_year, 1), consistency, gaps


def find_peak_performance(profile):
    """Identify athlete's peak performance period.

    Returns: peak year, peak stats, career trajectory
    """
    from collections import defaultdict
    from datetime import datetime

    yearly_stats = defaultdict(lambda: {'medals': 0, 'gold': 0, 'wins': 0, 'events': 0, 'points': 0})

    for cat in profile.get('categories', []):
        for comp in cat.get('competitions', []):
            try:
                year = comp.get('date', '')[:4]
                if not year.isdigit():
                    continue
                year = int(year)

                yearly_stats[year]['events'] += 1
                yearly_stats[year]['wins'] += comp.get('wins', 0)
                yearly_stats[year]['points'] += comp.get('points', 0)

                medal = comp.get('medal')
                if medal:
                    yearly_stats[year]['medals'] += 1
                    if medal == 'gold':
                        yearly_stats[year]['gold'] += 1
            except:
                continue

    if not yearly_stats:
        return None, {}, 'unknown'

    # Find peak year by weighted score
    def year_score(y):
        s = yearly_stats[y]
        return s['gold'] * 10 + s['medals'] * 5 + s['wins'] + s['points'] / 100

    peak_year = max(yearly_stats.keys(), key=year_score)

    # Determine career trajectory
    years_sorted = sorted(yearly_stats.keys())
    if len(years_sorted) >= 3:
        recent_years = years_sorted[-2:]
        early_years = years_sorted[:2]

        recent_score = sum(year_score(y) for y in recent_years) / len(recent_years)
        early_score = sum(year_score(y) for y in early_years) / len(early_years)

        if recent_score > early_score * 1.2:
            trajectory = 'improving'
        elif recent_score < early_score * 0.8:
            trajectory = 'declining'
        else:
            trajectory = 'consistent'
    else:
        trajectory = 'early_career'

    return peak_year, dict(yearly_stats[peak_year]), trajectory


def get_disciplines_competed(profile):
    """Get all disciplines athlete has competed in."""
    disciplines = set()
    for cat in profile.get('categories', []):
        discipline = extract_discipline(cat.get('category', ''))
        disciplines.add(discipline)
    return list(disciplines)


def get_age_categories_competed(profile):
    """Get all age categories athlete has competed in."""
    age_cats = set()
    for cat in profile.get('categories', []):
        age_cat = extract_age_category(cat.get('category', ''))
        age_cats.add(age_cat)
    return list(age_cats)


def generate_tactical_report(saudi_athlete, opponent):
    """Generate comprehensive tactical analysis for head-to-head matchup.

    As a Jiu Jitsu expert, this analyzes:
    - Experience differential
    - Style matchup (disciplines competed)
    - Recent form comparison
    - Event tier performance
    - Scoring patterns
    - Strategic recommendations
    """
    report = {
        'advantages': [],
        'warnings': [],
        'strategy': [],
        'key_stats': {}
    }

    # Get stats
    saudi_stats = saudi_athlete.get('overall_stats', {})
    opp_stats = opponent.get('overall_stats', {})

    saudi_medals = saudi_athlete.get('medal_summary', {})
    opp_medals = opponent.get('medal_summary', {})

    # Parse win rates
    try:
        saudi_wr = float(saudi_stats.get('win_rate', '0%').replace('%', ''))
    except:
        saudi_wr = 0
    try:
        opp_wr = float(opp_stats.get('win_rate', '0%').replace('%', ''))
    except:
        opp_wr = 0

    # Experience analysis
    saudi_events = saudi_stats.get('total_events', 0) or 0
    opp_events = opp_stats.get('total_events', 0) or 0

    report['key_stats']['experience_diff'] = saudi_events - opp_events

    if saudi_events > opp_events + 5:
        report['advantages'].append(f"Experience advantage: {saudi_events} events vs {opp_events}")
    elif opp_events > saudi_events + 5:
        report['warnings'].append(f"Experience gap: Opponent has {opp_events - saudi_events} more events")

    # Win rate analysis
    report['key_stats']['win_rate_diff'] = saudi_wr - opp_wr

    if saudi_wr > opp_wr + 15:
        report['advantages'].append(f"Superior win rate: {saudi_wr:.0f}% vs {opp_wr:.0f}%")
    elif opp_wr > saudi_wr + 15:
        report['warnings'].append(f"Opponent win rate: {opp_wr:.0f}% vs your {saudi_wr:.0f}%")

    # Medal analysis
    saudi_total_medals = saudi_medals.get('gold', 0) + saudi_medals.get('silver', 0) + saudi_medals.get('bronze', 0)
    opp_total_medals = opp_medals.get('gold', 0) + opp_medals.get('silver', 0) + opp_medals.get('bronze', 0)

    if saudi_medals.get('gold', 0) > opp_medals.get('gold', 0):
        report['advantages'].append(f"More gold medals: {saudi_medals.get('gold', 0)} vs {opp_medals.get('gold', 0)}")
    elif opp_medals.get('gold', 0) > saudi_medals.get('gold', 0) + 2:
        report['warnings'].append(f"Opponent has {opp_medals.get('gold', 0)} golds - proven winner")

    # Form analysis
    saudi_form, saudi_trend, _ = calculate_form_score(saudi_athlete)
    opp_form, opp_trend, _ = calculate_form_score(opponent)

    report['key_stats']['form_diff'] = saudi_form - opp_form

    if saudi_trend == 'improving':
        report['advantages'].append("Current form is improving")
    if opp_trend == 'declining':
        report['advantages'].append("Opponent form is declining")
    if saudi_trend == 'declining':
        report['warnings'].append("Recent form has been declining")
    if opp_trend == 'improving':
        report['warnings'].append("Opponent is on an upward trend")

    # Scoring pattern analysis
    try:
        saudi_pts_str = saudi_stats.get('points_scored_against', '0/0')
        opp_pts_str = opp_stats.get('points_scored_against', '0/0')

        if '/' in str(saudi_pts_str):
            s_scored, s_against = [int(x.strip()) for x in str(saudi_pts_str).replace(' ', '').split('/')]
            if s_against > 0:
                saudi_ratio = s_scored / s_against
                report['key_stats']['saudi_scoring_ratio'] = round(saudi_ratio, 2)

                if saudi_ratio >= 5:
                    report['advantages'].append(f"Dominant scoring: {saudi_ratio:.1f}x more points scored than conceded")
                elif saudi_ratio >= 3:
                    report['advantages'].append(f"Strong scoring efficiency: {saudi_ratio:.1f}:1 ratio")

        if '/' in str(opp_pts_str):
            o_scored, o_against = [int(x.strip()) for x in str(opp_pts_str).replace(' ', '').split('/')]
            if o_against > 0:
                opp_ratio = o_scored / o_against
                report['key_stats']['opp_scoring_ratio'] = round(opp_ratio, 2)

                if opp_ratio >= 5:
                    report['warnings'].append(f"Opponent scores heavily: {opp_ratio:.1f}x ratio")
                    report['strategy'].append("Focus on defense - opponent is a heavy scorer")
    except:
        pass

    # Strategic recommendations
    if saudi_wr > opp_wr:
        report['strategy'].append("Stick to your game plan - statistics favor you")
    else:
        report['strategy'].append("Consider tactical adjustments - opponent has edge statistically")

    if saudi_events < 5:
        report['strategy'].append("Gain experience - compete more frequently at lower-tier events")

    if opp_medals.get('gold', 0) > 3:
        report['strategy'].append("Study opponent's winning patterns - they know how to close matches")

    # Discipline-specific insight
    saudi_disciplines = get_disciplines_competed(saudi_athlete)
    opp_disciplines = get_disciplines_competed(opponent)

    if 'Ne-Waza' in opp_disciplines and 'Ne-Waza' not in saudi_disciplines:
        report['warnings'].append("Opponent has Ne-Waza experience - may be strong on ground")
        report['strategy'].append("Prepare ground defense techniques")

    return report


def render_opponent_scouting():
    """Render opponent scouting page - view and analyze pre-scraped opponents."""
    st.markdown('<p class="sub-header">🎯 Opponent Scouting</p>', unsafe_allow_html=True)

    # Load all profiles (pre-scraped data)
    all_profiles = load_athlete_profiles()

    # Separate Saudi and opponent profiles
    saudi_profiles = [p for p in all_profiles if p.get('country_code') == 'KSA']
    opponent_profiles = [p for p in all_profiles if p.get('country_code') != 'KSA']

    # Get unique countries with opponents
    countries_with_data = {}
    for p in opponent_profiles:
        cc = p.get('country_code', 'UNK')
        if cc not in countries_with_data:
            countries_with_data[cc] = []
        countries_with_data[cc].append(p)

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🇸🇦 Saudi Profiles", len(saudi_profiles))
    with col2:
        st.metric("🎯 Opponent Profiles", len(opponent_profiles))
    with col3:
        st.metric("🌍 Countries Scouted", len(countries_with_data))

    # Check if opponent data exists
    if not opponent_profiles:
        st.warning("""
        ⚠️ **No opponent data found.** Run the batch scraper to populate opponent profiles:
        ```bash
        python scrape_all_opponents.py --quick
        ```
        Or for full scrape of all competitor countries:
        ```bash
        python scrape_all_opponents.py
        ```
        """)
        return

    st.markdown("---")

    # Filters section
    st.markdown("### 🔍 Filter Opponents")

    # Get all available weight classes
    all_weights = get_all_weight_classes(opponent_profiles)

    # Filter row 1: Country, Gender, Weight, Discipline
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Country filter
        country_options = ['ALL'] + sorted(countries_with_data.keys())
        selected_country = st.selectbox(
            "🌍 Country",
            options=country_options,
            format_func=lambda x: f"All Countries ({len(opponent_profiles)})" if x == 'ALL'
                        else f"{x} - {COMPETITOR_COUNTRIES.get(x, x)} ({len(countries_with_data.get(x, []))})"
        )

    with col2:
        # Gender filter - default to Male (most common for Saudi team)
        gender_options = ['Male', 'Female', 'All']
        selected_gender = st.selectbox("👤 Gender", options=gender_options, index=0)

    with col3:
        # Weight class filter
        weight_options = ['All'] + all_weights
        selected_weight = st.selectbox("⚖️ Weight Class", options=weight_options)

    with col4:
        # Discipline filter (Jiu Jitsu specific)
        discipline_options = ['All', 'Fighting', 'Ne-Waza', 'Duo', 'Contact']
        selected_discipline = st.selectbox("🥋 Discipline", options=discipline_options)

    # Show country flag if selected
    if selected_country != 'ALL':
        st.markdown(f"""
        <div style="text-align: center; margin: 0.5rem 0;">
            <img src="{FLAG_URL_BASE}{selected_country}.png" style="width: 48px;">
        </div>
        """, unsafe_allow_html=True)

    # Warning if viewing all genders
    if selected_gender == 'All':
        st.warning("⚠️ Showing both Male and Female athletes. For competition scouting, select a specific gender.")

    # Apply filters
    filtered_opponents = opponent_profiles.copy()

    # Country filter
    if selected_country != 'ALL':
        filtered_opponents = [p for p in filtered_opponents if p.get('country_code') == selected_country]

    # Gender filter
    if selected_gender != 'All':
        filtered_opponents = [p for p in filtered_opponents if extract_gender_from_categories(p) == selected_gender]

    # Weight class filter
    if selected_weight != 'All':
        filtered_opponents = [p for p in filtered_opponents if selected_weight in extract_weight_classes(p)]

    # Discipline filter
    if selected_discipline != 'All':
        filtered_opponents = [p for p in filtered_opponents if selected_discipline in get_disciplines_competed(p)]

    st.markdown("---")

    # Sort options
    sort_option = st.radio(
        "Sort by",
        ["Total Medals", "Win Rate", "Gold Medals", "Events", "Form Score"],
        horizontal=True
    )

    # Sort function
    def sort_key(p):
        medals = p.get('medal_summary', {})
        stats = p.get('overall_stats', {})
        if sort_option == "Total Medals":
            return medals.get('gold', 0) * 3 + medals.get('silver', 0) * 2 + medals.get('bronze', 0)
        elif sort_option == "Win Rate":
            try:
                return float(stats.get('win_rate', '0%').replace('%', ''))
            except:
                return 0
        elif sort_option == "Gold Medals":
            return medals.get('gold', 0)
        elif sort_option == "Form Score":
            form, _, _ = calculate_form_score(p)
            return form
        else:
            return stats.get('total_events', 0) or 0

    filtered_opponents = sorted(filtered_opponents, key=sort_key, reverse=True)

    # Display opponents
    st.markdown(f"### 👥 {len(filtered_opponents)} Athletes")

    # Create a table view with enhanced analytics
    if filtered_opponents:
        opponent_data = []
        for opp in filtered_opponents[:50]:  # Limit to 50 for performance
            medals = opp.get('medal_summary', {})
            stats = opp.get('overall_stats', {})
            gender = extract_gender_from_categories(opp)
            weights = extract_weight_classes(opp)
            disciplines = get_disciplines_competed(opp)
            form_score, form_trend, _ = calculate_form_score(opp)

            # Form indicator
            if form_trend == 'improving':
                trend_icon = '📈'
            elif form_trend == 'declining':
                trend_icon = '📉'
            elif form_trend == 'inactive':
                trend_icon = '💤'
            else:
                trend_icon = '➡️'

            opponent_data.append({
                'Athlete': opp.get('name', 'Unknown'),
                'Country': opp.get('country_code', '?'),
                'Gender': gender,
                'Weight': ', '.join(weights) if weights else '-',
                'Age': opp.get('age', '-'),
                'Discipline': ', '.join(disciplines) if disciplines else 'Fighting',
                '🥇': medals.get('gold', 0),
                '🥈': medals.get('silver', 0),
                '🥉': medals.get('bronze', 0),
                'Win Rate': stats.get('win_rate', 'N/A'),
                'Form': f"{form_score} {trend_icon}",
                'Events': stats.get('total_events', 0),
            })

        df_opponents = pd.DataFrame(opponent_data)
        st.dataframe(df_opponents, use_container_width=True, hide_index=True)

        if len(filtered_opponents) > 50:
            st.caption(f"Showing top 50 of {len(filtered_opponents)} athletes")

    st.markdown("---")

    # Detailed opponent view
    st.markdown("### 📋 Detailed Opponent Profile")

    opp_selector = {p.get('profile_id'): f"{p.get('name', 'Unknown')} ({p.get('country_code')})"
                    for p in filtered_opponents if p.get('name')}

    if opp_selector:
        selected_opp_id = st.selectbox(
            "Select opponent for detailed view",
            options=list(opp_selector.keys()),
            format_func=lambda x: opp_selector.get(x, x)
        )

        selected_opp = next((p for p in filtered_opponents if p.get('profile_id') == selected_opp_id), None)

        if selected_opp:
            col1, col2 = st.columns([1, 2])

            with col1:
                photo_url = selected_opp.get('photo_url')
                if photo_url:
                    st.image(photo_url, width=150)
                else:
                    st.image(f"{FLAG_URL_BASE}{selected_opp.get('country_code', 'UNK')}.png", width=100)

                medals = selected_opp.get('medal_summary', {})
                st.markdown(f"""
                **Medals:**
                - 🥇 Gold: {medals.get('gold', 0)}
                - 🥈 Silver: {medals.get('silver', 0)}
                - 🥉 Bronze: {medals.get('bronze', 0)}
                """)

            with col2:
                st.markdown(f"### {selected_opp.get('name', 'Unknown')}")
                st.markdown(f"**Country:** {selected_opp.get('country', '')} ({selected_opp.get('country_code')})")
                st.markdown(f"**Age:** {selected_opp.get('age', 'N/A')}")

                stats = selected_opp.get('overall_stats', {})
                st.markdown(f"""
                **Career Stats:**
                - Events: {stats.get('total_events', 'N/A')}
                - Wins: {stats.get('total_wins', 'N/A')}
                - Losses: {stats.get('total_losses', 'N/A')}
                - Win Rate: {stats.get('win_rate', 'N/A')}
                """)

            # Competition history
            categories = selected_opp.get('categories', [])
            if categories:
                st.markdown("#### Competition Categories")
                for cat in categories:
                    rank_text = f"#{cat.get('rank')}" if cat.get('rank') else "N/R"
                    pts_text = f"{cat.get('points', 0):.0f} pts" if cat.get('points') else ""
                    with st.expander(f"**{cat.get('category', 'Unknown')}** - {rank_text} {pts_text}"):
                        comps = cat.get('competitions', [])
                        if comps:
                            for comp in comps[:5]:
                                medal_icon = {'gold': '🥇', 'silver': '🥈', 'bronze': '🥉'}.get(comp.get('medal'), '')
                                st.write(f"- {comp.get('date')}: **#{comp.get('rank')}** {medal_icon} at {comp.get('event', 'Unknown')}")

    st.markdown("---")

    # Weight Category Analysis
    st.markdown("### ⚖️ Weight Category Threats")
    st.markdown("Top opponents in each weight category based on medals and ranking.")

    # Get Saudi categories
    saudi_categories = set()
    for p in saudi_profiles:
        for cat in p.get('categories', []):
            if cat.get('category'):
                saudi_categories.add(cat.get('category'))

    # Build opponent lookup by category
    opponent_by_category = {}
    for p in opponent_profiles:
        for cat in p.get('categories', []):
            cat_name = cat.get('category')
            if cat_name and cat_name in saudi_categories:
                if cat_name not in opponent_by_category:
                    opponent_by_category[cat_name] = []
                opponent_by_category[cat_name].append({
                    'name': p.get('name'),
                    'country': p.get('country_code'),
                    'rank': cat.get('rank'),
                    'points': cat.get('points'),
                    'medals': p.get('medal_summary', {}),
                    'win_rate': p.get('overall_stats', {}).get('win_rate', 'N/A')
                })

    # Display threats by category
    if opponent_by_category:
        for cat_name in sorted(opponent_by_category.keys()):
            opponents = opponent_by_category[cat_name]
            # Sort by rank
            opponents_sorted = sorted(opponents, key=lambda x: x.get('rank') or 999)[:5]

            with st.expander(f"**{cat_name.replace('ADULTS JIU-JITSU ', '')}** - {len(opponents)} opponents"):
                for i, opp in enumerate(opponents_sorted, 1):
                    m = opp.get('medals', {})
                    st.write(f"{i}. **{opp['name']}** ({opp['country']}) - Rank #{opp.get('rank', 'N/A')} | "
                             f"🥇{m.get('gold', 0)} 🥈{m.get('silver', 0)} 🥉{m.get('bronze', 0)} | Win: {opp.get('win_rate', 'N/A')}")
    else:
        st.info("No overlapping weight categories found with scouted opponents.")

    # Top Global Threats
    st.markdown("---")
    st.markdown("### ⚠️ Top Global Threats")

    top_threats = sorted(
        opponent_profiles,
        key=lambda x: (
            x.get('medal_summary', {}).get('gold', 0) * 3 +
            x.get('medal_summary', {}).get('silver', 0) * 2 +
            x.get('medal_summary', {}).get('bronze', 0)
        ),
        reverse=True
    )[:10]

    if top_threats:
        threat_data = []
        for t in top_threats:
            medals = t.get('medal_summary', {})
            stats = t.get('overall_stats', {})
            threat_data.append({
                'Rank': threat_data.__len__() + 1,
                'Athlete': t.get('name', 'Unknown'),
                'Country': t.get('country_code', '?'),
                '🥇': medals.get('gold', 0),
                '🥈': medals.get('silver', 0),
                '🥉': medals.get('bronze', 0),
                'Win Rate': stats.get('win_rate', 'N/A')
            })

        st.dataframe(pd.DataFrame(threat_data), use_container_width=True, hide_index=True)


def render_top_athletes_tab(bracket_data, region="Asian"):
    """Render Top 20 Athletes tab for Asian or World."""
    from loss_chain_analyzer import LossChainAnalyzer, ASIAN_COUNTRIES

    st.markdown(f"### {region} Top 20 Athletes by Category")
    st.markdown(f"Shows top 20 {region.lower()} athletes per weight category with their **losses** - study who beat them!")

    # Initialize analyzer and load matches
    analyzer = LossChainAnalyzer()
    matches_file = RESULTS_DIR / "all_matches.json"

    if not matches_file.exists():
        st.warning("No match data available. Run the bracket parser first.")
        st.code("python parse_bracket_html.py --all", language="bash")
        return

    count = analyzer.load_matches(matches_file)

    if count == 0:
        st.warning("No matches found in data.")
        return

    # Load athlete profiles for photos
    profiles = load_athlete_profiles()
    profile_lookup = {}
    for p in profiles:
        # Create lookup by name (normalized) and country
        name = p.get('name', '').upper().strip()
        country = p.get('country_code', '').upper()
        if name:
            profile_lookup[f"{name}_{country}"] = p
            # Also try without country for looser matching
            if name not in profile_lookup:
                profile_lookup[name] = p
            # Also store reversed name (LAST FIRST -> FIRST LAST) for match data compatibility
            parts = name.split()
            if len(parts) >= 2:
                # Try "LAST FIRST" format (match data uses this)
                reversed_name = ' '.join(parts[1:]) + ' ' + parts[0]
                profile_lookup[f"{reversed_name}_{country}"] = p
                if reversed_name not in profile_lookup:
                    profile_lookup[reversed_name] = p
                # Also try just last name for looser matching
                profile_lookup[f"{parts[-1]}_{country}"] = p

    # Generate report based on region
    if region == "Asian":
        report = analyzer.generate_asian_scouting_report(top_n=20)
    else:
        report = analyzer.generate_world_scouting_report(top_n=20)

    # Display stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Matches", f"{len(analyzer.matches):,}")
    with col2:
        st.metric("Athletes", f"{len(analyzer.athlete_records):,}")
    with col3:
        st.metric("Categories", len(report['categories']))

    st.markdown("---")

    # Category filter
    categories = [cat['category'] for cat in report['categories']]
    selected_cat = st.selectbox(
        "Filter by Category",
        ["All Categories"] + sorted(categories),
        key=f"{region}_cat_filter"
    )

    # CSS for athlete cards
    st.markdown("""
    <style>
    .athlete-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #006C35;
    }
    .athlete-rank {
        font-size: 24px;
        font-weight: bold;
        color: #006C35;
        float: left;
        margin-right: 15px;
    }
    .athlete-name {
        font-size: 16px;
        font-weight: bold;
        color: #212529;
    }
    .athlete-country {
        font-size: 14px;
        color: #6c757d;
    }
    .athlete-record {
        font-size: 14px;
        color: #495057;
        margin-top: 5px;
    }
    .loss-item {
        background: #f8f9fa;
        border-radius: 6px;
        padding: 8px 12px;
        margin: 5px 0;
        border-left: 3px solid #dc3545;
    }
    .loss-to {
        font-weight: 500;
        color: #212529;
    }
    .loss-details {
        font-size: 12px;
        color: #6c757d;
    }
    </style>
    """, unsafe_allow_html=True)

    # Display categories
    for cat_report in report['categories']:
        cat_name = cat_report['category']

        if selected_cat != "All Categories" and cat_name != selected_cat:
            continue

        with st.expander(f"**{cat_name}** ({len(cat_report['athletes'])} athletes)", expanded=(selected_cat != "All Categories")):
            for i, athlete in enumerate(cat_report['athletes'], 1):
                # Try to find profile photo
                athlete_name = athlete['name'].upper().strip()
                athlete_country = athlete['country'].upper().strip()

                # Look up profile
                profile = profile_lookup.get(f"{athlete_name}_{athlete_country}") or profile_lookup.get(athlete_name)
                photo_url = profile.get('photo_url', '') if profile else ''
                flag_url = f"{FLAG_URL_BASE}{athlete_country}.png"

                # Check if Saudi
                is_saudi = athlete_country in ['KSA', 'SAU']
                card_border = "#006C35" if is_saudi else "#dee2e6"
                card_bg = "#f0fff4" if is_saudi else "white"

                # Build photo HTML
                if photo_url:
                    photo_html = f'<img src="{photo_url}" style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover; border: 2px solid {card_border};" onerror="this.style.display=\'none\'">'
                else:
                    photo_html = f'<div style="width: 60px; height: 60px; border-radius: 50%; background: #e9ecef; display: flex; align-items: center; justify-content: center; font-size: 24px; border: 2px solid {card_border};">👤</div>'

                # Win rate visual
                win_pct = int(athlete['win_rate'].replace('%', '')) if '%' in athlete['win_rate'] else 0
                if win_pct >= 70:
                    color = "#28a745"
                elif win_pct >= 50:
                    color = "#ffc107"
                else:
                    color = "#dc3545"

                # Athlete card with photo
                st.markdown(f"""
                <div style="background: {card_bg}; border: 2px solid {card_border}; border-radius: 10px; padding: 15px; margin: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <div style="display: flex; gap: 15px; align-items: center;">
                        <div style="flex-shrink: 0;">
                            {photo_html}
                        </div>
                        <div style="flex-grow: 1;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                <div>
                                    <span style="font-size: 24px; font-weight: bold; color: #006C35;">#{i}</span>
                                    <span style="font-size: 16px; font-weight: bold; margin-left: 10px;">{'🇸🇦 ' if is_saudi else ''}{athlete['name']}</span>
                                    <img src="{flag_url}" style="width: 20px; height: 14px; margin-left: 8px; vertical-align: middle;" onerror="this.style.display='none'">
                                    <span style="color: #6c757d; margin-left: 5px;">({athlete['country']})</span>
                                </div>
                                <div style="text-align: center; min-width: 80px;">
                                    <div style="font-size: 24px; font-weight: bold; color: {color};">{athlete['win_rate']}</div>
                                    <div style="font-size: 11px; color: #666;">Win Rate</div>
                                </div>
                            </div>
                            <div style="margin-top: 8px; color: #495057;">
                                Record: <strong>{athlete['wins']}W - {athlete['losses']}L</strong> | {athlete['total_matches']} matches
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Show losses
                losses = athlete.get('loss_details', [])
                if losses:
                    st.markdown("**Losses (Study these winners!):**")
                    for loss in losses[:5]:  # Show top 5 losses
                        event_short = (loss.get('event', '')[:35] + '...') if loss.get('event') and len(loss.get('event', '')) > 35 else loss.get('event', '')
                        st.markdown(f"""
                        <div class="loss-item">
                            <span class="loss-to">Lost to: {loss.get('lost_to', 'Unknown')} ({loss.get('winner_country', '')})</span>
                            <div class="loss-details">
                                Score: {loss.get('score', 'N/A')} | {loss.get('round', '')}
                                {f'<br>{event_short}' if event_short else ''}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    if len(losses) > 5:
                        st.caption(f"... and {len(losses) - 5} more losses")
                else:
                    st.success("No losses recorded - undefeated!")

                st.markdown("---")


def render_asian_top_20_page():
    """Render Asian Top 20 as standalone page."""
    st.markdown("## 🌏 Asian Top 20 Athletes")
    st.markdown("Top 20 Asian athletes per weight category with their **losses** - study who beat them!")

    # Load bracket data for the tab function
    matches_file = RESULTS_DIR / "all_matches.json"
    if matches_file.exists():
        with open(matches_file, 'r', encoding='utf-8') as f:
            bracket_data = json.load(f)
        render_top_athletes_tab(bracket_data, region="Asian")
    else:
        st.warning("No match data available. Run the bracket parser first.")
        st.code("python parse_bracket_html.py --all", language="bash")


def render_world_top_20_page():
    """Render World Top 20 as standalone page."""
    st.markdown("## 🌍 World Top 20 Athletes")
    st.markdown("Top 20 World athletes per weight category with their **losses** - study who beat them!")

    # Load bracket data for the tab function
    matches_file = RESULTS_DIR / "all_matches.json"
    if matches_file.exists():
        with open(matches_file, 'r', encoding='utf-8') as f:
            bracket_data = json.load(f)
        render_top_athletes_tab(bracket_data, region="World")
    else:
        st.warning("No match data available. Run the bracket parser first.")
        st.code("python parse_bracket_html.py --all", language="bash")


def render_visual_bracket(bracket_data):
    """Render visual tournament bracket with rounds and matches."""
    st.markdown("### Visual Tournament Bracket")
    st.markdown("View full bracket progression with rounds and match results")

    # Use the bracket_data passed in (from all_matches.json) which has full match data
    events = bracket_data.get('events', [])

    if not events:
        st.info("No bracket data available.")
        return

    # Build event selector
    event_names = sorted([e.get('event_name', f"Event {e.get('verid')}") for e in events])
    selected_event_name = st.selectbox("Select Event", event_names, key="visual_bracket_event")

    # Find selected event
    selected_event = None
    for e in events:
        if e.get('event_name') == selected_event_name:
            selected_event = e
            break

    if not selected_event:
        return

    categories = selected_event.get('categories', [])
    if not categories:
        st.info("No categories found for this event.")
        return

    # Category selector
    cat_names = sorted([c.get('category', f"Category {c.get('catid')}") for c in categories])
    selected_cat_name = st.selectbox("Select Category", cat_names, key="visual_bracket_cat")

    # Find selected category
    selected_cat = None
    for cat in categories:
        if cat.get('category') == selected_cat_name:
            selected_cat = cat
            break

    if not selected_cat:
        return

    # Display bracket info
    rounds = selected_cat.get('rounds', [])
    matches = selected_cat.get('matches', [])
    athletes = selected_cat.get('athletes', [])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rounds", len(rounds))
    with col2:
        st.metric("Matches", len(matches))
    with col3:
        st.metric("Athletes", len(athletes))

    if not matches:
        # Fallback to competitor list if no match data
        competitors = selected_cat.get('competitors', [])
        if competitors:
            st.markdown(f"**{len(competitors)} Competitors:**")
            for i, comp in enumerate(competitors, 1):
                name = comp.get('name', 'Unknown')
                country = comp.get('country', '')
                st.markdown(f"{i}. {name} ({country})")
        else:
            st.info("No match data available for this category.")
        return

    # Group matches by round
    matches_by_round = {}
    for match in matches:
        round_name = match.get('round', 'Unknown Round')
        if round_name not in matches_by_round:
            matches_by_round[round_name] = []
        matches_by_round[round_name].append(match)

    # Display each round
    for round_name in rounds:
        round_matches = matches_by_round.get(round_name, [])
        if not round_matches:
            continue

        st.markdown(f"#### {round_name}")

        for match in round_matches:
            red = match.get('red_corner') or {}
            blue = match.get('blue_corner') or {}
            winner = match.get('winner', '')

            red_name = red.get('name', 'BYE') or 'BYE'
            red_country = red.get('country', '') or ''
            red_score = red.get('score')

            blue_name = blue.get('name', 'BYE') or 'BYE'
            blue_country = blue.get('country', '') or ''
            blue_score = blue.get('score')

            # Determine winner styling
            red_win = winner and winner == red_name
            blue_win = winner and winner == blue_name

            # Format scores
            red_score_str = f"[{red_score}]" if red_score is not None else ""
            blue_score_str = f"[{blue_score}]" if blue_score is not None else ""

            # Create match display with winner highlight
            red_style = "**" if red_win else ""
            blue_style = "**" if blue_win else ""

            winner_icon = " 🏆" if red_win else ""
            st.markdown(f"{red_style}🔴 {red_name} ({red_country}) {red_score_str}{winner_icon}{red_style}")

            winner_icon = " 🏆" if blue_win else ""
            st.markdown(f"{blue_style}🔵 {blue_name} ({blue_country}) {blue_score_str}{winner_icon}{blue_style}")

            st.markdown("---")

    return  # Skip legacy HTML-based code below

    # Legacy HTML-based code (kept for reference but unreachable)
    BRACKETS_DIR = BASE_DIR / "Brackets"
    if not BRACKETS_DIR.exists():
        return

    bracket_files = list(BRACKETS_DIR.glob("bracket_*.html"))
    if not bracket_files:
        return

    # Build a list of available brackets with event/category info
    brackets_info = []
    for bf in bracket_files:
        # Parse filename: bracket_verid_catid.html
        parts = bf.stem.split('_')
        if len(parts) >= 3:
            verid = parts[1]
            catid = parts[2]

            # Find event name from bracket_data
            event_name = f"Event {verid}"
            cat_name = f"Category {catid}"
            for event in bracket_data.get('events', []):
                if event.get('verid') == verid:
                    event_name = event.get('event_name', event_name)
                    for cat in event.get('categories', []):
                        if cat.get('catid') == catid:
                            cat_name = cat.get('category', cat_name)
                            break
                    break

            brackets_info.append({
                'file': bf,
                'verid': verid,
                'catid': catid,
                'event_name': event_name,
                'cat_name': cat_name,
                'display': f"{event_name} - {cat_name}"
            })

    if not brackets_info:
        st.info("No valid bracket files found.")
        return

    # Group by event
    events_dict = {}
    for bi in brackets_info:
        event_key = bi['event_name']
        if event_key not in events_dict:
            events_dict[event_key] = []
        events_dict[event_key].append(bi)

    # Event selector
    event_names = sorted(events_dict.keys())
    selected_event = st.selectbox("Select Event", event_names, key="visual_bracket_event")

    if selected_event:
        categories = events_dict[selected_event]
        categories_sorted = sorted(categories, key=lambda x: x['cat_name'])

        # Category selector
        cat_options = [(c['cat_name'], c) for c in categories_sorted]
        selected_cat_name = st.selectbox(
            "Select Category",
            [c[0] for c in cat_options],
            key="visual_bracket_cat"
        )

        # Find selected bracket
        selected_bracket = None
        for cat_name, cat_info in cat_options:
            if cat_name == selected_cat_name:
                selected_bracket = cat_info
                break

        if selected_bracket:
            # Find matches for this category from parsed data
            cat_matches = []
            cat_rounds = []
            for event in bracket_data.get('events', []):
                if event.get('verid') == selected_bracket['verid']:
                    for cat in event.get('categories', []):
                        if cat.get('catid') == selected_bracket['catid']:
                            cat_matches = cat.get('matches', [])
                            cat_rounds = cat.get('rounds', [])
                            break
                    break

            if cat_matches:
                # CSS for tournament bracket with progression lines
                st.markdown("""
                <style>
                /* Tournament Bracket Container */
                .bracket-container {
                    display: flex;
                    flex-direction: row;
                    overflow-x: auto;
                    padding: 20px 0;
                    gap: 0;
                }
                .bracket-round {
                    display: flex;
                    flex-direction: column;
                    justify-content: space-around;
                    min-width: 220px;
                    position: relative;
                }
                .bracket-round-title {
                    text-align: center;
                    font-weight: bold;
                    color: #006c35;
                    padding: 8px;
                    background: linear-gradient(90deg, #e8f5e9 0%, #fff 100%);
                    border-radius: 4px;
                    margin-bottom: 15px;
                    font-size: 12px;
                    text-transform: uppercase;
                }
                /* Match Box */
                .bracket-match {
                    background: white;
                    border: 2px solid #dee2e6;
                    border-radius: 6px;
                    margin: 8px 5px;
                    position: relative;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.08);
                }
                .bracket-match.has-winner {
                    border-color: #28a745;
                }
                .bracket-match.saudi-match {
                    border-color: #006c35;
                    border-width: 3px;
                }
                /* Athlete in bracket */
                .bracket-athlete {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 6px 10px;
                    font-size: 11px;
                    border-bottom: 1px solid #eee;
                    min-height: 32px;
                }
                .bracket-athlete:last-child {
                    border-bottom: none;
                }
                .bracket-athlete.red {
                    border-left: 3px solid #dc3545;
                }
                .bracket-athlete.blue {
                    border-left: 3px solid #0d6efd;
                }
                .bracket-athlete.winner {
                    background: linear-gradient(90deg, #d4edda 0%, #fff 100%);
                    font-weight: bold;
                }
                .bracket-athlete.saudi {
                    background: linear-gradient(90deg, rgba(0,108,53,0.2) 0%, rgba(255,255,255,0.8) 100%);
                }
                .bracket-athlete.winner.saudi {
                    background: linear-gradient(90deg, #006c35 0%, #28a745 100%);
                    color: white;
                }
                .bracket-name {
                    flex: 1;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    max-width: 140px;
                }
                .bracket-country {
                    color: #6c757d;
                    font-size: 9px;
                    margin-left: 4px;
                }
                .bracket-score {
                    font-weight: bold;
                    min-width: 24px;
                    text-align: center;
                    padding: 2px 6px;
                    border-radius: 3px;
                    background: #f8f9fa;
                    font-size: 12px;
                }
                .bracket-athlete.winner .bracket-score {
                    background: #28a745;
                    color: white;
                }
                /* Connection lines */
                .bracket-connector {
                    position: relative;
                    width: 20px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-around;
                }
                .connector-line {
                    position: absolute;
                    border: 2px solid #ccc;
                    border-left: none;
                }
                /* Winner indicator */
                .winner-arrow {
                    color: #28a745;
                    font-size: 14px;
                    margin-left: 5px;
                }
                /* Final result */
                .final-result {
                    background: linear-gradient(135deg, #ffd700 0%, #ffed4a 100%);
                    border: 3px solid #ffc107;
                    text-align: center;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 10px;
                }
                .final-result .champion {
                    font-size: 16px;
                    font-weight: bold;
                    color: #212529;
                }
                .final-result .medal {
                    font-size: 24px;
                }
                </style>
                """, unsafe_allow_html=True)

                # Group matches by round - infer round names from bracket position if Unknown
                rounds_dict = {}
                unknown_count = 0
                for i, match in enumerate(cat_matches):
                    round_name = match.get('round', 'Unknown')
                    # Handle Unknown Round by inferring from bracket structure
                    if round_name in ['Unknown', 'Unknown Round', '']:
                        unknown_count += 1
                        # Infer round name based on position in bracket
                        total = len(cat_matches)
                        if total <= 1:
                            round_name = "Final"
                        elif total == 2:
                            round_name = "Semi-Final" if i < 1 else "Final"
                        elif total <= 4:
                            if i < 2:
                                round_name = "Semi-Final"
                            elif i < 3:
                                round_name = "Bronze Match"
                            else:
                                round_name = "Final"
                        elif total <= 8:
                            if i < 4:
                                round_name = "Quarter-Final"
                            elif i < 6:
                                round_name = "Semi-Final"
                            elif i < 7:
                                round_name = "Bronze Match"
                            else:
                                round_name = "Final"
                        else:
                            # Larger brackets - estimate based on position
                            if i < total // 2:
                                round_name = "Round 1"
                            elif i < total * 3 // 4:
                                round_name = "Quarter-Final"
                            elif i < total - 2:
                                round_name = "Semi-Final"
                            elif i < total - 1:
                                round_name = "Bronze Match"
                            else:
                                round_name = "Final"
                    if round_name not in rounds_dict:
                        rounds_dict[round_name] = []
                    rounds_dict[round_name].append(match)

                # Display info
                st.info(f"**{len(cat_matches)} matches** across **{len(rounds_dict)} rounds**")

                # Define round order (progression from early rounds to final)
                round_order = [
                    "Round 1", "Round 2", "Round of 16", "Round of 8",
                    "Quarter-Final", "Quarter-Finals", "Quarterfinal",
                    "Semi-Final", "Semi-Finals", "Semifinal",
                    "Bronze Match", "3rd Place", "Bronze",
                    "Final", "Gold Medal Match"
                ]

                # Sort rounds by tournament progression
                def get_round_order(rname):
                    rname_lower = rname.lower()
                    for i, r in enumerate(round_order):
                        if r.lower() in rname_lower or rname_lower in r.lower():
                            return i
                    # Pool/Main Tree rounds - extract number if present
                    if 'pool' in rname_lower or 'round' in rname_lower:
                        import re
                        nums = re.findall(r'\d+', rname)
                        if nums:
                            return int(nums[-1])  # Use last number as order
                    return 50  # Unknown rounds at end

                sorted_rounds = sorted(rounds_dict.keys(), key=get_round_order)

                # Build horizontal bracket view
                st.markdown('<div class="bracket-container">', unsafe_allow_html=True)

                # Create columns for each round (horizontal progression)
                num_rounds = len(sorted_rounds)
                if num_rounds > 0:
                    cols = st.columns(num_rounds)

                    for col_idx, round_name in enumerate(sorted_rounds):
                        with cols[col_idx]:
                            round_matches = rounds_dict[round_name]

                            # Round header
                            st.markdown(f'<div class="bracket-round-title">{round_name}</div>', unsafe_allow_html=True)

                            # Each match in this round
                            for match in round_matches:
                                red = match.get('red_corner') or {}
                                blue = match.get('blue_corner') or {}
                                winner = match.get('winner', '')
                                winner_country = match.get('winner_country', '')

                                # Match container classes
                                match_classes = ["bracket-match"]
                                if winner:
                                    match_classes.append("has-winner")
                                if red.get('country') in ['KSA', 'SAU'] or blue.get('country') in ['KSA', 'SAU']:
                                    match_classes.append("saudi-match")

                                # Red corner classes
                                red_classes = ["bracket-athlete", "red"]
                                if winner and winner == red.get('name'):
                                    red_classes.append("winner")
                                if red.get('country') in ['KSA', 'SAU', 'Saudi Arabia']:
                                    red_classes.append("saudi")

                                # Blue corner classes
                                blue_classes = ["bracket-athlete", "blue"]
                                if winner and winner == blue.get('name'):
                                    blue_classes.append("winner")
                                if blue.get('country') in ['KSA', 'SAU', 'Saudi Arabia']:
                                    blue_classes.append("saudi")

                                red_name = red.get('name', 'BYE') or 'BYE'
                                blue_name = blue.get('name', 'BYE') or 'BYE'
                                red_score = red.get('score', '-') if red.get('score') is not None else '-'
                                blue_score = blue.get('score', '-') if blue.get('score') is not None else '-'

                                # Winner arrow indicator
                                red_arrow = ' ➜' if winner and winner == red.get('name') else ''
                                blue_arrow = ' ➜' if winner and winner == blue.get('name') else ''

                                st.markdown(f"""
                                <div class="{' '.join(match_classes)}">
                                    <div class="{' '.join(red_classes)}">
                                        <span class="bracket-name">{red_name}<span class="bracket-country">{red.get('country', '')}</span></span>
                                        <span class="bracket-score">{red_score}</span>
                                        <span class="winner-arrow">{red_arrow}</span>
                                    </div>
                                    <div class="{' '.join(blue_classes)}">
                                        <span class="bracket-name">{blue_name}<span class="bracket-country">{blue.get('country', '')}</span></span>
                                        <span class="bracket-score">{blue_score}</span>
                                        <span class="winner-arrow">{blue_arrow}</span>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                            # Show final winner at end of bracket
                            if 'final' in round_name.lower() and round_matches:
                                final_match = round_matches[-1]
                                champion = final_match.get('winner', '')
                                champion_country = final_match.get('winner_country', '')
                                if champion:
                                    is_saudi = champion_country in ['KSA', 'SAU']
                                    medal_color = '#006c35' if is_saudi else '#ffc107'
                                    st.markdown(f"""
                                    <div class="final-result" style="border-color: {medal_color};">
                                        <div class="medal">🥇</div>
                                        <div class="champion">{champion}</div>
                                        <div style="color: #666; font-size: 12px;">{champion_country}</div>
                                    </div>
                                    """, unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

            else:
                # No parsed match data - offer to parse from HTML
                st.warning("No parsed match data for this bracket. Run the parser to extract match data.")
                st.code("python parse_bracket_html.py --all", language="bash")

                # Option to view raw HTML
                if st.checkbox("View raw HTML", key="view_raw_html"):
                    try:
                        with open(selected_bracket['file'], 'r', encoding='utf-8') as f:
                            html_content = f.read()
                        st.components.v1.html(
                            f'<div style="background: white; padding: 20px;">{html_content}</div>',
                            height=600,
                            scrolling=True
                        )
                    except Exception as e:
                        st.error(f"Error loading HTML: {e}")


def render_event_brackets():
    """Render Event Brackets page showing match results from scraped bracket data."""
    st.markdown('<p class="sub-header">Event Brackets & Match Results</p>', unsafe_allow_html=True)

    # Load bracket data
    bracket_data = load_bracket_data()

    if not bracket_data['all_matches']:
        st.warning("No bracket data available. Run the bracket scraper to collect match data.")
        st.info("""
        **To scrape bracket data:**
        1. Run `python scrape_all_events_overnight.py`
        2. Solve CAPTCHAs when prompted
        3. Then run `python parse_matches.py` to extract match details
        """)
        return

    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Events", len(bracket_data['events']))
    with col2:
        st.metric("Total Matches", f"{bracket_data['total_matches']:,}")
    with col3:
        total_categories = sum(len(e.get('categories', [])) for e in bracket_data['events'])
        st.metric("Categories", total_categories)
    with col4:
        saudi_data = bracket_data.get('saudi_matches', {})
        saudi_count = saudi_data.get('total_matches', 0) if saudi_data else 0
        st.metric("Saudi Matches", saudi_count)

    st.markdown("---")

    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Visual Bracket", "Events & Categories", "Saudi Matches", "Search Athlete", "Event Mappings"
    ])

    with tab1:
        render_visual_bracket(bracket_data)

    with tab2:
        st.markdown("### Browse Events")

        # Event selector
        events = bracket_data['events']
        event_names = [f"{e.get('event_name', 'Unknown')} ({e.get('verid', '')})" for e in events]

        if not event_names:
            st.info("No events found in bracket data.")
            return

        selected_event_idx = st.selectbox("Select Event", range(len(event_names)),
                                          format_func=lambda x: event_names[x])

        if selected_event_idx is not None:
            event = events[selected_event_idx]
            categories = event.get('categories', [])

            st.markdown(f"**{event.get('event_name', 'Unknown')}**")
            st.caption(f"Categories: {len(categories)} | Matches: {sum(len(c.get('matches', [])) for c in categories)}")

            if categories:
                # Category filter
                cat_names = [c.get('category', 'Unknown') for c in categories]
                selected_cat = st.selectbox("Filter by Category", ["All Categories"] + cat_names)

                if selected_cat == "All Categories":
                    filtered_cats = categories
                else:
                    filtered_cats = [c for c in categories if c.get('category') == selected_cat]

                # Display matches
                for cat in filtered_cats:
                    with st.expander(f"{cat.get('category', 'Unknown')} ({len(cat.get('matches', []))} matches)"):
                        matches = cat.get('matches', [])

                        for match in matches:
                            red = match.get('red_corner') or {}
                            blue = match.get('blue_corner') or {}
                            winner = match.get('winner', '')
                            round_name = match.get('round', 'Unknown')

                            # Determine winner styling
                            red_style = "font-weight: bold; color: #006C35;" if winner == red.get('name') else ""
                            blue_style = "font-weight: bold; color: #006C35;" if winner == blue.get('name') else ""

                            # Highlight Saudi athletes
                            red_flag = " 🇸🇦" if red.get('country') == 'KSA' else ""
                            blue_flag = " 🇸🇦" if blue.get('country') == 'KSA' else ""

                            st.markdown(f"""
                            <div style="padding: 8px; margin: 4px 0; background: #f8f9fa; border-radius: 4px; border-left: 3px solid {'#006C35' if winner else '#ddd'};">
                                <small style="color: #666;">{round_name}</small><br>
                                <span style="{red_style}">🔴 {red.get('name', 'BYE')} ({red.get('country', '')}){red_flag}</span>
                                <span style="color: #999; margin: 0 8px;">vs</span>
                                <span style="{blue_style}">🔵 {blue.get('name', 'BYE')} ({blue.get('country', '')}){blue_flag}</span>
                                <span style="margin-left: 15px; color: #666;">
                                    Score: {red.get('score', '-')} - {blue.get('score', '-')}
                                </span>
                            </div>
                            """, unsafe_allow_html=True)

    with tab3:
        st.markdown("### Saudi Athlete Matches")

        saudi_data = bracket_data.get('saudi_matches', {})
        if not saudi_data:
            st.info("No Saudi matches found in bracket data.")
        else:
            athletes = saudi_data.get('athletes', {})

            if not athletes:
                st.info("No Saudi athletes found in match data.")
            else:
                # Summary table
                st.markdown("#### Saudi Athletes Performance")
                athlete_stats = []
                for name, data in athletes.items():
                    athlete_stats.append({
                        'Athlete': name,
                        'Wins': data.get('wins', 0),
                        'Losses': data.get('losses', 0),
                        'Total': len(data.get('matches', [])),
                        'Win Rate': f"{data.get('wins', 0) / max(len(data.get('matches', [])), 1) * 100:.0f}%"
                    })

                if athlete_stats:
                    df_saudi = pd.DataFrame(athlete_stats)
                    df_saudi = df_saudi.sort_values('Wins', ascending=False)
                    st.dataframe(df_saudi, use_container_width=True, hide_index=True)

                # Individual athlete matches
                st.markdown("#### Match Details")
                selected_athlete = st.selectbox("Select Saudi Athlete", list(athletes.keys()))

                if selected_athlete:
                    athlete_data = athletes.get(selected_athlete, {})
                    matches = athlete_data.get('matches', [])

                    st.markdown(f"**{selected_athlete}** - {athlete_data.get('wins', 0)}W / {athlete_data.get('losses', 0)}L")

                    for match in matches:
                        red = match.get('red') or {}
                        blue = match.get('blue') or {}
                        winner = match.get('winner', '')
                        winner_country = match.get('winner_country', '')

                        # Determine if Saudi won
                        saudi_won = winner_country == 'KSA'
                        result_color = "#006C35" if saudi_won else "#dc3545"
                        result_text = "WIN" if saudi_won else "LOSS" if winner else "DRAW"

                        # Determine opponent
                        if red.get('country') == 'KSA':
                            opponent = blue
                        else:
                            opponent = red

                        st.markdown(f"""
                        <div style="padding: 12px; margin: 8px 0; background: white; border-radius: 8px;
                                    border-left: 4px solid {result_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong>{match.get('event', 'Unknown Event')}</strong><br>
                                    <small style="color: #666;">{match.get('category', '')} - {match.get('round', '')}</small>
                                </div>
                                <div style="text-align: right;">
                                    <span style="font-weight: bold; color: {result_color};">{result_text}</span><br>
                                    <small>vs {opponent.get('name', 'Unknown')} ({opponent.get('country', '')})</small>
                                </div>
                            </div>
                            <div style="margin-top: 8px; color: #666;">
                                Score: {red.get('score', '-')} - {blue.get('score', '-')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

    with tab4:
        st.markdown("### Search Athlete Matches")

        search_name = st.text_input("Enter athlete name", placeholder="e.g., ALKAABI")
        search_country = st.text_input("Country code (optional)", placeholder="e.g., KSA, UAE")

        if search_name and len(search_name) >= 2:
            matches = get_athlete_match_history(search_name, search_country if search_country else None)

            if matches:
                st.success(f"Found {len(matches)} matches for '{search_name}'")

                wins = sum(1 for m in matches if m.get('won'))
                losses = len(matches) - wins

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Matches", len(matches))
                with col2:
                    st.metric("Wins", wins)
                with col3:
                    st.metric("Losses", losses)

                for match in matches:
                    opponent = match.get('opponent') or {}
                    result_color = "#006C35" if match.get('won') else "#dc3545"
                    result_text = "WIN" if match.get('won') else "LOSS"

                    st.markdown(f"""
                    <div style="padding: 12px; margin: 8px 0; background: white; border-radius: 8px;
                                border-left: 4px solid {result_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>{match.get('event', 'Unknown')}</strong><br>
                                <small style="color: #666;">{match.get('category', '')} - {match.get('round', '')}</small>
                            </div>
                            <div style="text-align: right;">
                                <span style="font-weight: bold; color: {result_color};">{result_text}</span><br>
                                <small>vs {opponent.get('name', 'Unknown')} ({opponent.get('country', '')})</small>
                            </div>
                        </div>
                        <div style="margin-top: 8px; color: #666;">
                            Score: {match.get('athlete_score', '-')} - {match.get('opponent_score', '-')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info(f"No matches found for '{search_name}'")

    with tab5:
        st.markdown("### Event ID Mappings")
        st.markdown("""
        **Add event mappings manually** - If an event from athlete competition history
        can't be automatically matched to an event ID, you can add the mapping here.
        """)

        # Load current mappings
        MAPPINGS_FILE = BASE_DIR / "event_mappings.json"
        current_mappings = {}
        if MAPPINGS_FILE.exists():
            try:
                with open(MAPPINGS_FILE, 'r', encoding='utf-8') as f:
                    current_mappings = json.load(f)
            except:
                pass

        # Show current mappings count
        st.info(f"📋 Currently have **{len(current_mappings)}** event mappings saved")

        # Add new mapping form
        st.markdown("#### Add New Mapping")
        col1, col2 = st.columns([3, 1])

        with col1:
            new_event_name = st.text_input("Event Name",
                placeholder="e.g., ADULTS WORLD CHAMPIONSHIPS 2024",
                key="new_event_name")

        with col2:
            new_verid = st.text_input("Event ID (verid)",
                placeholder="e.g., 811",
                key="new_verid")

        if st.button("➕ Add Mapping", type="primary"):
            if new_event_name and new_verid:
                # Validate verid is numeric
                if new_verid.isdigit():
                    current_mappings[new_event_name.upper()] = new_verid
                    with open(MAPPINGS_FILE, 'w', encoding='utf-8') as f:
                        json.dump(current_mappings, f, indent=2, ensure_ascii=False)
                    st.success(f"✓ Added mapping: '{new_event_name}' → verid {new_verid}")
                    st.rerun()
                else:
                    st.error("verid must be a number (e.g., 765)")
            else:
                st.warning("Please enter both event name and verid")

        st.markdown("---")

        # Show existing mappings
        st.markdown("#### Current Mappings")

        if current_mappings:
            # Convert to dataframe for display
            mappings_df = pd.DataFrame([
                {"Event Name": name, "verid": verid}
                for name, verid in sorted(current_mappings.items())
            ])
            st.dataframe(mappings_df, use_container_width=True, hide_index=True)

            # Delete mapping option
            st.markdown("#### Delete Mapping")
            mapping_to_delete = st.selectbox(
                "Select mapping to delete",
                [""] + list(current_mappings.keys()),
                key="delete_mapping"
            )

            if mapping_to_delete and st.button("🗑️ Delete Selected", type="secondary"):
                del current_mappings[mapping_to_delete]
                with open(MAPPINGS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(current_mappings, f, indent=2, ensure_ascii=False)
                st.success(f"Deleted mapping for '{mapping_to_delete}'")
                st.rerun()
        else:
            st.info("No custom mappings saved yet. Use the built-in mappings or add new ones above.")

        st.markdown("---")

        # Show events needing mapping
        st.markdown("#### Events Needing Mapping")
        st.caption("These events from athlete profiles don't have a verid mapping yet:")

        # Try to load unmapped events from analysis file
        analysis_files = list(RESULTS_DIR.glob("scrape_analysis_*.json"))
        if analysis_files:
            latest_analysis = sorted(analysis_files)[-1]
            try:
                with open(latest_analysis, 'r', encoding='utf-8') as f:
                    analysis = json.load(f)

                need_mapping = analysis.get('need_mapping', [])
                if need_mapping:
                    for i, evt in enumerate(need_mapping[:15]):  # Show top 15
                        event_name = evt.get('event', 'Unknown')
                        athletes = evt.get('athletes', 0)
                        st.markdown(f"""
                        <div style="padding: 8px; margin: 4px 0; background: #fff3cd; border-radius: 4px; border-left: 3px solid #ffc107;">
                            <strong>{event_name}</strong><br>
                            <small style="color: #666;">{athletes} athletes need this data</small>
                        </div>
                        """, unsafe_allow_html=True)

                    if len(need_mapping) > 15:
                        st.caption(f"... and {len(need_mapping) - 15} more events")
                else:
                    st.success("All events have mappings!")
            except Exception as e:
                st.caption(f"Could not load analysis: {e}")
        else:
            st.caption("Run `python smart_bracket_scraper.py --list` to analyze unmapped events")


def render_asia_top_10():
    """Render Asia Top 10 Rankings by weight category for Asian Games preparation."""
    st.markdown('<p class="sub-header">🌏 Asia Top 10 Rankings</p>', unsafe_allow_html=True)

    st.markdown("""
    **Asian Games Preparation** - View the top 10 Asian athletes in each weight category.
    Use this to understand the competitive landscape and identify key rivals for upcoming Asian competitions.
    """)

    # Asian country codes
    ASIAN_COUNTRIES = {
        'KSA': 'Saudi Arabia', 'UAE': 'United Arab Emirates', 'KAZ': 'Kazakhstan',
        'THA': 'Thailand', 'JOR': 'Jordan', 'IRI': 'Iran', 'UZB': 'Uzbekistan',
        'JPN': 'Japan', 'KOR': 'South Korea', 'CHN': 'China', 'IND': 'India',
        'PAK': 'Pakistan', 'MGL': 'Mongolia', 'VIE': 'Vietnam', 'MAS': 'Malaysia',
        'INA': 'Indonesia', 'PHI': 'Philippines', 'SGP': 'Singapore', 'HKG': 'Hong Kong',
        'TPE': 'Chinese Taipei', 'BRN': 'Bahrain', 'QAT': 'Qatar', 'KUW': 'Kuwait',
        'OMA': 'Oman', 'IRQ': 'Iraq', 'LBN': 'Lebanon', 'SYR': 'Syria', 'AFG': 'Afghanistan',
        'TKM': 'Turkmenistan', 'KGZ': 'Kyrgyzstan', 'TJK': 'Tajikistan'
    }

    # Load all profiles
    profiles = load_athlete_profiles()

    if not profiles:
        st.warning("No athlete profiles found. Run the profile scraper first.")
        return

    # Filter to Asian athletes only
    asian_profiles = [p for p in profiles if p.get('country_code') in ASIAN_COUNTRIES]

    st.info(f"📊 **{len(asian_profiles)}** Asian athletes loaded from **{len(set(p.get('country_code') for p in asian_profiles))}** countries")

    # Build rankings by weight category
    category_rankings = {}

    for profile in asian_profiles:
        for cat in profile.get('categories', []):
            cat_name = cat.get('category')
            rank = cat.get('rank')
            points = cat.get('points') or 0

            if cat_name and rank:
                if cat_name not in category_rankings:
                    category_rankings[cat_name] = []

                category_rankings[cat_name].append({
                    'profile_id': profile.get('profile_id', ''),
                    'name': profile.get('name', 'Unknown'),
                    'country_code': profile.get('country_code', ''),
                    'country': profile.get('country', ASIAN_COUNTRIES.get(profile.get('country_code', ''), '')),
                    'age': profile.get('age', 'N/A'),
                    'photo_url': profile.get('photo_url', ''),
                    'flag_url': profile.get('flag_url', ''),
                    'rank': rank,
                    'points': points,
                    'medals': profile.get('medal_summary', {}),
                    'win_rate': profile.get('overall_stats', {}).get('win_rate', 'N/A'),
                    'total_events': profile.get('overall_stats', {}).get('total_events', 0),
                    'categories': profile.get('categories', [])  # Include full competition history
                })

    # Filter options
    col1, col2 = st.columns(2)

    with col1:
        gender_filter = st.selectbox(
            "Gender",
            ["All", "Male", "Female"],
            key="asia_gender"
        )

    with col2:
        age_filter = st.selectbox(
            "Age Group",
            ["All", "Adults", "U21", "U18"],
            key="asia_age"
        )

    # Filter categories
    filtered_categories = {}
    for cat_name, athletes in category_rankings.items():
        include = True
        cat_lower = cat_name.lower()

        if gender_filter == "Male" and 'female' in cat_lower:
            include = False
        elif gender_filter == "Female" and 'male' in cat_lower and 'female' not in cat_lower:
            include = False

        if age_filter == "Adults" and 'adults' not in cat_lower:
            include = False
        elif age_filter == "U21" and 'u21' not in cat_lower:
            include = False
        elif age_filter == "U18" and 'u18' not in cat_lower:
            include = False

        if include:
            filtered_categories[cat_name] = athletes

    if not filtered_categories:
        st.warning("No categories match the selected filters.")
        return

    st.markdown(f"### Found **{len(filtered_categories)}** weight categories")
    st.markdown("---")

    # Display each category
    for cat_name in sorted(filtered_categories.keys()):
        athletes = filtered_categories[cat_name]

        # Sort by world rank
        athletes_sorted = sorted(athletes, key=lambda x: x.get('rank', 9999))[:10]

        # Check if Saudi athlete in top 10
        saudi_in_top = any(a.get('country_code') == 'KSA' for a in athletes_sorted)
        indicator = "🇸🇦" if saudi_in_top else ""

        with st.expander(f"**{cat_name}** {indicator} ({len(athletes)} Asian athletes)", expanded=saudi_in_top):
            # Load bracket and enriched opponent data
            bracket_data = load_bracket_data()
            enriched_data = load_enriched_opponents()

            # Show data availability info
            if enriched_data:
                total_inferred = enriched_data.get('total_inferred_matches', 0)
                st.success(f"✅ **Opponent data loaded** - {total_inferred:,} inferred matches across {enriched_data.get('total_categories', 0)} categories. Expand profiles to see opponents.")
            elif bracket_data['all_matches']:
                st.success(f"✅ Bracket data loaded - {bracket_data['total_matches']:,} matches available.")
            else:
                st.info("ℹ️ Run `python enrich_asia_top10.py` to generate opponent data from profile analysis.")

            # Display profile cards for each top 10 athlete
            for i, athlete in enumerate(athletes_sorted, 1):
                is_saudi = athlete.get('country_code') == 'KSA'
                medals = athlete.get('medals', {})
                profile_id = athlete.get('profile_id', '')
                photo_url = athlete.get('photo_url', '')
                flag_url = athlete.get('flag_url', '')

                # Card styling based on Saudi or not
                card_bg = "#1a472a" if is_saudi else "#2d2d2d"
                border_color = "#00c853" if is_saudi else "#555"
                rank_color = "#00c853" if is_saudi else "#ffd700"
                # Use white text for Saudi cards for better readability
                name_color = "#ffffff" if is_saudi else "#ffffff"
                secondary_color = "#b8e6c1" if is_saudi else "#888"  # Light green for Saudi, gray for others
                stats_color = "#d4f0db" if is_saudi else "#aaa"  # Lighter green for Saudi stats

                # Build photo HTML - use placeholder if no photo
                if photo_url:
                    photo_html = f'<img src="{photo_url}" style="width: 70px; height: 70px; border-radius: 50%; object-fit: cover; border: 3px solid {border_color};" onerror="this.style.display=\'none\'">'
                else:
                    photo_html = f'<div style="width: 70px; height: 70px; border-radius: 50%; background: #444; display: flex; align-items: center; justify-content: center; font-size: 24px; border: 3px solid {border_color};">👤</div>'

                st.markdown(f"""
                <div style="background: {card_bg}; border: 2px solid {border_color}; border-radius: 10px; padding: 15px; margin-bottom: 10px;">
                    <div style="display: flex; gap: 15px; align-items: center;">
                        <div style="flex-shrink: 0;">
                            {photo_html}
                        </div>
                        <div style="flex-grow: 1;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <span style="font-size: 28px; font-weight: bold; color: {rank_color};">#{i}</span>
                                    <span style="font-size: 18px; margin-left: 10px; color: {name_color};">{'🇸🇦 ' if is_saudi else ''}<strong>{athlete.get('name', 'Unknown')}</strong></span>
                                </div>
                                <div style="text-align: right;">
                                    <span style="font-size: 16px; color: {name_color};">🥇{medals.get('gold', 0)} 🥈{medals.get('silver', 0)} 🥉{medals.get('bronze', 0)}</span>
                                </div>
                            </div>
                            <div style="margin-top: 5px; color: {secondary_color};">
                                {athlete.get('country_code', '')} | World Rank: <strong style="color: {name_color};">#{athlete.get('rank', 'N/R')}</strong>
                            </div>
                            <div style="margin-top: 8px; color: {stats_color};">
                                <span>Points: <strong style="color: {name_color};">{athlete.get('points', 0):.0f}</strong></span> |
                                <span>Win Rate: <strong style="color: {name_color};">{athlete.get('win_rate', 'N/A')}</strong></span> |
                                <span>Events: <strong style="color: {name_color};">{athlete.get('total_events', 0)}</strong></span> |
                                <span>Age: <strong style="color: {name_color};">{athlete.get('age', 'N/A')}</strong></span>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Build full profile for category-based matching
                full_profile = {
                    'name': athlete.get('name', ''),
                    'country_code': athlete.get('country_code', ''),
                    'categories': athlete.get('categories', [])
                }

                # Get match history using category-based matching (event + category + country)
                match_history = get_athlete_match_history_by_profile(full_profile)

                # Separate bracket matches (confirmed) from profile-only data (inferred)
                bracket_matches = [m for m in match_history if m.get('source') == 'bracket']
                profile_comps = [m for m in match_history if m.get('source') == 'profile']

                # Calculate W/L from bracket data
                bracket_wins = len([m for m in bracket_matches if m.get('won')])
                bracket_losses = len([m for m in bracket_matches if not m.get('won') and m.get('opponent_name') != 'BYE'])

                # Get inferred opponents from enriched data
                inferred_opponents = get_inferred_opponents(
                    athlete.get('name', ''),
                    athlete.get('country_code', ''),
                    cat_name,
                    enriched_data
                )
                inferred_wins = len([o for o in inferred_opponents if o.get('result') == 'win'])
                inferred_losses = len([o for o in inferred_opponents if o.get('result') == 'loss'])

                # Build competition history from profile (show wins/medal per event)
                competitions = []
                for cat in athlete.get('categories', []):
                    for comp in cat.get('competitions', []):
                        competitions.append({
                            'date': comp.get('date', ''),
                            'event': comp.get('event', ''),
                            'event_type': comp.get('event_type', ''),
                            'category': cat.get('category', ''),
                            'rank': comp.get('rank'),
                            'medal': comp.get('medal', ''),
                            'wins': comp.get('wins', 0),
                            'points': comp.get('points', 0)
                        })

                # Show competition history with bracket data where available
                total_wins_profile = sum(c.get('wins', 0) for c in competitions)
                expander_title = f"📊 Competition History - {len(competitions)} events"
                if inferred_opponents:
                    expander_title += f" | ⚔️ {len(inferred_opponents)} opponents ({inferred_wins}W-{inferred_losses}L)"
                elif bracket_matches:
                    expander_title += f" | ⚔️ {len(bracket_matches)} matches scraped ({bracket_wins}W-{bracket_losses}L)"

                with st.expander(expander_title, expanded=False):
                    # Show data source legend - white background
                    st.markdown("""
                    <div style="background: #f8f9fa; padding: 10px; border-radius: 6px; margin-bottom: 12px; font-size: 13px; border: 1px solid #dee2e6; color: #333;">
                        <strong style="color: #000;">Data Sources:</strong>
                        <span style="color: #198754;">🟢 Bracket Data</span> (confirmed) |
                        <span style="color: #0d6efd;">🔵 Inferred</span> (from rankings) |
                        <span style="color: #fd7e14;">🟡 Profile</span> (W/L only)
                    </div>
                    """, unsafe_allow_html=True)

                    # Group competitions by event (inferred opponents will show as dropdowns under each card)
                    competitions_sorted = sorted(competitions, key=lambda x: x.get('date', ''), reverse=True)

                    for comp in competitions_sorted[:15]:
                        event_name = comp.get('event', '')
                        category = comp.get('category', '')
                        rank = comp.get('rank', 0)
                        wins = comp.get('wins', 0)
                        medal = comp.get('medal', '')

                        # Extract weight class from category (e.g., "-62 KG" from "ADULTS JIU-JITSU MALE -62 KG")
                        import re
                        weight_match = re.search(r'([+-]?\d+\s*KG)', category.upper())
                        weight_class = weight_match.group(1) if weight_match else ""

                        # Also check if it's NO-GI
                        is_nogi = "NO-GI" in category.upper()
                        discipline_badge = "NO-GI" if is_nogi else ""

                        # Medal styling - using white/light backgrounds with dark text
                        if medal == 'gold':
                            medal_icon = "🥇"
                            bg_color = "#fff3cd"  # Light gold/yellow
                            border_color = "#ffc107"
                            text_color = "#664d03"
                        elif medal == 'silver':
                            medal_icon = "🥈"
                            bg_color = "#e9ecef"  # Light silver/gray
                            border_color = "#adb5bd"
                            text_color = "#495057"
                        elif medal == 'bronze':
                            medal_icon = "🥉"
                            bg_color = "#f8e4d0"  # Light bronze
                            border_color = "#cd7f32"
                            text_color = "#5c4033"
                        else:
                            medal_icon = f"#{rank}" if rank else ""
                            bg_color = "#ffffff"  # White
                            border_color = "#dee2e6"
                            text_color = "#212529"

                        # Check if we have bracket data for this event/category
                        event_brackets = [m for m in bracket_matches
                                         if event_name.upper() in m.get('event', '').upper()
                                         and category.upper() in m.get('category', '').upper()]

                        if event_brackets:
                            # Show with bracket data (confirmed opponents)
                            source_indicator = '<span style="color: #198754;">🟢</span>'
                        else:
                            source_indicator = '<span style="color: #fd7e14;">🟡</span>'

                        # Build weight badge HTML
                        weight_badge = f'<span style="background: #6f42c1; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; margin-left: 8px;">{weight_class}</span>' if weight_class else ""
                        nogi_badge = f'<span style="background: #fd7e14; color: white; padding: 2px 6px; border-radius: 10px; font-size: 10px; margin-left: 4px;">NO-GI</span>' if is_nogi else ""

                        st.markdown(f"""
                        <div style="background: {bg_color}; padding: 12px; margin: 8px 0; border-radius: 6px; border: 1px solid {border_color}; color: {text_color};">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    {source_indicator} <strong style="color: #000;">{event_name}</strong>{weight_badge}{nogi_badge}
                                </div>
                                <div>
                                    <span style="font-size: 20px;">{medal_icon}</span>
                                    <span style="color: #495057; font-weight: 600;"> | {wins}W</span>
                                </div>
                            </div>
                            <div style="color: #6c757d; font-size: 12px; margin-top: 6px;">
                                {comp.get('date', '')} | {comp.get('event_type', '')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Show individual matches if we have bracket data
                        if event_brackets:
                            for match in event_brackets:
                                won = match.get('won', False)
                                result_color = "#198754" if won else "#dc3545"  # Bootstrap green/red
                                result_bg = "#d1e7dd" if won else "#f8d7da"  # Light green/red bg
                                result_text = "✅ WIN" if won else "❌ LOSS"
                                opponent = match.get('opponent_name', 'Unknown')
                                opp_country = match.get('opponent_country', '')

                                if opponent and opponent != 'BYE' and opponent != 'Unknown':
                                    st.markdown(f"""
                                    <div style="padding: 8px 16px; margin: 4px 0 4px 20px; background: {result_bg}; border-radius: 4px; border-left: 4px solid {result_color}; font-size: 13px; color: #212529;">
                                        <strong>{result_text}</strong> vs <strong>{opponent}</strong> ({opp_country})
                                        <span style="float: right; color: #495057;">{match.get('round', '')} | {match.get('athlete_score', 0)}-{match.get('opponent_score', 0)}</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                        else:
                            # No bracket data - show inferred opponents for this specific event as dropdown
                            # Filter inferred_opponents to only those matching this event
                            event_inferred = [o for o in inferred_opponents
                                            if event_name.upper() in o.get('event', '').upper()
                                            or o.get('event', '').upper() in event_name.upper()]

                            if event_inferred:
                                # Count wins/losses for this event
                                event_wins = len([o for o in event_inferred if o.get('result') == 'win'])
                                event_losses = len([o for o in event_inferred if o.get('result') == 'loss'])

                                # Create unique key for expander
                                unique_key = f"{athlete.get('name', '')}_{event_name}_{category}".replace(' ', '_').replace('/', '_')

                                with st.expander(f"🔵 Inferred Opponents ({event_wins}W-{event_losses}L)", expanded=False):
                                    for opp in event_inferred:
                                        won = opp.get('result') == 'win'
                                        result_color = "#198754" if won else "#dc3545"
                                        result_bg = "#d1e7dd" if won else "#f8d7da"
                                        result_text = "✅ WIN" if won else "❌ LOSS"
                                        opponent = opp.get('opponent_name', 'Unknown')
                                        opp_country = opp.get('opponent_country', '')
                                        confidence = opp.get('confidence', 0)
                                        reasoning = opp.get('reasoning', '')[:50] + '...' if len(opp.get('reasoning', '')) > 50 else opp.get('reasoning', '')

                                        st.markdown(f"""
                                        <div style="padding: 8px 12px; margin: 4px 0; background: {result_bg}; border-radius: 4px; border-left: 4px solid {result_color}; font-size: 12px; color: #212529;">
                                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                                <div>
                                                    <strong>{result_text}</strong> vs <strong>{opponent}</strong> ({opp_country})
                                                </div>
                                                <span style="background: #e3f2fd; padding: 2px 6px; border-radius: 8px; font-size: 10px; color: #0d6efd;">{confidence:.0%}</span>
                                            </div>
                                            <div style="color: #6c757d; font-size: 10px; margin-top: 3px; font-style: italic;">
                                                {reasoning}
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)

                    if len(competitions_sorted) > 15:
                        st.caption(f"...and {len(competitions_sorted) - 15} more competitions")

                    if not bracket_matches and competitions:
                        st.info("💡 **Tip:** Run the bracket scraper to get actual opponent names for these events.")

            # Quick insights for Saudi athletes
            if saudi_in_top:
                st.markdown("---")
                saudi_athletes = [a for a in athletes_sorted if a.get('country_code') == 'KSA']
                for sa in saudi_athletes:
                    sa_rank = next((i for i, a in enumerate(athletes_sorted, 1) if a.get('name') == sa.get('name')), None)
                    if sa_rank:
                        st.success(f"🇸🇦 **{sa.get('name')}** is ranked **#{sa_rank} in Asia** (World #{sa.get('rank')})")

    # Summary statistics
    st.markdown("---")
    st.markdown("### 📈 Saudi Asia Rankings Summary")

    saudi_rankings = []
    for cat_name, athletes in filtered_categories.items():
        athletes_sorted = sorted(athletes, key=lambda x: x.get('rank', 9999))
        for i, athlete in enumerate(athletes_sorted[:10], 1):
            if athlete.get('country_code') == 'KSA':
                saudi_rankings.append({
                    'Category': cat_name,
                    'Athlete': athlete.get('name'),
                    'Asia Rank': i,
                    'World Rank': athlete.get('rank'),
                    'Points': athlete.get('points', 0)
                })

    if saudi_rankings:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Saudi in Asia Top 10", len(saudi_rankings))
        with col2:
            top_5 = len([r for r in saudi_rankings if r['Asia Rank'] <= 5])
            st.metric("In Top 5 Asia", top_5)
        with col3:
            top_3 = len([r for r in saudi_rankings if r['Asia Rank'] <= 3])
            st.metric("Podium Position", top_3)

        st.markdown("#### Saudi Athletes in Asia Top 10")
        df_summary = pd.DataFrame(saudi_rankings)
        df_summary = df_summary.sort_values('Asia Rank')
        st.dataframe(df_summary, use_container_width=True, hide_index=True)
    else:
        st.info("No Saudi athletes currently in Asia Top 10 for selected filters.")


def render_head_to_head():
    """Render head-to-head comparison between Saudi athlete and opponent."""
    st.markdown('<p class="sub-header">⚔️ Head-to-Head Analysis</p>', unsafe_allow_html=True)

    st.markdown("""
    Compare a **Saudi athlete** directly with a **potential opponent** to prepare match strategy.
    Athletes are automatically filtered to show **same-gender opponents only**.
    """)

    profiles = load_athlete_profiles()

    # Split into Saudi and opponents
    saudi_profiles = [p for p in profiles if p.get('country_code') == 'KSA' and p.get('categories')]
    opponent_profiles = [p for p in profiles if p.get('country_code') != 'KSA' and p.get('categories')]

    if not saudi_profiles:
        st.warning("No Saudi athlete profiles with competition data found.")
        return

    if not opponent_profiles:
        st.warning("No opponent profiles scouted yet. Go to 'Opponent Scouting' to scout opponents first.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🇸🇦 Saudi Athlete")
        saudi_names = {p.get('profile_id'): p.get('name', 'Unknown') for p in saudi_profiles}
        selected_saudi = st.selectbox(
            "Select Saudi Athlete",
            options=list(saudi_names.keys()),
            format_func=lambda x: saudi_names.get(x, x)
        )
        saudi_athlete = next((p for p in saudi_profiles if p.get('profile_id') == selected_saudi), None)

    # Get Saudi athlete's gender for matching
    saudi_gender = extract_gender_from_categories(saudi_athlete) if saudi_athlete else 'Unknown'

    # Filter opponents to SAME GENDER ONLY
    gender_matched_opponents = [
        p for p in opponent_profiles
        if extract_gender_from_categories(p) == saudi_gender or saudi_gender == 'Unknown'
    ]

    # Further filter by overlapping weight categories for better matchups
    if saudi_athlete:
        saudi_weights = set(extract_weight_classes(saudi_athlete))

    with col2:
        st.markdown("### 🎯 Opponent")

        # Show gender filter status
        if saudi_gender != 'Unknown':
            st.caption(f"Showing {saudi_gender} opponents only ({len(gender_matched_opponents)} athletes)")
        else:
            st.caption(f"Showing all opponents ({len(gender_matched_opponents)} athletes)")

        # Sort opponents by relevance (overlapping weight categories first)
        def opponent_relevance(opp):
            opp_weights = set(extract_weight_classes(opp))
            overlap = len(saudi_weights & opp_weights) if saudi_athlete else 0
            medals = opp.get('medal_summary', {})
            medal_score = medals.get('gold', 0) * 3 + medals.get('silver', 0) * 2 + medals.get('bronze', 0)
            return (overlap, medal_score)

        sorted_opponents = sorted(gender_matched_opponents, key=opponent_relevance, reverse=True)

        opp_names = {
            p.get('profile_id'): f"{p.get('name', 'Unknown')} ({p.get('country_code')}) - {', '.join(extract_weight_classes(p)) or 'N/A'}"
            for p in sorted_opponents
        }
        selected_opp = st.selectbox(
            "Select Opponent",
            options=list(opp_names.keys()),
            format_func=lambda x: opp_names.get(x, x)
        )
        opponent = next((p for p in sorted_opponents if p.get('profile_id') == selected_opp), None)

    if saudi_athlete and opponent:
        st.markdown("---")

        # Side-by-side comparison
        col1, col2 = st.columns(2)

        with col1:
            # Saudi athlete card
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #006C35 0%, #004d26 100%);
                        color: white; padding: 1.5rem; border-radius: 10px; text-align: center;">
                <img src="{saudi_athlete.get('photo_url', f'{FLAG_URL_BASE}KSA.png')}"
                     style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 3px solid gold;">
                <h3 style="margin: 0.5rem 0;">{saudi_athlete.get('name', 'Unknown')}</h3>
                <p>🇸🇦 Saudi Arabia | Age: {saudi_athlete.get('age', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

            medals = saudi_athlete.get('medal_summary', {})
            stats = saudi_athlete.get('overall_stats', {})

            st.metric("Total Medals", f"🥇{medals.get('gold', 0)} 🥈{medals.get('silver', 0)} 🥉{medals.get('bronze', 0)}")
            st.metric("Win Rate", stats.get('win_rate', 'N/A'))
            st.metric("Total Events", stats.get('total_events', 'N/A'))
            st.metric("Total Wins", stats.get('total_wins', 'N/A'))

        with col2:
            # Opponent card
            opp_country_code = opponent.get('country_code', 'UNK')
            opp_photo_url = opponent.get('photo_url', f'{FLAG_URL_BASE}{opp_country_code}.png')
            opp_name = opponent.get('name', 'Unknown')
            opp_country = opponent.get('country', '')
            opp_age = opponent.get('age', 'N/A')

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #8B0000 0%, #5c0000 100%);
                        color: white; padding: 1.5rem; border-radius: 10px; text-align: center;">
                <img src="{opp_photo_url}"
                     style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 3px solid silver;">
                <h3 style="margin: 0.5rem 0;">{opp_name}</h3>
                <p>{opp_country_code} {opp_country} | Age: {opp_age}</p>
            </div>
            """, unsafe_allow_html=True)

            medals = opponent.get('medal_summary', {})
            stats = opponent.get('overall_stats', {})

            st.metric("Total Medals", f"🥇{medals.get('gold', 0)} 🥈{medals.get('silver', 0)} 🥉{medals.get('bronze', 0)}")
            st.metric("Win Rate", stats.get('win_rate', 'N/A'))
            st.metric("Total Events", stats.get('total_events', 'N/A'))
            st.metric("Total Wins", stats.get('total_wins', 'N/A'))

        # Category overlap analysis
        st.markdown("---")
        st.markdown("### ⚖️ Shared Weight Categories")

        saudi_cats = {c.get('category'): c for c in saudi_athlete.get('categories', [])}
        opp_cats = {c.get('category'): c for c in opponent.get('categories', [])}

        shared_cats = set(saudi_cats.keys()) & set(opp_cats.keys())

        if shared_cats:
            for cat in shared_cats:
                st.markdown(f"#### {cat}")

                col1, col2 = st.columns(2)

                saudi_cat = saudi_cats[cat]
                opp_cat = opp_cats[cat]

                with col1:
                    st.markdown("**🇸🇦 Saudi**")
                    st.write(f"World Rank: **#{saudi_cat.get('rank', 'N/R')}**")
                    saudi_points = saudi_cat.get('points') or 0
                    st.write(f"Points: **{saudi_points:.0f}**")
                    st.write(f"Competitions: **{len(saudi_cat.get('competitions', []))}**")

                    # Recent form (last 3 results)
                    recent = saudi_cat.get('competitions', [])[:3]
                    if recent:
                        st.markdown("**Recent Results:**")
                        for r in recent:
                            medal_icon = {'gold': '🥇', 'silver': '🥈', 'bronze': '🥉'}.get(r.get('medal'), '')
                            st.write(f"- {r.get('date')}: #{r.get('rank')} {medal_icon}")

                with col2:
                    st.markdown("**🎯 Opponent**")
                    st.write(f"World Rank: **#{opp_cat.get('rank', 'N/R')}**")
                    opp_points = opp_cat.get('points') or 0
                    st.write(f"Points: **{opp_points:.0f}**")
                    st.write(f"Competitions: **{len(opp_cat.get('competitions', []))}**")

                    recent = opp_cat.get('competitions', [])[:3]
                    if recent:
                        st.markdown("**Recent Results:**")
                        for r in recent:
                            medal_icon = {'gold': '🥇', 'silver': '🥈', 'bronze': '🥉'}.get(r.get('medal'), '')
                            st.write(f"- {r.get('date')}: #{r.get('rank')} {medal_icon}")

                st.markdown("---")
        else:
            st.info("These athletes don't compete in the same weight categories.")

        # Enhanced Tactical Analysis using expert functions
        st.markdown("### 📋 Expert Tactical Analysis")

        # Generate comprehensive tactical report
        tactical_report = generate_tactical_report(saudi_athlete, opponent)

        # Display tactical report in organized sections
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### ✅ Advantages")
            if tactical_report['advantages']:
                for adv in tactical_report['advantages']:
                    st.success(adv)
            else:
                st.info("No clear statistical advantages identified")

        with col2:
            st.markdown("#### ⚠️ Warnings")
            if tactical_report['warnings']:
                for warn in tactical_report['warnings']:
                    st.warning(warn)
            else:
                st.info("No major concerns identified")

        # Strategic recommendations
        st.markdown("#### 🎯 Strategic Recommendations")
        if tactical_report['strategy']:
            for i, strat in enumerate(tactical_report['strategy'], 1):
                st.markdown(f"{i}. {strat}")
        else:
            st.info("Execute your standard game plan")

        # Form Analysis Section
        st.markdown("---")
        st.markdown("### 📈 Form Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🇸🇦 Saudi Athlete Form")
            saudi_form, saudi_trend, saudi_recent = calculate_form_score(saudi_athlete)

            # Form score gauge
            form_color = '#006C35' if saudi_form >= 60 else '#FFA500' if saudi_form >= 40 else '#FF4444'
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: #f9f9f9; border-radius: 10px; border-left: 5px solid {form_color};">
                <div style="font-size: 2.5rem; font-weight: bold; color: {form_color};">{saudi_form}</div>
                <div style="font-size: 0.9rem; color: #666;">Form Score (0-100)</div>
                <div style="margin-top: 0.5rem;">
                    <span style="font-size: 1.2rem;">{'📈' if saudi_trend == 'improving' else '📉' if saudi_trend == 'declining' else '➡️'}</span>
                    <strong>{saudi_trend.title()}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if saudi_recent:
                st.markdown("**Recent Results:**")
                for r in saudi_recent[:3]:
                    medal_icon = {'gold': '🥇', 'silver': '🥈', 'bronze': '🥉'}.get(r.get('medal'), '')
                    st.write(f"- {r.get('date', 'N/A')}: #{r.get('rank', '?')} {medal_icon}")

        with col2:
            st.markdown("#### 🎯 Opponent Form")
            opp_form, opp_trend, opp_recent = calculate_form_score(opponent)

            form_color = '#8B0000' if opp_form >= 60 else '#FFA500' if opp_form >= 40 else '#006C35'
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: #f9f9f9; border-radius: 10px; border-left: 5px solid {form_color};">
                <div style="font-size: 2.5rem; font-weight: bold; color: {form_color};">{opp_form}</div>
                <div style="font-size: 0.9rem; color: #666;">Form Score (0-100)</div>
                <div style="margin-top: 0.5rem;">
                    <span style="font-size: 1.2rem;">{'📈' if opp_trend == 'improving' else '📉' if opp_trend == 'declining' else '➡️'}</span>
                    <strong>{opp_trend.title()}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if opp_recent:
                st.markdown("**Recent Results:**")
                for r in opp_recent[:3]:
                    medal_icon = {'gold': '🥇', 'silver': '🥈', 'bronze': '🥉'}.get(r.get('medal'), '')
                    st.write(f"- {r.get('date', 'N/A')}: #{r.get('rank', '?')} {medal_icon}")

        # Discipline & Career Analysis
        st.markdown("---")
        st.markdown("### 🥋 Discipline & Career Profile")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🇸🇦 Saudi Athlete")
            saudi_disciplines = get_disciplines_competed(saudi_athlete)
            saudi_age_cats = get_age_categories_competed(saudi_athlete)
            saudi_freq, saudi_consistency, saudi_gaps = analyze_competition_frequency(saudi_athlete)
            saudi_peak_year, saudi_peak_stats, saudi_trajectory = find_peak_performance(saudi_athlete)

            st.markdown(f"**Disciplines:** {', '.join(saudi_disciplines) if saudi_disciplines else 'N/A'}")
            st.markdown(f"**Age Categories:** {', '.join(saudi_age_cats) if saudi_age_cats else 'N/A'}")
            st.markdown(f"**Competition Frequency:** {saudi_freq}/year ({saudi_consistency})")
            if saudi_peak_year:
                st.markdown(f"**Peak Year:** {saudi_peak_year} ({saudi_peak_stats.get('medals', 0)} medals, {saudi_peak_stats.get('wins', 0)} wins)")
            st.markdown(f"**Career Trajectory:** {saudi_trajectory.replace('_', ' ').title()}")

        with col2:
            st.markdown("#### 🎯 Opponent")
            opp_disciplines = get_disciplines_competed(opponent)
            opp_age_cats = get_age_categories_competed(opponent)
            opp_freq, opp_consistency, opp_gaps = analyze_competition_frequency(opponent)
            opp_peak_year, opp_peak_stats, opp_trajectory = find_peak_performance(opponent)

            st.markdown(f"**Disciplines:** {', '.join(opp_disciplines) if opp_disciplines else 'N/A'}")
            st.markdown(f"**Age Categories:** {', '.join(opp_age_cats) if opp_age_cats else 'N/A'}")
            st.markdown(f"**Competition Frequency:** {opp_freq}/year ({opp_consistency})")
            if opp_peak_year:
                st.markdown(f"**Peak Year:** {opp_peak_year} ({opp_peak_stats.get('medals', 0)} medals, {opp_peak_stats.get('wins', 0)} wins)")
            st.markdown(f"**Career Trajectory:** {opp_trajectory.replace('_', ' ').title()}")


def render_statistics(df_athletes, athletes_by_country):
    """Render statistics page."""
    st.markdown('<p class="sub-header">📊 Statistics & Insights</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Athletes Distribution")

        df_dist = pd.DataFrame([
            {'Country': k, 'Athletes': v}
            for k, v in sorted(athletes_by_country.items(), key=lambda x: -x[1])
        ])

        fig = px.bar(
            df_dist,
            x='Country',
            y='Athletes',
            color='Athletes',
            color_continuous_scale='Greens',
            title='Athletes per Country'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Summary Statistics")

        total = sum(athletes_by_country.values())
        saudi_count = athletes_by_country.get('KSA', 0)
        saudi_pct = (saudi_count / total * 100) if total > 0 else 0

        st.metric("Total Athletes Tracked", f"{total:,}")
        st.metric("Saudi Athletes", f"{saudi_count}")
        st.metric("Saudi % of Dataset", f"{saudi_pct:.1f}%")
        st.metric("Countries with Data", len(athletes_by_country))

        st.markdown("**Top 5 Countries:**")
        for i, (country, count) in enumerate(sorted(athletes_by_country.items(), key=lambda x: -x[1])[:5], 1):
            st.write(f"{i}. **{country}**: {count} athletes")

    # Gulf region analysis
    st.markdown("---")
    st.markdown("### 🏜️ Regional Focus: Gulf Countries")

    gulf_countries = ['KSA', 'UAE', 'QAT', 'KUW', 'BRN', 'OMN']
    gulf_data = {k: v for k, v in athletes_by_country.items() if k in gulf_countries}

    if gulf_data:
        col1, col2 = st.columns([1, 1])

        with col1:
            df_gulf = pd.DataFrame([
                {'Country': k, 'Athletes': v}
                for k, v in sorted(gulf_data.items(), key=lambda x: -x[1])
            ])

            fig = px.pie(
                df_gulf,
                values='Athletes',
                names='Country',
                title='Gulf Region Athletes',
                color_discrete_sequence=px.colors.sequential.Greens
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**Gulf Region Breakdown:**")
            for country, count in sorted(gulf_data.items(), key=lambda x: -x[1]):
                flag_url = f"{FLAG_URL_BASE}{country}.png"
                st.markdown(f"""
                <div style="padding: 0.5rem; margin: 0.25rem 0; background: #f9f9f9; border-radius: 5px; border-left: 3px solid #006C35;">
                    <img src="{flag_url}" style="width: 24px; vertical-align: middle; margin-right: 8px;">
                    <strong>{country}</strong>: {count} athletes
                </div>
                """, unsafe_allow_html=True)

            # Gulf total
            gulf_total = sum(gulf_data.values())
            st.markdown(f"**Total Gulf Athletes:** {gulf_total}")
    else:
        st.info("No Gulf country data available in current dataset.")


if __name__ == "__main__":
    main()
