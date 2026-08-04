# 第 7 课：HTTP 远程 MCP 服务

## 这节课学什么

前面的 `stdio` 是：客户端运行时临时启动 `server.py` 子进程。

这一课是：服务端自己先运行，客户端只知道一个 HTTP 地址。这更接近第三方软件或公司内部平台提供 MCP 的方式。

## 会遇到什么场景

例如 Figma、GitHub、3D 软件或公司订单平台已经在某台机器上提供 MCP 服务。你的 Agent 不负责启动它，只通过服务给出的 URL 连接它。

## 第一步：启动服务端

打开第一个 PowerShell，进入项目根目录，运行：

```powershell
py .\MCPDemo\07_HTTP远程MCP服务\server.py
```

看到下面文字后，不要关闭这个终端：

```text
HTTP MCP 服务已启动：http://127.0.0.1:8011/mcp
```

## 第二步：启动客户端

再打开第二个 PowerShell，同样进入项目根目录，运行：

```powershell
py .\MCPDemo\07_HTTP远程MCP服务\client.py
```

你会看到：

```text
通过 HTTP 拿到的工具：['get_order_status']
HTTP 工具返回：{"found": true, "order_id": "A1001", "status": "配送中", ...}
```

最后回到第一个终端，按 `Ctrl+C` 停止服务。

## 新代码只看这里

```python
"remote_order_service": {
    "transport": "streamable_http",
    "url": "http://127.0.0.1:8011/mcp",
}
```

以前 stdio 配置里有：

```python
"command": sys.executable,
"args": [str(SERVER_PATH)],
```

它的含义是“我自己启动本地服务进程”。

这课只有 URL，含义是“服务已经由别人运行，我通过网络连接它”。

## 一句话流程

服务端先监听 `8011` 端口 -> 客户端请求 `/mcp` 地址 -> 拿到工具说明 -> 发出工具调用 -> 服务端返回订单数据。

## 如果端口被占用

`server.py` 的 `PORT = 8011` 改成别的数字，例如 `8012`；然后 `client.py` 的 `MCP_URL` 也改成同一个端口。

运行后可查看 `输出/http_mcp_result.json`。
