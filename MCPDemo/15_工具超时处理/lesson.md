# 第 15 课：工具超时处理

## 这节课学什么

第三方 MCP 工具可能很慢。客户端需要规定：最多等几秒；超过时间就结束等待并记录超时。

## 场景

订单查询依赖外部数据库，退款工具依赖支付平台，文件工具依赖网盘。它们偶尔会慢，但 Agent 不能永远卡住等待。

## 第一步：启动慢服务

终端一运行：

```powershell
py .\MCPDemo\15_工具超时处理\server.py
```

服务端每次工具调用固定等待 2 秒。

## 第二步：默认超时测试

终端二直接运行：

```powershell
py .\MCPDemo\15_工具超时处理\client.py
```

客户端默认只等 1 秒，所以会显示：

```text
等待 1.0 秒后仍未拿到工具结果。
```

## 第三步：延长等待时间

同一个终端运行：

```powershell
$env:MCP_TOOL_TIMEOUT_SECONDS = "3"
py .\MCPDemo\15_工具超时处理\client.py
```

这次客户端等 3 秒，工具约 2 秒返回，因此会成功。

## 新代码只看这里

```python
tool_result = await asyncio.wait_for(
    tool.ainvoke({"order_id": "A1001"}),
    timeout=timeout_seconds,
)
```

值代入第一次运行后相当于：

```python
await asyncio.wait_for(工具调用, timeout=1.0)
```

工具要 2 秒，超过 1 秒就抛出 `TimeoutError`，程序进入：

```python
except TimeoutError:
```

## 一个容易误会的点

客户端超时表示“客户端不再等待”，不保证远端服务一定已经停止处理。

因此写操作工具不能因为客户端超时就盲目重试。下一课会讲：面对可能已经执行过的写操作，怎样避免重复提交。

运行后查看 `输出/tool_timeout_result.json`，完成后回到服务端按 `Ctrl+C` 停止。
