"""Planning tools for web automation agent."""

import json
from typing import List, Tuple
from ..agent.state import PlanStep


def create_initial_plan(url: str, query: str, llm) -> List[PlanStep]:
    """
    Create a high-level abstract plan for the given query.

    Args:
        url: Target URL
        query: User's automation request
        llm: Language model instance

    Returns:
        List of abstract PlanStep objects
    """
    prompt = f"""Given the following URL and query, create a high-level plan with 3-5 abstract steps to accomplish this task.

URL: {url}
Query: {query}

Return ONLY a JSON array of steps in this exact format:
[
  {{"description": "Step description", "action_type": "abstract"}},
  {{"description": "Step description", "action_type": "abstract"}}
]

Be concise and focus on the logical sequence of actions needed."""

    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        # Extract JSON from response
        start = content.find('[')
        end = content.rfind(']') + 1
        if start != -1 and end > start:
            json_str = content[start:end]
            steps_data = json.loads(json_str)
        else:
            # Fallback: create basic steps
            steps_data = [
                {"description": f"Navigate to {url}", "action_type": "navigate"},
                {"description": f"Execute: {query}", "action_type": "abstract"}
            ]

        plan_steps = []
        for idx, step_data in enumerate(steps_data, start=1):
            plan_steps.append(PlanStep(
                step_id=idx,
                description=step_data.get("description", "Unknown step"),
                action_type=step_data.get("action_type", "abstract"),
                selector=None,
                value=None,
                status="pending"
            ))

        return plan_steps

    except Exception as e:
        # Fallback plan on error
        return [
            PlanStep(
                step_id=1,
                description=f"Navigate to {url}",
                action_type="navigate",
                selector=None,
                value=url,
                status="pending"
            ),
            PlanStep(
                step_id=2,
                description=f"Execute query: {query}",
                action_type="abstract",
                selector=None,
                value=None,
                status="pending"
            )
        ]


def explore_and_refine_plan(plan_steps: List[PlanStep], page_source: str, llm) -> List[PlanStep]:
    """
    Refine abstract plan steps into concrete actions with selectors.

    Args:
        plan_steps: List of abstract plan steps
        page_source: HTML source of the target page
        llm: Language model instance

    Returns:
        List of refined PlanStep objects with concrete selectors
    """
    refined_steps = []

    # Truncate page source to avoid token limits
    page_snippet = page_source[:5000]

    for step in plan_steps:
        if step.action_type == "abstract":
            prompt = f"""Given this HTML snippet and abstract step, provide a concrete action.

HTML:
{page_snippet}

Abstract Step: {step.description}

Return ONLY a JSON object in this exact format:
{{
  "action_type": "click|input|navigate|wait",
  "selector": "CSS selector or XPath",
  "value": "value if needed (for input actions)"
}}

Choose the most appropriate action type and provide a reliable selector."""

            try:
                response = llm.invoke(prompt)
                content = response.content if hasattr(response, 'content') else str(response)

                # Extract JSON from response
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = content[start:end]
                    action_data = json.loads(json_str)

                    refined_steps.append(PlanStep(
                        step_id=step.step_id,
                        description=step.description,
                        action_type=action_data.get("action_type", "click"),
                        selector=action_data.get("selector"),
                        value=action_data.get("value"),
                        status="pending"
                    ))
                else:
                    # Keep original if parsing fails
                    refined_steps.append(step)

            except Exception as e:
                # Keep original on error
                refined_steps.append(step)
        else:
            # Keep non-abstract steps as-is
            refined_steps.append(step)

    return refined_steps


def validate_step_feasibility(step: PlanStep, driver) -> Tuple[bool, str]:
    """
    Validate if a step can be executed on the current page.

    Args:
        step: PlanStep to validate
        driver: Selenium WebDriver instance

    Returns:
        Tuple of (success: bool, message: str)
    """
    if not step.selector:
        return True, "No selector to validate"

    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        # Try to find element with multiple strategies
        element = None
        strategies = [
            (By.CSS_SELECTOR, step.selector),
            (By.XPATH, step.selector),
            (By.ID, step.selector.replace('#', ''))
        ]

        for by_type, selector in strategies:
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((by_type, selector))
                )
                break
            except:
                continue

        if not element:
            return False, f"Element not found: {step.selector}"

        # Check action-specific feasibility
        if step.action_type == "click":
            if not element.is_enabled():
                return False, "Element is not clickable (disabled)"
            if not element.is_displayed():
                return False, "Element is not visible"

        elif step.action_type == "input":
            tag_name = element.tag_name.lower()
            if tag_name not in ['input', 'textarea', 'select']:
                return False, f"Element is not an input field (tag: {tag_name})"
            if not element.is_enabled():
                return False, "Input field is disabled"

        return True, f"Step is feasible with selector: {step.selector}"

    except Exception as e:
        return False, f"Validation error: {str(e)}"
