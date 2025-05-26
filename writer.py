import sys
import asyncio
import ollama
import logging

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 設定 logging，輸出到 writer.log
logging.basicConfig(
    filename="writer.log",
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)

logging.info("beginning of writer")

async def main():
    prompt_file_path = "prompt.txt"
    try:
        with open(prompt_file_path, "r", encoding="utf-8") as f:
            dynamic_prompt = f.read()
            logging.info(f"Read prompt: {dynamic_prompt}")
    except Exception as e:
        logging.error(f"[writer] Error: Failed to read prompt file: {e}")
        sys.exit(1)

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "editor.py"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            resp = ollama.generate(
                model="deepseek-coder-v2",
                prompt=dynamic_prompt,
                stream=False,
                options={"num_ctx": 2048}
            )
            generated_content = resp["response"]

            save_success = await session.call_tool(
                "save_document",
                arguments={"content": generated_content}
            )
            if save_success:
                logging.info("[writer] Successfully saved generated code to shared_doc.cpp")
            else:
                logging.error("[writer] Error: Failed to save generated code")

            comment_text = "Writer: Generated new C++ code based on prompt."
            append_success = await session.call_tool(
                "append_comment",
                arguments={"comment": comment_text}
            )
            if append_success:
                logging.info("[writer] Appended comment to discussion log")
            else:
                logging.error("[writer] Error: Failed to append comment")

logging.info("Call writer.py successfully.")
asyncio.run(main())