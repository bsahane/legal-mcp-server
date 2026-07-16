# Indian Legal MCP Server

## MCP Tools Available

This project provides an MCP server with Indian legal tools. When asked about Indian law, statutes, legal scenarios, or legal documents, use the `indian-legal-mcp` MCP server tools.

Available tools:
- `legal_search` — Search Indian statutes by query or section number (type="statute")
- `explain_situation` — Get plain-language explanation of a legal scenario
- `submit_feedback` — Report errors in tool outputs (privacy-safe)

## How to use

Start the MCP server before using:
```bash
cd /path/to/indian-legal-mcp-server
uvicorn indian_legal_mcp_server.src.api:app --host 0.0.0.0 --port 5001
```

Then use `indian-legal-mcp` tools in prompts. For example:
- "Search section 144 BNSS using the legal_search tool"
- "Explain this situation: my brother was arrested without FIR"
