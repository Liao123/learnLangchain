# 模块 22：应用接入缓存

## 这节课在学什么？

前面已经学过缓存对象。这一课把它放到真正的 RAG 检索流程中。

一句话逻辑：

```text
先 cache.get(key)
-> 命中：直接使用 result，跳过 BGE
-> 未命中：调用 retrieve_parent_context()，再 cache.set(key, result)
```

## 程序运行时发生了什么？

默认连续检索两次同一个问题：

```text
第 1 次：周末几点营业？
-> 缓存没有 key
-> 调用 BGE
-> 找回“营业时间与到店服务”
-> result 存入缓存

第 2 次：周末几点营业？
-> 缓存有同一个 key
-> 直接取相同 result
-> 不调用 BGE
```

这次缓存的是 RAG 的 `result`，里面仍有 `best_score`、`matched_children`、`parents`、`context`，所以后面显示资料来源、拼 SystemMessage 的代码不需要改变。

## 这节要记住

- 缓存必须放在 `retrieve_parent_context()` 前面。
- 命中缓存时跳过的是 BGE 检索，不是 DeepSeek 最终回答。
- 完整应用 `app/rag_cli.py` 已经接入同一套缓存；它用改写后的 `retrieval_question` 作为 key 的问题部分。
- 对话历史会影响改写结果，所以两句看起来相同的用户原话，不一定得到相同 `retrieval_question`，也就不一定命中缓存。

## 怎么运行和验证？

```powershell
py .\RAGDemo\lessons\22_应用接入缓存\demo.py
```

本课不调用 DeepSeek，不需要 API Key。
