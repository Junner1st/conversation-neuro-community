# meta.py
import subprocess
import time
import sys
import os

def run_writer(error_log: str = None) -> bool:
    """
    运行 writer.py，让它根据（可选的）错误日志生成或修改 shared_doc.cpp。
    如果提供了 error_log，则把 --error-log 参数传给 writer.py；
    返回 True 表示 writer.py 执行成功（即进程退出码为 0）。
    """
    cmd = ["uv", "run", "writer.py"]
    if error_log:
        cmd += ["--error-log", error_log]
    proc = subprocess.run(cmd)
    return proc.returncode == 0

def compile_cpp(version: int) -> tuple[int, str]:
    """
    用 gcc 编译 shared_doc.cpp，输出文件为 a.out。
    将 gcc 的 stdout/stderr 都写入 compile.<version>.log。
    返回 (gcc 返回码, compile_log_path)。
    """
    compile_log = f"compile.{version}.log"
    with open(compile_log, "w", encoding="utf-8") as logf:
        proc = subprocess.run(
            ["gcc", "shared_doc.cpp", "-o", "a.out"],
            stdout=logf,
            stderr=logf
        )
    return proc.returncode, compile_log

def run_executable(version: int) -> tuple[int, str]:
    """
    运行编译出的可执行文件 a.out，将 stdout/stderr 写入 execute.<version>.log。
    返回 (执行返回码, execute_log_path)。
    """
    exec_log = f"execute.{version}.log"
    # 确保可执行权限
    if os.path.exists("a.out"):
        os.chmod("a.out", 0o755)
    with open(exec_log, "w", encoding="utf-8") as logf:
        proc = subprocess.run(
            ["./a.out"],
            stdout=logf,
            stderr=logf
        )
    return proc.returncode, exec_log

def run_reviewer(compile_log: str) -> bool:
    """
    当编译出错时，调用 reviewer.py 并传入 compile_log 路径。
    返回 True 表示 reviewer.py 退出码为 0。
    """
    cmd = ["uv", "run", "reviewer.py", "--compile-log", compile_log]
    proc = subprocess.run(cmd)
    return proc.returncode == 0

def check_task_complete(exec_log: str) -> bool:

    """
    简单地从 execute.<version>.log 中读取 stdout，判断是否包含“SUCCESS”关键字。
    如果包含就认为任务完成，否则继续下一轮。
    这个判断逻辑可以根据你的实际业务需求做调整。
    """
    try:
        with open(exec_log, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return False
    return "SUCCESS" in content

def main():
    version = 1

    while True:
        print(f"\n=== Round {version} Start ===")

        # 1. 先让 writer.py 运行一次（如果上轮有错误日志，就把日志路径传进去）
        error_log = None
        if version > 1:
            # 如果不是第 1 轮，则可能有 compile.log 或 execute.log 传给 writer
            # 这里默认先把 compile.log 传给 writer，实际也可以传 exec_log
            compile_log = f"compile.{version-1}.log"
            execute_log = f"execute.{version-1}.log"
            # 如果上次编译已通过但运行失败，就把 exec_log 传给 writer；否则把 compile_log
            if os.path.exists(compile_log):
                with open(compile_log, "r", encoding="utf-8") as f:
                    prev_compile = f.read()
                # 如果上轮编译有错误（gcc 返回码 ≠ 0），就给 writer 传 compile_log
                prev_gcc_ret = not ("error:" not in prev_compile and "Undefined" not in prev_compile)
                if prev_gcc_ret:
                    error_log = compile_log
                else:
                    # 若编译成功但运行失败，则给 writer 传 exec_log
                    if os.path.exists(execute_log):
                        with open(execute_log, "r", encoding="utf-8") as f:
                            prev_exec = f.read()
                        if "ERROR" in prev_exec or "Segmentation fault" in prev_exec:
                            error_log = execute_log

        print(f"[meta] Running writer.py (error_log={error_log})")
        ok_writer = run_writer(error_log)
        if not ok_writer:
            print("[meta] ❌ writer.py 本身运行出错（exit code ≠ 0），请检查 writer.py 脚本。")
            sys.exit(1)

        # 2. 编译 shared_doc.cpp
        print(f"[meta] Compiling shared_doc.cpp  → compile.{version}.log")
        gcc_ret, compile_log_path = compile_cpp(version)
        if gcc_ret != 0:
            print(f"[meta] ❌ 编译失败 (gcc 返回码={gcc_ret})，调用 reviewer.py 提出意见")
            run_reviewer(compile_log_path)
            # 直接进入下一轮，让 writer 根据 compile.<version>.log 调整
            version += 1
            continue

        # 3. 编译成功，则执行可执行程序
        print(f"[meta] 编译通过，运行 a.out  → execute.{version}.log")
        exec_ret, exec_log_path = run_executable(version)
        if exec_ret != 0:
            print(f"[meta] ❌ 程序运行出错 (返回码={exec_ret})，进入下一轮让 writer 修改")
            version += 1
            continue

        # 4. 程序正常返回，检查输出是否满足“任务完成”的条件
        task_done = check_task_complete(exec_log_path)
        if task_done:
            print(f"[meta] ✅ 第 {version} 轮任务完成，退出流程。")
            break
        else:
            print(f"[meta] 🔄 第 {version} 轮程序运行正常，但未达成预期结果，进入下一轮。")
            version += 1

    print("\n=== All Done ===")

if __name__ == "__main__":
    main()