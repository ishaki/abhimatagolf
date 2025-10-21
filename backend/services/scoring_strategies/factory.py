"""
Scoring Strategy Factory

Factory pattern implementation to create appropriate scoring strategy
based on event's scoring type.

This centralizes strategy creation and ensures only one instance
of each strategy exists (Singleton pattern per strategy type).
"""

from typing import Dict
from models.event import ScoringType
from services.scoring_strategies.base import ScoringStrategy
from core.app_logging import logger


class ScoringStrategyFactory:
    """
    Factory for creating scoring strategies

    Usage:
        strategy = ScoringStrategyFactory.get_strategy(ScoringType.STROKE)
        strategy.update_scorecard(scorecard, participant, hole)
    """

    # Cache of strategy instances (Singleton per type)
    _strategies: Dict[ScoringType, ScoringStrategy] = {}

    @classmethod
    def get_strategy(cls, scoring_type: ScoringType) -> ScoringStrategy:
        """
        Get appropriate scoring strategy for the given scoring type

        Args:
            scoring_type: Type of scoring system (from Event model)

        Returns:
            Concrete strategy instance

        Raises:
            ValueError: If scoring type is not supported

        Example:
            >>> strategy = ScoringStrategyFactory.get_strategy(ScoringType.STROKE)
            >>> isinstance(strategy, StrokeScoringStrategy)
            True
        """
        # Return cached instance if exists
        if scoring_type in cls._strategies:
            return cls._strategies[scoring_type]

        # Create new strategy instance
        strategy = cls._create_strategy(scoring_type)

        # Cache and return
        cls._strategies[scoring_type] = strategy
        logger.info(f"Created new {scoring_type} strategy instance")

        return strategy

    @classmethod
    def _create_strategy(cls, scoring_type: ScoringType) -> ScoringStrategy:
        """
        Create new strategy instance (internal method)

        Args:
            scoring_type: Type of scoring system

        Returns:
            New strategy instance

        Raises:
            ValueError: If scoring type not supported
        """
        # Import here to avoid circular dependencies
        from services.scoring_strategies.stroke import StrokeScoringStrategy
        from services.scoring_strategies.net_stroke import NetStrokeScoringStrategy
        from services.scoring_strategies.system36 import System36ScoringStrategy
        # Future: from services.scoring_strategies.stableford import StablefordScoringStrategy

        if scoring_type == ScoringType.STROKE:
            return StrokeScoringStrategy()

        elif scoring_type == ScoringType.NET_STROKE:
            return NetStrokeScoringStrategy()

        elif scoring_type == ScoringType.SYSTEM_36:
            return System36ScoringStrategy()

        elif scoring_type == ScoringType.STABLEFORD:
            # TODO: Implement Stableford strategy
            raise NotImplementedError(
                "Stableford scoring is not yet implemented. "
                "Coming soon in Phase 3.2!"
            )

        else:
            raise ValueError(
                f"Unknown scoring type: {scoring_type}. "
                f"Supported types: {[st.value for st in ScoringType]}"
            )

    @classmethod
    def clear_cache(cls):
        """
        Clear strategy cache (useful for testing)

        This forces recreation of strategy instances on next get_strategy() call.
        """
        cls._strategies = {}
        logger.info("Cleared scoring strategy cache")

    @classmethod
    def get_supported_types(cls) -> list[ScoringType]:
        """
        Get list of supported scoring types

        Returns:
            List of ScoringType enums that are implemented

        Example:
            >>> types = ScoringStrategyFactory.get_supported_types()
            >>> ScoringType.STROKE in types
            True
        """
        return [
            ScoringType.STROKE,
            ScoringType.NET_STROKE,
            ScoringType.SYSTEM_36,
            # ScoringType.STABLEFORD,  # Coming soon
        ]
