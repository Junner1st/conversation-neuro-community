# writer.py
import argparse
import os
import sys

def generate_initial_cpp() -> str:
    """
    如果没有任何错误日志，就生成一个最初版的 shared_doc.cpp。
    下面这个示例只是生成一个输出 "Hello, world!" 的简单程序。
    """
    return r'''
#include <iostream>
int main() {
    std::cout << "Hello, world!" << std::endl;
    return 0;
}
'''

def generate_fixed_cpp_from_compile_errors(error_log_path: str) -> str:
    """
    当上次编译失败时（有 compile.<version>.log），
    你可以在这里读取 error_log_path 并据此修改源码。
    下面示例只是示意：假设 error_log 中提示函数缺少分号，就插入分号。

    实际业务里，你可以：
      1. 解析 error_log_path 中的 gcc 报错信息（例如 “error: expected ';' before '}'”），
      2. 根据报错位置做自动修复，或者生成一个全新的版本，甚至把错误原文传给 Ollama 让它 rewrite 代码。
    """
    with open(error_log_path, "r", encoding="utf-8", errors="ignore") as f:
        errors = f.read()

    # 这里只是演示：如果看到 "expected ';'" 就在某行后加分号；否则维持初始版本
    if "expected ';'" in errors:
        # 举例：给出一个修正后的简单程序
        return r'''
#include <iostream>
int main() {
    std::cout << "修正后的 Hello, World!" << std::endl; // 添加了分号
    return 0;
}
'''
    else:
        # 如果不识别错误，就返回原先生成的初稿
        return generate_initial_cpp()

def generate_fixed_cpp_from_runtime_errors(error_log_path: str) -> str:
    """
    当上次运行 a.out 出错时（如段错误、逻辑不符合预期），
    你可以在这里据 error_log_path 中的 stderr/stdout 信息做调整。
    比如：
      - 读取错误日志中的 “Segmentation fault” 并加防越界检查
      - 读取程序输出并调整逻辑
    下面示例只是示意。
    """
    with open(error_log_path, "r", encoding="utf-8", errors="ignore") as f:
        run_errors = f.read()

    # 如果检测到运行时异常，就改写程序，让它打印 “SUCCESS”
    if "Segmentation fault" in run_errors or "ERROR" in run_errors:
        return r'''
#include <iostream>
int main() {
    // 之前有段错误，这里做了一些修正...
    std::cout << "SUCCESS" << std::endl;
    return 0;
}
'''
    else:
        # 如果不识别运行时错误，则返回一个简单的“SUCCESS”程序
        return r'''
#include <iostream>
int main() {
    std::cout << "SUCCESS" << std::endl;
    return 0;
}
'''

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--error-log",
        help="上一轮的错误日志路径（compile.x.log 或 execute.x.log）",
        default=None
    )
    args = parser.parse_args()

    # 根据有无 error_log，决定生成初版源码还是修正版源码
    if args.error_log is None:
        cpp_code = generate_initial_cpp()
    else:
        # 如果是编译期错误日志，则调用 compile 相关修复逻辑
        if "compile" in args.error_log:
            cpp_code = generate_fixed_cpp_from_compile_errors(args.error_log)
        else:
            # 否则假设是运行期错误日志
            cpp_code = generate_fixed_cpp_from_runtime_errors(args.error_log)

    # 将生成的 C++ 代码写入 shared_doc.cpp
    with open("shared_doc.cpp", "w", encoding="utf-8") as f:
        f.write(cpp_code)

    print(f"[writer] 已将新的 C++ 源码写入 shared_doc.cpp （来自 {args.error_log or 'initial'}）")
    sys.exit(0)

if __name__ == "__main__":
    main()
