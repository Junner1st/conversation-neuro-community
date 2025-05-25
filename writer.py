# writer.py
print("begining of writer")
import sys
import asyncio
import ollama

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

print("testttt:")
async def main():
    # # 1. Read dynamic prompt from command-line arguments
    # if len(sys.argv) < 2:
    #     print("[writer] Error: No prompt provided.", file=sys.stderr)
    #     sys.exit(1)
    # # Join all arguments into a single prompt string (allowing spaces/newlines)
    # # Find the "--prompt" argument and get the next argument as the file path
    # if "prompt" not in sys.argv:
    #     print("[writer] Error: --prompt argument not found.", file=sys.stderr)
    #     sys.exit(1)
    # prompt_index = sys.argv.index("prompt")
    # print(f"prompt_index: {prompt_index}")
    # if prompt_index + 1 >= len(sys.argv):
    #     print("[writer] Error: No file path provided after --prompt.", file=sys.stderr)
    #     sys.exit(1)
    # prompt_file_path = sys.argv[prompt_index + 1]
    # print(prompt_file_path)
    prompt_file_path = "prompt.txt"
    try:
        with open(prompt_file_path, "r", encoding="utf-8") as f:
            dynamic_prompt = f.read()
            print(dynamic_prompt)
    except Exception as e:
        print(f"[writer] Error: Failed to read prompt file: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Configure MCP server parameters to invoke editor.py
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "editor.py"],
        env=None
    )

    # 3. Start MCP client and call editor tools
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 4. Generate C++ code using Ollama with the dynamic prompt
            resp = ollama.generate(
                model="deepseek-coder-v2",
                prompt=dynamic_prompt,
                stream=False,
                options={"num_ctx": 2048}
            )
            generated_content = resp["response"]

            # 5. Save the generated content via editor.py's save_document tool
            save_success = await session.call_tool(
                "save_document",
                arguments={"content": generated_content}
            )
            if save_success:
                print("[writer] Successfully saved generated code to shared_doc.cpp")
            else:
                print("[writer] Error: Failed to save generated code", file=sys.stderr)

            # 6. Append a comment to the discussion log via editor.py's append_comment tool
            comment_text = "Writer: Generated new C++ code based on prompt."
            append_success = await session.call_tool(
                "append_comment",
                arguments={"comment": comment_text}
            )
            if append_success:
                print("[writer] Appended comment to discussion log")
            else:
                print("[writer] Error: Failed to append comment", file=sys.stderr)

print("Call writer.py sucessfully.")
asyncio.run(main())
