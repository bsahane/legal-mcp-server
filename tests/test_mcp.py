"""Tests for the MCP server module."""

from unittest.mock import Mock, patch

import pytest

from indian_legal_mcp_server.src.mcp import IndianLegalMCPServer


class TestIndianLegalMCPServer:
    """Test the IndianLegalMCPServer class."""

    @patch("indian_legal_mcp_server.src.mcp.force_reconfigure_all_loggers")
    @patch("indian_legal_mcp_server.src.mcp.settings")
    @patch("indian_legal_mcp_server.src.mcp.FastMCP")
    @patch("indian_legal_mcp_server.src.mcp.logger")
    def test_init_success(
        self, mock_logger, mock_fastmcp, mock_settings, mock_force_reconfigure
    ):
        mock_mcp = Mock()
        mock_fastmcp.return_value = mock_mcp
        mock_settings.PYTHON_LOG_LEVEL = "INFO"

        server = IndianLegalMCPServer()

        assert server.mcp == mock_mcp
        mock_logger.info.assert_called_with(
            "Indian Legal MCP Server initialized successfully"
        )
        mock_mcp.tool.assert_called()

    @patch("indian_legal_mcp_server.src.mcp.force_reconfigure_all_loggers")
    @patch("indian_legal_mcp_server.src.mcp.settings")
    @patch("indian_legal_mcp_server.src.mcp.FastMCP")
    @patch("indian_legal_mcp_server.src.mcp.logger")
    def test_init_failure(
        self, mock_logger, mock_fastmcp, mock_settings, mock_force_reconfigure
    ):
        mock_fastmcp.side_effect = Exception("Test error")
        mock_settings.PYTHON_LOG_LEVEL = "INFO"

        with pytest.raises(Exception, match="Test error"):
            IndianLegalMCPServer()

        mock_logger.error.assert_called_with(
            "Failed to initialize Indian Legal MCP Server: Test error"
        )

    @patch("indian_legal_mcp_server.src.mcp.force_reconfigure_all_loggers")
    @patch("indian_legal_mcp_server.src.mcp.settings")
    @patch("indian_legal_mcp_server.src.mcp.FastMCP")
    def test_register_mcp_tools(
        self, mock_fastmcp, mock_settings, mock_force_reconfigure
    ):
        mock_mcp = Mock()
        mock_fastmcp.return_value = mock_mcp
        mock_settings.PYTHON_LOG_LEVEL = "INFO"
        server = IndianLegalMCPServer()

        server._register_mcp_tools()

        mock_mcp.tool.assert_called()

    @patch("indian_legal_mcp_server.src.mcp.force_reconfigure_all_loggers")
    @patch("indian_legal_mcp_server.src.mcp.settings")
    @patch("indian_legal_mcp_server.src.mcp.FastMCP")
    def test_register_mcp_tools_functionality(
        self, mock_fastmcp, mock_settings, mock_force_reconfigure
    ):
        mock_mcp = Mock()
        mock_fastmcp.return_value = mock_mcp
        mock_settings.PYTHON_LOG_LEVEL = "INFO"
        server = IndianLegalMCPServer()

        server._register_mcp_tools()

        assert mock_mcp.tool.call_count >= 2

    def test_server_attributes(self):
        with (
            patch("indian_legal_mcp_server.src.mcp.settings") as mock_settings,
            patch("indian_legal_mcp_server.src.mcp.FastMCP"),
            patch("indian_legal_mcp_server.src.mcp.force_reconfigure_all_loggers"),
        ):
            mock_settings.PYTHON_LOG_LEVEL = "INFO"
            server = IndianLegalMCPServer()

        assert hasattr(server, "mcp")
        assert hasattr(server, "_register_mcp_tools")

    def test_tools_first_architecture_compliance(self):
        with (
            patch("indian_legal_mcp_server.src.mcp.settings") as mock_settings,
            patch("indian_legal_mcp_server.src.mcp.FastMCP"),
            patch("indian_legal_mcp_server.src.mcp.force_reconfigure_all_loggers"),
        ):
            mock_settings.PYTHON_LOG_LEVEL = "INFO"
            server = IndianLegalMCPServer()

        assert not hasattr(server, "_register_mcp_resources")
        assert not hasattr(server, "_register_mcp_prompts")
