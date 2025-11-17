#!/usr/bin/env python3
"""
LangGraph State Definition

Defines the state structure for the analysis pipeline.
"""

from typing import TypedDict, Dict, List, Any, Optional


class AnalysisState(TypedDict):
    """
    State for the LangGraph analysis pipeline.

    This state is passed through all nodes in the graph and contains
    all data needed for the analysis.
    """
    # Input
    trace_id: str

    # Loaded data
    raw_trace: Optional[Dict[str, Any]]
    converted_trajectory: Optional[Dict[str, Any]]

    # Analysis results
    phase1_results: Optional[Dict[str, Any]]
    phase2_results: Optional[Dict[str, Any]]

    # Output
    report: Optional[str]

    # Error tracking
    errors: List[str]
