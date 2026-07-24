# 模块 24：应用接入自动版本

## 这节课在学什么？

第 51 课已经知道“索引内容 -> hash -> 自动版本”。这一课把它接进 `rag_cli.py`，替换原来手写的缓存版本。

一句话逻辑：

```text
rag_cli.py 启动
-> get_index_content_version()
-> 自动得到 index-前12位hash
-> 加上 top_k、阈值
-> 作为缓存 key 的版本部分
```

## 程序运行时发生了什么？

当前索引会得到类似：

```text
index-001e7af6fbec
```

完整应用再把检索配置加上：

```text
index-001e7af6fbec-top3-threshold0.70
```

最后生成的缓存 key 大致是：

```text
public_customer:index-001e7af6fbec-top3-threshold0.70:周末几点营业？
```

当父子索引 JSON 内容变化时，前面的 `index-...` 自动变化，因此旧缓存不会命中。

## 这节要记住

- 版本不是每次提问都重新计算，而是应用启动时计算一次。
- 当前程序没有每轮重读索引，所以同一次程序运行中，索引版本保持不变。
- 重建索引后，重新启动 `rag_cli.py`，它就会读取新 hash。
- `top_k`、阈值会影响检索结果，所以也放进版本文字中。

## 怎么运行和验证？

完整应用需要 DeepSeek Key：

```powershell
py .\RAGDemo\app\聊天问答\rag_cli.py
```

启动后应看到：

```text
自动缓存版本：index-...-top3-threshold0.70
```

本课 demo 不需要 DeepSeek Key：

```powershell
py .\RAGDemo\lessons\24_应用接入自动版本\demo.py
```
