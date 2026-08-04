# 第 9 课：自定义请求头

## 这节课学什么

客户端发送：

```text
X-App-ID: coffee-customer-agent
```

服务端 HTTP 中间件读取这个 Header；允许时才把请求交给 MCP，错误时直接返回 `403`。

## 这正好回答上一个问题

`Authorization: Bearer ...` 会被 FastMCP 内置鉴权拿去调用 `verify_token(token)`。

`X-App-ID` 不会自动进 `verify_token()`。服务端必须自己写中间件读取：

```python
app_id = request.headers.get("X-App-ID")
```

## 第一步：启动服务端

终端一运行：

```powershell
py .\MCPDemo\09_自定义请求头\server.py
```

## 第二步：设置 App ID 并运行客户端

终端二运行：

```powershell
$env:MCP_DEMO_APP_ID = "coffee-customer-agent"
py .\MCPDemo\09_自定义请求头\client.py
```

成功时会看到：

```text
App ID 已通过服务端检查，拿到的工具：['get_order_status']
```

如果把环境变量改成 `other-app`，服务端会返回 `403`，客户端不会拿到工具。

## 新 API 只看这三行

```python
app = mcp.streamable_http_app()
app.add_middleware(RequireAppIdMiddleware)
uvicorn.run(app, host=HOST, port=PORT)
```

以前 `mcp.run(...)` 直接启动 FastMCP。

这次先拿到 FastMCP 的 HTTP 应用 `app`，包一层自己的 HTTP 中间件，再由 `uvicorn` 启动。这样才能处理自定义 Header。

## 很重要的安全说明

App ID 只是“客户端叫什么”，任何人都能伪造 `X-App-ID`。

因此它不能单独当作身份凭证。本课只演示自定义 Header 怎么被使用。

真实项目通常同时使用：

```text
Authorization Token：证明调用者身份和权限。
X-App-ID：标识是哪一个应用。
服务端 / API 网关：验证 Token，并确认该 Token 是否允许这个 App ID。
```

运行后查看 `输出/custom_header_result.json`。
