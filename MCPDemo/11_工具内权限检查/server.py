"""在 MCP 工具内部根据已验证 Token 的 subject 和 scopes 做订单权限检查。"""

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP


HOST = "127.0.0.1"
PORT = 8015
MCP_URL = f"http://{HOST}:{PORT}/mcp"

# 这是教学用的身份平台结果。真实项目会由 OAuth/JWT 验证产生这些 AccessToken 信息。
ACCESS_TOKENS = {
    # 普通会员 U1001：只能读取自己订单。
    "member-u1001-token": AccessToken(
        token="member-u1001-token",
        client_id="coffee-customer-agent",
        subject="U1001",
        scopes=["orders:read"],
    ),
    # 菜单 Agent：Token 有效，但没有订单读取权限。
    "menu-agent-token": AccessToken(
        token="menu-agent-token",
        client_id="coffee-menu-agent",
        subject="service-menu",
        scopes=["menu:read"],
    ),
    # 客服专员：有 orders:read:any，能查看任意用户订单。
    "support-agent-token": AccessToken(
        token="support-agent-token",
        client_id="coffee-support-agent",
        subject="support-001",
        scopes=["orders:read", "orders:read:any"],
    ),
}


class DemoTokenVerifier:
    """教学用：把请求 Token 转成服务端可信的 AccessToken。"""

    async def verify_token(self, token: str) -> AccessToken | None:
        return ACCESS_TOKENS.get(token)


mcp = FastMCP(
    "星光咖啡订单权限服务",
    host=HOST,
    port=PORT,
    # 这里不设置 required_scopes：所有有效 Token 都能连接。
    # 每个具体工具再按自己的业务规则检查 scope 和订单归属。
    auth=AuthSettings(
        issuer_url="https://auth.example.com",
        resource_server_url=MCP_URL,
    ),
    token_verifier=DemoTokenVerifier(),
)

# owner_user_id 是服务端内部数据，最终返回给客户端时不会包含它。
ORDERS = {
    "A1001": {
        "owner_user_id": "U1001",
        "status": "配送中",
        "estimated_arrival": "今天送达",
    },
    "A1002": {
        "owner_user_id": "U2002",
        "status": "已完成",
        "estimated_arrival": "已送达",
    },
}


@mcp.tool()
def get_order_status(order_id: str) -> dict:
    """查询订单状态。普通会员只能查询自己订单，客服专员可查询任意订单。"""
    # 这个函数返回当前 HTTP 请求已经通过验证的 AccessToken。
    # 对 member-u1001-token 而言，值大致是：
    # AccessToken(subject="U1001", scopes=["orders:read"], ...)
    access_token = get_access_token()
    if access_token is None:
        # 正常请求不会走到这里；没有有效 Token 的请求会在进入 MCP 前被拦住。
        return {"ok": False, "error": "authenticated_token_not_found"}

    if "orders:read" not in access_token.scopes:
        return {
            "ok": False,
            "error": "missing_orders_read_scope",
            "message": "当前身份没有查询订单的权限。",
        }

    order = ORDERS.get(order_id)
    if order is None:
        return {"ok": False, "error": "order_not_found", "message": "没有找到该订单。"}

    # 只有订单主人，或拥有 orders:read:any 的客服身份，才能看到订单状态。
    is_owner = order["owner_user_id"] == access_token.subject
    can_read_any_order = "orders:read:any" in access_token.scopes
    if not is_owner and not can_read_any_order:
        return {
            "ok": False,
            "error": "order_access_denied",
            "message": "当前身份无权查看这笔订单。",
        }

    return {
        "ok": True,
        "order_id": order_id,
        "status": order["status"],
        "estimated_arrival": order["estimated_arrival"],
    }


if __name__ == "__main__":
    print(f"带工具内权限检查的 HTTP MCP 服务已启动：{MCP_URL}")
    mcp.run(transport="streamable-http")
