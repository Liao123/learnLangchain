# RAG 学习项目

## 快速开始

当前持续维护的应用：

```powershell
py .\RAGDemo\app\聊天问答\rag_cli.py
```

运行前请在当前 PowerShell 窗口设置新的 `DEEPSEEK_API_KEY`。不要把真实 Key 写入代码、截图或 Markdown。

## 目录说明

- `app/`：当前实际应用，按“聊天问答、知识库构建、质量检查”等中文文件夹分类。
- `lessons/`：按知识模块组织的简短讲义与最小 Demo。
- `archive/`：第 21 到第 54 课的历史快照，可单独回看和运行。
- `data/`：原始 Markdown 与配套 JSON 索引。
- `models/`：可选的本地 BGE 模型目录，已被 Git 忽略。

学习时先读对应模块的 `lesson.md`，运行最小 Demo，最后回到 `app/聊天问答/rag_cli.py` 看这个概念如何进入完整应用。

修改当前父子 RAG 使用的 `data/source/长文档示例.md` 后，运行下面命令重新生成应用索引：

```powershell
py .\RAGDemo\app\知识库构建\build_parent_child_index.py
```
