#!/usr/bin/env python3
"""
Travel Planner — 独立行程生成脚本（可选，开发者工具）

本脚本是 travel-planner skill 的可选补充工具，用于批量生成行程。
**普通用户无需使用此脚本**，直接在 WorkBuddy 对话中输入即可。

如需使用本脚本，需要自备 OpenAI API Key 并在本地环境运行。

用法:
    python3 generate_itinerary.py --destination "Tokyo" --days 3
    python3 generate_itinerary.py --destination "巴黎" --days 5 --style comfort --budget 20000

环境变量:
    OPENAI_API_KEY  — OpenAI API 密钥（必需，仅使用本脚本时）
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error


# ========== Constants ==========

DEFAULT_MODEL = "gpt-4o"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
MAX_RETRIES = 3                          # 最大重试次数
RETRY_BACKOFF_BASE = 2.0                  # 指数退避基数（秒）
REQUEST_TIMEOUT = 60                       # 单次请求超时（秒）

STYLE_MAP = {
    "budget": "经济型（控制成本，选择性价比最高的方案）",
    "comfort": "舒适型（平衡体验与成本，选择中高品质方案）",
    "luxury": "豪华型（不设预算上限，选择最佳体验）",
}

TRAVEL_PROMPT_TEMPLATE = """You are a travel planner AI.

Create a structured travel plan:

User input: {destination}, {days} days

Travel style: {style}
{budget_line}{dates_line}{party_line}{interests_line}

Return the plan in {lang} with the following sections:
1. Overview — destination summary, best time to visit, key highlights
2. Day-by-day itinerary — morning/afternoon/evening activities with locations and estimated costs
3. Hotels — 2-3 options per night with price range and booking notes
4. Food — recommended restaurants per day with cuisine type and price
5. Transport — inter-city and intra-city transport options with costs
6. Budget — itemized cost breakdown with total estimate

Use {currency} for all prices. Provide practical, actionable recommendations."""


# ========== Error Messages (Chinese) ==========

ERROR_MESSAGES = {
    "missing_api_key": "错误：未设置 OPENAI_API_KEY 环境变量。\n"
                       "请执行以下命令设置：\n"
                       "  export OPENAI_API_KEY='sk-你的key'\n"
                       "然后重新运行脚本。",
    "network_error": "错误：网络连接异常，无法连接到 OpenAI 服务器。\n"
                     "请检查：1) 网络连接是否正常；2) 是否使用了代理/VPN。\n"
                     "本次请求已尝试 {retries} 次，仍无法成功。",
    "api_auth_error": "错误：API 密钥无效或已过期（HTTP 401）。\n"
                      "请检查 OPENAI_API_KEY 是否正确。",
    "api_rate_limit": "错误：API 请求频率过高（HTTP 429）。\n"
                      "请等待 60 秒后重试。",
    "api_server_error": "错误：OpenAI 服务器暂时不可用（HTTP {code}）。\n"
                        "已自动重试 {retries} 次，建议稍后再试。",
    "api_bad_request": "错误：请求参数有误（HTTP {code}）。\n"
                       "请检查输入的参数是否符合要求。",
    "input_invalid_days": "错误：天数必须为正整数（当前输入: {days}）。\n"
                          "请使用 --days 3 这样的格式。",
    "input_empty_destination": "错误：目的地不能为空。\n"
                               "请使用 --destination '东京' 指定目的地。",
    "output_parse_error": "错误：无法解析 API 返回内容。\n"
                          "建议稍后重试，或检查 OpenAI 服务状态。",
}


# ========== Input Validation ==========

def validate_inputs(args):
    """验证输入参数，提前发现格式错误"""
    errors = []

    if not args.destination or not args.destination.strip():
        errors.append(ERROR_MESSAGES["input_empty_destination"])

    if args.days is None or args.days < 1 or args.days > 365:
        errors.append(ERROR_MESSAGES["input_invalid_days"].format(days=args.days))

    if args.budget is not None and args.budget < 0:
        errors.append("错误：预算不能为负数。请使用 --budget 5000 指定正数预算。")

    if args.dates:
        # 简单日期格式验证
        parts = args.dates.split("~")
        if len(parts) != 2:
            errors.append("错误：日期格式应为 YYYY-MM-DD~YYYY-MM-DD，如 2026-08-01~2026-08-06。")

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
            print()
        sys.exit(1)


# ========== Prompt Builder ==========

def build_prompt(args):
    """构建旅行规划 prompt"""
    budget_line = f"Budget limit: {args.budget} CNY\n" if args.budget else ""
    dates_line = f"Travel dates: {args.dates}\n" if args.dates else ""
    party_line = f"Travel party: {args.party}\n" if args.party else ""
    interests_line = f"Special interests: {args.interests}\n" if args.interests else ""

    style_desc = STYLE_MAP.get(args.style, STYLE_MAP["comfort"])

    # 判断输出语言
    has_cjk = any('\u4e00' <= ch <= '\u9fff' for ch in args.destination)
    lang = "中文" if has_cjk else "English"
    currency = "CNY (¥)" if has_cjk else "local currency with CNY reference"

    prompt = TRAVEL_PROMPT_TEMPLATE.format(
        destination=args.destination,
        days=args.days,
        style=style_desc,
        budget_line=budget_line,
        dates_line=dates_line,
        party_line=party_line,
        interests_line=interests_line,
        lang=lang,
        currency=currency,
    )
    return prompt


# ========== API Call with Retry ==========

def call_openai_with_retry(prompt, model, api_key, max_retries=MAX_RETRIES):
    """调用 OpenAI API，带指数退避重试"""
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 4096,
    }).encode("utf-8")

    last_error = None

    for attempt in range(1, max_retries + 1):
        req = urllib.request.Request(
            OPENAI_API_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            last_error = e

            if e.code == 401:
                print(ERROR_MESSAGES["api_auth_error"], file=sys.stderr)
                sys.exit(1)
            elif e.code == 429:
                print(f"警告：API 请求频率受限（第 {attempt} 次重试）...", file=sys.stderr)
                if attempt < max_retries:
                    wait = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                    print(f"  等待 {wait} 秒后自动重试...", file=sys.stderr)
                    time.sleep(wait)
                    continue
                else:
                    print(ERROR_MESSAGES["api_rate_limit"], file=sys.stderr)
                    sys.exit(1)
            elif 500 <= e.code < 600:
                print(f"警告：服务器暂时不可用 HTTP {e.code}（第 {attempt} 次重试）...", file=sys.stderr)
                if attempt < max_retries:
                    wait = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                    print(f"  等待 {wait} 秒后自动重试...", file=sys.stderr)
                    time.sleep(wait)
                    continue
                else:
                    print(ERROR_MESSAGES["api_server_error"].format(code=e.code, retries=max_retries), file=sys.stderr)
                    sys.exit(1)
            else:
                print(ERROR_MESSAGES["api_bad_request"].format(code=e.code), file=sys.stderr)
                print(f"  服务器响应: {body[:200]}", file=sys.stderr)
                sys.exit(1)

        except urllib.error.URLError as e:
            last_error = e
            print(f"警告：网络连接异常（第 {attempt} 次重试）: {e.reason}", file=sys.stderr)
            if attempt < max_retries:
                wait = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                print(f"  等待 {wait} 秒后自动重试...", file=sys.stderr)
                time.sleep(wait)
                continue
            else:
                print(ERROR_MESSAGES["network_error"].format(retries=max_retries), file=sys.stderr)
                sys.exit(1)

        except Exception as e:
            print(f"错误：发生未知异常: {type(e).__name__}: {e}", file=sys.stderr)
            sys.exit(1)

    # Fallback: 如果所有重试都失败
    print(ERROR_MESSAGES["network_error"].format(retries=max_retries), file=sys.stderr)
    sys.exit(1)


# ========== Main Generator ==========

def generate_itinerary(args):
    """生成行程计划（入口）"""
    # 1. 输入验证
    validate_inputs(args)

    # 2. 检查 API Key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print(ERROR_MESSAGES["missing_api_key"], file=sys.stderr)
        sys.exit(1)

    # 3. 构建 prompt
    prompt = build_prompt(args)

    # 4. 调用 API（带重试）
    result = call_openai_with_retry(prompt, args.model, api_key)

    # 5. 输出结果
    if args.output == "json":
        output = json.dumps({
            "destination": args.destination,
            "days": args.days,
            "style": args.style,
            "plan": result,
        }, ensure_ascii=False, indent=2)
        print(output)
    else:
        print(result)


# ========== CLI Entry ==========

def main():
    parser = argparse.ArgumentParser(
        description="Travel Planner — 独立行程生成脚本（可选，需自备 API Key）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
注意：本脚本为可选开发者工具，普通用户直接在 WorkBuddy 中输入即可。

示例:
  python3 generate_itinerary.py --destination "Tokyo" --days 3
  python3 generate_itinerary.py --destination "巴黎" --days 5 --style comfort --budget 20000
  python3 generate_itinerary.py --destination "Osaka" --days 4 --interests "food,shopping" --output json
        """,
    )
    parser.add_argument("--destination", required=True, help="目的地（必需）")
    parser.add_argument("--days", type=int, required=True, help="旅行天数（必需，1-365）")
    parser.add_argument("--style", default="comfort",
                        choices=["budget", "comfort", "luxury"],
                        help="旅行风格（默认 comfort）")
    parser.add_argument("--budget", type=int, default=None,
                        help="预算上限 CNY（可选，正整数）")
    parser.add_argument("--dates", default=None,
                        help="旅行日期 YYYY-MM-DD~YYYY-MM-DD（可选）")
    parser.add_argument("--party", default=None,
                        help="旅行人数/类型，如 '2人' / 'family'（可选）")
    parser.add_argument("--interests", default=None,
                        help="兴趣偏好，逗号分隔（可选）")
    parser.add_argument("--output", default="markdown",
                        choices=["markdown", "json"],
                        help="输出格式（默认 markdown）")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"OpenAI 模型（默认 {DEFAULT_MODEL}）")

    args = parser.parse_args()
    generate_itinerary(args)


if __name__ == "__main__":
    main()
