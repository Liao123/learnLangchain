# 第 18 课：幂等键参数冲突

## 这节课学什么

同一个幂等键只能代表同一组业务参数。

```text
cancel-request-001 + A1001：可以重试。
cancel-request-001 + A1002：必须拒绝。
```

## 为什么需要这条规则

如果服务端只按幂等键查缓存：

```text
第一次：取消 A1001，键是 cancel-request-001。
第二次：取消 A1002，但错误复用了 cancel-request-001。
```

服务端可能错误地把 A1001 的旧结果返回给 A1002 请求，或者执行错误操作。

所以第一次请求时，不只保存结果，还要保存它的请求参数。

## 第零步：清空教学数据

```powershell
py .\MCPDemo\18_幂等键参数冲突\reset_data.py
```

## 第一步：启动服务端

终端一运行：

```powershell
py .\MCPDemo\18_幂等键参数冲突\server.py
```

## 第二步：运行三次调用演示

终端二运行：

```powershell
py .\MCPDemo\18_幂等键参数冲突\demo.py
```

你会依次看到：

```text
首次取消 A1001
-> cancelled_count: 1, idempotency_replayed: false

同键同参数重试 A1001
-> cancelled_count: 1, idempotency_replayed: true

同键但换成 A1002
-> error: idempotency_key_conflict
```

## 核心数据

第一次调用时，数据库保存：

```text
idempotency_key：cancel-request-001
request_json：{"order_id": "A1001"}
response_json：第一次取消 A1001 的结果
```

第二次调用时，服务端先比较：

```python
saved_request_json != request_json
```

相等：说明是同一件事的重试，可以复用结果。

不相等：说明同一个键被拿去做了不同事情，返回冲突错误。

## 真实企业里

请求参数很多或包含敏感信息时，通常保存规范化请求体的 Hash，而不是直接保存完整 `request_json`。

但本课只传一个 `order_id`，直接保存 JSON 更容易看清规则。
