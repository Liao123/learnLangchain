# 第 13 课：配置文件连接 MCP 服务

## 这节课学什么

把 MCP 服务地址从 Python 代码移到 `mcp_servers.json`。

以后换服务地址、增加服务、删除服务，主要改配置文件，不必到每个 Agent 的 Python 文件里找 URL。

## 会遇到什么场景

第三方软件会给你一段 MCP 配置，里面通常有服务名称、传输方式、URL、启动命令或鉴权信息。

你把它放进项目或 Agent 平台的 MCP 配置位置，客户端就按配置连接服务。

## 第一步：启动服务端

终端一运行：

```powershell
py .\MCPDemo\13_配置文件连接服务\server.py
```

## 第二步：运行客户端

终端二运行：

```powershell
py .\MCPDemo\13_配置文件连接服务\client.py
```

终端会显示：

```text
配置文件里的服务名称：['coffee_order_remote']
通过配置拿到的工具：['get_order_status']
```

## 配置文件内容

`mcp_servers.json`：

```json
{
  "mcpServers": {
    "coffee_order_remote": {
      "transport": "streamable_http",
      "url": "http://127.0.0.1:8017/mcp"
    }
  }
}
```

含义：

```text
coffee_order_remote：给这个连接起的名字。
streamable_http：通过 HTTP MCP 协议连接。
url：第三方 MCP 服务给出的地址。
```

## Python 只看三行

```python
config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
connections = config["mcpServers"]
client = MultiServerMCPClient(connections)
```

三行的值变化：

```text
文件文字
-> Python 字典 config
-> config 里面的 mcpServers 对象
-> MCP 客户端连接配置
```

## 和之前硬编码的区别

以前：

```python
client = MultiServerMCPClient({"service": {"url": "..."}})
```

这次：

```python
client = MultiServerMCPClient(connections)
```

`connections` 的内容来自 JSON 文件，不是写死在 Python 里。

## 关于 Token

本课服务没有鉴权，所以 JSON 没有 `headers`。

真实 Token 不应直接写进 JSON。上一课的 Token 仍应从环境变量或密钥管理服务读取，再由客户端安全地补到 `headers` 配置中。

运行后查看 `输出/configured_mcp_result.json`，完成后回到服务端终端按 `Ctrl+C` 停止服务。
