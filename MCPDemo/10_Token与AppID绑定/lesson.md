# 第 10 课：Token 与 App ID 绑定

## 这节课学什么

不能只检查 Token 有效，也不能只检查 `X-App-ID` 在名单里。

服务端要确认三件事：

```text
Token 是有效的
Token 属于当前 X-App-ID
Token 有调用订单工具的 orders:read 权限
```

## 为什么需要这一步

假设客户客服 Agent 的 Token 有订单权限，但它在请求头伪造：

```text
X-App-ID: coffee-menu-agent
```

如果服务端只检查“两个值各自存在”，就可能造成身份混乱。

这课要求它们必须配对：

```text
customer-agent-token <-> coffee-customer-agent <-> orders:read
```

## 第一步：启动服务端

终端一运行：

```powershell
py .\MCPDemo\10_Token与AppID绑定\server.py
```

## 第二步：设置两项客户端身份信息

终端二运行：

```powershell
$env:MCP_DEMO_TOKEN = "customer-agent-token"
$env:MCP_DEMO_APP_ID = "coffee-customer-agent"
py .\MCPDemo\10_Token与AppID绑定\client.py
```

成功时会看到：

```text
Token、App ID、orders:read 都已验证，拿到的工具：['get_order_status']
```

## 故意测试失败

保持 Token 不变，只改 App ID：

```powershell
$env:MCP_DEMO_APP_ID = "coffee-menu-agent"
py .\MCPDemo\10_Token与AppID绑定\client.py
```

服务端会拒绝，因为 `customer-agent-token` 不属于 `coffee-menu-agent`。

## 代码只看这一段

```python
identity = TOKEN_IDENTITIES.get(token)

if request_app_id != identity["app_id"]:
    return JSONResponse(status_code=403, ...)

if "orders:read" not in identity["scopes"]:
    return JSONResponse(status_code=403, ...)
```

`identity` 的实际值大致是：

```python
{
    "app_id": "coffee-customer-agent",
    "scopes": ["orders:read"],
}
```

它来自 Token 的可信验证结果，不来自模型，也不相信用户或模型提供的身份字段。

## 真实企业里是什么

本课的 `TOKEN_IDENTITIES` 字典只是教学假数据。

真实环境通常是：

```text
OAuth / SSO / API 网关验证 JWT
-> 得到 token 的 client_id、subject、scopes
-> 网关或 MCP 服务检查 app_id 是否对应、scope 是否够用
-> 放行 MCP 工具
```

运行后查看 `输出/verified_client_result.json`。这个文件只记录 Token 环境变量名，不记录 Token 的值。
