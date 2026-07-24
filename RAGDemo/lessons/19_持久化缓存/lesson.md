# 模块 19：持久化缓存

## 这节课在学什么？

前面的 `retrieval_cache = {}` 只存在 Python 内存里，程序一关就没了。这一课把字典保存为 JSON 文件，下次启动再读回来。

一句话逻辑：

```text
内存缓存字典
-> 写入 JSON 文件
-> 程序重启，内存字典变空
-> 从 JSON 文件读取
-> 缓存恢复
```

## 它解决什么问题？

如果程序每次重启都丢失缓存，重启后的第一个相同问题仍要重新检索。把缓存存到文件后，只要资料版本和 TTL 仍然有效，就能继续复用。

## 这节要记住

- `json.dumps()`：把 Python 字典变成 JSON 文字。
- `write_text()`：把文字写入文件。
- `read_text()`：从文件读取文字。
- `json.loads()`：把 JSON 文字还原为 Python 字典。
- JSON 只能保存字符串、数字、列表、字典、布尔值、`null` 等普通数据；不能直接保存 BGE 模型对象。

本课生成的缓存文件是 `demo_retrieval_cache.json`，就在 `demo.py` 同一文件夹。它保留在磁盘上，方便你亲眼看到里面的数据。

## 程序运行时发生了什么？

```text
内存缓存：
{"v1:周末几点营业？": {"context": "...晚上九点"}}

-> 保存到 demo_retrieval_cache.json
-> 模拟程序关闭：retrieval_cache = {}
-> 从 JSON 文件读回来
-> 恢复成原来的字典
```

## 怎么运行和验证？

```powershell
py .\RAGDemo\lessons\19_持久化缓存\demo.py
```

运行后打开同目录的 `demo_retrieval_cache.json`，能看到真正保存的缓存内容。

本课不调用 BGE、不调用 DeepSeek，也不需要新库。
