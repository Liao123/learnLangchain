# 模块 25：修改资料后重建知识库

## 这节只记一句

改了知识库 Markdown，必须重新生成索引 JSON，问答程序才会知道新内容。

## 直接做

### 1. 改本课资料

打开这个文件，把“周六和周日”营业到晚上九点，改成晚上十点：

```text
资料/长文档示例.md
```

### 2. 运行 Demo

```powershell
py .\RAGDemo\lessons\25_重建当前应用索引\demo.py
```

### 3. 看结果

看终端最后两行：

```text
演示索引已写入：父子知识库索引.json
构建后演示版本：index-...
```

再打开这个文件，搜索“晚上十点”，应该能找到：

```text
输出/父子知识库索引.json
```

## 要更新真实问答程序时

```text
先改：data/source/长文档示例.md
再运行：py .\RAGDemo\app\知识库构建\build_parent_child_index.py
再运行：py .\RAGDemo\app\聊天问答\rag_cli.py
```

本课先只看 `demo.py`，不用看 `rag_cli.py`、`rag_core.py`。
