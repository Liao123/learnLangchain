# 持续维护的 RAG 应用

`rag_cli.py` 是后续学习时持续修改的主程序。新功能先在这里实现、验证，再把一个稳定版本留到 `archive/`。

如果暂时分不清每个英文 Python 文件的用途，先看中文地图：[`中文说明/程序功能地图.md`](中文说明/程序功能地图.md)。

从项目根目录运行：

```powershell
py .\RAGDemo\app\rag_cli.py
```

应用优先读取 `RAGDemo/models/bge-small-zh-v1.5/` 中的本地模型；目录不存在时才会按索引中的模型名称加载，因此首次运行可能需要联网下载。

## 检索测试

`evaluate_retrieval.py` 不调用 DeepSeek。它用固定问题检查检索是否找对父章节，以及知识库外的问题是否被阈值拒答：

```powershell
py .\RAGDemo\app\evaluate_retrieval.py
```
## 元数据过滤示例

`metadata_filter_demo.py` 演示订单系统已知商品类型时，先筛资料再检索：

```powershell
py .\RAGDemo\app\metadata_filter_demo.py
```

## 重排序示例

`rerank_demo.py` 对比 BGE 初始排序和 reranker 重排序；首次运行可能需要下载 reranker 模型：

```powershell
py .\RAGDemo\app\rerank_demo.py
```

## 检索缓存

`rag_cli.py` 会缓存检索结果。相同的检索问题在 300 秒内再次出现时，会跳过 BGE 检索；缓存 key 包含索引内容自动生成的版本、检索配置和用户角色占位值。

## 更新知识库索引

当前父子 RAG 的原始资料是 `../data/source/长文档示例.md`。修改它后，运行：

```powershell
py .\RAGDemo\app\build_parent_child_index.py
```

命令会重新切父章节和子片段、重新调用 BGE 生成向量，再更新 `../data/indexes/父子知识库索引.json`。构建前会检查元数据编号；检查失败时不会覆盖旧索引。构建成功后重新启动 `rag_cli.py`。
