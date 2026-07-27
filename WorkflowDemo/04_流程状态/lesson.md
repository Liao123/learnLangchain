# 第 58 课：流程状态 state

## 这节只记一句

`state` 就是一份流程记录：AI 提取了什么、程序查到了什么、最后做了什么，都放进去。

```text
用户取消 A1001
-> state 记录订单号 A1001
-> state 记录订单状态 制作中
-> state 记录最终结果 不能取消
```

## 直接做

### 1. 设置 Key 后运行

```powershell
$env:DEEPSEEK_API_KEY="你的Key"
py .\WorkflowDemo\04_流程状态\demo.py
```

### 2. 看最后两部分

```text
流程 state：{...}
给用户：订单已经制作中，暂时不能取消。
```

### 3. 改问题再运行

把：

```python
question = "帮我取消订单 A1001"
```

改成其中一个：

```python
question = "请帮我取消 A1002"
question = "帮我查一下 A1001 的订单状态"
```

看 `state` 里的“动作、订单状态、最终答复”怎样变化。
