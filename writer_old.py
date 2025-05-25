# agent_writer.py
import asyncio
import ollama

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 想像这是主笔 Agent，它负责撰写或初始化文档
WRITER_PROMPT = (
    "You are a EXPERT PROGRAMMER. Please follow the demands to write or complete the script:\n"
    "1. Topic: Write a C++ program. Use uint64 to make an uint128 type.\n"
    "2. Includes all basic operations.\n"
    "3. Please output ONLY a Cpp script inside a pair of ```"
)

async def main():
    # 配置 MCP Server 的启动命令
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "editor.py"],
        env=None
    )

    # 1. 启动并连接到 MCP Server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 2. 直接用 Ollama 生成初稿
            resp = ollama.generate(
                model="deepseek-coder-v2",
                prompt=WRITER_PROMPT,
                stream=False,
                options={"num_ctx": 2048}
            )
            initial_content = resp["response"]

            # 3. 把生成的内容写入共享文档
            success = await session.call_tool(
                "save_document",
                arguments={"content": initial_content}
            )
            if success:
                print("Writer: 已将初稿保存到 shared_doc.<filename extension>")
            else:
                print("Writer: 保存文档时发生错误")

            # 4. 同时，可以在讨论日志写入一条说明
            comment = "Writer: 文档初稿已生成，等待 Reviewer 反馈。"
            await session.call_tool("append_comment", arguments={"comment": comment})

if __name__ == "__main__":
    asyncio.run(main())
