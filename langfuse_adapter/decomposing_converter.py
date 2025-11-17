#!/usr/bin/env python3
"""
Decomposing Converter

Extends trajectory_converter with LLM-based module decomposition for plain text outputs.
"""

import os
import asyncio
import logging
from typing import Dict, Any

from .trajectory_converter import convert_langfuse_to_agentdebug, _format_user_message
from .module_decomposer import ModuleDecomposer

logger = logging.getLogger(__name__)


async def convert_with_decomposition(trace: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Langfuse trace to AgentDebug format with LLM-based module decomposition.

    This function processes plain text agent outputs and decomposes them into
    memory, reflection, plan, and action modules using an LLM.

    Args:
        trace: Langfuse trace dict

    Returns:
        AgentDebug trajectory dict

    Environment variables:
        OPENAI_API_KEY: Required for decomposition
        OPENAI_MODEL: Model to use (default: gpt-4o)
        OPENAI_BASE_URL: API endpoint
        ENABLE_MODULE_DECOMPOSER: Set to 'false' to disable (default: 'true')
    """
    # Check if decomposer is enabled
    if os.getenv('ENABLE_MODULE_DECOMPOSER', 'true').lower() != 'true':
        logger.info("Module decomposer disabled, using standard conversion")
        return convert_langfuse_to_agentdebug(trace)

    # Check if API key is available
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.warning("OPENAI_API_KEY not set, using standard conversion without decomposition")
        return convert_langfuse_to_agentdebug(trace)

    try:
        # Initialize decomposer
        api_config = {
            "api_key": api_key,
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions"),
            "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
            "temperature": 0.0,
            "max_retries": 3,
            "timeout": 60
        }
        decomposer = ModuleDecomposer(api_config)

        # Get observations
        observations = trace.get('observations', [])
        if not observations:
            return convert_langfuse_to_agentdebug(trace)

        # Sort observations
        sorted_obs = sorted(
            observations,
            key=lambda x: x.get('start_time', '0') or '0'
        )

        # Build context and decompose plain text outputs
        previous_context = ""
        step_number = 0

        for obs in sorted_obs:
            if obs.get('type', '').upper() == 'GENERATION':
                step_number += 1
                output = obs.get('output')

                # Check if this is plain text that needs decomposition
                if isinstance(output, str) and not ('<memory>' in output or '<action>' in output):
                    logger.info(f"Decomposing step {step_number} with LLM")

                    # Decompose
                    modules = await decomposer.decompose(output, step_number, previous_context)

                    # Store decomposed modules in metadata for later formatting
                    if 'metadata' not in obs:
                        obs['metadata'] = {}
                    obs['metadata']['memory'] = modules.get('memory', '')
                    obs['metadata']['reflection'] = modules.get('reflection', '')
                    obs['metadata']['plan'] = modules.get('plan', '')
                    obs['metadata']['action'] = modules.get('action', output)

                    # Update context for next step
                    if modules.get('memory') or modules.get('action'):
                        context_parts = []
                        if modules.get('memory'):
                            context_parts.append(f"Memory: {modules['memory']}")
                        if modules.get('action'):
                            context_parts.append(f"Action: {modules['action']}")
                        previous_context = f"Step {step_number}: " + "; ".join(context_parts)

        # Now use standard converter (it will use the metadata we added)
        return convert_langfuse_to_agentdebug(trace)

    except Exception as e:
        logger.error(f"Decomposition failed: {e}, falling back to standard conversion")
        return convert_langfuse_to_agentdebug(trace)
