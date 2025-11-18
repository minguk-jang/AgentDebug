"""LangGraph workflow definition for web automation agent."""

from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    init_node,
    planning_node,
    exploration_node,
    validation_node,
    execution_node,
    documentation_node,
    finalize_node
)


# Create the state graph
workflow = StateGraph(AgentState)

# Add nodes to the graph
workflow.add_node("init", init_node)
workflow.add_node("planning", planning_node)
workflow.add_node("exploration", exploration_node)
workflow.add_node("validation", validation_node)
workflow.add_node("execution", execution_node)
workflow.add_node("documentation", documentation_node)
workflow.add_node("finalize", finalize_node)

# Define the workflow edges
workflow.set_entry_point("init")
workflow.add_edge("init", "planning")
workflow.add_edge("planning", "exploration")
workflow.add_edge("exploration", "validation")
workflow.add_edge("validation", "execution")
workflow.add_edge("execution", "documentation")
workflow.add_edge("documentation", "finalize")
workflow.add_edge("finalize", END)

# Compile the graph
app = workflow.compile()


def run_agent(url: str, query: str) -> AgentState:
    """
    Run the web automation agent workflow.

    Args:
        url: Target URL to automate
        query: Natural language query describing the automation task

    Returns:
        Final agent state with execution results and documentation

    Example:
        >>> result = run_agent("https://example.com", "Fill in the search box with 'Python'")
        >>> print(f"Steps executed: {len(result['plan_steps'])}")
        >>> print(f"Guide items: {len(result['guide_items'])}")
    """
    # Initialize state
    initial_state = {
        "url": url,
        "query": query,
        "plan_steps": [],
        "guide_items": [],
        "current_step": 0,
        "md_content": "",
        "exploration_results": {},
        "error_log": []
    }

    # Run the workflow
    result = app.invoke(initial_state)

    return result
