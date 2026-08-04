"""在 MCP 工具执行时记录服务端审计日志。"""

import json
from datetime import datetime
from pathlib import Path

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP


HOST = "127.0.0.1"
PORT = 8016
MCP_URL = f"http://{HOST}:{PORT}/mcp"
LESSON_DIR = Path(__file__).resolve().parent
AUDIT_LOG_PATH = LESSON_DIR / "输出" / "audit_log.jsonl"

# 教学用 Token 身份数据。真实项目由 OAuth/JWT/SSO 验证服务提供。
ACCESS_TOKENS = {
    "member-u1001-token": AccessToken(
        token="member-u1001-token",
        client_id="coffee-customer-agent",
        subject="U1001",
        scopes=["orders:read"],
    ),
    "support-agent-token": AccessToken(
        token="support-agent-token",
        client_id="coffee-support-agent",
        subject="support-001",
        scopes=["orders:read", "orders:read:any"],
    ),
}


class DemoTokenVerifier:
    async def verify_token(self, token: str) -> AccessToken | None:
        return ACCESS_TOKENS.get(token)


mcp = FastMCP(
    "星光咖啡订单审计服务",
    host=HOST,
    port=PORT,
    auth=AuthSettings(
        issuer_url="https://auth.example.com",
        resource_server_url=MCP_URL,
    ),
    token_verifier=DemoTokenVerifier(),
)

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


def append_audit_log(
    access_token: AccessToken | None,
    order_id: str,
    outcome: str,
    reason: str | None = None,
) -> None:
    """把本次工具调用追加为一行审计 JSON。"""
    # 正常成功时 event 的值大致是：
    # {"actor": "U1001", "client_id": "coffee-customer-agent", "tool_name": "get_order_status",
    #  "order_id": "A1001", "outcome": "success", "reason": None, ...}
    event = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "actor": access_token.subject if access_token else None,
        "client_id": access_token.client_id if access_token else None,
        "scopes": access_token.scopes if access_token else [],
        "tool_name": "get_order_status",
        "order_id": order_id,
        "outcome": outcome,
        "reason": reason,
    }

    # "a" 是追加模式：第 2 次调用会写在第 1 行后面，不会覆盖旧审计记录。
    # JSONL 的意思是一行一个 JSON 对象，适合不断追加日志。
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as audit_file:
        audit_file.write(json.dumps(event, ensure_ascii=False) + "\n")


@mcp.tool()
def get_order_status(order_id: str) -> dict:
    """查询订单状态，并在服务端记录成功或拒绝的审计事件。"""
    access_token = get_access_token()
    if access_token is None:
        append_audit_log(None, order_id, "denied", "authenticated_token_not_found")
        return {"ok": False, "error": "authenticated_token_not_found"}

    if "orders:read" not in access_token.scopes:
        append_audit_log(access_token, order_id, "denied", "missing_orders_read_scope")
        return {"ok": False, "error": "missing_orders_read_scope"}

    order = ORDERS.get(order_id)
    if order is None:
        append_audit_log(access_token, order_id, "not_found", "order_not_found")
        return {"ok": False, "error": "order_not_found", "message": "没有找到该订单。"}

    is_owner = order["owner_user_id"] == access_token.subject
    can_read_any_order = "orders:read:any" in access_token.scopes
    if not is_owner and not can_read_any_order:
        append_audit_log(access_token, order_id, "denied", "order_access_denied")
        return {"ok": False, "error": "order_access_denied", "message": "当前身份无权查看这笔订单。"}

    append_audit_log(access_token, order_id, "success")
    return {
        "ok": True,
        "order_id": order_id,
        "status": order["status"],
        "estimated_arrival": order["estimated_arrival"],
    }


if __name__ == "__main__":
    AUDIT_LOG_PATH.parent.mkdir(exist_ok=True)
    print(f"带审计日志的 HTTP MCP 服务已启动：{MCP_URL}")
    print(f"审计日志文件：{AUDIT_LOG_PATH}")
    mcp.run(transport="streamable-http")
