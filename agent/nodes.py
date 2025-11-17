#!/usr/bin/env python3
"""
LangGraph Node Implementations

Each function represents a node in the analysis pipeline.
"""

import os
import logging
from typing import Dict, Any
from .state import AnalysisState
from langfuse_adapter import load_trace, convert_langfuse_to_agentdebug
from detector import ErrorTypeDetector, CriticalErrorAnalyzer

logger = logging.getLogger(__name__)


async def load_trace_node(state: AnalysisState) -> AnalysisState:
    """
    Node 1: Load trace from Langfuse.

    Fetches the trace data using Langfuse API.
    """
    logger.info(f"[Node 1/5] Loading trace: {state['trace_id']}")

    try:
        trace = await load_trace(state["trace_id"])
        state["raw_trace"] = trace
        logger.info(f"✓ Successfully loaded trace with {len(trace.get('observations', []))} observations")
    except Exception as e:
        error_msg = f"Failed to load trace: {str(e)}"
        logger.error(f"✗ {error_msg}")
        state["errors"].append(error_msg)

    return state


async def convert_trajectory_node(state: AnalysisState) -> AnalysisState:
    """
    Node 2: Convert Langfuse trace to AgentDebug format.

    Transforms the trace into the format expected by the detector.
    """
    logger.info("[Node 2/5] Converting trace to AgentDebug format")

    try:
        if not state.get("raw_trace"):
            raise ValueError("No trace data available to convert")

        trajectory = convert_langfuse_to_agentdebug(state["raw_trace"])
        state["converted_trajectory"] = trajectory

        num_messages = len(trajectory.get('messages', []))
        task = trajectory.get('metadata', {}).get('task', 'N/A')
        logger.info(f"✓ Converted to {num_messages} messages")
        logger.info(f"  Task: {task[:100]}...")

    except Exception as e:
        error_msg = f"Failed to convert trajectory: {str(e)}"
        logger.error(f"✗ {error_msg}")
        state["errors"].append(error_msg)

    return state


async def phase1_analysis_node(state: AnalysisState) -> AnalysisState:
    """
    Node 3: Phase 1 - Fine-grained error detection.

    Analyzes each step and module for errors using the ErrorTypeDetector.
    """
    logger.info("[Node 3/5] Running Phase 1: Fine-grained error detection")

    try:
        if not state.get("converted_trajectory"):
            raise ValueError("No converted trajectory available for analysis")

        # Initialize detector with API config
        detector = ErrorTypeDetector({
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions"),
            "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
            "temperature": 0.0,
            "max_retries": 3,
            "timeout": 60
        })

        logger.info("  Analyzing trajectory steps...")
        results = await detector.analyze_trajectory(state["converted_trajectory"])
        state["phase1_results"] = results

        total_steps = results.get('total_steps', 0)
        errors_found = sum(
            1 for step in results.get('step_analyses', [])
            if any(e.get('error_detected', False) for e in step.get('errors', {}).values() if e)
        )

        logger.info(f"✓ Phase 1 complete: {total_steps} steps analyzed, {errors_found} steps with errors")

    except Exception as e:
        error_msg = f"Phase 1 analysis failed: {str(e)}"
        logger.error(f"✗ {error_msg}")
        state["errors"].append(error_msg)
        import traceback
        logger.error(traceback.format_exc())

    return state


async def phase2_analysis_node(state: AnalysisState) -> AnalysisState:
    """
    Node 4: Phase 2 - Critical error identification.

    Identifies the most critical error that led to task failure.
    """
    logger.info("[Node 4/5] Running Phase 2: Critical error identification")

    try:
        if not state.get("phase1_results"):
            raise ValueError("No Phase 1 results available for Phase 2 analysis")

        if not state.get("converted_trajectory"):
            raise ValueError("No converted trajectory available for Phase 2")

        # Check if task succeeded
        if state["phase1_results"].get("task_success"):
            logger.info("  Task succeeded - skipping critical error analysis")
            state["phase2_results"] = {
                "task_success": True,
                "critical_error": None,
                "message": "Task succeeded - no critical error to identify"
            }
            return state

        # Initialize analyzer with API config
        analyzer = CriticalErrorAnalyzer({
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions"),
            "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
            "temperature": 0.0,
            "max_retries": 3,
            "timeout": 60
        })

        logger.info("  Identifying critical error...")
        # Phase 2 needs the trajectory in the format it expects (with 'messages' or 'chat_history')
        trajectory_for_phase2 = {
            "messages": state["converted_trajectory"].get("messages", []),
            "metadata": state["converted_trajectory"].get("metadata", {})
        }

        critical_error = await analyzer.identify_critical_error(
            state["phase1_results"],
            trajectory_for_phase2
        )

        if critical_error:
            state["phase2_results"] = {
                "task_success": False,
                "critical_error": {
                    "critical_step": critical_error.critical_step,
                    "critical_module": critical_error.critical_module,
                    "error_type": critical_error.error_type,
                    "root_cause": critical_error.root_cause,
                    "evidence": critical_error.evidence,
                    "correction_guidance": critical_error.correction_guidance,
                    "cascading_effects": critical_error.cascading_effects,
                    "confidence": critical_error.confidence
                }
            }

            logger.info(f"✓ Critical error identified at Step {critical_error.critical_step}: "
                       f"{critical_error.critical_module}:{critical_error.error_type}")
        else:
            state["phase2_results"] = {
                "task_success": False,
                "critical_error": None,
                "message": "No critical error identified"
            }
            logger.warning("  No critical error identified despite task failure")

    except Exception as e:
        error_msg = f"Phase 2 analysis failed: {str(e)}"
        logger.error(f"✗ {error_msg}")
        state["errors"].append(error_msg)
        import traceback
        logger.error(traceback.format_exc())

    return state


def generate_report_node(state: AnalysisState) -> AnalysisState:
    """
    Node 5: Generate terminal report.

    Creates a formatted report for display in the terminal.
    """
    logger.info("[Node 5/5] Generating report")

    try:
        report = _generate_terminal_report(
            state.get("trace_id"),
            state.get("phase1_results"),
            state.get("phase2_results"),
            state.get("errors", [])
        )
        state["report"] = report
        logger.info("✓ Report generated")

    except Exception as e:
        error_msg = f"Report generation failed: {str(e)}"
        logger.error(f"✗ {error_msg}")
        state["errors"].append(error_msg)
        state["report"] = f"Error generating report: {str(e)}"

    return state


def _generate_terminal_report(
    trace_id: str,
    phase1_results: Dict[str, Any],
    phase2_results: Dict[str, Any],
    errors: list
) -> str:
    """
    Generate formatted terminal report.

    Creates a visually appealing report with error analysis.
    """
    lines = []

    # Header
    lines.append("╔" + "═" * 70 + "╗")
    lines.append("║" + " " * 8 + "LANGFUSE AGENT TRAJECTORY ERROR ANALYSIS REPORT" + " " * 15 + "║")
    lines.append("╚" + "═" * 70 + "╝")
    lines.append("")

    # Handle case where we have errors but no results
    if errors and not phase1_results:
        lines.append("❌ ANALYSIS FAILED")
        lines.append("")
        lines.append("Errors encountered:")
        for i, error in enumerate(errors, 1):
            lines.append(f"  {i}. {error}")
        return "\n".join(lines)

    # Basic info
    if phase1_results:
        task = phase1_results.get('task_description', 'N/A')
        total_steps = phase1_results.get('total_steps', 0)
        task_success = phase1_results.get('task_success', False)

        lines.append(f"Trace ID: {trace_id}")
        lines.append(f"Task: {task}")
        lines.append(f"Total Steps: {total_steps}")
        lines.append(f"Task Success: {'✓ Yes' if task_success else '✗ No'}")
        lines.append("")

    # Critical Error Section (Phase 2)
    if phase2_results and phase2_results.get('critical_error'):
        critical = phase2_results['critical_error']

        lines.append("━" * 72)
        lines.append("🔴 CRITICAL ERROR IDENTIFIED")
        lines.append("━" * 72)
        lines.append("")

        lines.append(f"Critical Step: {critical.get('critical_step')}")
        lines.append(f"Module: {critical.get('critical_module')}")
        lines.append(f"Error Type: {critical.get('error_type')}")
        lines.append(f"Confidence: {critical.get('confidence', 0):.2f}")
        lines.append("")

        lines.append("Root Cause:")
        lines.append(_wrap_text(critical.get('root_cause', 'N/A'), indent=2))
        lines.append("")

        lines.append("Evidence:")
        lines.append(_wrap_text(critical.get('evidence', 'N/A'), indent=2))
        lines.append("")

        lines.append("💡 Correction Guidance:")
        lines.append(_wrap_text(critical.get('correction_guidance', 'N/A'), indent=2))
        lines.append("")

        cascading = critical.get('cascading_effects', [])
        if cascading:
            lines.append("Cascading Effects:")
            for effect in cascading:
                step = effect.get('step', 'N/A')
                effect_desc = effect.get('effect', 'N/A')
                lines.append(f"  • Step {step}: {effect_desc}")
            lines.append("")

    elif phase2_results and phase2_results.get('task_success'):
        lines.append("━" * 72)
        lines.append("✅ TASK SUCCEEDED")
        lines.append("━" * 72)
        lines.append("")
        lines.append("No critical errors - task completed successfully!")
        lines.append("")

    # Step-by-step summary (Phase 1)
    if phase1_results and phase1_results.get('step_analyses'):
        lines.append("━" * 72)
        lines.append("📊 STEP-BY-STEP ERROR SUMMARY")
        lines.append("━" * 72)
        lines.append("")

        for step_analysis in phase1_results['step_analyses']:
            step_num = step_analysis.get('step')
            errors_dict = step_analysis.get('errors', {})

            # Check if there are any errors
            has_errors = any(
                e.get('error_detected', False)
                for e in errors_dict.values()
                if e
            )

            if has_errors:
                lines.append(f"Step {step_num}:")
                for module, error_info in errors_dict.items():
                    if error_info and error_info.get('error_detected'):
                        error_type = error_info.get('error_type', 'unknown')
                        reasoning = error_info.get('reasoning', 'N/A')
                        lines.append(f"  ⚠️  {module}: {error_type}")
                        lines.append(f"      {_truncate(reasoning, 100)}")
                lines.append("")

    lines.append("━" * 72)

    return "\n".join(lines)


def _wrap_text(text: str, width: int = 70, indent: int = 0) -> str:
    """Wrap text to specified width with indentation."""
    words = str(text).split()
    lines = []
    current_line = []
    current_length = 0
    indent_str = " " * indent

    for word in words:
        if current_length + len(word) + 1 <= width:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            if current_line:
                lines.append(indent_str + " ".join(current_line))
            current_line = [word]
            current_length = len(word)

    if current_line:
        lines.append(indent_str + " ".join(current_line))

    return "\n".join(lines)


def _truncate(text: str, max_length: int) -> str:
    """Truncate text to max length."""
    text = str(text)
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
