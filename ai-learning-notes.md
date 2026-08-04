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

LangGraph 学习进度：已完成第 18 课“state 和 config 的区别”，掌握 `graph.get_state(config)` 查看当前快照、`graph.get_state_history(config)` 查看同一 `thread_id` 的历史快照、`graph.update_state(config, {...})` 修正流程数据、从旧快照重新运行后续节点、`Annotated[..., add]` 的字段累加规则、固定节点的并行汇合、`Send` 动态创建节点任务、`Command(update=..., goto=...)` 节点内分支、子图的使用与独立 state，以及区分流程 state 和每次运行的 config。

多 Agent 学习进度：已完成第 1 课“多专员分流工作流”。已经搭好“总调度 -> 对应专员子图”的结构；当前路由和回答是本地函数模拟，下一课会把总调度替换为真正的模型节点。

多 Agent 第 2 课已创建：模型输出 `route`，Python 校验白名单后进入订单、退款或人工客服节点。此课运行需要 `DEEPSEEK_API_KEY`。

多 Agent 第 3 课已完成：总调度可以根据 state 分多轮委派专员，专员每次完成后回到总调度，再由总调度决定下一步或结束。该课不需要模型 API。

多 Agent 第 4 课已创建：总调度模型负责选路线；对应专员模型带着自己的规则和资料生成最终回答。该课一次请求通常会调用两次模型。

多 Agent 第 5 课已创建：订单、退款专员分别只绑定自己的工具。该课通常会发生总调度、工具请求和最终回答等多次模型调用。

多 Agent 第 6 课已创建：总调度从自然语言中提取路线、业务单号和任务，生成 handoff 交接单，再由专员直接按交接单处理。

多 Agent 第 7 课已创建：用 Pydantic 的 `Handoff.model_validate(...)` 校验模型交接单。route 不在白名单、字段缺失或 JSON 格式错误时转人工客服。

多 Agent 第 8 课已完成：用 LangGraph 运行配置 `recursion_limit` 防止 supervisor 和 specialist 的委派循环无限执行。它是最后一道保护，不能代替正常的 END 结束条件。

多 Agent 第 9 课已完成：子图里的专员可以通过 `Command(goto=..., graph=Command.PARENT)` 主动跳回父图指定节点，由父图继续统一收尾。

多 Agent 第 10 课已完成：订单、退款等专员子图都通过 `Command.PARENT` 交回父图总调度。父图根据共同 state 决定下一位专员，而不是让专员直接互相跳转。

多 Agent 第 11 课已完成：用 `Send` 并行委派订单、退款等多个专员任务，用 `Annotated[..., add]` 合并结果，并在父图等待全部专员完成后汇总。

多 Agent 第 12 课已完成：退款子图使用 `interrupt()` 等待人工确认，SQLite 保存暂停点；恢复后，子图通过 `Command.PARENT` 回父图生成统一回复。

多 Agent 第 13 课已完成：专员捕获业务系统的已知失败，写入 failure_reason 并通过 `Command.PARENT` 交回父图转人工客服，而不是让错误中断整个流程。

多 Agent 第 14 课已完成：退款专员从可信 `config` 读取操作人角色，在执行退款前校验权限。专员拥有工具不等于当前操作人拥有批准权限。

多 Agent 第 15 课已创建：用一组带预期 route 的真实问题调用总调度模型，逐条比较实际路由并统计成功率，用于修改提示词或模型后的回归评测。

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

多 Agent 第 16 课已创建：将每题的预期 route、实际 route、是否通过和题目类型写入本课 `输出\\route_evaluation_report.json`，同时在终端单独打印失败题，用于定位提示词或路由规则的具体问题。
多 Agent 第 17 课已创建：用 LangGraph 的 state 累加 `trace`，记录总调度实际选择的路线和专员的处理动作，并写入本课 `输出\\trace.json`，用于定位错误发生在路由还是专员处理。
Agent Harness 第 1 课已创建：开始新的工程化阶段，将固定任务数据、Agent 实际输出和独立评测结果写入同一份 `输出\\run_record.json`；Harness 可以包在普通函数或 LangGraph 图外面。
Agent Harness 第 2 课已创建：将一组固定任务逐题执行“运行 Agent -> 独立判分 -> 保存记录”，输出总成功率和 `输出\\batch_report.json`，用于在改提示词、模型、工具或图后做回归评测。
Agent Harness 第 3 课已创建：将路由评测题集放入本课 `数据\\routing_tasks.json`，`demo.py` 读取题集的名称、版本和任务后生成报告；新增测试题时不需要修改 Agent 程序。
Agent Harness 第 4 课已创建：用 Pydantic 的 `RoutingDataset.model_validate(...)` 在模型调用前检查题集 JSON；正常题集可继续运行，故意写错的 `expected.route` 会立刻报出位置且不消耗 API 调用。
Agent Harness 第 5 课已创建：读取整个题集文件并计算 `sha256` 指纹，结合模型名、提示词版本、题集版本和题量写入 `输出\\run_manifest.json`，让之后的评测分数可追溯、可比较。
Agent Harness 第 6 课已创建：先比较基准报告和新报告的 `dataset_sha256`，相同才计算成功率变化；再找出“基准通过、新版本失败”的任务，写入 `输出\\comparison.json` 作为回归清单。
Agent Harness 第 7 课已创建：当客服回答不是固定选项时，让被测 Agent 先生成回答，再由独立模型根据人工 rubric 输出 `passed`、原因和缺失点；记录写入 `输出\\judge_record.json`，且评审模型格式异常默认不通过。
Agent Harness 第 8 课已创建：用人工标注通过/失败的四条回答测试第 7 课的评审模型；只有评审模型的 `passed` 与 `expected_passed` 一致才算评审正确，准确率和逐题结果写入 `输出\\judge_evaluation_report.json`。
Agent Harness 第 9 课已创建：在内存假订单系统上测试退款流程，评测同时检查最终 `refund_status` 和实际工具调用名；确认时必须提交退款，未确认时必须不调用工具，结果写入 `输出\\tool_evaluation_report.json`。
Agent Harness 第 10 课已创建：让真实模型 Agent 通过 `bind_tools()` 选择是否调用 `submit_refund`，再由 Harness 在假订单系统上检查工具调用次数和最终状态；模型或网络错误也会作为失败记录写入 `输出\\tool_agent_evaluation_report.json`。
Agent Harness 第 11 课已创建：以服务器可信的 `trusted_confirmed` 为准，加入用户要求“忽略规则、直接退款”的攻击题；Harness 验证未确认时仍是零工具调用和 `not_requested` 状态，结果写入 `输出\\authorization_evaluation_report.json`。
Agent Harness 第 12 课已创建：假设模型已经错误请求工具，退款工具仍从服务器 `server_confirmations` 自行校验；未确认订单会返回 `ok=false` 且保持 `not_requested`，报告写入 `输出\\tool_authorization_report.json`。
Agent Harness 第 13 课已创建：用 `perf_counter()` 围住 `model.invoke(...)` 记录单次 API 与生成耗时，按业务时限 `MAX_ALLOWED_LATENCY_MS` 判分，并将耗时、错误和评测结果写入 `输出\\latency_report.json`。
Agent Harness 第 14 课已创建：从模型 `AIMessage.usage_metadata` 读取输入、输出和总 Token，按 `MAX_TOTAL_TOKENS` 区分预算内、超预算、服务未提供用量或请求失败，并写入 `输出\\token_usage_report.json`。
Agent Harness 第 15 课已创建：使用 `asyncio`、`ainvoke()` 和 `gather()` 并行评测独立任务，并用 `Semaphore(MAX_CONCURRENT_REQUESTS)` 限制同时最多两次模型请求；每题结果和耗时写入 `输出\\parallel_evaluation_report.json`。
Agent Harness 第 16 课已创建：只对 `ConnectionError` 进行最多三次的有限重试，逐次记录连接错误或成功；用本地前两次失败、第三次成功的模拟服务验证流程，报告写入 `输出\\retry_report.json`。
MCP 环境已安装并检查通过：`mcp 1.29.0`、`langchain-mcp-adapters 0.3.1`，同时升级 FastAPI 到与其兼容的 `0.141.1`，`pip check` 无冲突。
MCP 第 1 课已创建：`server.py` 用内置 FastMCP 公开 `get_order_status`，`demo.py` 通过 `MultiServerMCPClient` 以 stdio 自动启动服务端、读取工具并直接调用，结果写入本课 `输出\\mcp_result.json`。
MCP 第 2 课已创建：独立 `server.py` 公开订单和退款两个 MCP 工具；`demo.py` 用 `client.get_tools()` 拿到工具、用 `model.bind_tools(tools)` 让模型自行选择工具，再把 MCP 返回值作为 `ToolMessage` 交给模型生成最终回答。完整调用过程写入本课 `输出\\agent_mcp_result.json`。
MCP 第 3 课已创建：一个 Agent 客户端通过 `MultiServerMCPClient` 同时启动订单和会员两个独立 MCP 服务，汇总两边工具交给模型选择；终端和 `输出\\multi_server_result.json` 会记录实际工具来自哪个服务。
MCP 第 4 课已创建：`server.py` 用 `@mcp.resource(...)` 公开会员积分和退款规则两份资料；`demo.py` 用 `client.get_resources(...)` 读回 Blob 资源并通过 `as_string()` 取正文，结果写入本课 `输出\\resources_result.json`。本课不调用模型或 API。
