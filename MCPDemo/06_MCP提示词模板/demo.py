"""MCP 客户端：读取服务端 Prompt，并查看填充后的消息数组。"""

import asyncio
import json
import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient


LESSON_DIR = Path(__file__).resolve().parent
SERVER_PATH = LESSON_DIR / "server.py"
RESULT_PATH = LESSON_DIR / "输出" / "prompt_result.json"


async def main() -> None:
    client = MultiServerMCPClient(
        {
            "coffee_prompt": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(SERVER_PATH)],
            }
        }
    )

    # arguments 的值会传给服务端 draft_refund_response(order_id, refund_reason)：
    # {"order_id": "A1001", "refund_reason": "饮品洒漏"}。
    # 服务端将这两个值填入自己的固定模板，再把消息数组返回。
    prompt_messages = await client.get_prompt(
        server_name="coffee_prompt",
        prompt_name="draft_refund_response",
        arguments={
            "order_id": "A1001",
            "refund_reason": "饮品洒漏",
        },
    )

    # prompt_messages 的值大致是：
    # [HumanMessage(content="请按星光咖啡退款客服规范处理这条请求。\n\n订单号：A1001...")]
    records = []
    for message in prompt_messages:
        record = {
            "message_type": message.type,
            "content": str(message.content),
        }
        records.append(record)

        print(f"消息类型：{record['message_type']}")
        print("消息内容：")
        print(record["content"])

    with RESULT_PATH.open("w", encoding="utf-8") as result_file:
        json.dump(
            {
                "prompt_name": "draft_refund_response",
                "arguments": {
                    "order_id": "A1001",
                    "refund_reason": "饮品洒漏",
                },
                "messages": records,
            },
            result_file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n共拿到 {len(records)} 条可交给模型的消息。")
    print(f"完整结果已写入：{RESULT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
