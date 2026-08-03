# LangGraph 第 14 课：按商品动态分叉

## 这节课学什么

学习 `Send`：根据 state 里的实际数据，临时创建多个节点任务。

## 解决什么问题

固定写两个分叉节点，只能处理固定两件商品。但真实订单可能有 1 件、3 件或 20 件商品。

```text
items 有 3 件商品
-> 创建 3 个 check_item 任务
-> check_item 各运行一次
-> 汇总 3 个检查结果
```

## 运行

```powershell
py .\LangGraphDemo\14_按商品动态分叉\demo.py
```

## 观察结果

```text
为 拿铁 创建一个 check_item 任务。
为 美式 创建一个 check_item 任务。
为 蛋糕 创建一个 check_item 任务。

汇总结果：拿铁 x 2 已检查；美式 x 1 已检查；蛋糕 x 1 已检查
```

## 本课只记一句话

```text
Send("check_item", {"item": item}) 的意思是：临时让 check_item 节点拿着这一件商品运行一次。
```
