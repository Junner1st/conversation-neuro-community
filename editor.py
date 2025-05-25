# joint_edit_server.py
from mcp.server.fastmcp import FastMCP
import os
from typing import Tuple
import re

# 文档路径与日志路径
DOC_PATH = "shared_doc.cpp"
LOG_PATH = "discussion_log.txt"

def get_first_code_block(text):
    """
    取得文字中第一個被 ``` 包圍的程式碼區塊
    支援有語言標記和無語言標記兩種模式
    Args:
        text (str): 包含程式碼區塊的文字
    Returns:
        str or None: 第一個程式碼區塊的內容，如果沒有找到則返回 None
    """
    # 匹配模式：```可能的語言標記換行內容```
    pattern = r'```(?:\w+)?\n?(.*?)```'
    match = re.search(pattern, text, re.DOTALL)

    if match:
        return match.group(1).strip()
    return None

# 确保文件存在
for path in (DOC_PATH, LOG_PATH):
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write("")

# 创建 MCP Server 实例                                                                                                               mcp = FastMCP("joint-edit-server")

@mcp.tool()
def load_document() -> str:
    """读取当前文档内容并返回。"""
    with open(DOC_PATH, 'r', encoding='utf-8') as f:
        return f.read()

@mcp.tool()
def save_document(content: str) -> bool:
    """用传入的 content 覆盖文档，并在末尾记录版本信息（此处简化用时间戳）。"""
    try:
        with open(DOC_PATH, 'w', encoding='utf-8') as f:
            content = get_first_code_block(content)
            f.write(content)
        return True
    except Exception:
        return False

@mcp.tool()
def append_comment(comment: str) -> bool:
    """将讨论评论追加到日志文件末尾，每行一条。"""
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(comment.replace('\n', ' ') + "\n")
        return True
    except Exception:
        return False

if __name__ == "__main__":
    # 以 stdio 模式启动 MCP Server
    mcp.run()