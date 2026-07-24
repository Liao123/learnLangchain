# AI 应用开发学习记录

## 当前进度

### 第 1 步：安装并确认 LangChain

已执行：

```powershell
pip install langchain
```

已确认环境：

- Python：`3.13.9`
- LangChain：`1.3.12`

### 第 2 步：安装模型连接器

已执行：

```powershell
pip install -U langchain-openai
```

理解：LangChain 负责连接和组织 AI 能力，`langchain-openai` 负责连接 OpenAI 兼容的模型接口。

### 第 3 步：连接 DeepSeek

当前实际使用的模型配置：

- `base_url`：`https://api.deepseek.com`
- `model`：`deepseek-v4-pro`
- API Key：通过环境变量 `DEEPSEEK_API_KEY` 读取

在当前 PowerShell 会话中设置环境变量：

```powershell
$env:DEEPSEEK_API_KEY = "你的真实 Key"
```

代码通过下面的方式读取密钥：

```python
api_key = os.environ["DEEPSEEK_API_KEY"]
```

安全原则：真实 API Key 不写进代码、不提交到 Git，也不发到聊天中。如果 Key 曾经暴露，应立即在 DeepSeek 控制台作废并重新生成。

### 第 4 步：完成第一个单轮问答程序

示例文件：`01_hello_langchain.py`

已经学会：

- 使用 `ChatOpenAI` 创建模型对象
- 使用 `input()` 接收用户问题
- 使用 `model.invoke(...)` 调用模型
- 用 `system` 消息规定 AI 的身份和回答方式
- 用 `human` 消息传入用户问题
- 通过 `response.content` 取得并打印回答正文

单轮问答每次只携带当前问题，程序本身不会保存上一轮内容。

### 第 5 步：完成连续对话程序

示例文件：`02_hello_langchain.py`

已经学会：

- 使用 `while True` 让程序持续接收问题
- 使用 `messages` 列表保存对话历史
- 把用户问题追加为 `("human", question)`
- 调用模型后，把返回的 AI 消息追加到 `messages`
- 使用 `exit`、`quit` 或“退出”结束循环
- 忽略只包含空白字符的输入

`messages` 的变化过程：

1. 开始时只有一条 `system` 消息。
2. 用户提问后，追加一条 `human` 消息。
3. 模型收到当前完整的 `messages` 并生成回答。
4. 把模型返回的 AI 消息追加到 `messages`。
5. 下一轮调用会再次传入完整列表，因此模型能够看到前面的对话。

这里的“记忆”目前只是程序运行期间保存在内存中的消息列表；程序关闭后，对话记录不会自动保存。

### 第 6 步：初步学习断点调试

已经使用 `breakpoint()` 暂停程序，并接触以下调试命令：

- `p 表达式`：查看变量或表达式的值
- `n`：执行当前行并移动到下一行
- `c`：继续运行，直到下一个断点或程序结束

查看 `messages` 中角色和内容的示例：

```text
p [(m[0], m[1]) if isinstance(m, tuple) else (m.type, m.content) for m in messages]
```

通过在追加用户消息、调用模型和追加 AI 消息前后观察 `messages`，可以理解每一轮对话历史是如何形成的。

## 当前学习位置

已经完成：

- [x] 安装 LangChain
- [x] 安装模型连接器
- [x] 使用环境变量管理 API Key
- [x] 调用 DeepSeek 完成单轮问答
- [x] 使用 `messages` 完成连续对话
- [x] 初步使用断点观察程序执行过程

下一小步：继续理解 LangChain 中不同消息的类型，以及元组消息和模型返回的 AI 消息对象有什么区别。完成后再学习更正式的对话历史管理方式。

## 后续学习路线

按小步骤继续，不一次展开：

1. 理解 `SystemMessage`、`HumanMessage` 和 `AIMessage`
2. 整理连续对话代码并增加基础错误处理
3. 学习将对话历史保存到文件或数据库
4. 学习工具调用
5. 学习 RAG，让 AI 查询自己的资料

## 学习原则

- 每次只学习一个小概念
- 每一步都运行代码验证
- 遇到报错先记录完整错误信息
- API Key 不写进代码或公开发出来
- 先理解代码为什么有效，再继续增加新功能
