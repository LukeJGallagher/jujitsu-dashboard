"""
Loss Chain Analyzer
====================
Analyzes bracket data to identify beatable opponents for Team Saudi.

Key concept: If Athlete A lost to Athlete B, and Saudi athlete beat Athlete B,
then Athlete A is potentially beatable by Saudi.

Usage:
    python loss_chain_analyzer.py --category "94kg Male"
    python loss_chain_analyzer.py --saudi "Omar Nada"
    python loss_chain_analyzer.py --all
"""
import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "Results"
PROFILES_DIR = BASE_DIR / "Profiles"

# Saudi country codes
SAUDI_CODES = {'KSA', 'SAU', 'SAUDI'}

# Asian countries for scouting focus
ASIAN_COUNTRIES = {
    'KSA', 'SAU', 'UAE', 'KAZ', 'UZB', 'JPN', 'KOR', 'CHN', 'MNG', 'MGL',
    'THA', 'VIE', 'INA', 'MAS', 'SGP', 'PHI', 'IND', 'PAK', 'IRN', 'IRI',
    'JOR', 'KUW', 'BRN', 'QAT', 'OMA', 'YEM', 'SYR', 'LBN', 'IRQ'
}


@dataclass
class MatchResult:
    """Single match result."""
    winner: str
    winner_country: str
    loser: str
    loser_country: str
    score: Optional[str] = None
    event: Optional[str] = None
    category: Optional[str] = None
    round: Optional[str] = None
    date: Optional[str] = None


@dataclass
class AthleteRecord:
    """Athlete's complete win/loss record."""
    name: str
    country: str
    wins: List[MatchResult] = field(default_factory=list)
    losses: List[MatchResult] = field(default_factory=list)

    @property
    def win_rate(self) -> float:
        total = len(self.wins) + len(self.losses)
        return len(self.wins) / total if total > 0 else 0.0

    @property
    def total_matches(self) -> int:
        return len(self.wins) + len(self.losses)


@dataclass
class ScoutingTarget:
    """Potential scouting target for Saudi athlete."""
    opponent_name: str
    opponent_country: str
    beatability_score: float
    reasoning: List[str]
    key_losses: List[Dict]
    shared_opponents: List[str]
    recent_form: str  # "improving", "stable", "declining"
    world_rank: Optional[int] = None


class LossChainAnalyzer:
    """Analyze loss chains to find beatable opponents."""

    def __init__(self):
        self.matches: List[MatchResult] = []
        self.athlete_records: Dict[str, AthleteRecord] = {}
        self.loss_graph: Dict[str, Set[str]] = defaultdict(set)  # who_lost -> {who_beat_them}
        self.win_graph: Dict[str, Set[str]] = defaultdict(set)   # who_won -> {who_they_beat}

    def load_matches(self, filepath: Path = None) -> int:
        """Load match data from JSON file."""
        filepath = filepath or RESULTS_DIR / "all_matches.json"

        if not filepath.exists():
            print(f"Match file not found: {filepath}")
            return 0

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        count = 0
        for event in data.get('events', []):
            event_name = event.get('event_name', '')
            verid = event.get('verid', '')

            for category in event.get('categories', []):
                cat_name = category.get('category', '')

                for match in category.get('matches', []):
                    red = match.get('red_corner', {})
                    blue = match.get('blue_corner', {})
                    winner = match.get('winner', '')

                    if not winner or not red.get('name') or not blue.get('name'):
                        continue

                    # Determine loser
                    if winner == red.get('name'):
                        loser = blue.get('name')
                        loser_country = blue.get('country', '')
                        winner_country = red.get('country', '')
                    else:
                        loser = red.get('name')
                        loser_country = red.get('country', '')
                        winner_country = blue.get('country', '')

                    # Create match result
                    result = MatchResult(
                        winner=winner,
                        winner_country=winner_country,
                        loser=loser,
                        loser_country=loser_country,
                        score=f"{red.get('score', 0)}-{blue.get('score', 0)}",
                        event=event_name,
                        category=cat_name,
                        round=match.get('round', 'Unknown')
                    )

                    self.matches.append(result)
                    self._update_records(result)
                    count += 1

        print(f"Loaded {count} matches from {filepath.name}")
        return count

    def _update_records(self, match: MatchResult):
        """Update athlete records and graphs."""
        # Update winner record
        if match.winner not in self.athlete_records:
            self.athlete_records[match.winner] = AthleteRecord(
                name=match.winner,
                country=match.winner_country
            )
        self.athlete_records[match.winner].wins.append(match)

        # Update loser record
        if match.loser not in self.athlete_records:
            self.athlete_records[match.loser] = AthleteRecord(
                name=match.loser,
                country=match.loser_country
            )
        self.athlete_records[match.loser].losses.append(match)

        # Update graphs
        self.loss_graph[match.loser].add(match.winner)
        self.win_graph[match.winner].add(match.loser)

    def get_saudi_athletes(self) -> List[AthleteRecord]:
        """Get all Saudi athletes from records."""
        saudi = []
        for name, record in self.athlete_records.items():
            if record.country.upper() in SAUDI_CODES:
                saudi.append(record)
        return sorted(saudi, key=lambda x: -x.total_matches)

    def get_asian_opponents(self, category: str = None) -> List[AthleteRecord]:
        """Get Asian athletes (excluding Saudi) for scouting."""
        opponents = []
        for name, record in self.athlete_records.items():
            if record.country.upper() in ASIAN_COUNTRIES:
                if record.country.upper() not in SAUDI_CODES:
                    if category is None or self._athlete_in_category(name, category):
                        opponents.append(record)
        return opponents

    def _athlete_in_category(self, athlete_name: str, category: str) -> bool:
        """Check if athlete competed in given category."""
        for match in self.matches:
            if (match.winner == athlete_name or match.loser == athlete_name):
                if category.lower() in match.category.lower():
                    return True
        return False

    def find_shared_opponents(self, saudi_name: str, opponent_name: str) -> List[str]:
        """Find athletes both Saudi and opponent have faced."""
        saudi_faced = self.win_graph.get(saudi_name, set()) | self.loss_graph.get(saudi_name, set())
        opp_faced = self.win_graph.get(opponent_name, set()) | self.loss_graph.get(opponent_name, set())
        return list(saudi_faced & opp_faced)

    def calculate_beatability(self, saudi_record: AthleteRecord,
                              opponent_record: AthleteRecord) -> ScoutingTarget:
        """Calculate how beatable an opponent is for a Saudi athlete."""

        reasoning = []
        score = 0.0

        # 1. Shared losses - opponent lost to someone Saudi beat
        saudi_victims = self.win_graph.get(saudi_record.name, set())
        opponent_losses_to = self.loss_graph.get(opponent_record.name, set())
        shared_losses = saudi_victims & opponent_losses_to

        if shared_losses:
            score += 0.3 * len(shared_losses)
            for loser in shared_losses:
                reasoning.append(f"Lost to {loser} - whom {saudi_record.name} has beaten")

        # 2. Win rate comparison
        if saudi_record.win_rate > opponent_record.win_rate:
            diff = saudi_record.win_rate - opponent_record.win_rate
            score += 0.2 * diff
            reasoning.append(f"Lower win rate ({opponent_record.win_rate:.0%} vs {saudi_record.win_rate:.0%})")

        # 3. Recent form (using last 3 matches)
        recent_losses = opponent_record.losses[-3:] if len(opponent_record.losses) >= 3 else opponent_record.losses
        recent_wins = opponent_record.wins[-3:] if len(opponent_record.wins) >= 3 else opponent_record.wins

        if len(recent_losses) > len(recent_wins):
            score += 0.15
            form = "declining"
            reasoning.append(f"Recent form declining ({len(recent_losses)} losses in recent matches)")
        elif len(recent_wins) > len(recent_losses):
            form = "improving"
        else:
            form = "stable"

        # 4. Experience gap (if Saudi has more matches)
        if saudi_record.total_matches > opponent_record.total_matches:
            score += 0.1
            reasoning.append(f"Less experienced ({opponent_record.total_matches} vs {saudi_record.total_matches} matches)")

        # 5. Check for close losses (opponent lost narrowly = potentially beatable)
        close_losses = []
        for loss in opponent_record.losses:
            if loss.score:
                try:
                    parts = loss.score.split('-')
                    if len(parts) == 2:
                        s1, s2 = int(parts[0]), int(parts[1])
                        diff = abs(s1 - s2)
                        if diff <= 3:  # Close match
                            close_losses.append({
                                'to': loss.winner,
                                'score': loss.score,
                                'event': loss.event
                            })
                except:
                    pass

        if close_losses:
            score += 0.1 * min(len(close_losses), 3)
            reasoning.append(f"Has {len(close_losses)} close losses (competitive but beatable)")

        # Get key losses for scouting
        key_losses = []
        for loss in opponent_record.losses[-5:]:  # Last 5 losses
            key_losses.append({
                'to': loss.winner,
                'country': loss.winner_country,
                'score': loss.score,
                'event': loss.event,
                'round': loss.round
            })

        shared = self.find_shared_opponents(saudi_record.name, opponent_record.name)

        return ScoutingTarget(
            opponent_name=opponent_record.name,
            opponent_country=opponent_record.country,
            beatability_score=min(score, 1.0),  # Cap at 1.0
            reasoning=reasoning,
            key_losses=key_losses,
            shared_opponents=shared,
            recent_form=form
        )

    def generate_scouting_report(self, saudi_name: str = None,
                                  category: str = None) -> Dict:
        """Generate scouting report for Saudi athlete(s)."""

        report = {
            'generated_at': datetime.now().isoformat(),
            'total_matches_analyzed': len(self.matches),
            'scouting_reports': []
        }

        # Get Saudi athletes to analyze
        if saudi_name:
            saudi_athletes = [r for r in self.get_saudi_athletes()
                           if saudi_name.lower() in r.name.lower()]
        else:
            saudi_athletes = self.get_saudi_athletes()

        if not saudi_athletes:
            print(f"No Saudi athletes found matching: {saudi_name}")
            return report

        # Get Asian opponents
        opponents = self.get_asian_opponents(category)

        for saudi in saudi_athletes:
            athlete_report = {
                'saudi_athlete': saudi.name,
                'country': saudi.country,
                'total_wins': len(saudi.wins),
                'total_losses': len(saudi.losses),
                'win_rate': saudi.win_rate,
                'scouting_targets': []
            }

            # Analyze each opponent
            targets = []
            for opp in opponents:
                if opp.name == saudi.name:
                    continue

                target = self.calculate_beatability(saudi, opp)
                if target.beatability_score > 0:
                    targets.append(target)

            # Sort by beatability score (highest first)
            targets.sort(key=lambda x: -x.beatability_score)

            # Take top 10 targets
            for target in targets[:10]:
                athlete_report['scouting_targets'].append(asdict(target))

            report['scouting_reports'].append(athlete_report)

        return report

    def get_top_asian_athletes_by_category(self, top_n: int = 20) -> Dict[str, List[AthleteRecord]]:
        """Group top Asian athletes by their categories."""
        category_athletes = defaultdict(list)

        for name, record in self.athlete_records.items():
            if record.country.upper() in ASIAN_COUNTRIES:
                # Find their categories
                categories_seen = set()
                for match in record.wins + record.losses:
                    if match.category:
                        categories_seen.add(match.category)

                for cat in categories_seen:
                    category_athletes[cat].append(record)

        # Sort each category by total matches (most active first)
        for cat in category_athletes:
            category_athletes[cat].sort(key=lambda x: -x.total_matches)
            category_athletes[cat] = category_athletes[cat][:top_n]  # Top N

        return dict(category_athletes)

    def get_top_world_athletes_by_category(self, top_n: int = 20) -> Dict[str, List[AthleteRecord]]:
        """Group top World athletes (all countries) by their categories."""
        category_athletes = defaultdict(list)

        for name, record in self.athlete_records.items():
            # All athletes regardless of country
            categories_seen = set()
            for match in record.wins + record.losses:
                if match.category:
                    categories_seen.add(match.category)

            for cat in categories_seen:
                category_athletes[cat].append(record)

        # Sort each category by total matches (most active first)
        for cat in category_athletes:
            category_athletes[cat].sort(key=lambda x: -x.total_matches)
            category_athletes[cat] = category_athletes[cat][:top_n]  # Top N

        return dict(category_athletes)

    def generate_asian_scouting_report(self, category: str = None, top_n: int = 20) -> Dict:
        """Generate scouting report showing top Asian athletes and who they lost to."""
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_matches_analyzed': len(self.matches),
            'report_type': 'Asian Top 20',
            'categories': []
        }

        top_by_category = self.get_top_asian_athletes_by_category(top_n=top_n)

        # Filter by category if specified
        if category:
            top_by_category = {k: v for k, v in top_by_category.items()
                            if category.lower() in k.lower()}

        for cat_name, athletes in sorted(top_by_category.items()):
            cat_report = {
                'category': cat_name,
                'athletes': []
            }

            for athlete in athletes:
                losses_info = []
                for loss in athlete.losses:
                    losses_info.append({
                        'lost_to': loss.winner,
                        'winner_country': loss.winner_country,
                        'score': loss.score,
                        'event': loss.event,
                        'round': loss.round
                    })

                cat_report['athletes'].append({
                    'name': athlete.name,
                    'country': athlete.country,
                    'wins': len(athlete.wins),
                    'losses': len(athlete.losses),
                    'win_rate': f"{athlete.win_rate:.0%}",
                    'total_matches': athlete.total_matches,
                    'loss_details': losses_info
                })

            report['categories'].append(cat_report)

        return report

    def generate_world_scouting_report(self, category: str = None, top_n: int = 20) -> Dict:
        """Generate scouting report showing top World athletes and who they lost to."""
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_matches_analyzed': len(self.matches),
            'report_type': 'World Top 20',
            'categories': []
        }

        top_by_category = self.get_top_world_athletes_by_category(top_n=top_n)

        # Filter by category if specified
        if category:
            top_by_category = {k: v for k, v in top_by_category.items()
                            if category.lower() in k.lower()}

        for cat_name, athletes in sorted(top_by_category.items()):
            cat_report = {
                'category': cat_name,
                'athletes': []
            }

            for athlete in athletes:
                losses_info = []
                for loss in athlete.losses:
                    losses_info.append({
                        'lost_to': loss.winner,
                        'winner_country': loss.winner_country,
                        'score': loss.score,
                        'event': loss.event,
                        'round': loss.round
                    })

                cat_report['athletes'].append({
                    'name': athlete.name,
                    'country': athlete.country,
                    'wins': len(athlete.wins),
                    'losses': len(athlete.losses),
                    'win_rate': f"{athlete.win_rate:.0%}",
                    'total_matches': athlete.total_matches,
                    'loss_details': losses_info
                })

            report['categories'].append(cat_report)

        return report

    def print_loss_chains(self, athlete_name: str, depth: int = 2):
        """Print loss chain for an athlete."""
        print(f"\n=== LOSS CHAIN: {athlete_name} ===\n")

        losses_to = self.loss_graph.get(athlete_name, set())
        if not losses_to:
            print(f"  No recorded losses for {athlete_name}")
            return

        print(f"  {athlete_name} lost to:")
        for beater in losses_to:
            record = self.athlete_records.get(beater)
            country = record.country if record else "???"
            print(f"    -> {beater} ({country})")

            if depth > 1:
                # Who beat this person?
                second_losses = self.loss_graph.get(beater, set())
                for second in list(second_losses)[:3]:
                    rec2 = self.athlete_records.get(second)
                    c2 = rec2.country if rec2 else "???"
                    print(f"        -> {second} ({c2})")


def main():
    parser = argparse.ArgumentParser(description='Loss Chain Analyzer for JJIF Scouting')
    parser.add_argument('--saudi', type=str, help='Saudi athlete name to analyze')
    parser.add_argument('--category', type=str, help='Weight category to filter')
    parser.add_argument('--all', action='store_true', help='Analyze all Saudi athletes')
    parser.add_argument('--chains', type=str, help='Show loss chains for athlete')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--top-asian', action='store_true', help='Show top 20 Asian athletes per category with losses')
    parser.add_argument('--top-world', action='store_true', help='Show top 20 World athletes per category with losses')
    parser.add_argument('--top-n', type=int, default=20, help='Number of top athletes to show (default: 20)')

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = LossChainAnalyzer()

    # Load match data
    count = analyzer.load_matches()
    if count == 0:
        print("\nNo matches loaded. Run bracket scraper first:")
        print("  python robust_bracket_scraper.py --scrape 714")
        return

    print(f"\nTotal athletes in database: {len(analyzer.athlete_records)}")
    print(f"Saudi athletes found: {len(analyzer.get_saudi_athletes())}")
    print(f"Asian opponents: {len(analyzer.get_asian_opponents())}")

    # Show loss chains if requested
    if args.chains:
        analyzer.print_loss_chains(args.chains)
        return

    # Show top Asian athletes with losses
    if args.top_asian:
        report = analyzer.generate_asian_scouting_report(category=args.category, top_n=args.top_n)

        # Save report
        if args.output:
            output_path = Path(args.output)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = RESULTS_DIR / f"asian_top{args.top_n}_{timestamp}.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\nAsian Top {args.top_n} scouting report saved: {output_path}")

        # Print summary
        for cat_report in report['categories']:
            print(f"\n{'='*70}")
            print(f"CATEGORY: {cat_report['category']}")
            print(f"{'='*70}")

            for i, athlete in enumerate(cat_report['athletes'][:args.top_n], 1):
                print(f"\n  {i}. {athlete['name']} ({athlete['country']})")
                print(f"     Record: {athlete['wins']}W-{athlete['losses']}L ({athlete['win_rate']})")

                if athlete['loss_details']:
                    print(f"     LOSSES:")
                    for loss in athlete['loss_details'][:5]:
                        print(f"       - to {loss['lost_to']} ({loss['winner_country']}) {loss['score'] or ''}")
                        if loss['event']:
                            print(f"         @ {loss['event'][:40]}")
                else:
                    print(f"     No losses recorded")

        return

    # Show top World athletes with losses
    if args.top_world:
        report = analyzer.generate_world_scouting_report(category=args.category, top_n=args.top_n)

        # Save report
        if args.output:
            output_path = Path(args.output)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = RESULTS_DIR / f"world_top{args.top_n}_{timestamp}.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\nWorld Top {args.top_n} scouting report saved: {output_path}")

        # Print summary
        for cat_report in report['categories']:
            print(f"\n{'='*70}")
            print(f"CATEGORY: {cat_report['category']}")
            print(f"{'='*70}")

            for i, athlete in enumerate(cat_report['athletes'][:args.top_n], 1):
                print(f"\n  {i}. {athlete['name']} ({athlete['country']})")
                print(f"     Record: {athlete['wins']}W-{athlete['losses']}L ({athlete['win_rate']})")

                if athlete['loss_details']:
                    print(f"     LOSSES:")
                    for loss in athlete['loss_details'][:5]:
                        print(f"       - to {loss['lost_to']} ({loss['winner_country']}) {loss['score'] or ''}")
                        if loss['event']:
                            print(f"         @ {loss['event'][:40]}")
                else:
                    print(f"     No losses recorded")

        return

    # Generate scouting report
    if args.saudi or args.all:
        report = analyzer.generate_scouting_report(
            saudi_name=args.saudi if not args.all else None,
            category=args.category
        )

        # Save or print report
        if args.output:
            output_path = Path(args.output)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = RESULTS_DIR / f"scouting_report_{timestamp}.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\nScouting report saved: {output_path}")

        # Print summary
        for sr in report['scouting_reports']:
            print(f"\n{'='*60}")
            print(f"SAUDI ATHLETE: {sr['saudi_athlete']}")
            print(f"Win Rate: {sr['win_rate']:.0%} ({sr['total_wins']}W-{sr['total_losses']}L)")
            print(f"\nTOP BEATABLE OPPONENTS:")

            for i, target in enumerate(sr['scouting_targets'][:5], 1):
                print(f"\n  {i}. {target['opponent_name']} ({target['opponent_country']})")
                print(f"     Beatability: {target['beatability_score']:.0%}")
                print(f"     Form: {target['recent_form']}")
                for reason in target['reasoning'][:3]:
                    print(f"     - {reason}")
    else:
        parser.print_help()
        print("\n\nExamples:")
        print("  python loss_chain_analyzer.py --all")
        print("  python loss_chain_analyzer.py --saudi 'Omar Nada'")
        print("  python loss_chain_analyzer.py --chains 'ATHLETE NAME'")


if __name__ == '__main__':
    main()
