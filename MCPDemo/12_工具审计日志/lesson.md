# 第 12 课：工具审计日志

## 这节课学什么

工具执行后，服务端记录一条审计日志：

```text
谁调用了什么工具
传了什么订单号
结果是成功、拒绝还是找不到
发生在什么时间
```

## 会遇到什么场景

订单、退款、付款、删除文件这类工具不能只看最终回答。发生问题时，公司需要能查：到底是谁触发了哪个操作，服务端为什么允许或拒绝。

日志必须由服务端写，而不是相信 Agent 客户端自己上报。

## 第一步：启动服务端

终端一运行：

```powershell
py .\MCPDemo\12_工具审计日志\server.py
```

## 第二步：普通会员成功查询

终端二运行：

```powershell
$env:MCP_DEMO_TOKEN = "member-u1001-token"
py .\MCPDemo\12_工具审计日志\client.py
```

输入：

```text
A1001
```

然后打开 `输出/audit_log.jsonl`，会多出一行大致如下：

```json
{"timestamp":"...","actor":"U1001","client_id":"coffee-customer-agent","tool_name":"get_order_status","order_id":"A1001","outcome":"success","reason":null}
```

## 第三步：普通会员查别人的订单

保持 Token 不变，重新运行客户端，输入 `A1002`。

工具会拒绝，审计日志仍会追加一行：

```json
{"actor":"U1001","order_id":"A1002","outcome":"denied","reason":"order_access_denied"}
```

所以“被拒绝的敏感操作尝试”也能追溯。

## 新代码只看这里

```python
with AUDIT_LOG_PATH.open("a", encoding="utf-8") as audit_file:
    audit_file.write(json.dumps(event, ensure_ascii=False) + "\n")
```

`"a"` 是追加模式：每一次调用都在文件末尾新增一行，不覆盖旧日志。

`json.dumps(event)` 把当前审计事件字典变成一行 JSON 文字；最后的 `"\n"` 换行，所以文件格式叫 JSONL（一行一个 JSON）。

## 不要写进日志的东西

本课记录 `actor`、`client_id`、scope、订单号、工具名和结果。

不记录 Bearer Token 原文、密码、银行卡完整号等敏感凭证。

## 一句话流程

Token 验证 -> 工具内权限检查 -> 服务端追加审计日志 -> 返回成功或拒绝结果。
