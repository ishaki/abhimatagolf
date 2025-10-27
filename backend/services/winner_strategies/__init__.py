"""
Winner Calculation Strategy Package

This package contains the Strategy Pattern implementation for calculating
tournament winners based on different scoring types.

Each scoring type (Stroke, Net Stroke, System 36, Stableford) has its own
strategy that defines:
- Primary ranking metric (gross score, net score, points)
- Sort order (ascending for stroke-based, descending for points-based)
- Tie-breaking rules
- Eligibility criteria
- Display data formatting

Usage:
    from services.winner_strategies import WinnerStrategyFactory

    strategy = WinnerStrategyFactory.get_strategy(event.scoring_type)
    winners = strategy.calculate_winners(session, event, config)
"""

from services.winner_strategies.base import WinnerCalculationStrategy
from services.winner_strategies.factory import WinnerStrategyFactory

__all__ = [
    'WinnerCalculationStrategy',
    'WinnerStrategyFactory',
]
