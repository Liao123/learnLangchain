"""需要 Bearer Token 的 HTTP MCP 服务。"""

from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP


HOST = "127.0.0.1"
PORT = 8018
MCP_URL = f"http://{HOST}:{PORT}/mcp"
DEMO_ACCESS_TOKEN = "coffee-demo-token"


class DemoTokenVerifier:
    async def verify_token(self, token: str) -> AccessToken | None:
        if token != DEMO_ACCESS_TOKEN:
            return None
        return AccessToken(
            token=token,
            client_id="coffee-demo-client",
            subject="student-demo-user",
            scopes=["orders:read"],
        )


mcp = FastMCP(
    "星光咖啡受保护订单服务",
    host=HOST,
    port=PORT,
    auth=AuthSettings(
        issuer_url="https://auth.example.com",
        resource_server_url=MCP_URL,
        required_scopes=["orders:read"],
    ),
    token_verifier=DemoTokenVerifier(),
)


@mcp.tool()
def get_order_status(order_id: str) -> dict:
    """根据订单号查询订单状态。"""
    if order_id != "A1001":
        return {"found": False, "message": "没有找到该订单。"}
    return {
        "found": True,
        "order_id": "A1001",
        "status": "配送中",
        "estimated_arrival": "今天送达",
    }


if __name__ == "__main__":
    print(f"受保护的订单 MCP 服务已启动：{MCP_URL}")
    mcp.run(transport="streamable-http")
