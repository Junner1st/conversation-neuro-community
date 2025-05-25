# reviewer.py
import argparse
import sys

def generate_review_from_compile_errors(log_path: str) -> str:
    """
    读取 compile.X.log，提取关键信息并生成审校意见。
    你也可以把整个日志传给 Ollama 让它输出一段更自然的文字。
    下面示例只是把日志原文放在前面，再附一句典型的人工建议。
    """
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            compile_output = f.read()
    except FileNotFoundError:
        return "[reviewer] 找不到编译日志，请检查路径是否正确。\n"

    review_text = "[reviewer] 以下是编译错误日志原文：\n\n"
    review_text += compile_output
    review_text += "\n=== 审校建议 ===\n"
    review_text += (
        "请检查代码中报错行所指示的位置，"
        "通常是缺少分号或括号不匹配。"
        "根据日志中的提示逐一修复，然后重新编译。\n"
    )
    return review_text

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--compile-log",
        help="传入上一轮的编译日志路径 compile.X.log",
        required=True
    )
    args = parser.parse_args()

    review = generate_review_from_compile_errors(args.compile_log)
    # 这里我们把 review 输出到 stdout，meta.py 会将 stdout 重定向到 compile.X.log
    # 你也可以写到单独文件，或通过 MCP 传回更复杂的结构。
    print(review)
    sys.exit(0)

if __name__ == "__main__":
    main()
