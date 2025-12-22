"""
Batch Asian Events Scraper
==========================
Scrapes all verified Asian events from verified_asian_events.json.
Opens browser for CAPTCHA solving, then automatically scrapes categories and brackets.

Usage:
    python batch_asian_scraper.py              # Scrape all unscraped events
    python batch_asian_scraper.py --limit 5    # Scrape first 5 unscraped events
    python batch_asian_scraper.py --verid 814  # Scrape specific event
    python batch_asian_scraper.py --status     # Show scraping status
"""

import json
import time
import re
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "Results"
BRACKETS_DIR = BASE_DIR / "Brackets"
RESULTS_DIR.mkdir(exist_ok=True)
BRACKETS_DIR.mkdir(exist_ok=True)

BASE_URL = "https://www.sportdata.org/ju-jitsu/set-online"
VERIFIED_EVENTS_FILE = BASE_DIR / "verified_asian_events.json"


def load_verified_events():
    """Load verified Asian events."""
    if VERIFIED_EVENTS_FILE.exists():
        with open(VERIFIED_EVENTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('events', [])
    return []


def save_verified_events(events):
    """Save verified Asian events with updated status."""
    data = {
        "_comment": "Verified Asian event verids from sportdata.org - provided by user 2025-12-10",
        "_instructions": "Use batch_asian_scraper.py to scrape these events",
        "_total_events": len(events),
        "events": events
    }
    with open(VERIFIED_EVENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_scraped_verids():
    """Get list of already scraped verids."""
    scraped = set()
    for f in RESULTS_DIR.glob("brackets_*_*.json"):
        match = re.search(r'brackets_(\d+)_', f.name)
        if match:
            scraped.add(match.group(1))
    return scraped


def wait_for_captcha_or_content(page, timeout=300):
    """Wait for CAPTCHA to be solved or content to appear."""
    print("  Checking page...", flush=True)
    start = time.time()

    while time.time() - start < timeout:
        try:
            content = page.content()
        except:
            time.sleep(2)
            continue

        # Check for CAPTCHA
        if 'verify you are' in content.lower():
            elapsed = int(time.time() - start)
            if elapsed == 0 or elapsed % 15 == 0:
                print(f"  CAPTCHA detected - please solve in browser... ({elapsed}s)", flush=True)
            time.sleep(1)
            continue

        # Check for actual content
        has_content = page.evaluate('''() => {
            const catLinks = document.querySelectorAll('a[href*="catid="]');
            const tables = document.querySelectorAll('table');
            return catLinks.length > 0 || tables.length > 5;
        }''')

        if has_content:
            print("  Content loaded!", flush=True)
            return True

        time.sleep(1)

    print("  Timeout", flush=True)
    return False


def extract_event_name(page):
    """Extract event name from page."""
    try:
        title = page.evaluate('() => document.title')
        # Clean up title
        name = title.replace('SET Online Ju-Jitsu:', '').strip()
        if not name or name == 'SET Online Ju-Jitsu':
            h1 = page.evaluate('() => document.querySelector("h1")?.textContent || ""')
            name = h1.strip() if h1 else "Unknown Event"
        return name
    except:
        return "Unknown Event"


def get_categories(page, verid):
    """Extract categories from the event page."""
    # Go to category list page
    cat_url = f"{BASE_URL}/veranstaltung_info_main.php?active_menu=calendar&vernr={verid}&ver_info_action=catauslist#a_eventheadend"
    print(f"  Loading categories: vernr={verid}", flush=True)

    page.goto(cat_url, wait_until='domcontentloaded')
    page.wait_for_timeout(2000)

    if not wait_for_captcha_or_content(page):
        return []

    # Extract categories
    categories = page.evaluate('''() => {
        const cats = [];
        const seen = new Set();

        document.querySelectorAll('a[href*="catid="]').forEach(link => {
            const href = link.href || link.getAttribute('href') || '';
            const catMatch = href.match(/catid=(\\d+)/);

            if (catMatch) {
                const catid = catMatch[1];
                if (seen.has(catid)) return;
                seen.add(catid);

                const name = link.textContent.trim();
                if (name && name.length > 2) {
                    cats.push({
                        catid: catid,
                        name: name
                    });
                }
            }
        });

        return cats;
    }''')

    print(f"  Found {len(categories)} categories")
    return categories


def scrape_bracket(page, verid, catid, cat_name):
    """Scrape a single bracket."""
    url = f"{BASE_URL}/popup_mitschrift_main.php?popup_action=mitschriftcatxml&catid={catid}&verid={verid}"

    try:
        page.goto(url, wait_until='domcontentloaded', timeout=30000)
        page.wait_for_timeout(2000)

        content = page.content()

        # Check for CAPTCHA
        if 'verify you are' in content.lower():
            print(" [CAPTCHA]", end="", flush=True)
            if not wait_for_captcha_or_content(page, timeout=120):
                return None
            content = page.content()

        # Save bracket HTML
        html_file = BRACKETS_DIR / f"bracket_{verid}_{catid}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)

        # Extract competitors
        competitors = page.evaluate('''() => {
            const comps = [];
            const cells = document.querySelectorAll('.tournament-bracket__caption_info, td');

            cells.forEach(cell => {
                const text = cell.textContent.trim();
                // Look for country code pattern
                const match = text.match(/([A-Z]{3})\\s*$/);
                if (match) {
                    const name = text.replace(match[0], '').replace(/,/g, '').trim();
                    if (name.length > 2) {
                        comps.push({ name: name, country: match[1] });
                    }
                }
            });

            return [...new Map(comps.map(c => [c.name, c])).values()];
        }''')

        return {
            'catid': catid,
            'category': cat_name,
            'html_saved': str(html_file),
            'competitors': competitors
        }

    except Exception as e:
        print(f" [Error: {e}]")
        return None


def scrape_event(page, verid):
    """Scrape all brackets for an event."""
    print(f"\n{'='*60}")
    print(f"SCRAPING EVENT: verid={verid}")
    print(f"{'='*60}")

    # First go to event page to get name
    event_url = f"{BASE_URL}/veranstaltung_info_main.php?active_menu=calendar&vernr={verid}#a_eventhead"
    page.goto(event_url, wait_until='domcontentloaded')
    page.wait_for_timeout(2000)

    if not wait_for_captcha_or_content(page):
        return None

    event_name = extract_event_name(page)
    print(f"Event: {event_name}")

    # Get categories
    categories = get_categories(page, verid)

    if not categories:
        print("No categories found!")
        return None

    # Scrape each bracket
    results = {
        'verid': verid,
        'event_name': event_name,
        'scraped_at': datetime.now().isoformat(),
        'categories': []
    }

    for i, cat in enumerate(categories, 1):
        catid = cat['catid']
        name = cat['name'][:40] + "..." if len(cat['name']) > 40 else cat['name']

        print(f"  [{i}/{len(categories)}] {name}", end=" ", flush=True)

        result = scrape_bracket(page, verid, catid, cat['name'])
        if result:
            results['categories'].append(result)
            n = len(result.get('competitors', []))
            print(f"OK ({n} competitors)")
        else:
            print("FAILED")

        page.wait_for_timeout(500)

    # Save results
    output = RESULTS_DIR / f"brackets_{verid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved: {output.name}")
    print(f"Categories: {len(results['categories'])}")

    return results


def show_status():
    """Show scraping status."""
    events = load_verified_events()
    scraped = get_scraped_verids()

    print("=" * 60)
    print("ASIAN EVENTS SCRAPING STATUS")
    print("=" * 60)

    not_scraped = []
    already_scraped = []

    for event in events:
        verid = event['verid']
        if verid in scraped:
            already_scraped.append(verid)
        else:
            not_scraped.append(verid)

    print(f"\nTotal verified events: {len(events)}")
    print(f"Already scraped: {len(already_scraped)}")
    print(f"Not yet scraped: {len(not_scraped)}")

    if not_scraped:
        print(f"\nNot scraped verids: {', '.join(not_scraped[:20])}")
        if len(not_scraped) > 20:
            print(f"  ... and {len(not_scraped) - 20} more")

    print("\nTo scrape:")
    print("  python batch_asian_scraper.py --limit 5  # First 5 unscraped")
    print("  python batch_asian_scraper.py --verid 814  # Specific event")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Batch Asian Events Scraper')
    parser.add_argument('--status', action='store_true', help='Show scraping status')
    parser.add_argument('--limit', type=int, default=0, help='Max events to scrape (0=all)')
    parser.add_argument('--verid', type=str, help='Scrape specific event')

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    events = load_verified_events()
    scraped = get_scraped_verids()

    # Filter to unscraped events
    if args.verid:
        to_scrape = [e for e in events if e['verid'] == args.verid]
    else:
        to_scrape = [e for e in events if e['verid'] not in scraped]

    if not to_scrape:
        print("No events to scrape!")
        show_status()
        return

    if args.limit > 0:
        to_scrape = to_scrape[:args.limit]

    print("=" * 60)
    print(f"BATCH ASIAN EVENTS SCRAPER")
    print(f"Events to scrape: {len(to_scrape)}")
    print("=" * 60)

    with sync_playwright() as p:
        print("\nLaunching browser...", flush=True)
        browser = p.chromium.launch(
            headless=False,
            args=['--start-maximized', '--window-position=100,100']
        )
        context = browser.new_context(
            viewport={'width': 1400, 'height': 900},
            no_viewport=True
        )
        page = context.new_page()

        try:
            for i, event in enumerate(to_scrape, 1):
                verid = event['verid']

                print(f"\n{'#'*60}")
                print(f"# [{i}/{len(to_scrape)}] verid={verid}")
                print(f"{'#'*60}")

                result = scrape_event(page, verid)

                if result:
                    # Update status in verified events
                    for e in events:
                        if e['verid'] == verid:
                            e['status'] = 'scraped'
                            e['name'] = result.get('event_name', 'Unknown')
                            break
                    save_verified_events(events)

                # Brief pause between events
                time.sleep(2)

        finally:
            print("\nClosing browser...")
            context.close()
            browser.close()

    print("\nDone!")
    show_status()


if __name__ == "__main__":
    main()
