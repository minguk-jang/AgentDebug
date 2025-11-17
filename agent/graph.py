#!/usr/bin/env python3
"""
LangGraph Graph Definition

Defines the analysis pipeline graph structure.
"""

from langgraph.graph import StateGraph, END
from .state import AnalysisState
from .nodes import (
    load_trace_node,
    convert_trajectory_node,
    phase1_analysis_node,
    phase2_analysis_node,
    generate_report_node
)


def create_analysis_graph():
    """
    Create the analysis graph.

    Pipeline flow:
    1. Load trace from Langfuse
    2. Convert to AgentDebug format
    3. Phase 1: Fine-grained error detection
    4. Phase 2: Critical error identification
    5. Generate report

    Returns:
        Compiled LangGraph workflow
    """
    # Create workflow with state type
    workflow = StateGraph(AnalysisState)

    # Add nodes
    workflow.add_node("load", load_trace_node)
    workflow.add_node("convert", convert_trajectory_node)
    workflow.add_node("phase1", phase1_analysis_node)
    workflow.add_node("phase2", phase2_analysis_node)
    workflow.add_node("report", generate_report_node)

    # Define edges (linear pipeline)
    workflow.set_entry_point("load")
    workflow.add_edge("load", "convert")
    workflow.add_edge("convert", "phase1")
    workflow.add_edge("phase1", "phase2")
    workflow.add_edge("phase2", "report")
    workflow.add_edge("report", END)

    # Compile and return
    return workflow.compile()
