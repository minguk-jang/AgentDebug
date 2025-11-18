"""Guide generation tools for documenting workarounds and constraints."""

from typing import List
from ..agent.state import GuideItem


def add_workaround(
    guide_items: List[GuideItem],
    step_id: int,
    issue: str,
    workaround: str
) -> List[GuideItem]:
    """
    Add a workaround guide item for a specific issue.

    Args:
        guide_items: Current list of guide items
        step_id: Associated plan step ID
        issue: Description of the issue encountered
        workaround: Description of the workaround solution

    Returns:
        Updated list of guide items
    """
    new_item = GuideItem(
        item_id=len(guide_items) + 1,
        step_id=step_id,
        category="workaround",
        content=f"**Issue**: {issue}\n**Workaround**: {workaround}",
        metadata={"issue": issue, "workaround": workaround}
    )
    guide_items.append(new_item)
    return guide_items


def add_parameter_constraint(
    guide_items: List[GuideItem],
    step_id: int,
    param_name: str,
    constraint: str,
    example: str
) -> List[GuideItem]:
    """
    Add a parameter constraint guide item.

    Args:
        guide_items: Current list of guide items
        step_id: Associated plan step ID
        param_name: Name of the parameter
        constraint: Description of the constraint
        example: Example value satisfying the constraint

    Returns:
        Updated list of guide items
    """
    new_item = GuideItem(
        item_id=len(guide_items) + 1,
        step_id=step_id,
        category="parameter_constraint",
        content=f"**Parameter**: `{param_name}`\n**Constraint**: {constraint}\n**Example**: `{example}`",
        metadata={"param_name": param_name, "constraint": constraint, "example": example}
    )
    guide_items.append(new_item)
    return guide_items


def add_selector_fallback(
    guide_items: List[GuideItem],
    step_id: int,
    primary_selector: str,
    fallbacks: List[str]
) -> List[GuideItem]:
    """
    Add a selector fallback guide item.

    Args:
        guide_items: Current list of guide items
        step_id: Associated plan step ID
        primary_selector: Primary CSS selector or XPath
        fallbacks: List of alternative selectors

    Returns:
        Updated list of guide items
    """
    fallback_str = ', '.join(f'`{s}`' for s in fallbacks)
    new_item = GuideItem(
        item_id=len(guide_items) + 1,
        step_id=step_id,
        category="selector_fallback",
        content=f"**Primary**: `{primary_selector}`\n**Fallbacks**: {fallback_str}",
        metadata={"primary": primary_selector, "fallbacks": fallbacks}
    )
    guide_items.append(new_item)
    return guide_items
