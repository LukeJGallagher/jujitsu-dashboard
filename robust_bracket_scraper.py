"""
Robust Bracket Scraper
======================
Fixed version that properly handles CAPTCHA and extracts categories.
"""
import sys
import os

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import re
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "Results"
BRACKETS_DIR = BASE_DIR / "Brackets"
RESULTS_DIR.mkdir(exist_ok=True)
BRACKETS_DIR.mkdir(exist_ok=True)

BASE_URL = "https://www.sportdata.org/ju-jitsu/set-online"


def wait_for_captcha(page, timeout=600, target_url=None):
    """Wait for CAPTCHA to be solved and content to load.

    Args:
        page: Playwright page object
        timeout: Max seconds to wait
        target_url: URL to navigate back to after CAPTCHA is solved

    Returns:
        True if content loaded, False if timeout
    """
    print("Checking for CAPTCHA...", flush=True)

    start = time.time()
    captcha_was_detected = False

    while time.time() - start < timeout:
        try:
            content = page.content()
        except Exception as e:
            # Page is navigating, wait and retry
            if 'navigating' in str(e).lower():
                print("  Page navigating, waiting...", flush=True)
                time.sleep(2)
                continue
            raise

        # Check if we're on CAPTCHA page
        is_captcha = ('verify you are' in content.lower() or
                      ('recaptcha' in content.lower() and
                       'Please verify you are not a robot' in content))

        if is_captcha:
            captcha_was_detected = True
            elapsed = int(time.time() - start)
            if elapsed == 0 or elapsed % 10 == 0:
                print(f"  CAPTCHA detected - solve in browser... ({elapsed}s)", flush=True)
            time.sleep(1)
            continue

        # CAPTCHA was solved - need to navigate back to target URL
        if captcha_was_detected and target_url:
            print(f"  CAPTCHA solved! Re-navigating to target URL...", flush=True)
            time.sleep(2)  # Brief pause
            page.goto(target_url, wait_until='domcontentloaded')
            page.wait_for_timeout(3000)
            captcha_was_detected = False  # Reset so we don't loop forever
            continue

        # No CAPTCHA - check if we have actual content
        try:
            has_content = page.evaluate('''() => {
                // Check for category links
                const catLinks = document.querySelectorAll('a[href*="catid="]');
                if (catLinks.length > 0) return {type: 'categories', count: catLinks.length};

                // Check for bracket content
                const brackets = document.querySelectorAll('.bracket, .draw, .outline_draw');
                if (brackets.length > 0) return {type: 'brackets', count: brackets.length};

                // Check for any vernr links (event page)
                const eventLinks = document.querySelectorAll('a[href*="vernr="]');
                if (eventLinks.length > 0) return {type: 'events', count: eventLinks.length};

                return null;
            }''')

            if has_content:
                print(f"  Content loaded: {has_content['type']} ({has_content['count']} items)", flush=True)
                return True
        except Exception as e:
            if 'navigating' in str(e).lower():
                time.sleep(2)
                continue
            raise

        # Wait a bit more for AJAX
        time.sleep(1)

    print("  Timeout waiting for content", flush=True)
    return False


def get_categories(page, verid):
    """Extract categories from the event page."""
    # Step 1: Go to the event page first (not catauslist)
    event_url = f"{BASE_URL}/veranstaltung_info_main.php?active_menu=calendar&vernr={verid}#a_eventhead"
    print(f"\nStep 1: Loading event page: {event_url}", flush=True)

    page.goto(event_url, wait_until='domcontentloaded')
    page.wait_for_timeout(2000)

    # Wait for CAPTCHA to be solved - after solving, navigate to catauslist
    cat_url = f"{BASE_URL}/veranstaltung_info_main.php?active_menu=calendar&vernr={verid}&ver_info_action=catauslist#a_eventheadend"
    if not wait_for_captcha(page, target_url=cat_url):
        return []

    # Step 2: Now we should be on the category list page
    # Check the page title to make sure we're on the right event
    title = page.evaluate('() => document.title')
    print(f"  Page title: {title}")

    # Verify we're on the correct event - sportdata often redirects to wrong event after CAPTCHA
    current_url = page.url
    if f'vernr={verid}' not in current_url:
        print(f"  WARNING: Wrong event loaded! Current URL: {current_url}")
        print(f"  Attempting to force navigation to verid={verid}...")

        # Try multiple navigation attempts
        for attempt in range(3):
            print(f"  Navigation attempt {attempt + 1}/3...")
            page.goto(cat_url, wait_until='domcontentloaded')
            page.wait_for_timeout(4000)

            # Check if CAPTCHA appeared again
            content = page.content()
            if 'verify you are' in content.lower():
                print(f"  CAPTCHA appeared again - please solve it...")
                if not wait_for_captcha(page, timeout=120):
                    continue

            # Check if we got the right event now
            new_title = page.evaluate('() => document.title')
            print(f"  New page title: {new_title}")

            # Look for category links to verify success
            cat_count = page.evaluate('() => document.querySelectorAll("a[href*=\\"catid=\\"]").length')
            if cat_count > 0:
                print(f"  SUCCESS! Found {cat_count} category links")
                break
        else:
            print(f"  FAILED: Could not navigate to correct event after 3 attempts")

    # Save debug HTML
    html = page.content()
    debug_file = RESULTS_DIR / f"categories_debug_{verid}.html"
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  Saved debug HTML: {debug_file.name}")

    # Extract categories using multiple methods
    categories = page.evaluate('''() => {
        const cats = [];
        const seen = new Set();

        // Method 1: Links with catid parameter
        document.querySelectorAll('a[href*="catid="]').forEach(link => {
            const href = link.href || link.getAttribute('href') || '';
            const catMatch = href.match(/catid=(\d+)/);
            const verMatch = href.match(/verid=(\d+)/);

            if (catMatch) {
                const catid = catMatch[1];
                if (seen.has(catid)) return;
                seen.add(catid);

                const name = link.textContent.trim();
                if (name && name.length > 2) {
                    cats.push({
                        catid: catid,
                        name: name,
                        verid: verMatch ? verMatch[1] : null
                    });
                }
            }
        });

        // Method 2: onclick handlers with catid
        if (cats.length === 0) {
            document.querySelectorAll('[onclick*="catid"]').forEach(el => {
                const onclick = el.getAttribute('onclick') || '';
                const catMatch = onclick.match(/catid[=:]?\s*(\d+)/i);
                if (catMatch) {
                    const catid = catMatch[1];
                    if (seen.has(catid)) return;
                    seen.add(catid);

                    const name = el.textContent.trim();
                    if (name) {
                        cats.push({catid, name, verid: null});
                    }
                }
            });
        }

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

        # Check for CAPTCHA
        content = page.content()
        if 'verify you are' in content.lower():
            print(" [CAPTCHA]", end="", flush=True)
            if not wait_for_captcha(page, timeout=300, target_url=url):
                return None
            content = page.content()

        # Save bracket HTML
        html_file = BRACKETS_DIR / f"bracket_{verid}_{catid}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)

        # Extract competitor data
        competitors = page.evaluate('''() => {
            const comps = [];

            // Look for competitor names in bracket cells
            const cells = document.querySelectorAll('td[class*="name"], .competitor, .athlete-name, td');
            cells.forEach(cell => {
                const text = cell.textContent.trim();
                // Look for patterns like "Name (COUNTRY)"
                const match = text.match(/^([^(]+)\s*\(([A-Z]{3})\)/);
                if (match) {
                    comps.push({
                        name: match[1].trim(),
                        country: match[2]
                    });
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
        print(f" [Error: {e}]", end="", flush=True)
        return None


def scrape_event(verid, skip_existing=True):
    """Scrape all brackets for an event."""
    print("\n" + "=" * 70)
    print(f"SCRAPING EVENT: verid={verid}")
    print("=" * 70)

    # Check for existing data
    existing = list(RESULTS_DIR.glob(f"brackets_{verid}_*.json"))
    if existing and skip_existing:
        print(f"Already scraped: {existing[0].name}")
        print("Use --force to re-scrape")
        return None

    results = {
        'verid': verid,
        'scraped_at': datetime.now().isoformat(),
        'categories': []
    }

    with sync_playwright() as p:
        print("Launching browser...", flush=True)
        print(">>> LOOK FOR THE CHROMIUM BROWSER WINDOW <<<", flush=True)
        browser = p.chromium.launch(
            headless=False,
            args=['--start-maximized', '--window-position=100,100']
        )
        context = browser.new_context(
            viewport={'width': 1400, 'height': 900},
            no_viewport=True  # Use full window size
        )
        page = context.new_page()

        try:
            # Get categories
            categories = get_categories(page, verid)

            if not categories:
                print("\nNo categories found!")
                print("Check the debug HTML file for page structure")
                return None

            print(f"\nWill scrape {len(categories)} categories")
            print("-" * 50)

            # Scrape each category
            for i, cat in enumerate(categories, 1):
                catid = cat['catid']
                name = cat['name'][:40] + "..." if len(cat['name']) > 40 else cat['name']

                print(f"[{i}/{len(categories)}] {name}", end=" ", flush=True)

                result = scrape_bracket(page, verid, catid, cat['name'])

                if result:
                    results['categories'].append(result)
                    n_comps = len(result.get('competitors', []))
                    print(f" OK ({n_comps} competitors)")
                else:
                    print(" FAILED")

                # Rate limit
                page.wait_for_timeout(500)

                # Save progress periodically
                if i % 20 == 0:
                    progress_file = RESULTS_DIR / f"brackets_{verid}_progress.json"
                    with open(progress_file, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2, ensure_ascii=False)
                    print(f"  [Progress saved: {len(results['categories'])} categories]")

        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()

        finally:
            context.close()
            browser.close()

    # Save final results
    if results['categories']:
        output_file = RESULTS_DIR / f"brackets_{verid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n{'=' * 50}")
        print(f"COMPLETED: {output_file.name}")
        print(f"Categories scraped: {len(results['categories'])}")

        # Count competitors
        total_comps = sum(len(c.get('competitors', [])) for c in results['categories'])
        print(f"Total competitors: {total_comps}")

    return results


def load_mappings():
    """Load event mappings."""
    mappings_file = BASE_DIR / "event_mappings.json"
    if mappings_file.exists():
        with open(mappings_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def list_events():
    """List events available to scrape."""
    mappings = load_mappings()

    print("=" * 70)
    print("EVENTS AVAILABLE TO SCRAPE")
    print("=" * 70)

    # Group by scrape status
    not_scraped = []
    scraped = []

    for name, verid in sorted(mappings.items(), key=lambda x: x[1]):
        existing = list(RESULTS_DIR.glob(f"brackets_{verid}_*.json"))
        if existing:
            # Check if it has actual data
            try:
                with open(existing[0], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    n_cats = len(data.get('categories', []))
                    scraped.append((verid, name, n_cats))
            except:
                scraped.append((verid, name, 0))
        else:
            not_scraped.append((verid, name))

    print(f"\n--- NOT YET SCRAPED ({len(not_scraped)}) ---")
    for verid, name in not_scraped[:20]:
        print(f"  [{verid}] {name[:60]}")
    if len(not_scraped) > 20:
        print(f"  ... and {len(not_scraped) - 20} more")

    print(f"\n--- ALREADY SCRAPED ({len(scraped)}) ---")
    for verid, name, n_cats in scraped[:10]:
        print(f"  [{verid}] {name[:50]} ({n_cats} categories)")

    return not_scraped


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Robust Bracket Scraper')
    parser.add_argument('--list', action='store_true', help='List available events')
    parser.add_argument('--scrape', metavar='VERID', help='Scrape specific event')
    parser.add_argument('--scrape-all', action='store_true', help='Scrape all unmapped events')
    parser.add_argument('--force', action='store_true', help='Re-scrape even if data exists')

    args = parser.parse_args()

    if args.list:
        not_scraped = list_events()
        if not_scraped:
            print(f"\nTo scrape an event: python robust_bracket_scraper.py --scrape VERID")
            print(f"To scrape all: python robust_bracket_scraper.py --scrape-all")

    elif args.scrape:
        scrape_event(args.scrape, skip_existing=not args.force)

    elif args.scrape_all:
        not_scraped = list_events()
        if not not_scraped:
            print("\nAll events already scraped!")
            return

        print(f"\nWill scrape {len(not_scraped)} events")
        input("Press ENTER to start...")

        for verid, name in not_scraped:
            print(f"\n{'#' * 70}")
            print(f"# {name[:60]}")
            print(f"{'#' * 70}")
            scrape_event(verid, skip_existing=not args.force)
            time.sleep(2)

    else:
        list_events()
        print("\nUsage:")
        print("  --list          List available events")
        print("  --scrape VERID  Scrape specific event")
        print("  --scrape-all    Scrape all unscraped events")
        print("  --force         Re-scrape even if data exists")


if __name__ == "__main__":
    main()
