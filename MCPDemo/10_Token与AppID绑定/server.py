"""教学版网关：验证 Token、App ID 和 scope 的对应关系后才放行 MCP。"""

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


HOST = "127.0.0.1"
PORT = 8014
MCP_URL = f"http://{HOST}:{PORT}/mcp"

# 这张表模拟“身份平台已经验证 Token 后得到的可信身份数据”。
# 真实项目不会把 Token 写死在代码里，而会验证 OAuth/JWT 后取得同样结构的信息。
# 例如 customer-agent-token 只能代表 coffee-customer-agent，且有 orders:read 权限。
TOKEN_IDENTITIES = {
    "customer-agent-token": {
        "app_id": "coffee-customer-agent",
        "scopes": ["orders:read"],
    },
    "menu-agent-token": {
        "app_id": "coffee-menu-agent",
        "scopes": ["menu:read"],
    },
}

mcp = FastMCP("星光咖啡双重验证订单服务", host=HOST, port=PORT)


class RequireVerifiedClientMiddleware(BaseHTTPMiddleware):
    """同时检查 Bearer Token、X-App-ID 和 orders:read 权限。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path != "/mcp":
            return await call_next(request)

        # 1. 从 Authorization: Bearer customer-agent-token 中取出 Token 正文。
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"error": "missing_bearer_token"})
        token = authorization.removeprefix("Bearer ")

        # 2. 用 Token 找可信身份。token 不在表中，说明它无效，返回 401。
        identity = TOKEN_IDENTITIES.get(token)
        if identity is None:
            return JSONResponse(status_code=401, content={"error": "invalid_token"})

        # 3. App ID 必须和 Token 对应的 app_id 一致，不能由客户端随便冒充。
        request_app_id = request.headers.get("X-App-ID")
        if request_app_id != identity["app_id"]:
            return JSONResponse(
                status_code=403,
                content={"error": "app_id_does_not_match_token"},
            )

        # 4. 即使 Token 和 App ID 对得上，没有订单读取权限也不能进入 MCP。
        if "orders:read" not in identity["scopes"]:
            return JSONResponse(status_code=403, content={"error": "missing_orders_read_scope"})

        # 四项检查都通过，才把原始请求交给 FastMCP。
        return await call_next(request)


ORDERS = {
    "A1001": {"status": "配送中", "estimated_arrival": "今天送达"},
}


@mcp.tool()
def get_order_status(order_id: str) -> dict:
    """根据订单号查询订单状态。网关验证通过后才可能执行。"""
    order = ORDERS.get(order_id)
    if order is None:
        return {"found": False, "message": f"没有找到订单 {order_id}"}

    return {"found": True, "order_id": order_id, **order}


app = mcp.streamable_http_app()
app.add_middleware(RequireVerifiedClientMiddleware)


if __name__ == "__main__":
    print(f"带 Token、App ID、scope 绑定检查的 MCP 服务已启动：{MCP_URL}")
    uvicorn.run(app, host=HOST, port=PORT)
