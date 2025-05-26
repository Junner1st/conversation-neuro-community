import sys
import asyncio
import ollama
import logging
import re
import glob
import os

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


LOG_PATTERN = "*.log"
def find_latest_log() -> str:
    """
    Find the log file with the highest numeric prefix (e.g., '3.log' > '2.log').
    Returns the filename, or raises FileNotFoundError if none found.
    """
    log_files = glob.glob(LOG_PATTERN)
    max_version = -1
    latest_log = None

    for fname in log_files:
        base = os.path.basename(fname)
        # Match filenames like '123.log'
        m = re.match(r"^(\d+)\.log$", base)
        if m:
            version = int(m.group(1))
            if version > max_version:
                max_version = version
                latest_log = fname

    if latest_log is None:
        logging.info("No log files matching '*.log' found.")
    return latest_log or ""

async def main():
    prompt_file_path = "prompt.txt"
    discussion_file_path = "discussion_log.txt"
    program_source = "shared_doc.cpp"
    last_log_path = find_latest_log()

    try:
        with open(prompt_file_path, "r", encoding="utf-8") as f:
            dynamic_prompt = f.read()
            logging.info(f"Read prompt: {dynamic_prompt}")

        with open(discussion_file_path, "r", encoding="utf-8") as f:
            discussion = f.read()

        with open(program_source, "r", encoding="utf-8") as f:
            program_content = f.read()
        if last_log_path is not "":
            with open(last_log_path, "r", encoding="utf-8") as f:
                last_log_content = f.read()
        else:
            last_log_content = ""

    except Exception as e:
        logging.error(f"[writer] {e}")
        sys.exit(1)

    sep = "=====================================================================================================\n"
    previous_discussion = discussion.split(sep)[-1] if sep in discussion else ""

    prompt = f'''{dynamic_prompt}

The Code Now:
```cpp
{program_content}
```

The log (may containing errors or warnings):
{last_log_content}

The discussion log:
{previous_discussion}
'''

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
                #model="codellama:34b",
                prompt=prompt,
                stream=False,
                options={"num_ctx": 4000}
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
