#!/usr/bin/env python3
"""
Langfuse to AgentDebug Trajectory Converter

Converts Langfuse trace format to AgentDebug trajectory format.
"""

import os
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def convert_langfuse_to_agentdebug(trace: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Langfuse trace to AgentDebug trajectory format.

    Input (Langfuse trace):
        - trace.id
        - trace.observations: List[observation]
          - observation.type: "SPAN" | "GENERATION" | "EVENT"
          - observation.input: Any
          - observation.output: Any
          - observation.metadata: Dict

    Output (AgentDebug format):
        {
            "metadata": {
                "task_id": trace.id,
                "environment": "langfuse",
                "success": False,  # inferred or from metadata
                "task": "extracted task"
            },
            "messages": [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "<memory>...</memory><reflection>...</reflection><plan>...</plan><action>...</action>"},
                ...
            ]
        }
    """
    try:
        # Extract metadata
        task_id = trace.get('id', 'unknown')
        trace_metadata = trace.get('metadata', {})

        # Try to infer task success
        success = _infer_success(trace)

        # Extract task description
        task_description = _extract_task_description(trace)

        # Build message list from observations
        messages = _build_messages_from_observations(trace)

        # If no messages were built, try alternative extraction
        if not messages:
            logger.warning("No messages extracted from observations, attempting fallback")
            messages = _fallback_message_extraction(trace)

        trajectory = {
            "metadata": {
                "task_id": task_id,
                "environment": trace_metadata.get('environment', 'langfuse'),
                "success": success,
                "task": task_description
            },
            "messages": messages
        }

        logger.info(f"Converted trace {task_id} to AgentDebug format: {len(messages)} messages")
        return trajectory

    except Exception as e:
        logger.error(f"Error converting trace to AgentDebug format: {e}")
        # Return minimal valid structure
        return {
            "metadata": {
                "task_id": trace.get('id', 'unknown'),
                "environment": "langfuse",
                "success": False,
                "task": "Conversion failed"
            },
            "messages": [
                {"role": "user", "content": "Error during conversion"},
                {"role": "assistant", "content": f"<action>Error: {str(e)}</action>"}
            ]
        }


def _infer_success(trace: Dict[str, Any]) -> bool:
    """Infer whether the task was successful."""
    metadata = trace.get('metadata', {})

    # Check metadata for explicit success field
    if 'success' in metadata:
        return bool(metadata['success'])
    if 'won' in metadata:
        return bool(metadata['won'])
    if 'task_success' in metadata:
        return bool(metadata['task_success'])

    # Check trace output
    output = trace.get('output')
    if output:
        if isinstance(output, dict):
            if 'success' in output:
                return bool(output['success'])
        elif isinstance(output, str):
            # Look for success indicators in output
            if any(word in output.lower() for word in ['success', 'completed', 'done']):
                return True

    # Check last observation
    observations = trace.get('observations', [])
    if observations:
        last_obs = observations[-1]
        if last_obs.get('output'):
            output_str = str(last_obs['output']).lower()
            if 'success' in output_str or 'completed' in output_str:
                return True

    # Default to False (conservative)
    return False


def _extract_task_description(trace: Dict[str, Any]) -> str:
    """Extract task description from trace."""
    # Check metadata first
    metadata = trace.get('metadata', {})
    if 'task' in metadata:
        return str(metadata['task'])
    if 'task_description' in metadata:
        return str(metadata['task_description'])

    # Check trace name
    name = trace.get('name')
    if name and name != 'unknown':
        return name

    # Check trace input
    trace_input = trace.get('input')
    if trace_input:
        if isinstance(trace_input, dict):
            if 'task' in trace_input:
                return str(trace_input['task'])
            if 'query' in trace_input:
                return str(trace_input['query'])
        elif isinstance(trace_input, str):
            # Extract task from input string
            if 'task:' in trace_input.lower():
                match = re.search(r'task:\s*(.+?)(?:\n|$)', trace_input, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            return trace_input[:200]  # First 200 chars

    # Check first observation
    observations = trace.get('observations', [])
    if observations:
        first_obs = observations[0]
        if first_obs.get('input'):
            input_str = str(first_obs['input'])
            if 'task' in input_str.lower():
                match = re.search(r'task:\s*(.+?)(?:\n|$)', input_str, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            return input_str[:200]

    return "Unknown task"


def _build_messages_from_observations(trace: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Build message list from observations.

    Strategy:
    1. GENERATION type observations -> assistant messages
    2. User inputs from observation inputs -> user messages
    3. Alternate between user and assistant messages
    """
    observations = trace.get('observations', [])
    if not observations:
        return []

    messages = []

    # Sort observations by start_time if available
    sorted_obs = sorted(
        observations,
        key=lambda x: x.get('start_time', '0') or '0'
    )

    # Track if we need an initial user message
    need_initial_user = True

    for i, obs in enumerate(sorted_obs):
        obs_type = obs.get('type', '').upper()
        obs_input = obs.get('input')
        obs_output = obs.get('output')
        obs_metadata = obs.get('metadata', {})

        # If this is a GENERATION, it's an assistant message
        if obs_type == 'GENERATION':
            # Add user message before this if needed
            if need_initial_user and obs_input:
                user_content = _format_user_message(obs_input)
                messages.append({
                    "role": "user",
                    "content": user_content
                })
                need_initial_user = False

            # Format assistant output
            if obs_output:
                assistant_content = _format_assistant_message(obs_output, obs_metadata)
                messages.append({
                    "role": "assistant",
                    "content": assistant_content
                })

                # Add environment response if available (next observation's input or metadata)
                if i + 1 < len(sorted_obs):
                    next_obs = sorted_obs[i + 1]
                    env_response = _extract_environment_response(next_obs)
                    if env_response:
                        messages.append({
                            "role": "user",
                            "content": env_response
                        })

        # If this is a SPAN, it might contain agent steps
        elif obs_type == 'SPAN':
            # Check if this span has meaningful output
            if obs_output:
                # If metadata indicates this is an agent step, format it
                if _is_agent_step(obs):
                    assistant_content = _format_assistant_message(obs_output, obs_metadata)
                    messages.append({
                        "role": "assistant",
                        "content": assistant_content
                    })

    return messages


def _format_user_message(content: Any) -> str:
    """Format user message content."""
    if isinstance(content, dict):
        # Check for common message fields
        if 'content' in content:
            return str(content['content'])
        if 'message' in content:
            return str(content['message'])
        if 'messages' in content and isinstance(content['messages'], list):
            # Extract last user message
            for msg in reversed(content['messages']):
                if isinstance(msg, dict) and msg.get('role') == 'user':
                    return str(msg.get('content', ''))
        # Otherwise, format the whole dict
        return str(content)
    return str(content)


def _format_assistant_message(output: Any, metadata: Dict) -> str:
    """
    Format assistant message in AgentDebug XML format.

    Expected format:
    <memory>...</memory><reflection>...</reflection><plan>...</plan><action>...</action>

    Note: For plain text outputs without structure, this returns a simple <action> wrapper.
    Use convert_langfuse_to_agentdebug_with_decomposer() for LLM-based module decomposition.
    """
    # If output is already in XML format, return as-is
    if isinstance(output, str):
        if '<memory>' in output or '<action>' in output or '<plan>' in output:
            return output

    # Check metadata for module information
    memory = metadata.get('memory', '')
    reflection = metadata.get('reflection', '')
    plan = metadata.get('plan', '') or metadata.get('planning', '')
    action = metadata.get('action', '')

    # If we have module information in metadata, use it
    if any([memory, reflection, plan, action]):
        parts = []
        if memory:
            parts.append(f"<memory>{memory}</memory>")
        if reflection:
            parts.append(f"<reflection>{reflection}</reflection>")
        if plan:
            parts.append(f"<plan>{plan}</plan>")
        if action:
            parts.append(f"<action>{action}</action>")
        return ''.join(parts)

    # Try to parse output if it's structured
    if isinstance(output, dict):
        parts = []
        if 'memory' in output:
            parts.append(f"<memory>{output['memory']}</memory>")
        if 'reflection' in output:
            parts.append(f"<reflection>{output['reflection']}</reflection>")
        if 'plan' in output or 'planning' in output:
            plan_content = output.get('plan', output.get('planning', ''))
            parts.append(f"<plan>{plan_content}</plan>")
        if 'action' in output:
            parts.append(f"<action>{output['action']}</action>")

        if parts:
            return ''.join(parts)

        # If no module fields, treat whole output as action
        return f"<action>{str(output)}</action>"

    # Default: wrap entire output as action
    output_str = str(output)
    if output_str:
        return f"<action>{output_str}</action>"

    return "<action>No output</action>"


def _extract_environment_response(obs: Dict) -> Optional[str]:
    """Extract environment response from observation."""
    # Check input (environment typically responds via next step's input)
    obs_input = obs.get('input')
    if obs_input:
        # Check metadata for environment response marker
        metadata = obs.get('metadata', {})
        if metadata.get('is_environment_response'):
            return _format_user_message(obs_input)

    # Check for observation result
    if obs.get('output') and obs.get('type') == 'EVENT':
        return str(obs['output'])

    return None


def _is_agent_step(obs: Dict) -> bool:
    """Check if observation represents an agent step."""
    metadata = obs.get('metadata', {})

    # Check for explicit markers
    if metadata.get('is_agent_step'):
        return True

    # Check observation name
    name = obs.get('name', '').lower()
    if any(keyword in name for keyword in ['agent', 'step', 'decision', 'planning']):
        return True

    # Check if output has agent-like structure
    output = obs.get('output')
    if isinstance(output, dict):
        if any(key in output for key in ['memory', 'reflection', 'plan', 'action']):
            return True
    elif isinstance(output, str):
        if '<memory>' in output or '<action>' in output or '<plan>' in output:
            return True

    return False


def _fallback_message_extraction(trace: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Fallback message extraction when standard method fails.

    Creates a minimal valid trajectory from trace input/output.
    """
    messages = []

    # Add initial user message from trace input
    trace_input = trace.get('input')
    if trace_input:
        messages.append({
            "role": "user",
            "content": _format_user_message(trace_input)
        })
    else:
        # Use task description as initial message
        task = _extract_task_description(trace)
        messages.append({
            "role": "user",
            "content": f"Your task is: {task}"
        })

    # Add assistant message from trace output
    trace_output = trace.get('output')
    if trace_output:
        messages.append({
            "role": "assistant",
            "content": _format_assistant_message(trace_output, {})
        })
    else:
        # Create minimal assistant message
        messages.append({
            "role": "assistant",
            "content": "<action>No output available</action>"
        })

    logger.warning("Used fallback message extraction - trajectory may be incomplete")
    return messages
