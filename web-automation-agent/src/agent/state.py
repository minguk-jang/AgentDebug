"""State definitions for LangGraph agent."""

from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    """Represents a single step in the automation plan."""

    step_id: int = Field(..., description="Unique identifier for the step")
    description: str = Field(..., description="Human-readable description of the step")
    action_type: str = Field(..., description="Type of action: click, input, wait, navigate, abstract")
    selector: Optional[str] = Field(None, description="CSS selector or XPath for the target element")
    value: Optional[str] = Field(None, description="Value to input (for input actions)")
    status: str = Field(default="pending", description="Status: pending, success, failed")


class GuideItem(BaseModel):
    """Represents a guide item with workarounds, constraints, or fallbacks."""

    item_id: int = Field(..., description="Unique identifier for the guide item")
    step_id: int = Field(..., description="Associated plan step ID")
    category: str = Field(..., description="Category: workaround, parameter_constraint, selector_fallback")
    content: str = Field(..., description="Markdown-formatted content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentState(TypedDict):
    """Complete state for the web automation agent."""

    url: str
    query: str
    plan_steps: List[PlanStep]
    guide_items: List[GuideItem]
    current_step: int
    md_content: str
    exploration_results: Dict[str, Any]
    error_log: List[str]
