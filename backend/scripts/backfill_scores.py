"""
Backfill Script for Scoring Strategy Refactoring

This script updates existing scorecards to populate net_score and points fields
using the new Strategy Pattern implementation.

Usage:
    # Dry run (preview changes without committing)
    python scripts/backfill_scores.py --dry-run

    # Actually update the database
    python scripts/backfill_scores.py

    # Update only specific event
    python scripts/backfill_scores.py --event-id 1

    # Verbose output
    python scripts/backfill_scores.py --verbose
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from core.database import engine
from models.scorecard import Scorecard
from models.participant import Participant
from models.event import Event
from models.course import Hole
from services.scoring_strategies import ScoringStrategyFactory
from core.app_logging import logger


class ScoreBackfiller:
    """Backfills existing scorecards with calculated values"""

    def __init__(self, dry_run: bool = False, verbose: bool = False, event_id: int = None):
        self.dry_run = dry_run
        self.verbose = verbose
        self.event_id = event_id
        self.stats = {
            'total_scorecards': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'by_scoring_type': {}
        }

    def run(self):
        """Main backfill process"""
        mode = "DRY RUN" if self.dry_run else "LIVE UPDATE"
        print(f"\n{'='*60}")
        print(f"  Scoring Strategy Backfill - {mode}")
        print(f"{'='*60}\n")

        if self.dry_run:
            print("[!] DRY RUN MODE: No changes will be saved to database\n")

        with Session(engine) as session:
            # Get scorecards to process
            scorecards = self._get_scorecards(session)
            self.stats['total_scorecards'] = len(scorecards)

            print(f"Found {len(scorecards)} scorecards to process\n")

            if len(scorecards) == 0:
                print("[OK] No scorecards need backfilling!")
                return

            # Process each scorecard
            for i, scorecard in enumerate(scorecards, 1):
                if self.verbose or i % 10 == 0:
                    print(f"Processing {i}/{len(scorecards)}...", end='\r')

                try:
                    self._process_scorecard(session, scorecard)
                except Exception as e:
                    self.stats['errors'] += 1
                    logger.error(f"Error processing scorecard {scorecard.id}: {e}")
                    if self.verbose:
                        print(f"\n[ERROR] Error on scorecard {scorecard.id}: {e}")

            # Commit changes if not dry run
            if not self.dry_run:
                session.commit()
                print("\n[OK] Changes committed to database")
            else:
                session.rollback()
                print("\n[!] Changes rolled back (dry run)")

        # Print summary
        self._print_summary()

    def _get_scorecards(self, session: Session) -> list[Scorecard]:
        """Get scorecards that need backfilling"""
        query = select(Scorecard).where(Scorecard.strokes > 0)

        # Filter by event if specified
        if self.event_id:
            query = query.where(Scorecard.event_id == self.event_id)

        return session.exec(query).all()

    def _process_scorecard(self, session: Session, scorecard: Scorecard):
        """Process a single scorecard"""
        # Get related data
        participant = session.get(Participant, scorecard.participant_id)
        if not participant:
            self.stats['skipped'] += 1
            return

        event = session.get(Event, scorecard.event_id)
        if not event:
            self.stats['skipped'] += 1
            return

        hole = session.get(Hole, scorecard.hole_id)
        if not hole:
            self.stats['skipped'] += 1
            return

        # Get strategy for this event's scoring type
        strategy = ScoringStrategyFactory.get_strategy(event.scoring_type)

        # Store old values for logging
        old_net_score = scorecard.net_score
        old_points = scorecard.points

        # Apply strategy to calculate new values
        scorecard = strategy.update_scorecard(scorecard, participant, hole)

        # Track statistics
        if event.scoring_type not in self.stats['by_scoring_type']:
            self.stats['by_scoring_type'][event.scoring_type] = 0
        self.stats['by_scoring_type'][event.scoring_type] += 1

        # Check if values changed
        if old_net_score != scorecard.net_score or old_points != scorecard.points:
            self.stats['updated'] += 1

            if self.verbose:
                print(f"\n[NOTE] Scorecard {scorecard.id} (Event: {event.name}, Hole {hole.number}):")
                print(f"   Scoring Type: {event.scoring_type}")
                print(f"   Strokes: {scorecard.strokes}")
                print(f"   Net Score: {old_net_score} -> {scorecard.net_score}")
                print(f"   Points: {old_points} -> {scorecard.points}")
        else:
            self.stats['skipped'] += 1

        # Update in session (will be committed/rolled back later)
        session.add(scorecard)

    def _print_summary(self):
        """Print backfill summary"""
        print(f"\n{'='*60}")
        print("  Backfill Summary")
        print(f"{'='*60}\n")

        print(f"Total Scorecards Processed: {self.stats['total_scorecards']}")
        print(f"[OK] Updated: {self.stats['updated']}")
        print(f"[SKIP] Skipped (no change): {self.stats['skipped']}")
        print(f"[ERROR] Errors: {self.stats['errors']}\n")

        if self.stats['by_scoring_type']:
            print("By Scoring Type:")
            for scoring_type, count in self.stats['by_scoring_type'].items():
                print(f"  - {scoring_type}: {count}")

        print(f"\n{'='*60}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Backfill scorecards with calculated net_score and points"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without committing to database'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output for each scorecard'
    )
    parser.add_argument(
        '--event-id',
        type=int,
        help='Only backfill scorecards for specific event'
    )

    args = parser.parse_args()

    # Run backfill
    backfiller = ScoreBackfiller(
        dry_run=args.dry_run,
        verbose=args.verbose,
        event_id=args.event_id
    )

    try:
        backfiller.run()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n[!] Backfill interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Backfill failed: {e}")
        logger.exception("Backfill failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
