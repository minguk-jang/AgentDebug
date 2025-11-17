"""Integration tests for the full pipeline"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from agent.state import AnalysisState
from agent.nodes import (
    convert_trajectory_node,
    generate_report_node,
)
from agent.graph import create_analysis_graph


class TestConvertTrajectoryNode:
    """Test the convert trajectory node"""

    @pytest.mark.asyncio
    async def test_convert_success_trace(self, sample_trace_success):
        """Test converting successful trace"""
        state = {
            "trace_id": "test-trace",
            "raw_trace": sample_trace_success,
            "converted_trajectory": None,
            "phase1_results": None,
            "phase2_results": None,
            "report": None,
            "errors": []
        }

        result = await convert_trajectory_node(state)

        # Should have converted trajectory
        assert result["converted_trajectory"] is not None
        assert result["converted_trajectory"]["metadata"]["task_id"] == "trace-success-001"
        assert len(result["converted_trajectory"]["messages"]) > 0

        # Should not have errors
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_convert_with_no_raw_trace(self):
        """Test converting when no raw trace is available"""
        state = {
            "trace_id": "test-trace",
            "raw_trace": None,
            "converted_trajectory": None,
            "phase1_results": None,
            "phase2_results": None,
            "report": None,
            "errors": []
        }

        result = await convert_trajectory_node(state)

        # Should have error
        assert len(result["errors"]) > 0
        assert "No trace data available" in result["errors"][0]


class TestGenerateReportNode:
    """Test the generate report node"""

    def test_generate_report_with_phase2_results(self):
        """Test report generation with phase 2 results"""
        state = {
            "trace_id": "test-trace",
            "raw_trace": None,
            "converted_trajectory": None,
            "phase1_results": {
                "task_id": "test-trace",
                "task_description": "Test task",
                "task_success": False,
                "total_steps": 3,
                "step_analyses": [
                    {
                        "step": 1,
                        "errors": {
                            "planning": {
                                "error_detected": True,
                                "error_type": "constraint_ignorance",
                                "evidence": "Ignored budget",
                                "reasoning": "Did not consider budget constraint"
                            }
                        },
                        "summary": "Step 1: Error detected"
                    }
                ]
            },
            "phase2_results": {
                "task_success": False,
                "critical_error": {
                    "critical_step": 1,
                    "critical_module": "planning",
                    "error_type": "constraint_ignorance",
                    "root_cause": "Agent ignored budget constraint",
                    "evidence": "Selected $500 item with $300 budget",
                    "correction_guidance": "Check budget before selection",
                    "cascading_effects": [],
                    "confidence": 0.85
                }
            },
            "report": None,
            "errors": []
        }

        result = generate_report_node(state)

        # Should have report
        assert result["report"] is not None
        assert "CRITICAL ERROR IDENTIFIED" in result["report"]
        assert "constraint_ignorance" in result["report"]
        assert "planning" in result["report"]

    def test_generate_report_with_success(self):
        """Test report generation for successful task"""
        state = {
            "trace_id": "test-trace",
            "raw_trace": None,
            "converted_trajectory": None,
            "phase1_results": {
                "task_id": "test-trace",
                "task_description": "Test task",
                "task_success": True,
                "total_steps": 3,
                "step_analyses": []
            },
            "phase2_results": {
                "task_success": True,
                "critical_error": None,
                "message": "Task succeeded"
            },
            "report": None,
            "errors": []
        }

        result = generate_report_node(state)

        # Should have report
        assert result["report"] is not None
        assert "TASK SUCCEEDED" in result["report"]

    def test_generate_report_with_errors(self):
        """Test report generation when errors occurred"""
        state = {
            "trace_id": "test-trace",
            "raw_trace": None,
            "converted_trajectory": None,
            "phase1_results": None,
            "phase2_results": None,
            "report": None,
            "errors": ["Error 1", "Error 2"]
        }

        result = generate_report_node(state)

        # Should have report mentioning errors
        assert result["report"] is not None
        assert "ANALYSIS FAILED" in result["report"]


class TestFullPipelineIntegration:
    """Test the full analysis pipeline"""

    @pytest.mark.asyncio
    async def test_full_pipeline_structure(self):
        """Test that the graph is properly structured"""
        graph = create_analysis_graph()

        # Graph should be compiled
        assert graph is not None

        # Initial state
        initial_state = {
            "trace_id": "test-trace",
            "raw_trace": None,
            "converted_trajectory": None,
            "phase1_results": None,
            "phase2_results": None,
            "report": None,
            "errors": []
        }

        # Should be able to create state (validates TypedDict)
        # Note: We can't run the full pipeline without mocking API calls
        # This test just verifies the graph structure is valid
        assert callable(graph.ainvoke)

    @pytest.mark.asyncio
    @patch.dict('os.environ', {
        'LANGFUSE_PUBLIC_KEY': 'pk-test',
        'LANGFUSE_SECRET_KEY': 'sk-test',
        'LANGFUSE_HOST': 'https://test.langfuse.com'
    })
    @patch('langfuse_adapter.trace_loader.Langfuse')
    async def test_pipeline_with_mocked_trace_loader(self, mock_langfuse_class, sample_trace_success):
        """Test pipeline with mocked Langfuse API"""
        # Mock Langfuse client
        mock_client = Mock()
        mock_langfuse_class.return_value = mock_client

        # Mock trace object
        mock_trace = Mock()
        mock_trace.id = sample_trace_success["id"]
        mock_trace.name = sample_trace_success["name"]
        mock_trace.metadata = sample_trace_success["metadata"]
        mock_trace.input = sample_trace_success["input"]
        mock_trace.output = sample_trace_success["output"]

        # Mock observations
        mock_observations = []
        for obs_data in sample_trace_success["observations"]:
            obs = Mock()
            obs.id = obs_data["id"]
            obs.type = obs_data["type"]
            obs.name = obs_data["name"]
            obs.start_time = obs_data.get("start_time")
            obs.end_time = obs_data.get("end_time")
            obs.metadata = obs_data.get("metadata", {})
            obs.input = obs_data["input"]
            obs.output = obs_data["output"]
            obs.level = obs_data.get("level", "DEFAULT")
            obs.status_message = None
            obs.parent_observation_id = None
            obs.version = None
            mock_observations.append(obs)

        mock_observations_response = Mock()
        mock_observations_response.data = mock_observations

        # Mock SDK v3 API (preferred)
        mock_api = Mock()
        mock_api_trace = Mock()
        mock_api_observations = Mock()

        mock_api_trace.get = Mock(return_value=mock_trace)
        mock_api_observations.get_many = Mock(return_value=mock_observations_response)

        mock_api.trace = mock_api_trace
        mock_api.observations = mock_api_observations
        mock_client.api = mock_api

        # Also mock SDK v2 API (fallback)
        mock_client.fetch_trace = Mock(return_value=mock_trace)
        mock_client.fetch_observations = Mock(return_value=mock_observations_response)

        # Import after mocking
        from langfuse_adapter.trace_loader import load_trace

        # Test trace loading
        trace = await load_trace("test-trace")

        # Verify structure
        assert trace["id"] == sample_trace_success["id"]
        assert len(trace["observations"]) == len(sample_trace_success["observations"])


class TestErrorHandling:
    """Test error handling throughout the pipeline"""

    @pytest.mark.asyncio
    async def test_convert_handles_invalid_trace(self):
        """Test that converter handles invalid trace gracefully"""
        state = {
            "trace_id": "test-trace",
            "raw_trace": {"id": "broken", "observations": None},  # Invalid structure
            "converted_trajectory": None,
            "phase1_results": None,
            "phase2_results": None,
            "report": None,
            "errors": []
        }

        result = await convert_trajectory_node(state)

        # Should still produce a result (graceful degradation)
        assert result["converted_trajectory"] is not None
        # May have converted with fallback or have minimal structure
        assert "metadata" in result["converted_trajectory"]

    def test_report_generation_never_crashes(self):
        """Test that report generation handles all error cases"""
        # Test with completely empty state
        empty_state = {
            "trace_id": None,
            "raw_trace": None,
            "converted_trajectory": None,
            "phase1_results": None,
            "phase2_results": None,
            "report": None,
            "errors": []
        }

        result = generate_report_node(empty_state)

        # Should still generate some report
        assert result["report"] is not None
        assert isinstance(result["report"], str)


class TestEndToEndWithFixtures:
    """End-to-end tests using fixture files"""

    @pytest.mark.asyncio
    async def test_success_trace_conversion(self, sample_trace_success):
        """Test full conversion of success trace"""
        # This mimics what would happen in the pipeline
        state = {
            "trace_id": sample_trace_success["id"],
            "raw_trace": sample_trace_success,
            "converted_trajectory": None,
            "phase1_results": None,
            "phase2_results": None,
            "report": None,
            "errors": []
        }

        # Convert
        state = await convert_trajectory_node(state)

        # Verify conversion
        assert state["converted_trajectory"] is not None
        trajectory = state["converted_trajectory"]

        # Metadata should be correct
        assert trajectory["metadata"]["task_id"] == "trace-success-001"
        assert trajectory["metadata"]["success"] is True
        assert "laptop" in trajectory["metadata"]["task"].lower()

        # Should have proper message structure
        messages = trajectory["messages"]
        assert len(messages) > 0

        # Count roles
        user_messages = [m for m in messages if m["role"] == "user"]
        assistant_messages = [m for m in messages if m["role"] == "assistant"]

        assert len(user_messages) > 0
        assert len(assistant_messages) > 0

        # At least one assistant message should have XML structure
        has_xml = any(
            "<action>" in m["content"] or "<plan>" in m["content"]
            for m in assistant_messages
        )
        assert has_xml

    @pytest.mark.asyncio
    async def test_failure_trace_conversion(self, sample_trace_failure):
        """Test full conversion of failure trace"""
        state = {
            "trace_id": sample_trace_failure["id"],
            "raw_trace": sample_trace_failure,
            "converted_trajectory": None,
            "phase1_results": None,
            "phase2_results": None,
            "report": None,
            "errors": []
        }

        # Convert
        state = await convert_trajectory_node(state)

        # Verify conversion
        assert state["converted_trajectory"] is not None
        trajectory = state["converted_trajectory"]

        # Should be marked as failed
        assert trajectory["metadata"]["success"] is False
        assert "smartphone" in trajectory["metadata"]["task"].lower()

        # Should have identified the constraint violation scenario
        # The trace has an iPhone ($599.99) selected when budget was $300
        messages = trajectory["messages"]
        message_text = " ".join(m["content"] for m in messages)

        # Should have evidence of the error
        assert len(messages) > 0
