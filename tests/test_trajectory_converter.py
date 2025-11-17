"""Tests for trajectory_converter module"""

import pytest
from langfuse_adapter.trajectory_converter import (
    convert_langfuse_to_agentdebug,
    _infer_success,
    _extract_task_description,
    _format_assistant_message,
    _format_user_message,
)


class TestConvertLangfuseToAgentDebug:
    """Test main conversion function"""

    def test_convert_success_trace(self, sample_trace_success):
        """Test conversion of successful trace"""
        result = convert_langfuse_to_agentdebug(sample_trace_success)

        # Check metadata
        assert result["metadata"]["task_id"] == "trace-success-001"
        assert result["metadata"]["success"] is True
        assert "laptop under $500" in result["metadata"]["task"]
        assert result["metadata"]["environment"] == "webshop"

        # Check messages
        assert "messages" in result
        assert len(result["messages"]) > 0

        # First message should be user message
        assert result["messages"][0]["role"] == "user"

        # Should have assistant messages with XML structure
        assistant_messages = [m for m in result["messages"] if m["role"] == "assistant"]
        assert len(assistant_messages) > 0

        # Check that at least one assistant message has proper XML format
        has_xml_format = any(
            "<action>" in m["content"] or "<plan>" in m["content"]
            for m in assistant_messages
        )
        assert has_xml_format, "Should have at least one message with XML format"

    def test_convert_failure_trace(self, sample_trace_failure):
        """Test conversion of failed trace"""
        result = convert_langfuse_to_agentdebug(sample_trace_failure)

        # Check metadata
        assert result["metadata"]["task_id"] == "trace-failure-002"
        assert result["metadata"]["success"] is False
        assert "smartphone under $300" in result["metadata"]["task"]

        # Should still have messages
        assert len(result["messages"]) > 0

    def test_convert_minimal_trace(self, sample_trace_minimal):
        """Test conversion of minimal trace structure"""
        result = convert_langfuse_to_agentdebug(sample_trace_minimal)

        # Should not crash and return valid structure
        assert "metadata" in result
        assert "messages" in result
        assert result["metadata"]["task_id"] == "trace-minimal-003"

    def test_convert_empty_trace(self):
        """Test conversion with empty trace"""
        empty_trace = {
            "id": "empty-trace",
            "observations": []
        }

        result = convert_langfuse_to_agentdebug(empty_trace)

        # Should still return valid structure with fallback
        assert "metadata" in result
        assert "messages" in result
        assert len(result["messages"]) >= 1  # At least fallback messages


class TestInferSuccess:
    """Test success inference logic"""

    def test_infer_from_metadata_success(self):
        """Test inferring success from metadata.success"""
        trace = {"metadata": {"success": True}}
        assert _infer_success(trace) is True

    def test_infer_from_metadata_won(self):
        """Test inferring success from metadata.won"""
        trace = {"metadata": {"won": True}}
        assert _infer_success(trace) is True

    def test_infer_from_output_dict(self):
        """Test inferring success from output dict"""
        trace = {"output": {"success": True}}
        assert _infer_success(trace) is True

    def test_infer_from_output_string(self):
        """Test inferring success from output string"""
        trace = {"output": "Task completed successfully"}
        assert _infer_success(trace) is True

    def test_infer_default_false(self):
        """Test default to False when no success indicators"""
        trace = {"metadata": {}, "output": None}
        assert _infer_success(trace) is False


class TestExtractTaskDescription:
    """Test task description extraction"""

    def test_extract_from_metadata_task(self):
        """Test extracting from metadata.task"""
        trace = {"metadata": {"task": "Find a product"}}
        assert _extract_task_description(trace) == "Find a product"

    def test_extract_from_trace_name(self):
        """Test extracting from trace name"""
        trace = {"name": "product-search-task", "metadata": {}}
        assert _extract_task_description(trace) == "product-search-task"

    def test_extract_from_input_dict(self):
        """Test extracting from input dict"""
        trace = {"input": {"task": "Complete the task"}, "metadata": {}}
        assert _extract_task_description(trace) == "Complete the task"

    def test_extract_from_input_string(self):
        """Test extracting from input string"""
        trace = {"input": "Task: Find items\nDescription...", "metadata": {}}
        result = _extract_task_description(trace)
        assert "Find items" in result

    def test_extract_default(self):
        """Test default when no task found"""
        trace = {"metadata": {}}
        assert _extract_task_description(trace) == "Unknown task"


class TestFormatAssistantMessage:
    """Test assistant message formatting"""

    def test_format_xml_passthrough(self):
        """Test that existing XML format passes through"""
        output = "<memory>test</memory><action>do_something</action>"
        result = _format_assistant_message(output, {})
        assert result == output

    def test_format_from_metadata(self):
        """Test formatting from metadata"""
        output = "some output"
        metadata = {
            "memory": "remembered info",
            "plan": "next steps",
            "action": "execute"
        }
        result = _format_assistant_message(output, metadata)

        assert "<memory>remembered info</memory>" in result
        assert "<plan>next steps</plan>" in result
        assert "<action>execute</action>" in result

    def test_format_from_dict(self):
        """Test formatting from dict output"""
        output = {
            "memory": "info",
            "reflection": "thinking",
            "plan": "planning",
            "action": "act"
        }
        result = _format_assistant_message(output, {})

        assert "<memory>info</memory>" in result
        assert "<reflection>thinking</reflection>" in result
        assert "<plan>planning</plan>" in result
        assert "<action>act</action>" in result

    def test_format_plain_string(self):
        """Test formatting plain string as action"""
        output = "just some text"
        result = _format_assistant_message(output, {})

        assert "<action>just some text</action>" == result

    def test_format_empty_output(self):
        """Test formatting empty output"""
        result = _format_assistant_message("", {})
        assert "<action>No output</action>" == result


class TestFormatUserMessage:
    """Test user message formatting"""

    def test_format_string(self):
        """Test formatting plain string"""
        content = "User message"
        result = _format_user_message(content)
        assert result == "User message"

    def test_format_dict_with_content(self):
        """Test formatting dict with content field"""
        content = {"content": "Message text"}
        result = _format_user_message(content)
        assert result == "Message text"

    def test_format_dict_with_messages(self):
        """Test formatting dict with messages array"""
        content = {
            "messages": [
                {"role": "system", "content": "System"},
                {"role": "user", "content": "User message"}
            ]
        }
        result = _format_user_message(content)
        assert result == "User message"

    def test_format_dict_fallback(self):
        """Test formatting dict without special fields"""
        content = {"data": "value"}
        result = _format_user_message(content)
        assert "data" in result


class TestAgentDebugFormatValidation:
    """Test that output matches AgentDebug expected format"""

    def test_success_trace_has_required_fields(self, sample_trace_success):
        """Test that converted trace has all required fields"""
        result = convert_langfuse_to_agentdebug(sample_trace_success)

        # Required top-level fields
        assert "metadata" in result
        assert "messages" in result

        # Required metadata fields
        assert "task_id" in result["metadata"]
        assert "environment" in result["metadata"]
        assert "success" in result["metadata"]
        assert "task" in result["metadata"]

        # Messages should be list of dicts with role and content
        for msg in result["messages"]:
            assert "role" in msg
            assert "content" in msg
            assert msg["role"] in ["user", "assistant"]
            assert isinstance(msg["content"], str)

    def test_assistant_messages_have_module_structure(self, sample_trace_success):
        """Test that assistant messages follow module structure"""
        result = convert_langfuse_to_agentdebug(sample_trace_success)

        assistant_messages = [
            m for m in result["messages"] if m["role"] == "assistant"
        ]

        # At least one assistant message should have module tags
        for msg in assistant_messages:
            content = msg["content"]
            # Should have at least action tag
            assert "<action>" in content or "<plan>" in content, \
                f"Message should have module tags: {content[:100]}"
