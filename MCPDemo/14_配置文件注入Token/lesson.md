# 第 14 课：配置文件注入 Token

## 这节课学什么

MCP 服务地址可以放配置文件，Token 不可以写死。

本课 JSON 只保存占位文字：

```text
Bearer ${MCP_DEMO_TOKEN}
```

客户端运行时从环境变量读取真实值，再替换占位文字后连接服务。

## 第一步：启动服务端

终端一运行：

```powershell
py .\MCPDemo\14_配置文件注入Token\server.py
```

## 第二步：设置环境变量并运行客户端

终端二运行：

```powershell
$env:MCP_DEMO_TOKEN = "coffee-demo-token"
py .\MCPDemo\14_配置文件注入Token\client.py
```

## JSON 中保存什么

`mcp_servers.json` 的值：

```json
"Authorization": "Bearer ${MCP_DEMO_TOKEN}"
```

它只是模板，不是真实请求头，也不包含真实 Token。

## Python 中发生什么

```python
token = os.getenv("MCP_DEMO_TOKEN")
template = "Bearer ${MCP_DEMO_TOKEN}"
authorization = template.replace("${MCP_DEMO_TOKEN}", token)
```

值变化：

```text
JSON 模板：Bearer ${MCP_DEMO_TOKEN}
环境变量：coffee-demo-token
内存中的请求头：Bearer coffee-demo-token
```

最后这个请求头只在本次程序内存中使用，不会被写回 JSON 文件。

## 为什么这样做

配置文件可以提交到 Git、发给同事、给不同环境复用。

Token 放环境变量或密钥管理服务，每个人或每台服务器有自己的值，不会因为复制配置文件而泄漏。

## 生产补充

本课用 `replace()` 手动替换一个固定变量，是为了看清过程。

实际工程通常由部署平台、容器、CI/CD、Agent 平台或专门的配置库注入环境变量；核心原则不变：配置写“去哪里连”，密钥系统提供“拿什么身份连”。

结果在 `输出/configured_auth_result.json`；文件只记录占位模板和环境变量名，不保存 Token 值。
