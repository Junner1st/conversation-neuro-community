# reviewer.py

import sys
import os
import re
import glob
import asyncio
import ollama
import logging

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(
    filename="reviewer.log",
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)


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
        raise FileNotFoundError("No log files matching '*.log' found.")
    return latest_log


async def main():
    # 1. Locate and read the latest log file
    try:
        latest_log = find_latest_log()
    except FileNotFoundError as e:
        logging.error(f"[reviewer] Error: {e}", file=sys.stderr)
        sys.exit(1)

    with open(latest_log, "r", encoding="utf-8") as f:
        log_content = f.read()

    with open("shared_doc.cpp", "r", encoding="utf-8") as f:
        code = f.read()

    with open("prompt.txt", "r", encoding="utf-8") as f:
        initial_prompt = f.read()
    # 2. Construct the review prompt using the log content
    review_prompt = f"""
You are a senior C++ code reviewer. Here is the task for the writer:
```
{initial_prompt}
```
and your mission is to give advise and the correct code.

Here is the current C++ code in shared_doc.cpp:
```cpp
{code}
```

The following is the entire content of the most recent log file ({latest_log}), which may contain compiler or runtime errors:
```
{log_content}
```

Please do the following:
1. Analyze the errors above and provide detailed feedback on how to fix the C++ code.
2. If you can propose a corrected C++ code snippet, wrap it all inside a pair of triple backticks with "```cpp ... ```".
3. Keep your feedback focused on solving the errors and improving code correctness.
4. Make a FINAL summary of ["TASK_COMPLETED", "TASK_OK", "TASK_FAILED"]. If the code align to writer's task, no errors in the log, and nothing to imporve, output an final status "TASK_COMPLETED". And if there is error or warnning in the log, or something need to be disscussed, the final status is "TASK_OK". If there is a massive of error, the status' going to be "TASK_FAILED".
"""

    # 3. Configure MCP client to connect to editor.py
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "editor.py"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 4. Use Ollama to generate review feedback
            resp = ollama.generate(
                model="yi:34b",
                prompt=review_prompt,
                stream=False,
                options={"num_ctx": 4000}
            )
            review_output = resp["response"]
            logging.info(f"[reviewer] Review output: {review_output}")

            # 5. Append the review feedback to discussion log via editor.py

            review_output = "=====================================================================================================\n" \
                            + review_output

            append_success = await session.call_tool(
                "append_comment",
                arguments={"comment": review_output}
            )
            if not append_success:
                logging.info("[reviewer] Warning: Failed to append comment to discussion log.")

            # 6. Check if the review includes a corrected C++ snippet between ```cpp ... ```
            # code_matches = re.findall(r"```cpp(.*?)```", review_output, re.DOTALL)
            # if code_matches:
            #     # If multiple code blocks found, take the first
            #     corrected_code = code_matches[0].strip()

            # 8. Output the full review feedback to stdout (for meta.py to capture)
            logging.info(review_output)

if __name__ == "__main__":
    asyncio.run(main())

