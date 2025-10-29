"""
Winner Configuration Schemas

Request/Response schemas for winner configuration management
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from models.winner_configuration import TieBreakingMethod, CalculationTrigger


class WinnerConfigurationBase(BaseModel):
    """Base schema for winner configuration"""
    tie_breaking_method: TieBreakingMethod = Field(
        default=TieBreakingMethod.STANDARD_GOLF,
        description="Method used to break ties"
    )
    award_categories: Dict[str, Any] = Field(
        default_factory=lambda: {
            "overall": [
                {"rank": 1, "name": "Champion", "description": "Overall Winner"},
                {"rank": 2, "name": "Runner-up", "description": "Second Place"},
                {"rank": 3, "name": "Third Place", "description": "Third Place"}
            ],
            "division": [
                {"rank": 1, "name": "Division Winner", "description": "First in Division"},
                {"rank": 2, "name": "Division Runner-up", "description": "Second in Division"}
            ]
        },
        description="Award categories for overall and division winners"
    )
    winners_per_division: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of winners to recognize per division (1-10)"
    )
    top_overall_count: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Number of overall winners to recognize (0-10). Set to 0 to disable overall winners (division-based only)"
    )
    calculation_trigger: CalculationTrigger = Field(
        default=CalculationTrigger.MANUAL_ONLY,
        description="When to automatically calculate winners"
    )
    allow_manual_override: bool = Field(
        default=True,
        description="Allow event admins to manually edit winner results"
    )
    include_best_gross: bool = Field(
        default=False,
        description="Include 'Best Gross Score' award"
    )
    include_best_net: bool = Field(
        default=False,
        description="Include 'Best Net Score' award"
    )
    exclude_incomplete_rounds: bool = Field(
        default=True,
        description="Exclude participants who haven't completed all 18 holes"
    )
    minimum_holes_for_ranking: int = Field(
        default=18,
        ge=9,
        le=18,
        description="Minimum holes required to be eligible for ranking"
    )


class WinnerConfigurationCreate(WinnerConfigurationBase):
    """Schema for creating winner configuration"""
    event_id: int = Field(..., description="Event ID")


class WinnerConfigurationUpdate(BaseModel):
    """Schema for updating winner configuration (all fields optional)"""
    tie_breaking_method: Optional[TieBreakingMethod] = None
    award_categories: Optional[Dict[str, Any]] = None
    winners_per_division: Optional[int] = Field(None, ge=1, le=10)
    top_overall_count: Optional[int] = Field(None, ge=0, le=10)
    calculation_trigger: Optional[CalculationTrigger] = None
    allow_manual_override: Optional[bool] = None
    include_best_gross: Optional[bool] = None
    include_best_net: Optional[bool] = None
    exclude_incomplete_rounds: Optional[bool] = None
    minimum_holes_for_ranking: Optional[int] = Field(None, ge=9, le=18)


class WinnerConfigurationResponse(WinnerConfigurationBase):
    """Schema for winner configuration response"""
    id: int
    event_id: int
    created_at: datetime
    updated_at: datetime
    created_by: int

    class Config:
        from_attributes = True


class WinnerManualOverride(BaseModel):
    """Schema for manually overriding winner result fields"""
    overall_rank: Optional[int] = Field(None, ge=1, description="Override overall rank")
    division_rank: Optional[int] = Field(None, ge=1, description="Override division rank")
    award_category: Optional[str] = Field(None, max_length=100, description="Override award category")
    prize_details: Optional[str] = Field(None, max_length=500, description="Add/update prize details")
    is_tied: Optional[bool] = Field(None, description="Override tie status")
