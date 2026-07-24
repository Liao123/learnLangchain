# LangChain + DeepSeek AI 应用开发教学讲义

> 适用对象：会一点点 Python、希望理解并讲解 AI 应用怎么工作的初学者。
>
> 本讲义记录的是本项目已经走过的学习路线。它的目标不是背 API，而是理解：**大模型负责理解和表达，Python 程序负责组织流程、保存资料和执行真实操作。**

## 1. 先建立一张总地图

一个常见的 AI 应用，可以拆成下面几部分：

```text
用户用自然语言提问
        ↓
Python 组织消息 messages（规则、历史、资料）
        ↓
DeepSeek 模型理解问题
        ├── 直接生成回答
        ├── 返回 JSON，供程序读取
        └── 请求调用工具
                    ↓
             Python 执行真实工具
                    ↓
             工具结果写回 messages
                    ↓
             DeepSeek 组织最终回答
```

关键分工：

| 部分 | 主要职责 | 例子 |
| --- | --- | --- |
| DeepSeek | 理解人话、提取信息、决定是否需要工具、生成文字 | “3 杯咖啡多少钱？” |
| Python | 调用 API、保存上下文、执行计算/查数据库等真实动作 | `12.5 * 3` |
| LangChain | 用统一写法连接不同模型、消息和工具 | `model.invoke(messages)` |
| 本地资料/数据库 | 提供可核实的业务事实 | 退款政策、订单信息 |

不要把 AI 理解成“程序自动什么都会做”。模型不能直接操作你的电脑、数据库或订单系统；它需要通过程序提供的工具和资料完成这些事情。

---

## 2. 项目环境与安全原则

当前项目使用：

```text
Python 3.13
LangChain
langchain-openai
DeepSeek OpenAI 兼容接口
模型：deepseek-v4-pro
```

模型配置的核心写法：

```python
model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)
```

在当前 PowerShell 窗口临时设置 Key：

```powershell
$env:DEEPSEEK_API_KEY = "你的真实 Key"
```

这只对当前 PowerShell 窗口有效；关闭窗口后需要重新设置。

安全原则：

- 不把真实 API Key 写进 `.py` 文件。
- 不把真实 API Key 发到聊天记录、截图或 Git 仓库。
- 如果 Key 泄露，去 DeepSeek 平台作废旧 Key，再创建新 Key。
- 不要因为模型能调用工具，就让它获得没有审核的删除、转账或发消息权限。

---

## 3. 项目文件学习地图

| 阶段 | 文件 | 学习重点 |
| --- | --- | --- |
| 单轮问答 | `01_hello_langchain.py` | 创建模型、发送问题、读取 `response.content` |
| 连续对话 | `02_hello_langchain.py` | `while` 循环与 `messages` 上下文 |
| 消息对象 | `03_hello_langchain.py` | `SystemMessage`、`HumanMessage`、AI 返回消息 |
| 基础错误处理 | `04_hello_langchain.py` | 出错时不要让整个对话程序直接结束 |
| 历史保存尝试 | `05` 至 `08` | 将消息/历史保存为 JSON 的基础思路 |
| 本地聊天历史 | `09_本地文件记忆.py` | 启动时读历史，结束时写历史 |
| 代码整理 | `10_函数整理本地记忆.py` | 用函数分开“读取、保存、聊天”等职责 |
| 历史操作 | `11_清空历史记录.py`、`12_查看历史记录.py` | 本地程序功能，不是 AI 理解能力本身 |
| 提示词影响 | `13_提示词如何影响回答.py` | 同一问题，系统规则不同，回答不同 |
| 提示词结构 | `14_提示词的三个部分.py` | 身份、对象、输出要求 |
| JSON 输出 | `15_让AI返回JSON.py` | 让模型结果可被程序稳定读取 |
| Few-shot 示例 | `16_给AI一个示例.py` | 用输入/输出示例稳定复杂格式 |
| 单工具调用 | `17_AI调用计算工具.py` | Function Calling 的完整闭环 |
| 多工具选择 | `18_AI选择不同工具.py` | AI 返回工具名，Python 按名称执行 |
| 工具 + JSON | `19_工具结果转JSON.py` | 先获取真实结果，再输出给程序使用的 JSON |
| 本地知识问答 | `20_让AI阅读本地知识.py` | 把 Markdown 资料加入提示词 |
| 示例知识库 | `咖啡店知识库.md` | 本地资料来源 |

建议教学顺序：先讲 01、02、13、14；再讲 15、17、18、19；最后讲 20 和后续 RAG。不要一开始就讲历史文件、向量数据库或复杂 Agent。

---

## 4. 最重要的概念：模型没有自动记忆

### 4.1 `messages` 是什么

`messages` 是一个列表，保存“本次要交给模型看的上下文”。例如：

```python
messages = [
    SystemMessage(content="你是一名耐心的 Python 教师。"),
    HumanMessage(content="什么是变量？"),
]
```

调用：

```python
response = model.invoke(messages)
```

模型只会看到这次请求中实际传入的内容。下一次调用 API 时，如果不再传前面的消息，模型不会自动记得。

### 4.2 一轮对话后，历史如何变化

```text
开始：
[系统规则]

用户提问后：
[系统规则, 用户问题]

模型回答后：
[系统规则, 用户问题, AI 回答]
```

下一轮把完整列表再传进去，模型才看得到前文。这是“上下文”，不是模型永久记忆。

### 4.3 临时上下文与长期记忆的区别

```text
Python 变量 messages
→ 程序运行期间有效
→ 程序关闭后消失

JSON 文件或数据库中的历史
→ 下次启动可以重新读取
→ 才能形成跨运行的长期记忆
```

`09_本地文件记忆.py` 等文件做的就是第二件事。

---

## 5. 提示词：不是“咒语”，而是工作说明

系统消息（`SystemMessage`）通常用于告诉 AI：

- 你是谁：例如“你是咖啡店客服”。
- 面向谁：例如“向 Python 初学者解释”。
- 如何输出：例如“分三点回答，每点不超过两句”。
- 有哪些边界：例如“只依据提供的知识库回答，不知道就明确说不知道”。

一个实用模板：

```text
角色：你是一名……
对象：回答对象是……
任务：你需要完成……
依据：只能使用……
输出：请按……格式输出。
```

`13_提示词如何影响回答.py` 和 `14_提示词的三个部分.py` 说明：模型能力没有换，但规则不同，回答的风格、深度和格式会明显改变。

---

## 6. JSON 输出：让 AI 的结果能被程序使用

自然语言适合人阅读：

```text
小王会在周五下午三点去上海参加 Python 培训。
```

程序通常更需要固定字段：

```json
{
  "人物": "小王",
  "时间": "周五下午三点",
  "地点": "上海",
  "事情": "参加 Python 培训"
}
```

`15_让AI返回JSON.py` 的关键：

```python
json_model = model.bind(
    response_format={"type": "json_object"}
)
```

`bind()` 不会立刻调用 AI。它是从基础 `model` 派生一个“要求 JSON 输出”的配置。

最终结果仍然是文字，需要转换：

```python
data = json.loads(response.content)
```

此时 `data` 变成 Python 字典，可以读取：

```python
print(data["地点"])
```

### Few-shot 示例为什么有用

`16_给AI一个示例.py` 在提示词中补充一组“输入是什么、正确 JSON 应该长什么样”。

它不是训练模型，也不会永久改变模型；它只影响当前请求。简单任务未必需要，字段很多或格式复杂时更有用。

---

## 7. Function Calling / Tool Calling：AI 会决定，Python 会执行

`17_AI调用计算工具.py` 是本项目最重要的流程之一。

### 7.1 为什么需要工具

模型会生成文字，但不应该让它自行“心算”、查订单或执行退款。真实业务结果应该来自受控的 Python 函数、数据库或公司接口。

```python
@tool
def calculate_total_price(unit_price: float, quantity: int) -> str:
    """根据商品单价和数量，计算商品总价。单价单位是元。"""
    total = unit_price * quantity
    return f"{total:.2f} 元"
```

这里：

- `@tool`：把 Python 函数包装成 LangChain 工具。
- 函数名：默认成为工具名。
- 参数类型 `float`、`int`：告诉模型参数应该是什么类型。
- 文档字符串：告诉模型什么时候应该使用该工具。

### 7.2 工具调用的完整五步

```text
1. 用户：3 杯咖啡，每杯 12.5 元，一共多少钱？

2. tool_model：返回工具请求
   工具名：calculate_total_price
   参数：{"unit_price": 12.5, "quantity": 3}

3. Python：真正调用函数，算出 37.50 元

4. ToolMessage：把“37.50 元”写回消息历史

5. tool_model：根据用户问题和工具结果，生成自然语言回答
   “3 杯咖啡一共是 37.50 元。”
```

第一步模型返回的不是最终答案，而是类似这样的请求：

```python
tool_call = first_response.tool_calls[0]
tool_call["name"]  # "calculate_total_price"
tool_call["args"]  # {"unit_price": 12.5, "quantity": 3}
```

注意：读取 `tool_call["name"]` 不会自动执行工具。模型只能提出请求；真正执行的是下面的 Python 代码：

```python
tool_result = calculate_total_price.invoke(tool_call["args"])
```

### 7.3 `ToolMessage` 不是“翻译器”

```python
ToolMessage(
    content=tool_result,
    tool_call_id=tool_call["id"],
)
```

`ToolMessage` 只是一张工具回执：

```text
编号为 call_xxx 的工具请求，真实执行结果是：37.50 元。
```

它不生成自然语言。把结果“白话表达给用户”的是第二次：

```python
final_response = tool_model.invoke(messages)
```

`tool_call_id` 只用于把“工具请求”和“工具结果”对应起来；它不是会话 ID，也不会让另一个模型自动知道任务。

### 7.4 为什么要调用模型两次

```text
第一次：理解问题 → 选择工具、准备参数
Python：执行工具 → 得到可信事实
第二次：根据可信事实 → 组织面向用户的回答
```

因此工具调用通常比普通问答慢一些，因为至少会发生两次模型请求。

---

## 8. 多工具：避免把工具名称写死

`18_AI选择不同工具.py` 有两个工具：计算总价、查询退款政策。

单工具 Demo 中可以简化成：

```python
calculate_total_price.invoke(tool_call["args"])
```

但多个工具时，不能把函数名写死。需要用一张“工具名 → 工具对象”的表：

```python
tools = [calculate_total_price, get_return_policy]

tools_by_name = {
    tool.name: tool
    for tool in tools
}
```

这段是字典推导式，等价于：

```python
tools_by_name = {}

for tool in tools:
    tools_by_name[tool.name] = tool
```

当模型返回 `"get_return_policy"` 时：

```python
selected_tool = tools_by_name.get(tool_call["name"])
tool_result = selected_tool.invoke(tool_call["args"])
```

生产项目还应增加：工具白名单、参数校验、权限判断、错误处理和日志记录。绝不能因为模型返回了某个名字就执行任意系统命令。

---

## 9. `model`、`tool_model`、`json_model` 的关系

它们不是三个会私下交流的 AI，也没有共享记忆。

```python
model = ChatOpenAI(...)

tool_model = model.bind_tools([calculate_total_price])

json_model = model.bind(
    response_format={"type": "json_object"}
)
```

可以理解为同一个 DeepSeek 模型，加了不同的“本次请求规则”：

| 变量 | 额外能力/要求 | 常见用途 |
| --- | --- | --- |
| `model` | 没有特别附加配置 | 普通自然语言回答 |
| `tool_model` | 知道可调用工具的名称、说明和参数 | 请求工具；或拿到工具结果后自然语言回答 |
| `json_model` | 要求返回 JSON 对象 | 把结果交给程序、数据库或前端 |

它们之所以能接力，不是靠某个 ID，而是 Python 把同一份 `messages` 显式传入下一次调用。

`19_工具结果转JSON.py` 的流程：

```text
tool_model 读取 messages
→ 请求计算工具
→ Python 计算并追加 ToolMessage
→ json_model 读取同一份 messages
→ 输出 JSON
```

例如最终 JSON：

```json
{
  "商品": "咖啡",
  "数量": 3,
  "总价": 37.5,
  "货币": "元"
}
```

程序是否选择自然语言还是 JSON，是由 Python 下一行调用哪个模型变量决定的；不会因为“工具已经结束”而自动触发。

---

## 10. 本地知识问答与真正 RAG

### 10.1 `20_让AI阅读本地知识.py` 做了什么

它读取：

```text
咖啡店知识库.md
```

再把全文放进系统消息：

```python
with open(knowledge_file, "r", encoding="utf-8") as file:
    knowledge = file.read()
```

然后要求模型只依据这份资料回答。

这适合一两页短资料，是非常重要的第一步：**回答有依据，不再只依赖模型已有知识。**

### 10.2 为什么它还不算完整 RAG

资料多了以后，把全文都发给模型会有三个问题：

- 慢，输入越长，费用和等待时间越高。
- 容易让模型在大量无关文字中遗漏重点。
- 超过模型上下文长度后，根本无法全部发送。

真正的 RAG（Retrieval-Augmented Generation，检索增强生成）会这样做：

```text
准备资料时：
Markdown/PDF/网页
→ 切成小段（chunk）
→ 每段转换为语义向量（embedding）
→ 保存到向量库

用户提问时：
问题 → 语义向量
→ 找到最相关的 3～5 个片段
→ 只把这些片段 + 用户问题发送给 DeepSeek
→ DeepSeek 依据片段生成回答
```

### 10.3 `sentence-transformers` 是下一步要用的工具

它不负责聊天，而是把句子和文档片段转换成可比较的“语义向量 安装 python -m pip install sentence-transformers”。 

```text
用户：没拆封的咖啡豆能退吗？
资料：未拆封的咖啡豆可在购买后 7 天内退款。
→ 两句话意思接近，向量距离也更接近
→ 程序找到这条资料
```

它比简单关键词匹配更好，因为“能退吗”和“退款政策”字面不同，意思却接近。

本项目已经安装完成。安装命令记录如下，今后换电脑或新建虚拟环境时可以再次执行：

```powershell
python -m pip install sentence-transformers
```

中文语义检索 RAG Demo 已经开始学习。首次运行通常还会下载一个公开的中文嵌入模型。

---

## 11. 常见误解与正确理解

| 常见误解 | 正确理解 |
| --- | --- |
| AI 会自动记住上一轮 | 每次调用都要传 `messages`；跨程序运行还要保存到文件或数据库 |
| `tool_call["name"]` 会自动运行工具 | 它只是模型建议使用的工具名；Python 必须主动执行 |
| `ToolMessage` 会把结果变成白话 | 它只保存工具结果；第二次模型调用才生成白话回答 |
| `tool_model` 是“只会选工具”的另一个 AI | 它是同一模型的工具配置；也能根据工具回执自然语言回答 |
| `json_model` 与 `tool_model` 用 ID 共享任务 | 它们不共享状态；Python 用同一份 `messages` 让它们看见同一上下文 |
| JSON 就等于 AI 更聪明 | JSON 只让输出格式更稳定，方便程序读取 |
| 本地 Markdown 全文发送就是完整 RAG | 它是知识注入的简化版；真正 RAG 还需要检索最相关片段 |
| AI 工具调用等于 AI 获得无限权限 | 工具由 Python 提供，程序必须限制可执行范围 |

---

## 12. 每次练习的推荐方式

1. 先读代码顶部的中文注释，先说出“这段要解决什么问题”。
2. 再运行：

   ```powershell
   python .\文件名.py
   ```

3. 每次只改一个地方，例如 `question`、系统规则或知识库的一条内容。
4. 运行后观察输出，不符合预期就保存完整报错或截图。
5. 能用自己的话复述流程，再学习下一个概念。

尤其是工具调用，要能复述这句话：

```text
模型理解并请求工具，Python 执行工具，ToolMessage 交回结果，模型再组织回答。
```

---

## 13. 后续学习路线

### 下一阶段：真正 RAG

1. 安装并理解 `sentence-transformers`。
2. 把 Markdown 按段落切分。
3. 为每段资料创建语义向量。
4. 用用户问题找出最相近段落。
5. 将检索到的段落交给 DeepSeek，并要求标明依据。

### 再下一阶段：把 Demo 变成小应用

1. 加入多轮用户输入。
2. 加入文档来源、引用和“资料不足”的回答。
3. 为工具加入异常处理、参数校验、权限控制。
4. 使用网页界面或 API 服务提供给他人使用。
5. 保存对话、用户信息和知识库索引。

学习重点始终是：先理解每个环节的职责，再增加功能；不要为了“像 AI”而把简单问题交给模型，也不要为了“像编程”而把自然语言理解写成大量死板字符串判断。

---

## 14. RAGDemo 阶段记录（第 22～29 课）

这一阶段的目标是理解：程序如何从本地资料中找到与问题最相关的内容，再把原始中文资料交给 DeepSeek。BGE 只负责语义向量和相似度排序，不负责切文档，也不负责把数字向量“翻译回中文”。

### 14.1 普通索引流程

第 22～25 课建立了普通 RAG 的基本流程：

```text
Markdown 知识库
→ 切成 chunks
→ BGE 为每个 chunk 生成一个向量
→ chunks 和 embeddings 一起保存到 JSON
→ 用户问题生成一个 query_embedding
→ semantic_search() 找到最相似的片段
→ 取回原始中文 chunk
→ DeepSeek 根据检索资料回答
```

JSON 中的对应关系是：

```text
chunks[0]      ↔ embeddings[0]
chunks[1]      ↔ embeddings[1]
chunks[2]      ↔ embeddings[2]
```

每个向量不是“一个数字对应一个字”。BGE-small-zh-v1.5 当前输出 512 个数字，512 个数字作为整体表示这一段文字的语义。

### 14.2 长文档切块与 `chunk_overlap`

第 26 课使用 `RecursiveCharacterTextSplitter` 观察长文档切块，第 27 课把切块结果和向量写入 `长文档知识库索引.json`。

```text
26_长文档切块与重叠.py
→ 只切块并打印，不会修改 JSON

27_长文档构建知识库索引.py
→ 切块、生成 BGE 向量并写入 JSON
```

`chunk_overlap=30` 是目标重叠量，不是强制复制前一个片段最后 30 个字符。切块器优先保留完整段落、句子等自然单位；如果一个自然单位本身已经超过 30 个字符，就可能无法保留，因此实际重叠量可能是 0。

`chunk_overlap` 只能解决相邻片段的边界问题，不能解决“第一段的前提影响第五段结论”这种远距离依赖。远距离依赖需要父子切块、公共前提继承、章节摘要或结构化关系。

### 14.3 父子索引

第 28 课创建 `父子知识库索引.json`：

```text
父章节：保存完整章节和上下文
├── 子片段1：用于精确语义检索
├── 子片段2：用于精确语义检索
└── 子片段3：用于精确语义检索
```

父章节保存在 `parents`，子片段保存在 `children`，只有子片段的 `embedding_text` 被交给 BGE 生成向量：

```python
child_embedding_texts = [
    child["embedding_text"]
    for child in children
]

child_embeddings = embedding_model.encode(
    child_embedding_texts,
    normalize_embeddings=True,
)
```

`child_embeddings[i]` 与 `children[i]` 依靠相同数组下标对应。向量本身不保存 `parent_id`，`parent_id` 保存在对应的子对象中。

### 14.4 `corpus_id` 如何找到父章节

在当前使用的 `sentence_transformers.util.semantic_search()` 中，返回结果的 `corpus_id` 是传入的 `child_embeddings` 数组下标：

```python
child_index = result["corpus_id"]
matched_child = children[child_index]
parent_id = matched_child["parent_id"]
matched_parent = parents_by_id[parent_id]
```

完整链路是：

```text
corpus_id
→ children[corpus_id]
→ matched_child["parent_id"]
→ parents_by_id[parent_id]
→ 完整父章节
→ DeepSeek
```

`parents_by_id` 是字典推导式：

```python
parents_by_id = {
    parent["parent_id"]: parent
    for parent in parents
}
```

它把父章节列表转换成“父章节 ID → 父章节对象”的查询表，方便通过 ID 直接取回完整父章节。

### 14.5 当前文件与学习状态

```text
RAGDemo/
├── 22_构建知识库索引.py
├── 23_查询知识库索引.py
├── 24_终端连续查询知识库.py
├── 25_相似度阈值避免乱答.py
├── 26_长文档切块与重叠.py
├── 27_长文档构建知识库索引.py
├── 28_构建父子知识库索引.py
├── 29_查询父子知识库.py
├── 长文档示例.md
├── 长文档知识库索引.json
└── 父子知识库索引.json
```

第 29 课代码已经创建，当前下一步需要亲自运行：

```powershell
python .\RAGDemo\29_查询父子知识库.py
```

运行时重点观察三段输出：BGE 找到的子片段、通过 `parent_id` 找回的完整父章节、DeepSeek 的最终回答。

---
## 15. 官方参考资料

- [DeepSeek JSON Output 文档](https://api-docs.deepseek.com/guides/json_mode/)
- [DeepSeek Tool Calls 文档](https://api-docs.deepseek.com/guides/tool_calls/)
- [LangChain Tools 文档](https://docs.langchain.com/oss/python/langchain/tools)
- [Sentence Transformers 语义搜索文档](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html)
