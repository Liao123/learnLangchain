"""MCP 客户端：读取知识服务公开的资源资料。"""

import asyncio
import json
import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient


LESSON_DIR = Path(__file__).resolve().parent
SERVER_PATH = LESSON_DIR / "server.py"
RESULT_PATH = LESSON_DIR / "输出" / "resources_result.json"


async def main() -> None:
    # client 会启动 server.py，并建立一个名为 coffee_knowledge 的 MCP 连接。
    client = MultiServerMCPClient(
        {
            "coffee_knowledge": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(SERVER_PATH)],
            }
        }
    )

    # get_resources() 的意思是“读取服务端公开的资料”。
    # 这一次 resources 的值大致有两个 Blob 对象。URI 保存在每个 Blob 的 metadata["uri"] 中：
    # [Blob(metadata={"uri": "coffee://knowledge/member-points"}), Blob(metadata={"uri": "coffee://knowledge/refund-policy"})]
    resources = await client.get_resources(server_name="coffee_knowledge")

    records = []
    for resource in resources:
        # resource.as_string() 把 Blob 中的资料内容取成普通 Python 字符串。
        # 例如正文开头会是："# 会员积分规则\n\n- 普通会员..."。
        resource_text = resource.as_string()
        record = {
            # 当前适配器把 MCP 的 URI 放在 metadata 中；例如 metadata["uri"] 是 coffee://knowledge/member-points。
            "uri": str(resource.metadata["uri"]),
            "mime_type": resource.mimetype,
            "content": resource_text,
        }
        records.append(record)

        print(f"\n资源 URI：{record['uri']}")
        print(f"资料类型：{record['mime_type']}")
        print("资料正文：")
        print(resource_text)

    with RESULT_PATH.open("w", encoding="utf-8") as result_file:
        json.dump({"resources": records}, result_file, ensure_ascii=False, indent=2)

    print(f"\n共读取 {len(records)} 份 MCP 资源。")
    print(f"完整结果已写入：{RESULT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
