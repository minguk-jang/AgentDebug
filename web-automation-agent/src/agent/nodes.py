"""LangGraph node functions for web automation workflow."""

import os
from typing import Dict, Any
from .state import AgentState, PlanStep
from ..tools.planning import create_initial_plan, explore_and_refine_plan, validate_step_feasibility
from ..tools.guide import add_workaround, add_parameter_constraint, add_selector_fallback
from ..tools.exploration import analyze_page_structure, test_action_dry_run, capture_interaction_result
from ..tools.documentation import init_md_document, append_plan_step, append_guide_section
from ..utils.web_driver import get_driver, safe_click, safe_input


def init_node(state: AgentState) -> AgentState:
    """
    Initialize the agent state with default values.

    Args:
        state: Current agent state

    Returns:
        Updated agent state
    """
    state['md_content'] = init_md_document(state['url'], state['query'])
    state['current_step'] = 0
    state['plan_steps'] = []
    state['guide_items'] = []
    state['exploration_results'] = {}
    state['error_log'] = []

    return state


def planning_node(state: AgentState) -> AgentState:
    """
    Create an initial high-level plan for the automation task.

    Args:
        state: Current agent state

    Returns:
        Updated agent state with plan steps
    """
    try:
        from langchain_anthropic import ChatAnthropic

        # Initialize LLM
        llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0
        )

        # Create initial plan
        initial_plan = create_initial_plan(state['url'], state['query'], llm)
        state['plan_steps'] = initial_plan

        # Add plan steps to markdown
        for step in initial_plan:
            state['md_content'] = append_plan_step(state['md_content'], step)

    except Exception as e:
        error_msg = f"Planning node error: {str(e)}"
        state['error_log'].append(error_msg)
        # Create fallback plan
        state['plan_steps'] = [
            PlanStep(
                step_id=1,
                description=f"Execute query: {state['query']}",
                action_type="abstract",
                selector=None,
                value=None,
                status="pending"
            )
        ]

    return state


def exploration_node(state: AgentState) -> AgentState:
    """
    Explore the target page and refine the plan with concrete actions.

    Args:
        state: Current agent state

    Returns:
        Updated agent state with refined plan
    """
    driver = None
    try:
        from langchain_anthropic import ChatAnthropic

        # Initialize driver and LLM
        driver = get_driver()
        driver.get(state['url'])

        llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0
        )

        # Get page source and analyze structure
        page_source = driver.page_source
        analysis = analyze_page_structure(driver)
        state['exploration_results'] = analysis

        # Refine plan with concrete actions
        refined_plan = explore_and_refine_plan(state['plan_steps'], page_source, llm)
        state['plan_steps'] = refined_plan

        # Update markdown with refined steps
        state['md_content'] = init_md_document(state['url'], state['query'])  # Reset
        for step in refined_plan:
            state['md_content'] = append_plan_step(state['md_content'], step)

    except Exception as e:
        error_msg = f"Exploration node error: {str(e)}"
        state['error_log'].append(error_msg)

    finally:
        if driver:
            driver.quit()

    return state


def validation_node(state: AgentState) -> AgentState:
    """
    Validate that plan steps are feasible and suggest fallbacks.

    Args:
        state: Current agent state

    Returns:
        Updated agent state with validation results and fallbacks
    """
    driver = None
    try:
        from langchain_anthropic import ChatAnthropic

        driver = get_driver()
        driver.get(state['url'])

        llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0
        )

        # Validate each step
        for step in state['plan_steps']:
            if step.selector:
                is_valid, message = validate_step_feasibility(step, driver)

                if not is_valid:
                    # Generate fallback selectors using LLM
                    prompt = f"""The selector `{step.selector}` failed validation: {message}

Suggest 3 alternative CSS selectors for: {step.description}

Return ONLY a JSON array of strings:
["selector1", "selector2", "selector3"]"""

                    try:
                        response = llm.invoke(prompt)
                        content = response.content if hasattr(response, 'content') else str(response)

                        # Extract JSON array
                        import json
                        start = content.find('[')
                        end = content.rfind(']') + 1
                        if start != -1 and end > start:
                            fallbacks = json.loads(content[start:end])
                            state['guide_items'] = add_selector_fallback(
                                state['guide_items'],
                                step.step_id,
                                step.selector,
                                fallbacks
                            )

                            # Add to markdown
                            state['md_content'] = append_guide_section(
                                state['md_content'],
                                state['guide_items'][-1]
                            )
                    except:
                        pass

    except Exception as e:
        error_msg = f"Validation node error: {str(e)}"
        state['error_log'].append(error_msg)

    finally:
        if driver:
            driver.quit()

    return state


def execution_node(state: AgentState) -> AgentState:
    """
    Execute the plan steps and document results.

    Args:
        state: Current agent state

    Returns:
        Updated agent state with execution results
    """
    driver = None
    try:
        from selenium.webdriver.common.by import By
        import time

        driver = get_driver()
        driver.get(state['url'])

        # Execute each step
        for idx, step in enumerate(state['plan_steps']):
            state['current_step'] = idx

            try:
                before_url = driver.current_url

                if step.action_type == "click":
                    success = safe_click(driver, step.selector)
                    if success:
                        step.status = "success"
                    else:
                        step.status = "failed"
                        state['guide_items'] = add_workaround(
                            state['guide_items'],
                            step.step_id,
                            f"Click failed on selector: {step.selector}",
                            "Try using JavaScript click or verify element visibility"
                        )

                elif step.action_type == "input":
                    if step.value:
                        success = safe_input(driver, step.selector, step.value)
                        if success:
                            step.status = "success"
                        else:
                            step.status = "failed"
                            state['guide_items'] = add_workaround(
                                state['guide_items'],
                                step.step_id,
                                f"Input failed on selector: {step.selector}",
                                "Verify input field is enabled and visible"
                            )
                    else:
                        step.status = "failed"
                        state['guide_items'] = add_parameter_constraint(
                            state['guide_items'],
                            step.step_id,
                            "value",
                            "Must provide a value for input actions",
                            "example_text"
                        )

                elif step.action_type == "navigate":
                    if step.value:
                        driver.get(step.value)
                        step.status = "success"
                    else:
                        step.status = "failed"

                elif step.action_type == "wait":
                    wait_time = int(step.value) if step.value else 2
                    time.sleep(wait_time)
                    step.status = "success"

                else:
                    step.status = "skipped"

                # Capture interaction result
                result = capture_interaction_result(driver, step.action_type, before_url)
                state['exploration_results'][f'step_{step.step_id}_result'] = result

                # Small delay between actions
                time.sleep(1)

            except Exception as step_error:
                step.status = "failed"
                error_msg = f"Step {step.step_id} execution error: {str(step_error)}"
                state['error_log'].append(error_msg)

                # Add workaround
                state['guide_items'] = add_workaround(
                    state['guide_items'],
                    step.step_id,
                    str(step_error),
                    "Review selector and page state, consider adding explicit wait"
                )

        # Update markdown with final step statuses
        state['md_content'] = init_md_document(state['url'], state['query'])
        for step in state['plan_steps']:
            state['md_content'] = append_plan_step(state['md_content'], step)

    except Exception as e:
        error_msg = f"Execution node error: {str(e)}"
        state['error_log'].append(error_msg)

    finally:
        if driver:
            driver.quit()

    return state


def documentation_node(state: AgentState) -> AgentState:
    """
    Ensure all plan steps and guide items are documented.

    Args:
        state: Current agent state

    Returns:
        Updated agent state with complete documentation
    """
    try:
        # Add all guide items to markdown
        for guide_item in state['guide_items']:
            state['md_content'] = append_guide_section(state['md_content'], guide_item)

        # Add error log if present
        if state['error_log']:
            error_section = "\n## Error Log\n\n"
            for idx, error in enumerate(state['error_log'], 1):
                error_section += f"{idx}. {error}\n"
            state['md_content'] += error_section

    except Exception as e:
        error_msg = f"Documentation node error: {str(e)}"
        state['error_log'].append(error_msg)

    return state


def finalize_node(state: AgentState) -> AgentState:
    """
    Finalize and save the documentation.

    Args:
        state: Current agent state

    Returns:
        Updated agent state with completion status
    """
    try:
        from ..tools.documentation import finalize_md
        from ..utils.web_driver import sanitize_filename

        # Generate output filename
        filename = sanitize_filename(state['query'])
        output_path = f"outputs/{filename}.md"

        # Save documentation
        result = finalize_md(state['md_content'], output_path)
        state['md_content'] += f"\n\n---\n{result}\n"

    except Exception as e:
        error_msg = f"Finalize node error: {str(e)}"
        state['error_log'].append(error_msg)

    return state
