# 第 8 课：HTTP MCP 鉴权

## 这节课学什么

远程 MCP 服务不应该谁知道 URL 都能调用。

客户端在 HTTP 请求头带 `Authorization: Bearer <Token>`；服务端验证 Token 和权限后，才允许读取工具、调用工具。

## 这是教学模拟

本课的 `coffee-demo-token` 是公开的假 Token，只用来观察流程，不是密钥。

真实企业里，登录系统或 OAuth 身份平台签发 Token；MCP 服务验证它的签名、过期时间、用户身份和权限。真实 Token 只能放环境变量或密钥管理服务，不能写进代码或提交 Git。

## 第一步：启动服务端

打开第一个 PowerShell，运行：

```powershell
py .\MCPDemo\08_HTTP鉴权\server.py
```

保持这个终端运行。服务地址是：

```text
http://127.0.0.1:8012/mcp
```

## 第二步：设置客户端 Token 并运行

打开第二个 PowerShell，运行：

```powershell
$env:MCP_DEMO_TOKEN = "coffee-demo-token"
py .\MCPDemo\08_HTTP鉴权\client.py
```

你会看到：

```text
鉴权通过，拿到的工具：['get_order_status']
订单查询结果：{"found": true, "order_id": "A1001", "status": "配送中", ...}
```

把 Token 故意改成别的值时，客户端会提示连接受保护服务失败。这代表服务端返回了 `401 Unauthorized`，工具不会被读取或执行。

最后回到第一个终端，按 `Ctrl+C` 停止服务。

## 关键代码

客户端：

```python
"headers": {"Authorization": f"Bearer {token}"}
```

`token` 从 `MCP_DEMO_TOKEN` 环境变量读取。每次连接、读取工具、调用工具时，HTTP 请求都会带这条请求头。

服务端：

```python
async def verify_token(self, token: str) -> AccessToken | None:
```

Token 正确时返回 `AccessToken(scopes=["orders:read"])`；错误时返回 `None`，服务端拒绝请求。

## 你要记住的安全顺序

模型决定“想调用什么工具” -> 客户端发出请求 -> MCP 服务验证 Token 和权限 -> 工具才真正执行。

因此模型的提示词不是权限系统。即使模型被诱导请求订单工具，没有 Token 或没有 `orders:read` 权限，服务端仍应拒绝。

运行后查看 `输出/authenticated_mcp_result.json`。文件只记录 Token 环境变量名，不记录 Token 值。
