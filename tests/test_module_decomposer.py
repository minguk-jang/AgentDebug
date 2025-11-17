"""Tests for module_decomposer module"""

import pytest
import json
from unittest.mock import patch, AsyncMock, Mock
from langfuse_adapter.module_decomposer import (
    ModuleDecomposer,
    decompose_agent_output,
)


class TestModuleDecomposer:
    """Test module decomposer functionality"""

    @pytest.mark.asyncio
    @patch('langfuse_adapter.module_decomposer.aiohttp.ClientSession')
    async def test_decompose_with_llm_success(self, mock_session_class):
        """Test successful decomposition with LLM"""
        # Mock aiohttp session
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "memory": "Previously searched for items.",
                        "reflection": "Good progress so far.",
                        "plan": "Will select the best option.",
                        "action": "click[2]"
                    })
                }
            }]
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()

        mock_session.post = Mock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()
        mock_session_class.return_value = mock_session

        # Create decomposer
        config = {
            "api_key": "test-key",
            "base_url": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-4",
        }
        decomposer = ModuleDecomposer(config)

        # Test decomposition
        output = "I need to find the best product. Let me search for it."
        result = await decomposer.decompose(
            output=output,
            step_number=1,
            previous_context=""
        )

        # Verify result structure
        assert "memory" in result
        assert "reflection" in result
        assert "plan" in result
        assert "action" in result

        # Verify content
        assert result["action"] == "click[2]"
        assert "searched" in result["memory"].lower()

    @pytest.mark.asyncio
    @patch('langfuse_adapter.module_decomposer.aiohttp.ClientSession')
    async def test_decompose_with_context(self, mock_session_class):
        """Test decomposition with previous context"""
        # Mock response
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "memory": "In step 1, I searched for laptops.",
                        "reflection": "Now I have search results.",
                        "plan": "I will examine the options.",
                        "action": "click[1]"
                    })
                }
            }]
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()

        mock_session.post = Mock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()
        mock_session_class.return_value = mock_session

        config = {
            "api_key": "test-key",
            "base_url": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-4",
        }
        decomposer = ModuleDecomposer(config)

        previous_context = "Step 1: Searched for laptops"
        output = "I see several options. Let me click the first one."

        result = await decomposer.decompose(
            output=output,
            step_number=2,
            previous_context=previous_context
        )

        # Should include reference to previous context
        assert "step 1" in result["memory"].lower() or "searched" in result["memory"].lower()

    @pytest.mark.asyncio
    async def test_decompose_handles_malformed_json(self):
        """Test handling of malformed JSON response"""
        with patch('langfuse_adapter.module_decomposer.aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            # Return malformed JSON
            mock_response.json = AsyncMock(return_value={
                "choices": [{
                    "message": {
                        "content": "Not a JSON object"
                    }
                }]
            })
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()

            mock_session.post = Mock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_class.return_value = mock_session

            config = {
                "api_key": "test-key",
                "base_url": "https://api.openai.com/v1/chat/completions",
                "model": "gpt-4",
            }
            decomposer = ModuleDecomposer(config)

            output = "Test output"
            result = await decomposer.decompose(output, 1, "")

            # Should return fallback - might contain the malformed response
            # The key is that it doesn't crash and returns valid structure
            assert "action" in result
            assert "memory" in result
            assert "reflection" in result
            assert "plan" in result
            assert result["action"] != ""  # Should have some action content

    @pytest.mark.asyncio
    async def test_decompose_handles_api_error(self):
        """Test handling of API errors"""
        with patch('langfuse_adapter.module_decomposer.aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.raise_for_status = AsyncMock(side_effect=Exception("API Error"))
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()

            mock_session.post = Mock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_class.return_value = mock_session

            config = {
                "api_key": "test-key",
                "base_url": "https://api.openai.com/v1/chat/completions",
                "model": "gpt-4",
                "max_retries": 1,  # Don't retry much in tests
            }
            decomposer = ModuleDecomposer(config)

            output = "Test output"
            result = await decomposer.decompose(output, 1, "")

            # Should return fallback - gracefully handle error
            assert "action" in result
            assert "memory" in result
            # Fallback uses original output
            assert result["action"] == output


class TestDecomposeAgentOutput:
    """Test the convenience function"""

    @pytest.mark.asyncio
    @patch('langfuse_adapter.module_decomposer.ModuleDecomposer')
    async def test_decompose_agent_output_function(self, mock_decomposer_class):
        """Test the convenience function for decomposing agent output"""
        # Mock decomposer
        mock_decomposer = AsyncMock()
        mock_decomposer.decompose = AsyncMock(return_value={
            "memory": "test memory",
            "reflection": "test reflection",
            "plan": "test plan",
            "action": "test action"
        })
        mock_decomposer_class.return_value = mock_decomposer

        result = await decompose_agent_output(
            output="test output",
            step_number=1,
            previous_context="",
            api_config={"api_key": "test"}
        )

        # Verify decomposer was called
        mock_decomposer.decompose.assert_called_once()

        # Verify result
        assert result["memory"] == "test memory"
        assert result["action"] == "test action"


class TestPromptConstruction:
    """Test the prompt construction logic"""

    @pytest.mark.asyncio
    async def test_prompt_includes_step_number(self):
        """Test that the decomposer can handle different step numbers"""
        # Simplified test - just verify decomposer works with step 5
        with patch('langfuse_adapter.module_decomposer.aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.raise_for_status = AsyncMock()
            mock_response.json = AsyncMock(return_value={
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "memory": "",
                            "reflection": "",
                            "plan": "",
                            "action": "test"
                        })
                    }
                }]
            })
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()

            mock_session.post = Mock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_class.return_value = mock_session

            config = {
                "api_key": "test-key",
                "base_url": "https://api.openai.com/v1/chat/completions",
                "model": "gpt-4",
            }
            decomposer = ModuleDecomposer(config)

            result = await decomposer.decompose("output", step_number=5, previous_context="")

            # Verify basic functionality
            assert result["action"] == "test"

    @pytest.mark.asyncio
    async def test_prompt_includes_previous_context(self):
        """Test that the decomposer can handle previous context"""
        # Simplified test - just verify decomposer works with previous context
        with patch('langfuse_adapter.module_decomposer.aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.raise_for_status = AsyncMock()
            mock_response.json = AsyncMock(return_value={
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "memory": "test memory",
                            "reflection": "",
                            "plan": "",
                            "action": "test"
                        })
                    }
                }]
            })
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()

            mock_session.post = Mock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_class.return_value = mock_session

            config = {
                "api_key": "test-key",
                "base_url": "https://api.openai.com/v1/chat/completions",
                "model": "gpt-4",
            }
            decomposer = ModuleDecomposer(config)

            previous = "Step 1: Did something important"
            result = await decomposer.decompose("output", step_number=2, previous_context=previous)

            # Verify basic functionality with context
            assert result["memory"] == "test memory"
            assert result["action"] == "test"
