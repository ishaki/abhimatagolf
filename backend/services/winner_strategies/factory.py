"""
Winner Strategy Factory

Factory pattern implementation to create appropriate winner calculation strategy
based on event's scoring type.

This centralizes strategy creation and ensures only one instance of each strategy
exists (Singleton pattern per strategy type).
"""

from typing import Dict
from models.event import ScoringType
from services.winner_strategies.base import WinnerCalculationStrategy
from core.app_logging import logger


class WinnerStrategyFactory:
    """
    Factory for creating winner calculation strategies

    Usage:
        strategy = WinnerStrategyFactory.get_strategy(ScoringType.STROKE)
        primary_metric = strategy.get_primary_metric(participant_data)
        sort_order = strategy.get_sort_order()
    """

    # Cache of strategy instances (Singleton per type)
    _strategies: Dict[ScoringType, WinnerCalculationStrategy] = {}

    @classmethod
    def get_strategy(cls, scoring_type: ScoringType) -> WinnerCalculationStrategy:
        """
        Get appropriate winner calculation strategy for the given scoring type

        Args:
            scoring_type: Type of scoring system (from Event model)

        Returns:
            Concrete strategy instance

        Raises:
            ValueError: If scoring type is not supported

        Example:
            >>> strategy = WinnerStrategyFactory.get_strategy(ScoringType.STROKE)
            >>> isinstance(strategy, StrokeWinnerStrategy)
            True
        """
        # Return cached instance if exists
        if scoring_type in cls._strategies:
            return cls._strategies[scoring_type]

        # Create new strategy instance
        strategy = cls._create_strategy(scoring_type)

        # Cache and return
        cls._strategies[scoring_type] = strategy
        logger.info(f"Created new winner calculation strategy for {scoring_type}")

        return strategy

    @classmethod
    def _create_strategy(cls, scoring_type: ScoringType) -> WinnerCalculationStrategy:
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
        from services.winner_strategies.stroke_winner import StrokeWinnerStrategy
        from services.winner_strategies.net_stroke_winner import NetStrokeWinnerStrategy
        from services.winner_strategies.system36_winner import System36WinnerStrategy
        # Future: from services.winner_strategies.stableford_winner import StablefordWinnerStrategy

        if scoring_type == ScoringType.STROKE:
            return StrokeWinnerStrategy()

        elif scoring_type == ScoringType.NET_STROKE:
            return NetStrokeWinnerStrategy()

        elif scoring_type == ScoringType.SYSTEM_36:
            return System36WinnerStrategy()

        elif scoring_type == ScoringType.STABLEFORD:
            # TODO: Implement Stableford winner strategy
            raise NotImplementedError(
                "Stableford winner calculation is not yet implemented. "
                "Coming soon in Phase 4!"
            )

        else:
            raise ValueError(
                f"Unknown scoring type: {scoring_type}. "
                f"Supported types: {[st.value for st in cls.get_supported_types()]}"
            )

    @classmethod
    def clear_cache(cls):
        """
        Clear strategy cache (useful for testing)

        This forces recreation of strategy instances on next get_strategy() call.
        """
        cls._strategies = {}
        logger.info("Cleared winner strategy cache")

    @classmethod
    def get_supported_types(cls) -> list[ScoringType]:
        """
        Get list of supported scoring types

        Returns:
            List of ScoringType enums that have implemented winner strategies

        Example:
            >>> types = WinnerStrategyFactory.get_supported_types()
            >>> ScoringType.STROKE in types
            True
        """
        return [
            ScoringType.STROKE,
            ScoringType.NET_STROKE,
            ScoringType.SYSTEM_36,
            # ScoringType.STABLEFORD,  # Coming soon
        ]

    @classmethod
    def is_supported(cls, scoring_type: ScoringType) -> bool:
        """
        Check if a scoring type is supported

        Args:
            scoring_type: Scoring type to check

        Returns:
            True if strategy exists for this scoring type

        Example:
            >>> WinnerStrategyFactory.is_supported(ScoringType.STROKE)
            True
            >>> WinnerStrategyFactory.is_supported(ScoringType.STABLEFORD)
            False
        """
        return scoring_type in cls.get_supported_types()
