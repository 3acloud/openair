from typing import Union
import asyncio
import os
import shutil
import uuid
import re
from pathlib import Path
from utilities.ask_answer import Answer
from utilities.workflow import Workflow
from utilities.detect import detect_available_agent
from worker.tasks import task
import base64
import json
import subprocess
from types import SimpleNamespace


def gen_image(inputfile, outputfile):
    instruction = f"根据文件'{inputfile}'里的Prompt（UTF-8格式文本），生成图片输出到'{outputfile}'。"
    ps_command = f'codex exec --skip-git-repo-check "{instruction}"'

    cmd = [
        "pwsh",
        "-NoProfile",
        "-Command",
        ps_command
    ]

    try:
        # 使用 Popen 以便实时打印输出并同时收集全部内容
        proc = subprocess.Popen(
            cmd,
            cwd='SERVERFILES',
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
    except FileNotFoundError:
        return False

    for line in proc.stdout:
        print(line, end='')       # 实时输出到终端

    # 等待进程结束
    returncode = proc.wait()

    if returncode != 0:
        return False

    return True


def gen_cimage(inputfile, outputfile):
    """调用 Claude Code；需要预先配置可用的图片生成工具及其权限。"""
    instruction = (
        f"根据文件'{inputfile}'里的Prompt（UTF-8格式文本），"
        f"生成图片输出到'{outputfile}'。"
    )

    # 通过环境变量传递指令，避免路径里的引号等字符被 PowerShell 解析。
    env = os.environ.copy()
    env["CLAUDE_GEN_IMAGE_INSTRUCTION"] = instruction
    ps_command = (
        "$ErrorActionPreference = 'Stop'\n"
        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)\n"
        "& claude -p $env:CLAUDE_GEN_IMAGE_INSTRUCTION --output-format text\n"
        "exit $LASTEXITCODE"
    )
    cmd = ["pwsh", "-NoProfile", "-NonInteractive", "-Command", ps_command]

    try:
        proc = subprocess.Popen(
            cmd,
            cwd="SERVERFILES",
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
    except OSError:
        return False

    with proc.stdout:
        for line in proc.stdout:
            print(line, end="", flush=True)

    return proc.wait() == 0


def gen_ximage(inputfile, outputfile):
    """通过已安装并登录的 Grok Build 生成图片；相对路径基于 SERVERFILES。"""
    workdir = Path("SERVERFILES").resolve()
    input_path = (workdir / inputfile).resolve()
    output_path = (workdir / outputfile).resolve()

    if not workdir.is_dir() or not input_path.is_file():
        return False

    instruction = (
        f"读取 UTF-8 文本文件 {str(input_path)!r} 里的 Prompt，"
        f"使用图片生成工具生成图片，并将实际图片文件保存到 {str(output_path)!r}。"
        "如目标目录不存在，请先创建。不要用文本文件代替图片；"
        "如果无法生成或保存，请明确报告失败。"
    )

    # 直接传递参数，避免 PowerShell 对引号、美元符号等进行解释。
    # 自动批准工具调用，使该函数可以无人值守运行。
    cmd = ["grok", "-p", instruction, "--always-approve"]

    try:
        with subprocess.Popen(
            cmd,
            cwd=workdir,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        ) as proc:
            for line in proc.stdout:
                print(line, end="", flush=True)

            returncode = proc.wait()

        return (
            returncode == 0
            and output_path.is_file()
            and output_path.stat().st_size > 0
        )
    except OSError:
        return False


def gen_dimage(inputfile, outputfile):
    """实时打印 Harness 输出；任务正常完成返回 True，否则返回 False。"""
    workdir = Path("SERVERFILES").resolve()
    input_path = Path(inputfile)
    output_path = Path(outputfile)
    if not input_path.is_absolute():
        input_path = workdir / input_path
    if not output_path.is_absolute():
        output_path = workdir / output_path

    if not workdir.is_dir() or not input_path.is_file():
        print(f"工作目录或 Prompt 文件不存在：{workdir} / {input_path}")
        return False

    instruction = (
        f"读取文件 {json.dumps(str(input_path), ensure_ascii=False)} 中的 Prompt"
        "（UTF-8 格式文本），使用已配置的图片生成工具生成图片，"
        f"将图片保存到 {json.dumps(str(output_path), ensure_ascii=False)}。"
        "如没有可用的图片生成工具，请明确报告失败。"
    )

    # PowerShell 单引号字符串只需将单引号加倍；EncodedCommand 避免多层转义。
    quoted_instruction = "'" + instruction.replace("'", "''") + "'"
    ps_command = (
        "$ErrorActionPreference = 'Stop'\n"
        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)\n"
        "$OutputEncoding = [Console]::OutputEncoding\n"
        f"& dsh --profile headless {quoted_instruction}\n"
        "exit $LASTEXITCODE\n"
    )
    encoded_command = base64.b64encode(ps_command.encode("utf-16-le")).decode("ascii")
    cmd = ["pwsh", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded_command]

    try:
        with subprocess.Popen(
            cmd,
            cwd=str(workdir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        ) as proc:
            for line in proc.stdout:
                print(line, end="", flush=True)
            returncode = proc.wait()
    except OSError as exc:
        print(f"无法启动 DeepSeek Harness：{exc}")
        return False

    if returncode != 0:
        return False
    if not output_path.is_file() or output_path.stat().st_size == 0:
        print(f"Harness 已退出，但未找到非空图片文件：{output_path}")
        return False
    return True


def gen_aimage(inputfile, outputfile):
    """通过 Antigravity CLI 生成图片，实时打印输出并返回退出状态。

    相对文件路径以 SERVERFILES 为基准。运行前需安装 Antigravity CLI，
    使用 agy 完成登录，并配置可用的图片生成工具及其调用权限。
    True 表示 CLI 成功退出，未额外验证输出图片的内容。
    """
    inputfile = os.fspath(inputfile)
    outputfile = os.fspath(outputfile)
    instruction = (
        f"根据文件'{inputfile}'里的Prompt（UTF-8格式文本），"
        f"生成图片输出到'{outputfile}'。"
    )

    # -p 执行一次非交互任务；直接传递参数，避免 PowerShell 转义问题。
    cmd = ["agy", "-p", instruction]

    try:
        with subprocess.Popen(
            cmd,
            cwd="SERVERFILES",
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        ) as proc:
            for line in proc.stdout:
                print(line, end="", flush=True)

            return proc.wait() == 0
    except OSError as exc:
        print(f"无法启动 Antigravity CLI：{exc}", flush=True)
        return False


def edit_image(imagefile, inputfile, outputfile):
    if imagefile.lower().endswith(".zip"):
        instruction = f"根据文件'{inputfile}'里的Prompt（UTF-8格式文本），处理压缩包'{imagefile}'里的图片，结果输出到'{outputfile}'。"
    else:
        instruction = f"根据文件'{inputfile}'里的Prompt（UTF-8格式文本），编辑图片'{imagefile}'，结果输出到'{outputfile}'。"
    ps_command = f'codex exec --skip-git-repo-check "{instruction}"'

    cmd = [
        "pwsh",
        "-NoProfile",
        "-Command",
        ps_command
    ]

    try:
        # 使用 Popen 以便实时打印输出并同时收集全部内容
        proc = subprocess.Popen(
            cmd,
            cwd='SERVERFILES',
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
    except FileNotFoundError:
        return False

    for line in proc.stdout:
        print(line, end='')       # 实时输出到终端

    # 等待进程结束
    returncode = proc.wait()

    if returncode != 0:
        return False

    return True


def edit_dimage(imagefile, inputfile, outputfile):
    """实时打印 Harness 输出；进程退出码为 0 时返回 True，否则 False。"""
    imagefile = os.fsdecode(imagefile)
    inputfile = os.fsdecode(inputfile)
    outputfile = os.fsdecode(outputfile)

    if imagefile.lower().endswith(".zip"):
        instruction = (
            f"根据文件'{inputfile}'里的Prompt（UTF-8格式文本），"
            f"处理压缩包'{imagefile}'里的图片，结果输出到'{outputfile}'。"
        )
    else:
        instruction = (
            f"根据文件'{inputfile}'里的Prompt（UTF-8格式文本），"
            f"编辑图片'{imagefile}'，结果输出到'{outputfile}'。"
        )

    # 指令作为数据传递，不拼接到 PowerShell 代码中；支持 npm 的 dsh.ps1/dsh.cmd。
    env = os.environ.copy()
    env["EDIT_DIMAGE_INSTRUCTION"] = instruction
    ps_command = (
        "$ErrorActionPreference = 'Stop'; "
        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); "
        "$dshCommand = Get-Command dsh -ErrorAction Stop; "
        "& $dshCommand.Source --profile headless $env:EDIT_DIMAGE_INSTRUCTION; "
        "exit $LASTEXITCODE"
    )
    cmd = ["pwsh", "-NoProfile", "-NonInteractive", "-Command", ps_command]

    try:
        with subprocess.Popen(
            cmd,
            cwd="SERVERFILES",
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        ) as proc:
            for line in proc.stdout:
                print(line, end="", flush=True)
            return proc.wait() == 0
    except OSError as exc:
        print(f"启动 DeepSeek Harness 失败：{exc}", flush=True)
        return False


def edit_cimage(imagefile, inputfile, outputfile):
    """调用 Claude Code 处理图片，实时打印日志，按进程退出码返回结果。

    相对文件路径以 SERVERFILES 为基准。Claude Code 需要已登录，
    并配置可用的图片编辑工具及相应工具权限。
    """
    imagefile = os.fsdecode(imagefile)
    inputfile = os.fsdecode(inputfile)
    outputfile = os.fsdecode(outputfile)

    if imagefile.lower().endswith(".zip"):
        instruction = (
            f"根据文件'{inputfile}'里的Prompt（UTF-8格式文本），"
            f"处理压缩包'{imagefile}'里的图片，结果输出到'{outputfile}'。"
        )
    else:
        instruction = (
            f"根据文件'{inputfile}'里的Prompt（UTF-8格式文本），"
            f"编辑图片'{imagefile}'，结果输出到'{outputfile}'。"
        )

    claude = shutil.which("claude")
    if claude is None:
        print("未找到 Claude Code，请先安装并将 claude 加入 PATH。", flush=True)
        return False

    # 直接传递参数，文件名中的引号、$ 等字符不会被 PowerShell 解释。
    # stream-json + verbose 输出逐行 JSON 日志，包含工具调用和执行结果。
    cmd = [
        claude,
        "--print",
        "--permission-mode", "acceptEdits",
        "--output-format", "stream-json",
        "--verbose",
        instruction,
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            cwd="SERVERFILES",
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
    except OSError as exc:
        print(f"无法启动 Claude Code：{exc}", flush=True)
        return False

    with proc.stdout:
        for line in proc.stdout:
            print(line, end="", flush=True)

    return proc.wait() == 0


def edit_ximage(imagefile, inputfile, outputfile):
    """在 SERVERFILES 中执行任务，实时打印日志并返回进程是否成功退出。

    相对文件路径以 SERVERFILES 为基准。运行前需安装 Grok Build，
    完成 grok login 或设置 XAI_API_KEY，并配置可用的图片编辑工具。
    True 表示 CLI 正常退出，不代表已验证输出图片的内容。
    """
    imagefile = os.fspath(imagefile)
    inputfile = os.fspath(inputfile)
    outputfile = os.fspath(outputfile)

    if imagefile.lower().endswith(".zip"):
        instruction = (
            f"根据文件'{inputfile}'里的Prompt（UTF-8格式文本），"
            f"处理压缩包'{imagefile}'里的图片，结果输出到'{outputfile}'。"
        )
    else:
        instruction = (
            f"根据文件'{inputfile}'里的Prompt（UTF-8格式文本），"
            f"编辑图片'{imagefile}'，结果输出到'{outputfile}'。"
        )

    # -p 使用非交互模式；自动批准工具调用，避免脚本等待确认。
    # 直接传递参数，无需 PowerShell 拼接或转义指令。
    cmd = ["grok", "-p", instruction, "--always-approve"]

    try:
        with subprocess.Popen(
            cmd,
            cwd="SERVERFILES",
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        ) as proc:
            for line in proc.stdout:
                print(line, end="", flush=True)

            return proc.wait() == 0
    except OSError as exc:
        print(f"无法启动 Grok Build：{exc}", flush=True)
        return False


def edit_aimage(imagefile, inputfile, outputfile):
    """通过 Antigravity CLI 处理图片或 ZIP，实时输出日志。

    相对文件路径以 SERVERFILES 为基准。运行前需安装 Antigravity CLI，
    使用 agy 完成登录，并配置可用的图片编辑工具及其调用权限。
    返回 True 表示 CLI 成功退出，未额外验证输出文件的内容。
    """
    imagefile = os.fspath(imagefile)
    inputfile = os.fspath(inputfile)
    outputfile = os.fspath(outputfile)

    if imagefile.lower().endswith(".zip"):
        instruction = (
            f"根据文件'{inputfile}'里的Prompt（UTF-8格式文本），"
            f"处理压缩包'{imagefile}'里的图片，结果输出到'{outputfile}'。"
        )
    else:
        instruction = (
            f"根据文件'{inputfile}'里的Prompt（UTF-8格式文本），"
            f"编辑图片'{imagefile}'，结果输出到'{outputfile}'。"
        )

    # -p 执行一次非交互任务；参数直接传递，不经 PowerShell 解析。
    cmd = ["agy", "-p", instruction]

    try:
        with subprocess.Popen(
            cmd,
            cwd="SERVERFILES",
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        ) as proc:
            for line in proc.stdout:
                print(line, end="", flush=True)

            return proc.wait() == 0
    except OSError as exc:
        print(f"无法启动 Antigravity CLI：{exc}", flush=True)
        return False
    

@task
def image_ai(
    workflow_data: dict,
    node_id: str,
):
    workflow = Workflow(workflow_data)
    level = workflow.get_node_field_value(node_id, "Level")
    prompt = workflow.get_node_field_value(node_id, "Prompt")

    fields = workflow.get_node_fields(node_id)
    for field in fields:
        if field in ("输出"):
            continue
        if workflow.get_node_field_value(node_id, field) == "BranchSkip":
            workflow.update_node_field_value(node_id, "输出", "BranchSkip")
            return workflow.data

    input_prompt: Union[str, list] = workflow.get_node_field_value(node_id, "Prompt")
    if isinstance(input_prompt, str):
        prompts = [input_prompt]
    elif isinstance(input_prompt, list):
        prompts = input_prompt

    init_image = workflow.get_node_field_value(node_id, "Init Image")
    if init_image == None:
        init_image = workflow.get_node_field_value(node_id, "init_image")
    if init_image == None:
        init_image = ""
    results = []
    gened = False
    for prompt in prompts:
        inputfile = "{" + str(uuid.uuid4()) + "}.txt" 
        with open(f"SERVERFILES/{inputfile}", "w", encoding='utf-8') as f:
            f.write(prompt)
        outputfile = "{" + str(uuid.uuid4()) + "}.jpg" 
        workflow.data["tempfiles"].append(f"SERVERFILES/{inputfile}")
        workflow.data["tempfiles"].append(f"SERVERFILES/{outputfile}")
        if init_image == "":
            agent = detect_available_agent()
            if agent == "Claude Code":
                gened = gen_cimage(inputfile, outputfile)
            elif agent == "Codex":
                gened = gen_image(inputfile, outputfile)
            elif agent == "Antigravity":
                gened = gen_aimage(inputfile, outputfile)
            elif agent == "Grok Build":
                gened = gen_ximage(inputfile, outputfile)
            elif agent == "DeepSeek Harness":
                gened = gen_dimage(inputfile, outputfile)
            else:
                gened = False
        else:
            init_image = init_image.replace('Image://', 'SERVERFILES/', 1) if init_image.startswith('Image://') else init_image
            init_image = init_image.replace('File://', 'SERVERFILES/', 1) if init_image.startswith('File://') else init_image
            if init_image.find("SERVERFILES") == -1:
                init_image = "SERVERFILES/" + init_image
            workflow.data["tempfiles"].append(init_image)
            agent = detect_available_agent()
            if agent == "Claude Code":
                gened = edit_cimage(init_image, inputfile, outputfile)
            elif agent == "Codex":
                gened = edit_image(init_image, inputfile, outputfile)
            elif agent == "Antigravity":
                gened = edit_aimage(init_image, inputfile, outputfile)
            elif agent == "Grok Build":
                gened = edit_ximage(init_image, inputfile, outputfile)
            elif agent == "DeepSeek Harness":
                gened = edit_dimage(init_image, inputfile, outputfile)
            else:
                gened = False
        if gened:
            if os.path.exists(f"SERVERFILES/{outputfile}"):
                results.append("Image://" + outputfile)
                if (workflow.nodesout.get(node_id) == False):
                    if workflow_data["answered"]:
                        Answer("\n", workflow_data["wid"], workflow_data["streamrunid"])
                    else:
                        workflow_data["answered"] = True
                    Answer("Image://" + outputfile, workflow_data["wid"], workflow_data["streamrunid"])
            else:
                gened = False
                break
        else:
            break
    if gened:
        output = results[0] if isinstance(input_prompt, str) else results
        workflow.update_node_field_value(node_id, "输出", output)
        return workflow.data



async def ltask(workflow,node_id,responses,i,prompt):
    inputfile = "{" + str(uuid.uuid4()) + "}.txt" 
    with open(f"SERVERFILES/{inputfile}", "w", encoding='utf-8') as f:
        f.write(prompt)
    outputfile = "{" + str(uuid.uuid4()) + "}.txt" 
    workflow.data["tempfiles"].append(f"SERVERFILES/{inputfile}")
    workflow.data["tempfiles"].append(f"SERVERFILES/{outputfile}")
    agent = detect_available_agent()
    if agent == "Claude Code":
        run_claude(inputfile, outputfile)
    elif agent == "Codex":
        run_codex(inputfile, outputfile)
    elif agent == "Antigravity":
        run_antigravity(inputfile, outputfile)
    elif agent == "Grok Build":
        run_grok(inputfile, outputfile)
    elif agent == "DeepSeek Harness":
        run_dsh(inputfile, outputfile)
    else:
        pass
    if os.path.exists(f"SERVERFILES/{outputfile}"):
        with open(f"SERVERFILES/{outputfile}", "r", encoding="utf-8") as f:
            responses[i] = SimpleNamespace(output_text=f.read().rstrip('\n'))
        return



def read_ximage(imagefile, inputfile, outputfile):
    instruction = f"根据文件'{inputfile}'里的Prompt（UTF-8格式文本），理解图片'{imagefile}'，结果输出到'{outputfile}'。"

    cmd = [
        "grok",
        "--no-auto-update",
        "--always-approve",
        "--output-format",
        "plain",
    ]
    cmd.extend(["-p", instruction])

    try:
        proc = subprocess.Popen(
            cmd,
            cwd="SERVERFILES",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return False

    for line in proc.stdout:
        print(line, end="")

    return proc.wait() == 0


def read_cimage(imagefile, inputfile, outputfile):
    """在 SERVERFILES 中调用 Claude Code 读图并写入结果。"""
    instruction = (
        f"根据文件'{inputfile}'里的Prompt（UTF-8格式文本），"
        f"理解图片'{imagefile}'，结果以UTF-8格式输出到'{outputfile}'。"
    )

    cmd = [
        "claude",
        "--dangerously-skip-permissions",
        "--output-format",
        "text",
        "-p",
        instruction,
    ]

    # Claude Code 通过环境变量禁用自动更新。
    env = os.environ.copy()
    env["DISABLE_AUTOUPDATER"] = "1"

    try:
        proc = subprocess.Popen(
            cmd,
            cwd="SERVERFILES",
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return False

    with proc.stdout:
        for line in proc.stdout:
            print(line, end="", flush=True)

    return proc.wait() == 0


def read_dimage(imagefile, inputfile, outputfile):
    """
    通过 DeepSeek Harness 根据 UTF-8 Prompt 理解图片并写入结果。
    """
    instruction = (
        f"根据文件'{inputfile}'里的Prompt（UTF-8格式文本），"
        f"理解图片'{imagefile}'，结果以UTF-8格式输出到'{outputfile}'。"
    )

    # 解析完整路径，同时兼容 Windows 下 npm 安装生成的 dsh.cmd。
    executable = shutil.which("dsh")
    if executable is None:
        return False

    cmd = [executable, "--profile", "headless", instruction]

    try:
        proc = subprocess.Popen(
            cmd,
            cwd="SERVERFILES",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
    except FileNotFoundError:
        return False

    with proc.stdout:
        for line in proc.stdout:
            print(line, end="", flush=True)

    return proc.wait() == 0


def read_aimage(imagefile, inputfile, outputfile):
    """通过 Antigravity CLI 理解图片，实时打印日志并返回退出状态。

    相对文件路径以 SERVERFILES 为基准。运行前需安装 Antigravity CLI，
    使用 agy 完成登录，并配置可用的图片理解能力及文件访问权限。
    True 表示 CLI 成功退出，未额外验证输出文件的内容。
    """
    imagefile = os.fspath(imagefile)
    inputfile = os.fspath(inputfile)
    outputfile = os.fspath(outputfile)
    instruction = (
        f"根据文件'{inputfile}'里的Prompt（UTF-8格式文本），"
        f"理解图片'{imagefile}'，结果输出到'{outputfile}'。"
    )

    # -p 执行一次非交互任务；参数直接传递，不经 PowerShell 解析。
    cmd = ["agy", "-p", instruction]

    try:
        with subprocess.Popen(
            cmd,
            cwd="SERVERFILES",
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        ) as proc:
            for line in proc.stdout:
                print(line, end="", flush=True)

            return proc.wait() == 0
    except OSError as exc:
        print(f"无法启动 Antigravity CLI：{exc}", flush=True)
        return False


def read_image(imagefile, inputfile, outputfile):
    instruction = f"根据文件'{inputfile}'里的Prompt（UTF-8格式文本），理解图片'{imagefile}'，结果输出到'{outputfile}'。"
    ps_command = f'codex exec --skip-git-repo-check "{instruction}"'

    cmd = [
        "pwsh",
        "-NoProfile",
        "-Command",
        ps_command
    ]

    try:
        # 使用 Popen 以便实时打印输出并同时收集全部内容
        proc = subprocess.Popen(
            cmd,
            cwd='SERVERFILES',
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
    except FileNotFoundError:
        return False

    with proc.stdout:
        for line in proc.stdout:
            print(line, end="", flush=True)

    return proc.wait() == 0


@task
def l_ai(
    workflow_data: dict,
    node_id: str,
):
    workflow = Workflow(workflow_data)

    fields = workflow.get_node_fields(node_id)
    for field in fields:
        if field in ("输出"):
            continue
        if workflow.get_node_field_value(node_id, field) == "BranchSkip":
            workflow.update_node_field_value(node_id, "输出", "BranchSkip")
            return workflow.data

    input_image = workflow.get_node_field_value(node_id, "Image")
    if input_image == None:
        input_image = ""
    if input_image != "":
        if isinstance(input_image, str):
            parts = [x.strip() for x in re.split(r'[;,]', input_image) if x.strip()]
            input_image = parts if len(parts) > 1 else parts[0]
        if isinstance(input_image, str):
            images = [input_image]
        elif isinstance(input_image, list):
            images = input_image
        results = []
        for image in images:
            image = image.replace('Image://', 'SERVERFILES/', 1) if image.startswith('Image://') else image
            image = image.replace('File://', 'SERVERFILES/', 1) if image.startswith('File://') else image
            if image.find("SERVERFILES") == -1:
                image = "SERVERFILES/" + image
            workflow.data["tempfiles"].append(image)
            prompt = workflow.get_node_field_value(node_id, "Prompt")

            inputfile = "{" + str(uuid.uuid4()) + "}.txt" 
            with open(f"SERVERFILES/{inputfile}", "w", encoding='utf-8') as f:
                f.write(prompt)
            outputfile = "{" + str(uuid.uuid4()) + "}.txt" 
            workflow.data["tempfiles"].append(f"SERVERFILES/{inputfile}")
            workflow.data["tempfiles"].append(f"SERVERFILES/{outputfile}")
            agent = detect_available_agent()
            if agent == "Claude Code":
                read_cimage(image, inputfile, outputfile)
            elif agent == "Codex":
                read_image(image, inputfile, outputfile)
            elif agent == "Antigravity":
                read_aimage(image, inputfile, outputfile)
            elif agent == "Grok Build":
                read_ximage(image, inputfile, outputfile)
            elif agent == "DeepSeek Harness":
                read_dimage(image, inputfile, outputfile)
            else:
                pass
            if os.path.exists(f"SERVERFILES/{outputfile}"):
                with open(f"SERVERFILES/{outputfile}", "r", encoding="utf-8") as f:
                    output=f.read()

            results.append(output)
        result = results if isinstance(input_image, list) else results[0]
        workflow.update_node_field_value(node_id, "输出", result)
        if (workflow.nodesout.get(node_id) == False):
            if workflow_data["answered"]:
                Answer("\n", workflow_data["wid"], workflow_data["streamrunid"])
            else:
                workflow_data["answered"] = True
            Answer(result, workflow_data["wid"], workflow_data["streamrunid"])
        return workflow.data

    input_prompt: Union[str, list] = workflow.get_node_field_value(node_id, "Prompt")

    if isinstance(input_prompt, str):
        prompts = [input_prompt]
    elif isinstance(input_prompt, list):
        prompts = input_prompt

    nodeout = workflow.nodesout.get(node_id)

    results = []
    if (nodeout == False):
        pass
    else:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # 当前线程没有事件循环，创建一个新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        tasks = []
        responses = {}
        i = 0
        for prompt in prompts:
            tasks.append(loop.create_task(ltask(workflow,node_id,responses,i,prompt)))
            i += 1
        if tasks:
            loop.run_until_complete(asyncio.wait(tasks))
        i = 0
        for prompt in prompts:
            try:
                if hasattr(responses[i], 'output_text'):
                    result = responses[i].output_text
                else:
                    result = responses[i].choices[0].message.content
                result = result.encode('gbk',errors='ignore').decode('gbk').encode('utf-8').decode('utf-8')
            except Exception:
                result = ""
            results.append(result)
            i += 1

    output = results[0] if isinstance(input_prompt, str) else results
    workflow.update_node_field_value(node_id, "输出", output)
    return workflow.data



def run_claude(inputfile, outputfile):
    """在 SERVERFILES 中调用 Claude Code，按退出码返回是否成功。"""
    instruction = (
        f"处理'{inputfile}'里的请求（UTF-8格式文本），输出到'{outputfile}'。"
        "绝对不允许列出当前目录下的所有项目。使用UTF-8。"
    )

    cmd = [
        "claude",
        "--dangerously-skip-permissions",
        "--output-format",
        "text",
        "-p",
        instruction,
    ]

    # Claude Code 通过环境变量禁用自动更新。
    env = os.environ.copy()
    env["DISABLE_AUTOUPDATER"] = "1"

    try:
        proc = subprocess.Popen(
            cmd,
            cwd="SERVERFILES",
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return False

    with proc:
        for line in proc.stdout:
            print(line, end="", flush=True)

    return proc.returncode == 0


def run_grok(inputfile, outputfile):
    instruction = f"处理'{inputfile}'里的请求（UTF-8格式文本），输出到'{outputfile}'。绝对不允许列出当前目录下的所有项目。使用UTF-8。"

    cmd = [
        "grok",
        "--no-auto-update",
        "--always-approve",
        "--output-format",
        "plain",
    ]
    cmd.extend(["-p", instruction])

    try:
        proc = subprocess.Popen(
            cmd,
            cwd="SERVERFILES",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return False

    for line in proc.stdout:
        print(line, end="")

    return proc.wait() == 0


def run_dsh(inputfile, outputfile):
    instruction = (
        f"处理'{inputfile}'里的请求（UTF-8格式文本），输出到'{outputfile}'。"
        "绝对不允许列出当前目录下的所有项目。使用UTF-8。"
    )

    # Headless 模式接收位置参数，默认以纯文本输出并在任务完成后退出。
    cmd = ["dsh", "--profile", "headless", instruction]

    env = os.environ.copy()
    # 保留原来的自动批准行为；此模式同时允许完整文件访问。
    env["DSH_PERMISSION_MODE"] = "danger-full-access"

    try:
        proc = subprocess.Popen(
            cmd,
            cwd="SERVERFILES",
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return False

    for line in proc.stdout:
        print(line, end="", flush=True)

    return proc.wait() == 0



def run_antigravity(inputfile, outputfile):
    """在 SERVERFILES 中运行 Antigravity，实时输出日志并返回退出状态。

    运行前需安装 Antigravity CLI 并使用 agy 完成登录。
    自动批准工具权限请求，沿用原函数的无人值守执行方式。
    True 表示 CLI 成功退出，未额外验证输出文件的内容。
    """
    project_dir = os.path.abspath("SERVERFILES")
    antigravity_executable = (
        shutil.which("agy.exe")
        or shutil.which("agy.cmd")
        or shutil.which("agy")
    )
    if antigravity_executable is None:
        return False

    inputfile = os.fspath(inputfile)
    outputfile = os.fspath(outputfile)
    instruction = (
        f"处理'{inputfile}'里的请求（UTF-8格式文本），"
        f"用补丁方式创建文件并输出到'{outputfile}'。"
        "绝对不允许列出当前目录下的所有项目。使用UTF-8。"
    )

    # -p 执行一次非交互任务；直接传递参数，不经 PowerShell 解析。
    # cwd 指定工作区；无需 Codex 的信任配置和 Git 检查参数。
    cmd = [
        antigravity_executable,
        "--dangerously-skip-permissions",
        "-p",
        instruction,
    ]

    try:
        with subprocess.Popen(
            cmd,
            cwd=project_dir,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        ) as proc:
            for line in proc.stdout:
                print(line, end="", flush=True)

            return proc.wait() == 0
    except OSError as exc:
        print(f"无法启动 Antigravity CLI：{exc}", flush=True)
        return False


def run_codex(inputfile, outputfile):
    project_dir = os.path.abspath("SERVERFILES")

    codex_executable = (
        shutil.which("codex.cmd")
        or shutil.which("codex.exe")
        or shutil.which("codex")
    )

    if codex_executable is None:
        return 0

    instruction = (
        f"处理'{inputfile}'里的请求（UTF-8格式文本），"
        f"用补丁方式创建文件并输出到'{outputfile}'。"
        "绝对不允许列出当前目录下的所有项目。使用UTF-8。"
    )

    cmd = [
        codex_executable,
        "-C", project_dir,
        "-c", f"projects.'{project_dir}'.trust_level=\"trusted\"",
        "--sandbox", "danger-full-access",
        "--ask-for-approval", "never",
    ]

    cmd.extend([
        "exec",
        "--skip-git-repo-check",
        instruction,
    ])

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return False

    for line in proc.stdout:
        print(line, end="")

    return proc.wait() == 0

