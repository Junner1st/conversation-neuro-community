#!/usr/bin/env python3
"""
meta.py

Orchestrator script that manages the following workflow each round:
1. Invoke writer.py to generate/modify shared_doc.cpp.
2. Compile shared_doc.cpp into a.out, logging to compile.<version>.log.
3. If compile errors occur:
      - Invoke reviewer.py for feedback.
      - Increment version and repeat from step 1.
   Else:
4. Run a.out, logging to execute.<version>.log.
5. If execution errors occur:
      - Invoke reviewer.py for feedback.
      - Increment version and repeat from step 1.
   Else:
6. Analyze output to decide completion. If not complete:
      - Increment version and repeat from step 1.
   Else:
7. Exit successfully.
"""

import subprocess
import sys
import os

# -------- Configuration --------

# Commands to run writer and reviewer. Adjust if using a different invocation method.
# For example, if you truly need "uv run writer.py", replace ['python', 'writer.py'] accordingly.
run_writer_cmd = ["uv", "run", "writer.py"]

run_reviewer_cmd = ["uv", "run", "reviewer.py"]

# C++ source and executable names
cpp_source = "shared_doc.cpp"
executable = "a.out"
excutor_command = lambda source, output: ["g++", source, "-std=c++17", "-Wall", "-Wextra", "-o", output]

# Maximum number of rounds to avoid infinite loops (adjust as needed)
MAX_ROUNDS = 15


DOC_PATH = "shared_doc.cpp"
LOG_PATH = "discussion_log.txt"
for path in (DOC_PATH, LOG_PATH):
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write("")

def check_completion(output: str) -> bool:
    """
    Inspect 'output' from a.out and decide whether the task is complete.
    Customize this function to match specific completion criteria.
    Example: return True if "TASK_COMPLETED" appears in output.
    """
    return "TASK_COMPLETED" in output

def run_subprocess(cmd: list, capture_stdout: bool = True, capture_stderr: bool = True) -> subprocess.CompletedProcess:
    """
    Run a subprocess and return the CompletedProcess.
    stdout and stderr are captured by default.
    """
    print(cmd)
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE if capture_stdout else None,
            stderr=subprocess.PIPE if capture_stderr else None,
            text=True,
            check=False  # We manually inspect returncode
        )
        return result
    except Exception as e:
        print(f"[meta] Failed to run command: {' '.join(cmd)}\nError: {e}")
        sys.exit(1)

def write_to_log(filename: str, content: str):
    """
    Write 'content' to 'filename'. Overwrite if it exists.
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"[meta] Error writing to log {filename}: {e}")
        sys.exit(1)

def append_to_log(filename: str, content: str):
    """
    Append 'content' to 'filename'.
    """
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"[meta] Error appending to log {filename}: {e}")
        sys.exit(1)

def main():
    version = 1

    Initial_prompt = '''1. You are a C++ code generator. Your task is to generate a C++ program that meets the requirements specified in the prompt.
2. The generated code should be complete and functional, capable of being compiled and executed without errors.
3. The "whole code" should be written inside a pair of triple backticks (```cpp ... ```).
4. The output format should be:
```cpp
code...
```
Feedbacks...
5. Your Task: Make a C++ uint128 type from uint64. And please implement all basic operations (+,-,*,/,>>,<<,>,<,=) and type transformations for this type.
'''

# 5. Your Task: Generate a C++ Hello World program that prints "Hello, World!" to the console.


    while version <= MAX_ROUNDS:
        print(f"\n[meta] === Round {version} ===")

        # 1. Invoke writer.py to (re)generate shared_doc.cpp
        ## 1.1 Read log
        log_filename = f"{version - 1}.log" if version > 1 else None
        if log_filename and os.path.exists(log_filename):
            with open(log_filename, "r", encoding="utf-8") as f:
                last_log = f.read()
            print(f"[meta] Last log ({log_filename}):\n{last_log}")
        else:
            last_log = None
            print("[meta] No previous log found.")

        ## 1.2 Run writer.py with the initial prompt or last log
        print("[meta] Invoking writer.py ...")
        prompt = (Initial_prompt + "\n\n" + last_log) if last_log else Initial_prompt
        print(f"[meta] Delivering prompt to writer.py:\n{prompt}")

        with open("prompt.txt", "w", encoding="utf-8") as prompt_file:
            prompt_file.write(prompt)

        cmd = run_writer_cmd
        print(f'{" ".join(cmd)}')
        writer_proc = run_subprocess(cmd)
        if writer_proc.returncode != 0:
            print(f"[meta] writer.py exited with code {writer_proc.returncode}. Aborting.")
            sys.exit(1)

        # 2. Compile shared_doc.cpp
        compile_log = f"{version}.log"
        print(f"[meta] Compiling {cpp_source} → {executable}, logging to {compile_log}")
        gcc_cmd = excutor_command(cpp_source, executable)
        compile_proc = run_subprocess(gcc_cmd)
        # Write compile stdout+stderr to log
        compile_output = ""
        if compile_proc.stdout:
            compile_output += compile_proc.stdout
        if compile_proc.stderr:
            compile_output += compile_proc.stderr
        write_to_log(compile_log, compile_output)

        # 3. Check compile result
        if compile_proc.returncode != 0:
            print(f"[meta] Compilation failed (see {compile_log}). Invoking reviewer.py ...")
            # 3-1. Invoke reviewer.py to analyze compile errors
            reviewer_proc = run_subprocess(run_reviewer_cmd)
            # Append reviewer feedback to compile log
            feedback = "\n\n[meta] Reviewer feedback:\n"
            if reviewer_proc.stdout:
                feedback += reviewer_proc.stdout
            if reviewer_proc.stderr:
                feedback += reviewer_proc.stderr
            append_to_log(compile_log, feedback)
            version += 1
            continue  # Next round

        # 4. Run the compiled executable
        run_log = f"{version}.log"
        print(f"[meta] Running {executable}, logging to {run_log}")
        exec_cmd = [f"./{executable}"]
        exec_proc = run_subprocess(exec_cmd)
        # Write execution stdout+stderr to log
        exec_output = ""
        if exec_proc.stdout:
            exec_output += exec_proc.stdout
        if exec_proc.stderr:
            exec_output += exec_proc.stderr
        write_to_log(run_log, exec_output)

        # 5. Check execution result
        # print(f"[meta] Execution failed (see {run_log}). Invoking reviewer.py ...")
        print(f"[meta] Execution finished. (see {run_log}). Invoking reviewer.py ...")
        reviewer_proc = run_subprocess(run_reviewer_cmd)
        feedback = "\n\n[meta] Reviewer feedback:\n"
        if reviewer_proc.stdout:
            feedback += reviewer_proc.stdout
        if reviewer_proc.stderr:
            feedback += reviewer_proc.stderr
        append_to_log(run_log, feedback)
        version += 1
        # continue  # Next round

        # 6. Analyze output to see if task is complete
        print("[meta] Execution succeeded. Checking task completion criteria ...")
        with open("reviewer.log", "r", encoding="utf-8") as f:
            reviewer_log = f.read()
        #if check_completion(exec_output):
        if check_completion(reviewer_log):
            print(f"[meta] Task completion detected in round {version}. Exiting.")
            break
        else:
            print(f"[meta] Task not complete in round {version}. Proceeding to next round.")
            version += 1

    else:
        # 如果达到 MAX_ROUNDS 仍未完成
        print(f"[meta] Reached maximum rounds ({MAX_ROUNDS}) without completion. Exiting with failure.")
        sys.exit(1)

if __name__ == "__main__":
    main()
