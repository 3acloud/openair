"""按优先级实际调用 CLI 默认模型。仅使用 Python 标准库。

运行：python ret.py
导入：result = detect_available_agent(timeout=45)
探测会消耗少量模型额度；检测的是当前配置的默认模型，不枚举所有模型。
DeepSeek Harness 使用官方 headless profile：
https://deepseek-harness.github.io/deepseek-harness/en/guide/network-proxy
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import signal
import subprocess
import uuid
from pathlib import Path
from typing import Any

available_agent = ''

def _executable(name: str) -> str | None:
    # Windows 的 npm 同时安装 .cmd 和 .ps1，优先采用可执行入口。
    names = (name + ".exe", name + ".cmd", name) if os.name == "nt" else (name,)
    return next((path for item in names if (path := shutil.which(item))), None)


def _launch_args(command: list[str]) -> list[str]:
    if os.name == "nt" and Path(command[0]).suffix.lower() in {".cmd", ".bat", ".ps1"}:
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if not powershell:
            raise OSError("Windows 脚本入口需要 PowerShell")
        quoted = " ".join("'" + arg.replace("'", "''") + "'" for arg in command)
        return [powershell, "-NoProfile", "-NonInteractive", "-Command",
                "& " + quoted + "; exit $LASTEXITCODE"]
    return command


def _run(command: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    # 允许本函数在 Claude Code 的终端中探测独立的非交互调用。
    env.pop("CLAUDECODE", None)
    options: dict[str, Any] = {}
    if os.name == "nt":
        options["creationflags"] = subprocess.CREATE_NO_WINDOW
    else:
        options["start_new_session"] = True
    process = subprocess.Popen(
        _launch_args(command), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", env=env, **options,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        # 同时停止 npm/PowerShell 包装器的子进程，避免超时后继续请求模型。
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                check=False, creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if process.poll() is None:
            process.kill()
        process.communicate()
        raise
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def _validate(provider: str, stdout: str, token: str) -> bool:
    if provider == "Claude Code":
        try:
            result = json.loads(stdout)
        except ValueError:
            return False
        if not isinstance(result, dict):
            return False
        return (result.get("type") == "result"
                and result.get("subtype") == "success"
                and not result.get("is_error")
                and str(result.get("result", "")).strip() == token)
    if provider == "Codex":
        answered = completed = failed = False
        for line in stdout.splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if not isinstance(event, dict):
                continue
            item = event.get("item") or {}
            if (event.get("type") == "item.completed" and isinstance(item, dict)
                    and item.get("type") == "agent_message"):
                answered |= str(item.get("text", "")).strip() == token
            completed |= event.get("type") == "turn.completed"
            failed |= event.get("type") in {"error", "turn.failed"}
        return answered and completed and not failed
    # Antigravity 的默认 -p 输出是回复文本，进度及错误写入 stderr。
    # headless 的纯文本输出必须包含完整的独立回复行，不能仅命中回显的提示词。
    clean = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", stdout)
    return any(line.strip() == token for line in clean.splitlines())


def detect_available_agent(
    timeout: float = 45,
    *,
    diagnostics: list[dict[str, str]] | None = None,
) -> str:
    """依次探测 Claude Code → Codex → Antigravity → Grok Build → DeepSeek Harness。

    每项最多等待 timeout 秒，实际调用成功后立即返回工具名称：
    'Claude Code'、'Codex'、'Antigravity'、'Grok Build' 或 'DeepSeek Harness'。
    全部不可用时返回空字符串 ''。
    使用当前进程的 PATH、环境变量、工作目录和 CLI 登录/模型配置。
    diagnostics 可传入空列表，接收已尝试工具的状态，不包含原始日志或密钥。
    """
    global available_agent
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout 必须是大于 0 的有限秒数")
    # 每次重新探测，避免缓存已失效的登录、网络或模型配置。
    available_agent = ''
    token = "PROBE_" + uuid.uuid4().hex
    prompt = "Do not use any tools. Reply with exactly this text and nothing else: " + token
    candidates = (
        ("Claude Code", "claude", ["-p", "--output-format", "json", "--tools", "",
                                   "--no-session-persistence"]),
        ("Codex", "codex", ["exec", "--skip-git-repo-check", "--sandbox", "read-only",
                             "--ephemeral", "--json"]),
        ("Antigravity", "agy", ["-p"]),
        ("Grok Build", "grok", ["--output-format", "plain", "--max-turns", "1",
                                "--no-subagents", "--tools", "", "-p"]),
        ("DeepSeek Harness", "dsh", ["--profile", "headless"]),
    )
    for provider, name, flags in candidates:
        executable = _executable(name)
        status = "not_installed"
        if executable:
            command = [executable, *flags, prompt]
            try:
                result = _run(command, timeout)
                valid = _validate(provider, result.stdout, token)
                if result.returncode == 0 and valid:
                    if diagnostics is not None:
                        diagnostics.append({"provider": provider, "status": "available"})
                    available_agent = provider
                    return provider
                status = (f"exit_code_{result.returncode}" if result.returncode
                          else "invalid_response")
            except subprocess.TimeoutExpired:
                status = "timeout"
            except OSError as exc:
                status = f"launch_failed:{type(exc).__name__}"
        if diagnostics is not None:
            diagnostics.append({"provider": provider, "status": status})
    return ""
