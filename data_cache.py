"""
Data Cache Builder
==================
Pre-aggregates and caches data for fast dashboard loading.
Run periodically or after scraping to update the cache.

Usage:
    python data_cache.py              # Build all caches
    python data_cache.py --profiles   # Only profile cache
    python data_cache.py --matches    # Only match cache
"""

import json
import pickle
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
PROFILES_DIR = BASE_DIR / "Profiles"
RESULTS_DIR = BASE_DIR / "Results"
CACHE_DIR = BASE_DIR / "Cache"
CACHE_DIR.mkdir(exist_ok=True)


def build_profile_cache():
    """Build aggregated profile cache for fast loading."""
    print("Building profile cache...")

    profiles = []
    profile_files = list(PROFILES_DIR.glob("*.json"))

    for pf in profile_files:
        try:
            with open(pf, 'r', encoding='utf-8') as f:
                profile = json.load(f)
                profiles.append(profile)
        except Exception as e:
            print(f"  Error loading {pf.name}: {e}")

    # Aggregate by country
    by_country = defaultdict(list)
    for p in profiles:
        country = p.get('country_code', 'UNK')
        by_country[country].append(p)

    # Build summary stats
    country_stats = {}
    for country, athletes in by_country.items():
        total_gold = sum(a.get('medal_summary', {}).get('gold', 0) for a in athletes)
        total_silver = sum(a.get('medal_summary', {}).get('silver', 0) for a in athletes)
        total_bronze = sum(a.get('medal_summary', {}).get('bronze', 0) for a in athletes)

        # Top performers
        top_by_winrate = sorted(
            [a for a in athletes if a.get('overall_stats', {}).get('total_events', 0) >= 3],
            key=lambda x: float(str(x.get('overall_stats', {}).get('win_rate', '0%')).replace('%', '') or 0),
            reverse=True
        )[:10]

        country_stats[country] = {
            'total_athletes': len(athletes),
            'total_gold': total_gold,
            'total_silver': total_silver,
            'total_bronze': total_bronze,
            'total_medals': total_gold + total_silver + total_bronze,
            'top_performers': [
                {
                    'name': a.get('name'),
                    'win_rate': a.get('overall_stats', {}).get('win_rate'),
                    'events': a.get('overall_stats', {}).get('total_events'),
                    'medals': a.get('medal_summary', {})
                }
                for a in top_by_winrate
            ]
        }

    # Create searchable index
    search_index = {}
    for p in profiles:
        name = p.get('name', '').lower()
        profile_id = p.get('profile_id', '')
        search_index[name] = profile_id
        # Also index partial names
        parts = name.split()
        for part in parts:
            if part not in search_index:
                search_index[part] = []
            if isinstance(search_index[part], list):
                search_index[part].append(profile_id)

    cache = {
        'timestamp': datetime.now().isoformat(),
        'total_profiles': len(profiles),
        'countries': list(by_country.keys()),
        'country_stats': country_stats,
        'search_index': search_index,
        'profiles': profiles  # Full profiles for detail views
    }

    # Save as pickle for fastest loading
    cache_file = CACHE_DIR / "profiles_cache.pkl"
    with open(cache_file, 'wb') as f:
        pickle.dump(cache, f)

    # Also save JSON for debugging
    json_cache = {k: v for k, v in cache.items() if k != 'profiles'}
    json_cache['profile_count'] = len(profiles)
    with open(CACHE_DIR / "profiles_summary.json", 'w', encoding='utf-8') as f:
        json.dump(json_cache, f, indent=2, ensure_ascii=False)

    print(f"  Cached {len(profiles)} profiles from {len(by_country)} countries")
    return cache


def build_match_cache():
    """Build aggregated match cache for fast loading."""
    print("Building match cache...")

    # Load all_matches.json if exists
    matches_file = BASE_DIR / "all_matches.json"
    if not matches_file.exists():
        print("  No all_matches.json found")
        return None

    with open(matches_file, 'r', encoding='utf-8') as f:
        matches = json.load(f)

    # Aggregate by event
    by_event = defaultdict(list)
    by_category = defaultdict(list)
    saudi_matches = []

    for m in matches:
        event = m.get('event', 'Unknown')
        category = m.get('category', 'Unknown')
        by_event[event].append(m)
        by_category[category].append(m)

        # Check for Saudi involvement
        red = m.get('red', {})
        blue = m.get('blue', {})
        if any(c in str(red.get('country', '')) for c in ['KSA', 'Saudi', 'SAU']):
            saudi_matches.append(m)
        elif any(c in str(blue.get('country', '')) for c in ['KSA', 'Saudi', 'SAU']):
            saudi_matches.append(m)

    # Calculate Saudi stats
    saudi_wins = sum(1 for m in saudi_matches
                     if any(c in str(m.get('winner', '')) for c in ['KSA', 'Saudi']))

    cache = {
        'timestamp': datetime.now().isoformat(),
        'total_matches': len(matches),
        'events': list(by_event.keys()),
        'categories': list(by_category.keys()),
        'matches_by_event': {k: len(v) for k, v in by_event.items()},
        'matches_by_category': {k: len(v) for k, v in by_category.items()},
        'saudi_matches_count': len(saudi_matches),
        'saudi_wins': saudi_wins,
        'saudi_win_rate': f"{(saudi_wins/len(saudi_matches)*100):.1f}%" if saudi_matches else "N/A"
    }

    # Save summary
    with open(CACHE_DIR / "matches_summary.json", 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

    # Save Saudi matches separately for quick access
    with open(CACHE_DIR / "saudi_matches.json", 'w', encoding='utf-8') as f:
        json.dump(saudi_matches, f, indent=2, ensure_ascii=False)

    print(f"  Cached {len(matches)} matches, {len(saudi_matches)} Saudi matches")
    return cache


def build_rankings_cache():
    """Build Asian and World rankings cache."""
    print("Building rankings cache...")

    # Load profiles
    cache_file = CACHE_DIR / "profiles_cache.pkl"
    if not cache_file.exists():
        print("  Building profiles first...")
        build_profile_cache()

    with open(cache_file, 'rb') as f:
        profile_cache = pickle.load(f)

    profiles = profile_cache.get('profiles', [])

    # Asian countries
    asian_codes = [
        'KSA', 'UAE', 'KUW', 'BRN', 'QAT', 'JOR', 'IRI', 'KAZ', 'UZB',
        'THA', 'JPN', 'KOR', 'MGL', 'INA', 'PHI', 'VIE', 'MAS', 'SGP',
        'IND', 'PAK', 'TJK', 'KGZ', 'TKM', 'LBN', 'SYR', 'IRQ', 'AFG',
        'NPL', 'CHN', 'TPE', 'HKG'
    ]

    # Filter Asian athletes
    asian_athletes = [p for p in profiles if p.get('country_code') in asian_codes]

    # Build rankings by category
    rankings = defaultdict(list)

    for p in profiles:
        for cat in p.get('categories', []):
            cat_name = cat.get('category', '')
            rank = cat.get('rank')
            points = cat.get('points', 0)

            if rank and points:
                rankings[cat_name].append({
                    'name': p.get('name'),
                    'country': p.get('country_code'),
                    'rank': rank,
                    'points': points,
                    'profile_id': p.get('profile_id')
                })

    # Sort each category by rank
    for cat in rankings:
        rankings[cat] = sorted(rankings[cat], key=lambda x: x['rank'])[:50]  # Top 50

    # Asian-only rankings
    asian_rankings = defaultdict(list)
    for p in asian_athletes:
        for cat in p.get('categories', []):
            cat_name = cat.get('category', '')
            rank = cat.get('rank')
            points = cat.get('points', 0)

            if rank and points:
                asian_rankings[cat_name].append({
                    'name': p.get('name'),
                    'country': p.get('country_code'),
                    'rank': rank,
                    'points': points,
                    'profile_id': p.get('profile_id')
                })

    for cat in asian_rankings:
        asian_rankings[cat] = sorted(asian_rankings[cat], key=lambda x: x['rank'])[:20]

    cache = {
        'timestamp': datetime.now().isoformat(),
        'world_rankings': dict(rankings),
        'asian_rankings': dict(asian_rankings),
        'categories': list(rankings.keys())
    }

    with open(CACHE_DIR / "rankings_cache.json", 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

    print(f"  Cached rankings for {len(rankings)} categories")
    return cache


def build_head_to_head_index():
    """Build head-to-head match index for quick lookups."""
    print("Building head-to-head index...")

    matches_file = BASE_DIR / "all_matches.json"
    if not matches_file.exists():
        print("  No all_matches.json found")
        return None

    with open(matches_file, 'r', encoding='utf-8') as f:
        matches = json.load(f)

    # Build athlete pair index
    h2h_index = defaultdict(list)

    for m in matches:
        red = m.get('red', {}).get('name', '')
        blue = m.get('blue', {}).get('name', '')

        if red and blue:
            # Create consistent key (alphabetically sorted)
            key = tuple(sorted([red.lower(), blue.lower()]))
            h2h_index[str(key)].append(m)

    # Save index
    with open(CACHE_DIR / "h2h_index.json", 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_pairs': len(h2h_index),
            'index': {k: v for k, v in h2h_index.items()}
        }, f, indent=2, ensure_ascii=False)

    print(f"  Indexed {len(h2h_index)} athlete pairs")
    return h2h_index


def build_all_caches():
    """Build all caches."""
    print("=" * 50)
    print("BUILDING ALL DATA CACHES")
    print("=" * 50)

    start = datetime.now()

    build_profile_cache()
    build_match_cache()
    build_rankings_cache()
    build_head_to_head_index()

    elapsed = (datetime.now() - start).total_seconds()

    print("=" * 50)
    print(f"All caches built in {elapsed:.1f}s")
    print(f"Cache directory: {CACHE_DIR}")
    print("=" * 50)


# Quick load functions for dashboard
def load_profiles_fast():
    """Load profiles from cache (fast)."""
    cache_file = CACHE_DIR / "profiles_cache.pkl"
    if cache_file.exists():
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    return None


def load_saudi_matches_fast():
    """Load Saudi matches from cache (fast)."""
    cache_file = CACHE_DIR / "saudi_matches.json"
    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def load_rankings_fast():
    """Load rankings from cache (fast)."""
    cache_file = CACHE_DIR / "rankings_cache.json"
    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Build data caches')
    parser.add_argument('--profiles', action='store_true', help='Only build profile cache')
    parser.add_argument('--matches', action='store_true', help='Only build match cache')
    parser.add_argument('--rankings', action='store_true', help='Only build rankings cache')
    parser.add_argument('--h2h', action='store_true', help='Only build head-to-head index')

    args = parser.parse_args()

    if args.profiles:
        build_profile_cache()
    elif args.matches:
        build_match_cache()
    elif args.rankings:
        build_rankings_cache()
    elif args.h2h:
        build_head_to_head_index()
    else:
        build_all_caches()
