from unittest.mock import patch, MagicMock

from langchain.tools import BaseTool
import pytest

from neuro_san.internals.run_context.langchain.base_tool_factory import BaseToolFactory


class TestBaseToolFactory:
    """Simplified test suite for BaseToolFactory."""

    @pytest.fixture
    def factory(self):
        """Fixture to provide a fresh instance of BaseToolFactory."""
        return BaseToolFactory()

    def test_create_agent_tool(self, factory):
        """Test that the tool is resolved with correct arguments."""
        # Mock base_tool_infos (as if loaded by load method)
        factory.base_tool_infos = {
            "test_tool": {
                "class": "mock_package.mock_module.TestTool",
                "args": {"param1": "value1", "param2": "value2"}
            }
        }

        # Mock user-provided arguments
        user_args = {"param2": "user_value", "param3": "extra_value"}

        with patch("leaf_common.config.resolver.Resolver.resolve_class_in_module") as mock_resolver:
            # Mock class resolution
            mock_tool_class = MagicMock(spec=BaseTool)
            mock_resolver.return_value = mock_tool_class

            # Create tool
            tool = factory.create_agent_tool("test_tool", user_args)

            # Ensure the correct class was resolved
            mock_resolver.assert_called_once_with("TestTool", module_name="mock_module")

            # Ensure the tool was initialized with the correct merged args
            mock_tool_class.assert_called_once_with(param1="value1", param2="user_value", param3="extra_value")

            # Ensure the returned tool is an instance of the mocked class
            assert tool is mock_tool_class.return_value
