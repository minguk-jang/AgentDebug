#!/usr/bin/env python3
"""
Module Decomposer

Uses LLM to decompose plain text agent output into structured modules:
- Memory: What the agent recalls from previous steps
- Reflection: How the agent evaluates the current situation
- Planning: What the agent plans to do next
- Action: The actual action to execute
"""

import os
import json
import asyncio
import aiohttp
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ModuleDecomposer:
    """Decomposes plain text agent output into AgentDebug modules using LLM"""

    def __init__(self, api_config: Dict[str, Any]):
        """
        Initialize the decomposer.

        Args:
            api_config: Configuration dict containing:
                - api_key: OpenAI API key
                - base_url: API endpoint URL
                - model: Model name to use
                - temperature: (optional) Temperature for generation
                - max_retries: (optional) Max retry attempts
                - timeout: (optional) Request timeout in seconds
        """
        self.config = api_config
        self.headers = {
            "Authorization": f"Bearer {api_config['api_key']}",
            "Content-Type": "application/json"
        }

    async def decompose(
        self,
        output: str,
        step_number: int,
        previous_context: str,
    ) -> Dict[str, str]:
        """
        Decompose agent output into modules.

        Args:
            output: The plain text agent output
            step_number: Current step number
            previous_context: Summary of previous steps

        Returns:
            Dictionary with keys: memory, reflection, plan, action
        """
        try:
            # Build prompt
            prompt = self._build_decomposition_prompt(
                output, step_number, previous_context
            )

            # Call LLM
            response = await self._call_llm(prompt)

            # Parse response
            modules = self._parse_modules(response)

            logger.debug(f"Decomposed step {step_number}: {modules}")
            return modules

        except Exception as e:
            logger.warning(f"Decomposition failed for step {step_number}: {e}")
            # Return fallback - put everything in action
            return self._fallback_decomposition(output)

    def _build_decomposition_prompt(
        self,
        output: str,
        step_number: int,
        previous_context: str
    ) -> str:
        """Build the prompt for LLM decomposition"""

        prompt = f"""You are analyzing an AI agent's output and need to decompose it into 4 structured modules.

Step Number: {step_number}

Agent Output:
{output}

Previous Context:
{previous_context if previous_context else "This is the first step."}

Your task is to decompose this output into 4 modules:

1. **Memory**: What the agent is recalling or referencing from previous steps. Extract any mentions of "previously", "earlier", "I remember", etc. If this is step 1 or there's no memory reference, leave empty.

2. **Reflection**: How the agent is evaluating the current situation, progress, or results. Look for phrases like "good", "I can see", "the results show", "this looks", etc. If there's no evaluation, leave empty.

3. **Planning**: What the agent plans or intends to do next. Look for phrases like "I will", "I should", "I plan to", "next I'll", "let me", etc. This describes the intention.

4. **Action**: The actual executable action or command. This could be:
   - A command like `search[query]`, `click[button]`, `add_to_cart`
   - If no explicit command exists, extract the main action verb and object
   - If the output is purely explanatory, summarize the key action being described

Important guidelines:
- Be concise - extract only the essential information for each module
- If a module doesn't apply, use an empty string ""
- The action field should NEVER be empty - if there's no clear action command, describe what the agent is doing
- Don't invent information - only extract what's actually in the output

Output ONLY valid JSON in this exact format:
{{
    "memory": "extracted memory content or empty string",
    "reflection": "extracted reflection content or empty string",
    "plan": "extracted planning content or empty string",
    "action": "extracted action or description"
}}

Do not include any text before or after the JSON object."""

        return prompt

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API for decomposition"""
        payload = {
            "model": self.config['model'],
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert at analyzing AI agent outputs and decomposing them into "
                        "structured modules (memory, reflection, planning, action). "
                        "Always respond with valid JSON only."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.config.get('temperature', 0.0),
            "response_format": {"type": "json_object"}
        }

        proxy = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')

        async with aiohttp.ClientSession() as session:
            for attempt in range(self.config.get('max_retries', 3)):
                try:
                    async with session.post(
                        self.config['base_url'],
                        headers=self.headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=self.config.get('timeout', 60)),
                        proxy=proxy if proxy else None
                    ) as response:
                        response.raise_for_status()
                        data = await response.json()
                        return data['choices'][0]['message']['content']

                except Exception as e:
                    if attempt == self.config.get('max_retries', 3) - 1:
                        logger.error(f"LLM API call failed after retries: {e}")
                        raise
                    await asyncio.sleep(2 ** attempt)

        return ""

    def _parse_modules(self, response: str) -> Dict[str, str]:
        """Parse LLM response into modules"""
        try:
            # Try to parse as JSON
            modules = json.loads(response)

            # Validate structure
            required_keys = ['memory', 'reflection', 'plan', 'action']
            for key in required_keys:
                if key not in modules:
                    modules[key] = ""

            # Ensure all values are strings
            for key in required_keys:
                if modules[key] is None:
                    modules[key] = ""
                else:
                    modules[key] = str(modules[key])

            return modules

        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON response: {response[:200]}")
            # Try to extract JSON from response
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if json_match:
                try:
                    modules = json.loads(json_match.group(0))
                    return {
                        'memory': modules.get('memory', ''),
                        'reflection': modules.get('reflection', ''),
                        'plan': modules.get('plan', ''),
                        'action': modules.get('action', '')
                    }
                except:
                    pass

            # Complete fallback
            return {
                'memory': '',
                'reflection': '',
                'plan': '',
                'action': response[:500] if response else ''
            }

    def _fallback_decomposition(self, output: str) -> Dict[str, str]:
        """Fallback decomposition when LLM fails"""
        return {
            'memory': '',
            'reflection': '',
            'plan': '',
            'action': output  # Put entire output as action
        }


async def decompose_agent_output(
    output: str,
    step_number: int,
    previous_context: str,
    api_config: Dict[str, Any]
) -> Dict[str, str]:
    """
    Convenience function to decompose agent output.

    Args:
        output: Plain text agent output
        step_number: Current step number
        previous_context: Summary of previous steps
        api_config: API configuration dict

    Returns:
        Dictionary with memory, reflection, plan, action
    """
    decomposer = ModuleDecomposer(api_config)
    return await decomposer.decompose(output, step_number, previous_context)
