from langchain_mcp_adapters.client import MultiServerMCPClient

mcp_client = MultiServerMCPClient(
  {
    # "yfinance": {
    #   "command": "uv",
    #   "args": [
    #     "--directory",
    #     "/Users/1113744/Projs/Personal/new-langgraph-project/src/tools",
    #     "run",
    #     "finance_server.py"
    #   ],
    #   "transport": "stdio"
    # },
    "exa": {
        "command": "npx",
        "args": [
          "-y",
          "@smithery/cli@latest",
          "run",
          "exa",
          "--key",
          "c31e34f2-14e5-4e2e-8da8-bfc125e9b36d",
          "--profile",
          "estimated-spider-QbBpTs"
        ],
        "transport": "stdio"
    }
  }
)


async def get_tools():
    tools = await mcp_client.get_tools()
    return tools
