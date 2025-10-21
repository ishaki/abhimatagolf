"""
Scoring Strategies Package

This package implements the Strategy Pattern for golf scoring systems.
Each scoring type (Stroke, Net Stroke, System 36, Stableford) has its own
strategy class that handles scoring calculations.

Architecture:
- ScoringStrategy (base.py): Abstract base class
- ScoringStrategyFactory (factory.py): Creates appropriate strategy
- Concrete strategies: stroke.py, net_stroke.py, system36.py, stableford.py

Usage:
    from services.scoring_strategies import ScoringStrategyFactory
    from models.event import ScoringType

    strategy = ScoringStrategyFactory.get_strategy(ScoringType.STROKE)
    updated_scorecard = strategy.update_scorecard(scorecard, participant, hole)
"""

from services.scoring_strategies.base import ScoringStrategy
from services.scoring_strategies.factory import ScoringStrategyFactory

__all__ = [
    'ScoringStrategy',
    'ScoringStrategyFactory',
]
