# 学习资料

- `source/`：原始 Markdown 知识库。
- `indexes/`：由构建索引课程生成的 JSON 索引。

索引中的向量和文本必须配套使用。重新切块或更换嵌入模型后，应重新生成对应索引，不能只替换其中一个文件。

- `indexes/父子知识库元数据.json`：父章节的业务标签，例如商品类型和业务主题；元数据过滤课程会在相似度检索前使用它。

当前 `app/rag_cli.py` 的父子 RAG 使用 `source/长文档示例.md` 作为原始资料，使用 `indexes/父子知识库索引.json` 作为检索索引。修改原始资料后，运行：

```powershell
py .\RAGDemo\app\build_parent_child_index.py
```

构建完成后再重新启动 `app/rag_cli.py`。如果增加或删除 Markdown 二级标题章节，也要同步检查 `indexes/父子知识库元数据.json` 的 `parent_1`、`parent_2` 等编号。
