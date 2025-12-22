"""
Scrape All Asian Country Athlete Profiles
==========================================
Batch scraper for all Asian JJIF athlete profiles.
Run when you have a stable connection.

Usage:
    python scrape_all_asian_profiles.py
    python scrape_all_asian_profiles.py --priority-only  # Just key rivals
"""

import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from scrape_athlete_profiles import scrape_athlete_profiles

# Asian countries - Priority order (key rivals first)
ASIAN_COUNTRIES = [
    # Priority 1: Gulf region + key rivals
    ('KSA', 'Saudi Arabia'),
    ('UAE', 'United Arab Emirates'),
    ('KUW', 'Kuwait'),
    ('BRN', 'Bahrain'),
    ('QAT', 'Qatar'),
    ('JOR', 'Jordan'),
    ('IRI', 'Iran'),

    # Priority 2: Strong Asian nations
    ('KAZ', 'Kazakhstan'),
    ('UZB', 'Uzbekistan'),
    ('THA', 'Thailand'),
    ('JPN', 'Japan'),
    ('KOR', 'South Korea'),
    ('MGL', 'Mongolia'),

    # Priority 3: Southeast Asia
    ('INA', 'Indonesia'),
    ('PHI', 'Philippines'),
    ('VIE', 'Vietnam'),
    ('MAS', 'Malaysia'),
    ('SGP', 'Singapore'),

    # Priority 4: South/Central Asia
    ('IND', 'India'),
    ('PAK', 'Pakistan'),
    ('TJK', 'Tajikistan'),
    ('KGZ', 'Kyrgyzstan'),
    ('TKM', 'Turkmenistan'),

    # Priority 5: Other Asian
    ('LBN', 'Lebanon'),
    ('SYR', 'Syria'),
    ('IRQ', 'Iraq'),
    ('AFG', 'Afghanistan'),
    ('NPL', 'Nepal'),
    ('CHN', 'China'),
    ('TPE', 'Chinese Taipei'),
    ('HKG', 'Hong Kong'),
]

# Just the key rivals for quick scrape
PRIORITY_COUNTRIES = ASIAN_COUNTRIES[:13]  # Gulf + strong Asian nations


def scrape_all_asian(priority_only=False):
    """Scrape profiles for all Asian countries."""
    countries = PRIORITY_COUNTRIES if priority_only else ASIAN_COUNTRIES

    print("=" * 70)
    print("ASIAN COUNTRIES PROFILE SCRAPER")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Countries to scrape: {len(countries)}")
    print("=" * 70)

    results_summary = []

    for i, (code, name) in enumerate(countries, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(countries)}] SCRAPING: {name} ({code})")
        print(f"{'='*70}")

        start_time = time.time()

        try:
            profiles = scrape_athlete_profiles(country_code=code)
            elapsed = time.time() - start_time

            results_summary.append({
                'country': name,
                'code': code,
                'profiles': len(profiles),
                'time': f"{elapsed:.1f}s",
                'status': 'SUCCESS'
            })

            print(f"\n✓ {name}: {len(profiles)} profiles in {elapsed:.1f}s")

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n✗ {name}: ERROR - {e}")

            results_summary.append({
                'country': name,
                'code': code,
                'profiles': 0,
                'time': f"{elapsed:.1f}s",
                'status': f'ERROR: {str(e)[:50]}'
            })

        # Brief pause between countries to avoid rate limiting
        if i < len(countries):
            print("\nPausing 5 seconds before next country...")
            time.sleep(5)

    # Final summary
    print("\n" + "=" * 70)
    print("SCRAPING COMPLETE - SUMMARY")
    print("=" * 70)
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n{'Country':<25} {'Code':<6} {'Profiles':<10} {'Time':<10} {'Status'}")
    print("-" * 70)

    total_profiles = 0
    for r in results_summary:
        print(f"{r['country']:<25} {r['code']:<6} {r['profiles']:<10} {r['time']:<10} {r['status']}")
        total_profiles += r['profiles']

    print("-" * 70)
    print(f"TOTAL: {total_profiles} profiles from {len(countries)} countries")
    print("=" * 70)

    # Save summary
    summary_file = Path(__file__).parent / "Results" / f"asian_scrape_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"Asian Countries Profile Scrape Summary\n")
        f.write(f"{'='*50}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for r in results_summary:
            f.write(f"{r['country']} ({r['code']}): {r['profiles']} profiles - {r['status']}\n")
        f.write(f"\nTotal: {total_profiles} profiles\n")

    print(f"\nSummary saved to: {summary_file}")

    return results_summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Scrape all Asian country profiles')
    parser.add_argument('--priority-only', '-p', action='store_true',
                        help='Only scrape priority countries (Gulf + key rivals)')

    args = parser.parse_args()

    scrape_all_asian(priority_only=args.priority_only)
