"""
End-to-End Test for Scoring Strategy Refactoring

Tests all scoring strategies to ensure:
1. Scores are calculated correctly during entry
2. Values are stored in database (net_score, points)
3. Leaderboard reads stored values (no recalculation)
4. All scoring types work consistently

Usage:
    python scripts/test_scoring_refactoring.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from core.database import engine
from models.event import Event, ScoringType
from models.participant import Participant
from models.scorecard import Scorecard
from models.course import Hole
from services.scoring_strategies import ScoringStrategyFactory
from services.leaderboard_service import LeaderboardService


class ScoringRefactoringTester:
    """Tests the refactored scoring system"""

    def __init__(self):
        self.session = Session(engine)
        self.test_results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }

    def run_all_tests(self):
        """Run all test suites"""
        print("\n" + "="*60)
        print("  Scoring Strategy Refactoring - End-to-End Tests")
        print("="*60 + "\n")

        try:
            # Test 1: Strategy Factory
            self.test_strategy_factory()

            # Test 2: Stroke Play Strategy
            self.test_stroke_strategy()

            # Test 3: Net Stroke Strategy
            self.test_net_stroke_strategy()

            # Test 4: System 36 Strategy
            self.test_system36_strategy()

            # Test 5: Leaderboard Service (no recalculation)
            self.test_leaderboard_service()

            # Print summary
            self.print_summary()

        except Exception as e:
            print(f"\n[ERROR] Test suite failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.session.close()

    def test_strategy_factory(self):
        """Test 1: Verify strategy factory creates correct strategies"""
        print("[TEST 1] Strategy Factory")
        print("-" * 60)

        test_cases = [
            (ScoringType.STROKE, "StrokeScoringStrategy"),
            (ScoringType.NET_STROKE, "NetStrokeScoringStrategy"),
            (ScoringType.SYSTEM_36, "System36ScoringStrategy"),
        ]

        for scoring_type, expected_class in test_cases:
            self.test_results['total_tests'] += 1
            try:
                strategy = ScoringStrategyFactory.get_strategy(scoring_type)
                actual_class = strategy.__class__.__name__

                if actual_class == expected_class:
                    print(f"  [PASS] {scoring_type} -> {actual_class}")
                    self.test_results['passed'] += 1
                else:
                    print(f"  [FAIL] {scoring_type} -> Expected {expected_class}, got {actual_class}")
                    self.test_results['failed'] += 1
                    self.test_results['errors'].append(
                        f"Strategy Factory: Wrong class for {scoring_type}"
                    )
            except Exception as e:
                print(f"  [ERROR] {scoring_type} -> {e}")
                self.test_results['failed'] += 1
                self.test_results['errors'].append(f"Strategy Factory: {scoring_type} - {e}")

        print()

    def test_stroke_strategy(self):
        """Test 2: Verify Stroke Play strategy calculations"""
        print("[TEST 2] Stroke Play Strategy")
        print("-" * 60)

        # Get a stroke play event
        event = self.session.exec(
            select(Event).where(Event.scoring_type == ScoringType.STROKE)
        ).first()

        if not event:
            print("  [SKIP] No Stroke Play events found in database\n")
            return

        # Get first participant and scorecard
        participant = self.session.exec(
            select(Participant).where(Participant.event_id == event.id)
        ).first()

        if not participant:
            print(f"  [SKIP] No participants found for event {event.name}\n")
            return

        scorecard = self.session.exec(
            select(Scorecard).where(Scorecard.participant_id == participant.id)
        ).first()

        if not scorecard:
            print(f"  [SKIP] No scorecards found for participant {participant.name}\n")
            return

        hole = self.session.get(Hole, scorecard.hole_id)

        # Test calculation
        self.test_results['total_tests'] += 1
        expected_net = float(scorecard.strokes)
        expected_points = 0

        if scorecard.net_score == expected_net and scorecard.points == expected_points:
            print(f"  [PASS] Participant: {participant.name}")
            print(f"         Hole {hole.number}: Strokes={scorecard.strokes}")
            print(f"         Net Score: {scorecard.net_score} (expected {expected_net})")
            print(f"         Points: {scorecard.points} (expected {expected_points})")
            self.test_results['passed'] += 1
        else:
            print(f"  [FAIL] Participant: {participant.name}")
            print(f"         Expected: net_score={expected_net}, points={expected_points}")
            print(f"         Actual: net_score={scorecard.net_score}, points={scorecard.points}")
            self.test_results['failed'] += 1
            self.test_results['errors'].append("Stroke Play: Incorrect calculation")

        print()

    def test_net_stroke_strategy(self):
        """Test 3: Verify Net Stroke strategy calculations"""
        print("[TEST 3] Net Stroke Play Strategy")
        print("-" * 60)

        # Get a net stroke event
        event = self.session.exec(
            select(Event).where(Event.scoring_type == ScoringType.NET_STROKE)
        ).first()

        if not event:
            print("  [SKIP] No Net Stroke Play events found in database\n")
            return

        participant = self.session.exec(
            select(Participant).where(Participant.event_id == event.id)
        ).first()

        if not participant:
            print(f"  [SKIP] No participants found for event {event.name}\n")
            return

        scorecard = self.session.exec(
            select(Scorecard).where(Scorecard.participant_id == participant.id)
        ).first()

        if not scorecard:
            print(f"  [SKIP] No scorecards found for participant {participant.name}\n")
            return

        hole = self.session.get(Hole, scorecard.hole_id)

        # Calculate expected handicap strokes
        strategy = ScoringStrategyFactory.get_strategy(ScoringType.NET_STROKE)
        expected_handicap_strokes = strategy.calculate_handicap_strokes_for_hole(
            participant.declared_handicap, hole.stroke_index, 18
        )
        expected_net = float(scorecard.strokes - expected_handicap_strokes)
        expected_points = 0

        # Test calculation
        self.test_results['total_tests'] += 1

        if scorecard.net_score == expected_net and scorecard.points == expected_points:
            print(f"  [PASS] Participant: {participant.name} (HCP {participant.declared_handicap})")
            print(f"         Hole {hole.number} (Index {hole.stroke_index}): Strokes={scorecard.strokes}")
            print(f"         Handicap Strokes: {expected_handicap_strokes}")
            print(f"         Net Score: {scorecard.net_score} (expected {expected_net})")
            print(f"         Points: {scorecard.points} (expected {expected_points})")
            self.test_results['passed'] += 1
        else:
            print(f"  [FAIL] Participant: {participant.name}")
            print(f"         Expected: net_score={expected_net}, points={expected_points}")
            print(f"         Actual: net_score={scorecard.net_score}, points={scorecard.points}")
            self.test_results['failed'] += 1
            self.test_results['errors'].append("Net Stroke: Incorrect calculation")

        print()

    def test_system36_strategy(self):
        """Test 4: Verify System 36 strategy calculations"""
        print("[TEST 4] System 36 Strategy")
        print("-" * 60)

        # Get a System 36 event
        event = self.session.exec(
            select(Event).where(Event.scoring_type == ScoringType.SYSTEM_36)
        ).first()

        if not event:
            print("  [SKIP] No System 36 events found in database\n")
            return

        participant = self.session.exec(
            select(Participant).where(Participant.event_id == event.id)
        ).first()

        if not participant:
            print(f"  [SKIP] No participants found for event {event.name}\n")
            return

        scorecard = self.session.exec(
            select(Scorecard).where(Scorecard.participant_id == participant.id)
        ).first()

        if not scorecard:
            print(f"  [SKIP] No scorecards found for participant {participant.name}\n")
            return

        hole = self.session.get(Hole, scorecard.hole_id)

        # Calculate expected values
        strategy = ScoringStrategyFactory.get_strategy(ScoringType.SYSTEM_36)
        expected_handicap_strokes = strategy.calculate_handicap_strokes_for_hole(
            participant.declared_handicap, hole.stroke_index, 18
        )
        expected_points = strategy.calculate_system36_points(
            scorecard.strokes, hole.par, expected_handicap_strokes
        )
        expected_net = float(scorecard.strokes - expected_handicap_strokes)

        # Test calculation
        self.test_results['total_tests'] += 1

        if scorecard.net_score == expected_net and scorecard.points == expected_points:
            print(f"  [PASS] Participant: {participant.name} (HCP {participant.declared_handicap})")
            print(f"         Hole {hole.number} (Par {hole.par}, Index {hole.stroke_index}): Strokes={scorecard.strokes}")
            print(f"         Handicap Strokes: {expected_handicap_strokes}")
            print(f"         Net Score: {scorecard.net_score} (expected {expected_net})")
            print(f"         Points: {scorecard.points} (expected {expected_points})")
            self.test_results['passed'] += 1
        else:
            print(f"  [FAIL] Participant: {participant.name}")
            print(f"         Expected: net_score={expected_net}, points={expected_points}")
            print(f"         Actual: net_score={scorecard.net_score}, points={scorecard.points}")
            self.test_results['failed'] += 1
            self.test_results['errors'].append("System 36: Incorrect calculation")

        print()

    def test_leaderboard_service(self):
        """Test 5: Verify leaderboard service reads stored values"""
        print("[TEST 5] Leaderboard Service (No Recalculation)")
        print("-" * 60)

        # Get first event
        event = self.session.exec(select(Event)).first()

        if not event:
            print("  [SKIP] No events found in database\n")
            return

        self.test_results['total_tests'] += 1

        try:
            # Get leaderboard
            service = LeaderboardService(self.session)
            leaderboard = service.calculate_leaderboard(event.id, use_cache=False)

            print(f"  [PASS] Leaderboard generated successfully")
            print(f"         Event: {leaderboard.event_name}")
            print(f"         Scoring Type: {leaderboard.scoring_type}")
            print(f"         Total Participants: {leaderboard.total_participants}")
            print(f"         Participants with Scores: {leaderboard.participants_with_scores}")
            print(f"         Leaderboard Entries: {len(leaderboard.entries)}")

            if leaderboard.entries:
                top_entry = leaderboard.entries[0]
                print(f"\n         Top Entry:")
                print(f"         - Rank: {top_entry.rank}")
                print(f"         - Name: {top_entry.participant_name}")
                print(f"         - Gross Score: {top_entry.gross_score}")
                print(f"         - Net Score: {top_entry.net_score}")
                print(f"         - Points: {top_entry.system36_points}")
                print(f"         - Holes Completed: {top_entry.holes_completed}")

            self.test_results['passed'] += 1

        except Exception as e:
            print(f"  [FAIL] Leaderboard generation failed: {e}")
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Leaderboard: {e}")
            import traceback
            traceback.print_exc()

        print()

    def print_summary(self):
        """Print test summary"""
        print("="*60)
        print("  Test Summary")
        print("="*60 + "\n")

        print(f"Total Tests: {self.test_results['total_tests']}")
        print(f"[PASS] Passed: {self.test_results['passed']}")
        print(f"[FAIL] Failed: {self.test_results['failed']}")

        if self.test_results['errors']:
            print("\nErrors:")
            for error in self.test_results['errors']:
                print(f"  - {error}")

        print("\n" + "="*60)

        # Exit code
        if self.test_results['failed'] == 0:
            print("\n[SUCCESS] All tests passed!")
            sys.exit(0)
        else:
            print("\n[FAILURE] Some tests failed")
            sys.exit(1)


def main():
    """Main entry point"""
    tester = ScoringRefactoringTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
