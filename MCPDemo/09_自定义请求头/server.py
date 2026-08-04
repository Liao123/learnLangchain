"""通过 HTTP 中间件读取 X-App-ID，再决定是否放行 MCP 请求。"""

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


HOST = "127.0.0.1"
PORT = 8013
MCP_URL = f"http://{HOST}:{PORT}/mcp"
EXPECTED_APP_ID = "coffee-customer-agent"

# FastMCP 仍然负责 MCP 协议、工具注册和工具调用。
mcp = FastMCP("星光咖啡 App ID 示例服务", host=HOST, port=PORT)


class RequireAppIdMiddleware(BaseHTTPMiddleware):
    """每个 HTTP 请求到达 MCP 端点前，先检查自定义 X-App-ID 请求头。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        # request.headers.get("X-App-ID") 的值来自客户端 headers 配置。
        # 正确示例："coffee-customer-agent"；没有或错误时，直接返回 403。
        if request.url.path == "/mcp":
            app_id = request.headers.get("X-App-ID")
            if app_id != EXPECTED_APP_ID:
                return JSONResponse(
                    status_code=403,
                    content={"error": "app_id_not_allowed", "message": "X-App-ID 不在允许列表中。"},
                )

        # 只有通过检查的请求才会交给 FastMCP 的 /mcp 端点继续处理。
        return await call_next(request)


ORDERS = {
    "A1001": {"status": "配送中", "estimated_arrival": "今天送达"},
}


@mcp.tool()
def get_order_status(order_id: str) -> dict:
    """根据订单号查询订单状态。只有被允许的 App ID 能调用。"""
    order = ORDERS.get(order_id)
    if order is None:
        return {"found": False, "message": f"没有找到订单 {order_id}"}

    return {"found": True, "order_id": order_id, **order}


# streamable_http_app() 生成 FastMCP 的 HTTP 应用对象。
# add_middleware(...) 把我们自己的 App ID 检查包在 MCP 端点外面。
app = mcp.streamable_http_app()
app.add_middleware(RequireAppIdMiddleware)


if __name__ == "__main__":
    print(f"带 X-App-ID 检查的 HTTP MCP 服务已启动：{MCP_URL}")
    print(f"允许的教学 App ID：{EXPECTED_APP_ID}")
    # 这里不用 mcp.run()，因为要先把 FastMCP HTTP app 包进自定义中间件后再启动。
    uvicorn.run(app, host=HOST, port=PORT)
