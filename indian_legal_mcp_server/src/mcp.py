"""Indian Legal MCP Server implementation.

Registers 5 consolidated MCP tools + 1 utility tool for Indian legal research.
v0.1 ships: legal_search, explain_situation, submit_feedback.
"""

from fastmcp import FastMCP

from indian_legal_mcp_server.src.settings import settings
from indian_legal_mcp_server.src.tools.explain_situation import explain_situation
from indian_legal_mcp_server.src.tools.legal_compute import legal_compute
from indian_legal_mcp_server.src.tools.legal_lookup import legal_lookup
from indian_legal_mcp_server.src.tools.legal_search import legal_search
from indian_legal_mcp_server.src.tools.submit_feedback import submit_feedback
from indian_legal_mcp_server.utils.pylogger import (
    force_reconfigure_all_loggers,
    get_python_logger,
)

logger = get_python_logger()


class IndianLegalMCPServer:
    """Main Indian Legal MCP Server implementation following tools-first architecture."""

    def __init__(self):
        try:
            self.mcp = FastMCP("indian-legal")

            force_reconfigure_all_loggers(settings.PYTHON_LOG_LEVEL)

            self._register_mcp_tools()

            logger.info("Indian Legal MCP Server initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Indian Legal MCP Server: {e}")
            raise

    def _register_mcp_tools(self) -> None:
        """Register MCP tools.

        v0.1: legal_search, explain_situation, submit_feedback
        v0.5: + legal_compute, legal_lookup
        v1.0: + draft_document
        """
        self.mcp.tool()(legal_search)
        self.mcp.tool()(explain_situation)
        self.mcp.tool()(submit_feedback)
        self.mcp.tool()(legal_compute)
        self.mcp.tool()(legal_lookup)
