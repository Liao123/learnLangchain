"""带 Bearer Token 验证的 HTTP MCP 服务。"""

from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP


HOST = "127.0.0.1"
PORT = 8012
MCP_URL = f"http://{HOST}:{PORT}/mcp"

# 这是教学用的假 Token，不是真实密钥，也不能用于任何外部服务。
# 生产环境应由 OAuth / 公司身份平台验证 Token，不能像这里一样把值写死。
DEMO_ACCESS_TOKEN = "coffee-demo-token"


class DemoTokenVerifier:
    """教学用验证器：Token 正确就返回“这个客户端拥有哪些权限”。"""

    async def verify_token(self, token: str) -> AccessToken | None:
        # token 的值来自客户端请求头：Authorization: Bearer coffee-demo-token。
        if token != DEMO_ACCESS_TOKEN:
            return None

        # AccessToken 表示服务端确认了调用者身份和权限。
        # scopes=["orders:read"] 表示此调用者只有读取订单的权限。
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
    # required_scopes 表示没有 orders:read 权限的 Token 会被服务端拒绝。
    auth=AuthSettings(
        issuer_url="https://auth.example.com",
        resource_server_url=MCP_URL,
        required_scopes=["orders:read"],
    ),
    token_verifier=DemoTokenVerifier(),
)

ORDERS = {
    "A1001": {"status": "配送中", "estimated_arrival": "今天送达"},
}


@mcp.tool()
def get_order_status(order_id: str) -> dict:
    """根据订单号查询订单状态。调用者必须先通过 HTTP Token 验证。"""
    order = ORDERS.get(order_id)
    if order is None:
        return {"found": False, "message": f"没有找到订单 {order_id}"}

    return {"found": True, "order_id": order_id, **order}


if __name__ == "__main__":
    print(f"受保护的 HTTP MCP 服务已启动：{MCP_URL}")
    print("只有带有效 Bearer Token 的客户端才能读取工具或调用工具。")
    mcp.run(transport="streamable-http")
