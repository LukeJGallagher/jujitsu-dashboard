"""
Parse HTML bracket data from sportdata.org

Extracts match results including:
- Athlete names
- Countries
- Scores
- Round information
- Winners (determined by score comparison)
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import re
import json
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

BRACKETS_DIR = Path(__file__).parent / "Brackets"
RESULTS_DIR = Path(__file__).parent / "Results"


def parse_bracket_html(html_content):
    """Parse bracket HTML and extract match data."""
    soup = BeautifulSoup(html_content, 'html.parser')

    bracket_data = {
        'event_name': '',
        'category': '',
        'rounds': [],
        'matches': [],
        'athletes': set()
    }

    # Get event/category title
    title_div = soup.find('div', class_='newsheader')
    if title_div:
        h3 = title_div.find('h3')
        if h3:
            title_text = h3.get_text(separator='\n').strip()
            lines = title_text.split('\n')
            if len(lines) >= 2:
                bracket_data['event_name'] = lines[0].strip()
                bracket_data['category'] = lines[1].strip()
            else:
                bracket_data['category'] = title_text

    # Find all rounds
    rounds = soup.find_all('div', class_='tournament-bracket__round')

    for round_div in rounds:
        round_title = round_div.find('h3', class_='tournament-bracket__round-title')
        round_name = round_title.get_text().strip() if round_title else 'Unknown Round'

        bracket_data['rounds'].append(round_name)

        # Find all matches in this round
        # Each li.tournament-bracket__item contains TWO match divs (red vs blue)
        items = round_div.find_all('li', class_='tournament-bracket__item')

        # Process each item as a complete match (contains both corners)
        for i in range(0, len(items), 2):
            # Get two consecutive items (red corner and blue corner)
            red_item = items[i] if i < len(items) else None
            blue_item = items[i + 1] if i + 1 < len(items) else None

            match = {
                'round': round_name,
                'red_corner': extract_competitor(red_item) if red_item else None,
                'blue_corner': extract_competitor(blue_item) if blue_item else None,
                'winner': None
            }

            # Determine winner by score
            if match['red_corner'] and match['blue_corner']:
                red_score = match['red_corner'].get('score', 0) or 0
                blue_score = match['blue_corner'].get('score', 0) or 0

                if red_score > blue_score:
                    match['winner'] = match['red_corner']['name']
                    match['winner_country'] = match['red_corner']['country']
                elif blue_score > red_score:
                    match['winner'] = match['blue_corner']['name']
                    match['winner_country'] = match['blue_corner']['country']

                # Add athletes
                if match['red_corner']['name']:
                    bracket_data['athletes'].add(match['red_corner']['name'])
                if match['blue_corner']['name']:
                    bracket_data['athletes'].add(match['blue_corner']['name'])

            # Only add valid matches
            if match['red_corner'] or match['blue_corner']:
                bracket_data['matches'].append(match)

    # Convert set to list for JSON
    bracket_data['athletes'] = list(bracket_data['athletes'])

    return bracket_data


def extract_competitor(item):
    """Extract competitor info from a bracket item."""
    if not item:
        return None

    competitor = {
        'name': '',
        'country': '',
        'federation': '',
        'score': None
    }

    # Get name from caption_info - could be td or direct class
    caption = item.find('td', class_='tournament-bracket__caption_info')
    if not caption:
        caption = item.find(class_='tournament-bracket__caption_info')

    if caption:
        # Get raw text and clean it
        raw_text = caption.get_text(separator=' ').strip()

        # Remove the federation info part to get just the name
        info_span = caption.find('span', class_='tournament-bracket__caption_info2')
        if info_span:
            info_text = info_span.get_text().strip()
            # Format: "FEDERATION NAME,COUNTRY"
            parts = info_text.rsplit(',', 1)
            if len(parts) == 2:
                competitor['federation'] = parts[0].strip()
                competitor['country'] = parts[1].strip()
            # Remove federation text from name
            raw_text = raw_text.replace(info_text, '').strip()

        # Clean up name - remove extra whitespace and special chars
        name = re.sub(r'\s+', ' ', raw_text).strip()
        # Remove trailing non-name characters
        name = re.sub(r'[\s\u00a0]+$', '', name)
        competitor['name'] = name

    # Get country code from abbr (more reliable)
    abbr = item.find('abbr', class_='tournament-bracket__code')
    if abbr:
        competitor['country'] = abbr.get('title', '') or abbr.get_text().strip()

    # Get score
    score_span = item.find('span', class_='tournament-bracket__number')
    if score_span:
        score_text = score_span.get_text().strip()
        try:
            competitor['score'] = int(score_text)
        except ValueError:
            competitor['score'] = 0

    # Return if we have at least a name or country
    return competitor if (competitor['name'] or competitor['country']) else None


def find_athlete_matches(bracket_data, athlete_name):
    """Find all matches for a specific athlete."""
    athlete_matches = []

    for match in bracket_data.get('matches', []):
        red = match.get('red_corner', {}) or {}
        blue = match.get('blue_corner', {}) or {}

        # Check if athlete is in this match
        athlete_in_red = athlete_name.upper() in (red.get('name', '') or '').upper()
        athlete_in_blue = athlete_name.upper() in (blue.get('name', '') or '').upper()

        if athlete_in_red or athlete_in_blue:
            # Determine if athlete won or lost
            winner = match.get('winner', '')
            athlete_won = athlete_name.upper() in (winner or '').upper()

            # Get opponent info
            if athlete_in_red:
                athlete_info = red
                opponent_info = blue
            else:
                athlete_info = blue
                opponent_info = red

            athlete_matches.append({
                'round': match.get('round', ''),
                'athlete': athlete_info,
                'opponent': opponent_info,
                'won': athlete_won,
                'score': f"{athlete_info.get('score', 0)}-{opponent_info.get('score', 0) if opponent_info else 0}"
            })

    return athlete_matches


def format_bracket_summary(bracket_data):
    """Format bracket data for display."""
    lines = []

    lines.append(f"Event: {bracket_data.get('event_name', 'Unknown')}")
    lines.append(f"Category: {bracket_data.get('category', 'Unknown')}")
    lines.append(f"Total Athletes: {len(bracket_data.get('athletes', []))}")
    lines.append(f"Total Matches: {len(bracket_data.get('matches', []))}")
    lines.append("")

    # Group matches by round
    rounds = {}
    for match in bracket_data.get('matches', []):
        round_name = match.get('round', 'Unknown')
        if round_name not in rounds:
            rounds[round_name] = []
        rounds[round_name].append(match)

    for round_name, matches in rounds.items():
        lines.append(f"\n=== {round_name} ===")
        for match in matches:
            red = match.get('red_corner', {}) or {}
            blue = match.get('blue_corner', {}) or {}

            red_name = red.get('name', 'BYE') or 'BYE'
            red_country = red.get('country', '') or ''
            red_score = red.get('score', '-') if red.get('score') is not None else '-'

            blue_name = blue.get('name', 'BYE') or 'BYE'
            blue_country = blue.get('country', '') or ''
            blue_score = blue.get('score', '-') if blue.get('score') is not None else '-'

            winner = match.get('winner', '')
            winner_marker = ''
            if winner and winner == red_name:
                winner_marker = ' [W]'

            lines.append(f"  {red_name} ({red_country}) [{red_score}]{winner_marker}")

            winner_marker = ''
            if winner and winner == blue_name:
                winner_marker = ' [W]'
            lines.append(f"  vs {blue_name} ({blue_country}) [{blue_score}]{winner_marker}")
            lines.append("")

    return '\n'.join(lines)


def parse_all_brackets(verid_filter=None):
    """Parse all bracket HTML files and save to all_matches.json."""
    all_data = {
        'parsed_at': datetime.now().isoformat(),
        'events': {},
        'all_matches': [],
        'total_matches': 0
    }

    # Get bracket files
    pattern = f"bracket_{verid_filter}_*.html" if verid_filter else "bracket_*.html"
    bracket_files = list(BRACKETS_DIR.glob(pattern))

    print(f"Found {len(bracket_files)} bracket files")

    for bf in bracket_files:
        # Parse filename: bracket_verid_catid.html
        parts = bf.stem.split('_')
        if len(parts) < 3:
            continue

        verid = parts[1]
        catid = parts[2]

        try:
            with open(bf, 'r', encoding='utf-8') as f:
                html = f.read()

            parsed = parse_bracket_html(html)

            # Initialize event if needed
            if verid not in all_data['events']:
                all_data['events'][verid] = {
                    'verid': verid,
                    'event_name': parsed.get('event_name', f'Event {verid}'),
                    'categories': []
                }

            # Update event name if found
            if parsed.get('event_name'):
                all_data['events'][verid]['event_name'] = parsed['event_name']

            # Add category data
            category_data = {
                'catid': catid,
                'category': parsed.get('category', f'Category {catid}'),
                'rounds': parsed.get('rounds', []),
                'matches': parsed.get('matches', []),
                'athletes': parsed.get('athletes', [])
            }

            all_data['events'][verid]['categories'].append(category_data)

            # Add to all_matches flat list
            for match in parsed.get('matches', []):
                match_entry = {
                    'event': parsed.get('event_name', ''),
                    'verid': verid,
                    'category': parsed.get('category', ''),
                    'catid': catid,
                    **match
                }
                all_data['all_matches'].append(match_entry)

            all_data['total_matches'] += len(parsed.get('matches', []))

        except Exception as e:
            print(f"Error parsing {bf.name}: {e}")

    # Convert events dict to list
    all_data['events'] = list(all_data['events'].values())

    return all_data


def main():
    """Parse and display bracket from saved HTML file."""
    import argparse

    parser = argparse.ArgumentParser(description='Parse bracket HTML files')
    parser.add_argument('--all', action='store_true', help='Parse all bracket files')
    parser.add_argument('--verid', type=str, help='Parse specific event verid')
    args = parser.parse_args()

    if args.all or args.verid:
        # Parse all brackets
        print("=" * 60)
        print("PARSING ALL BRACKETS")
        print("=" * 60)

        all_data = parse_all_brackets(args.verid)

        # Save to all_matches.json
        output_file = RESULTS_DIR / "all_matches.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)

        print(f"\nSaved to: {output_file}")
        print(f"Events: {len(all_data['events'])}")
        print(f"Total matches: {all_data['total_matches']}")
        return

    # Default: parse single file
    bracket_files = list(BRACKETS_DIR.glob('*.html'))
    if not bracket_files:
        print("No bracket HTML files found in Brackets/")
        return

    # Sort by modification time
    bracket_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    print(f"Found {len(bracket_files)} bracket files")
    print(f"Parsing: {bracket_files[0].name}")

    with open(bracket_files[0], 'r', encoding='utf-8') as f:
        html_content = f.read()

    bracket_data = parse_bracket_html(html_content)

    # Print summary
    print("\n" + "=" * 60)
    print(format_bracket_summary(bracket_data))

    # Save parsed data
    output_file = RESULTS_DIR / f"parsed_bracket_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(bracket_data, f, indent=2, ensure_ascii=False)

    print(f"\nParsed data saved to: {output_file}")

    # Demo: Find matches for a specific athlete
    if bracket_data.get('athletes'):
        sample_athlete = bracket_data['athletes'][0]
        print(f"\n--- Sample: Matches for {sample_athlete} ---")
        matches = find_athlete_matches(bracket_data, sample_athlete)
        for m in matches:
            result = "WON" if m['won'] else "LOST"
            opp = m['opponent']
            opp_name = opp.get('name', 'Unknown') if opp else 'BYE'
            print(f"  {m['round']}: {result} vs {opp_name} ({m['score']})")


if __name__ == "__main__":
    main()
