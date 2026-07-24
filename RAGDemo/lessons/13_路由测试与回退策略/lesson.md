# 模块 13：路由测试与回退策略

## 这节课在学什么？

这节只学一件事：**先写好预期结果，再让程序检查实际路由是否符合预期。**

一句话逻辑：

```text
写好“这道题应该路由到哪里”
-> 程序实际路由一次
-> 比较预期和实际
-> 相同就是通过，不同就是失败
```

这次默认只测一题：`周末几点营业？`。不要一开始同时看四题、三层循环和检索代码。

## 它解决什么问题？

你以后修改了关键词，例如删掉“周末”，可能让原来正确的问题突然没有路由。测试能把这种变化直接指出来。

## 程序运行时发生了什么？

```text
测试题：周末几点营业？
预期路由：到店服务
-> 第 40 课的路由代码实际运行
-> 实际路由：到店服务
-> 比较两个列表：相同
-> 再检查实际动作是否是 single_route
-> BGE 在 parent_4 的 child_8、child_9 中检索
-> 检查最终章节是否是 parent_4
-> 这题通过
```

## 这节要记住

- `expected_routes`：你事先规定的正确路由。
- `actual_route_names`：程序这次实际得到的路由。
- `route_passed = actual_route_names == expected_routes`：完全相同才通过。
- 第 40 课的路由循环已移到 `app/rag_core.py`，因为你已经见过它。现在的重点是测试结果，不是再读一遍路由实现。

## 换题练习

先一次只改下面三个变量，观察不同回退策略：

```python
# 无路由：预期不加载 BGE，直接 reject。
question = "店里能维修电脑吗？"
expected_routes = []
expected_action = "reject"
expected_parent_id = None
```

```python
# 多路由：合并两个主题的范围后再检索。
question = "门店会员有什么优惠？"
expected_routes = ["会员与订单", "到店服务"]
expected_action = "multi_route_fallback"
expected_parent_id = None
```

## 怎么运行和验证？

```powershell
py .\RAGDemo\lessons\13_路由测试与回退策略\demo.py
```

默认题应显示：

```text
预期路由：['到店服务']
实际路由：['到店服务']
测试结果：通过
```
