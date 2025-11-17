#!/usr/bin/env python3
"""
Langfuse Trace Loader

Loads trace data from Langfuse API using the Langfuse SDK.
"""

import os
from typing import Dict, Any, List
from langfuse import Langfuse
import logging

logger = logging.getLogger(__name__)


async def load_trace(trace_id: str) -> Dict[str, Any]:
    """
    Load trace from Langfuse API.

    Args:
        trace_id: The Langfuse trace ID to retrieve

    Returns:
        Dict containing:
            - id: trace ID
            - name: trace name
            - metadata: trace metadata
            - observations: list of observations (spans, generations, events)
            - input: trace input (if available)
            - output: trace output (if available)

    Raises:
        ValueError: If required environment variables are missing
        Exception: If trace retrieval fails
    """
    # Get Langfuse credentials from environment
    public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
    secret_key = os.getenv('LANGFUSE_SECRET_KEY')
    host = os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')

    if not public_key or not secret_key:
        raise ValueError(
            "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set in environment. "
            "Please check your .env file."
        )

    try:
        # Initialize Langfuse client
        logger.info(f"Connecting to Langfuse at {host}")
        langfuse = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )

        # Fetch the trace (support both SDK v2 and v3)
        logger.info(f"Fetching trace: {trace_id}")
        try:
            # Try SDK v3 API first
            if hasattr(langfuse, 'api') and hasattr(langfuse.api, 'trace'):
                trace = langfuse.api.trace.get(trace_id)
            # Fall back to SDK v2 API
            elif hasattr(langfuse, 'fetch_trace'):
                trace = langfuse.fetch_trace(trace_id)
            else:
                raise AttributeError("Langfuse SDK method not found. Please upgrade langfuse SDK.")
        except Exception as e:
            logger.error(f"Failed to fetch trace: {e}")
            raise ValueError(f"Trace not found or API error: {trace_id}") from e

        if not trace:
            raise ValueError(f"Trace not found: {trace_id}")

        # Convert trace to dict format
        trace_data = {
            'id': trace.id,
            'name': trace.name,
            'metadata': trace.metadata or {},
            'input': trace.input,
            'output': trace.output,
            'observations': []
        }

        # Fetch observations (spans, generations, events)
        logger.info("Fetching trace observations...")
        try:
            # Try SDK v3 API first
            if hasattr(langfuse, 'api') and hasattr(langfuse.api, 'observations'):
                observations = langfuse.api.observations.list(trace_id=trace_id)
            # Fall back to SDK v2 API
            elif hasattr(langfuse, 'fetch_observations'):
                observations = langfuse.fetch_observations(trace_id=trace_id)
            else:
                raise AttributeError("Langfuse SDK observations method not found")
        except Exception as e:
            logger.error(f"Failed to fetch observations: {e}")
            raise

        # Convert observations to dict format
        for obs in observations.data:
            obs_dict = {
                'id': obs.id,
                'type': obs.type,  # 'span', 'generation', or 'event'
                'name': obs.name,
                'start_time': str(obs.start_time) if obs.start_time else None,
                'end_time': str(obs.end_time) if obs.end_time else None,
                'metadata': obs.metadata or {},
                'input': obs.input,
                'output': obs.output,
                'level': obs.level,
                'status_message': obs.status_message,
                'parent_observation_id': obs.parent_observation_id,
                'version': obs.version,
            }

            # Add generation-specific fields
            if obs.type == 'GENERATION':
                obs_dict['model'] = getattr(obs, 'model', None)
                obs_dict['model_parameters'] = getattr(obs, 'model_parameters', {})
                obs_dict['usage'] = getattr(obs, 'usage', {})
                obs_dict['prompt_tokens'] = getattr(obs, 'prompt_tokens', None)
                obs_dict['completion_tokens'] = getattr(obs, 'completion_tokens', None)

            trace_data['observations'].append(obs_dict)

        logger.info(f"Successfully loaded trace with {len(trace_data['observations'])} observations")

        return trace_data

    except Exception as e:
        logger.error(f"Failed to load trace {trace_id}: {e}")
        raise
