#!/usr/bin/env python3
"""Generate next week's baby menu and update the GitHub Pages HTML.

This script is designed for GitHub Actions. It calls the OpenAI API, asks for a
strict JSON menu, validates a few household rules, then replaces the inline menu
data in docs/baby-menu/index.html.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "docs" / "baby-menu" / "index.html"
TIMEZONE = ZoneInfo("Asia/Shanghai")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.5")


RULES = """
你要为一个 2 岁半、无过敏忌口的宝宝生成下一周 7 天食谱。

必须遵守这些家庭规则：
1. 一天三餐：早餐、午餐、晚餐。不安排加餐。
2. 早餐可以是鸡蛋或肉类，但必须藏一点具体绿叶菜，比如菠菜、小白菜、生菜、西兰花碎。
3. 午餐必须有肉/鱼/虾，并且写成“主食：...｜肉菜：...｜素菜：...”。
4. 晚餐不放肉、不放鱼虾，可以有鸡蛋或纯素，并且写成“主食：...｜蛋菜/素菜：...｜素菜：...”。
5. 每天最多 1 个鸡蛋。当天早餐用了鸡蛋，午餐和晚餐不能再出现鸡蛋、蒸蛋、蛋花、炒蛋等。
6. 每顿饭必须有主食，主食在米饭、馒头、包子、鸡蛋饼、面条、疙瘩汤、小馄饨、小饼等之间轮换。
7. 如果一餐里有带馅儿的小馄饨、小包子、包子、饺子，只需要再配一道汤或素菜，不要再配两道菜。
8. 同一餐的主食、肉菜/蛋菜、素菜里的主要食材不要重复。例如主食有南瓜，菜里就不要再用南瓜。
9. 一日三餐的主要食材尽量不要重复；两天之内主要食材也尽量不要重复。配菜可以少量重复。
10. 绿色叶菜不要写“清炒”，宝宝不爱吃。叶菜要藏进馅、饼、面、汤、羹里。
11. 不要出现蒜、蒜蓉、蒜末、秋葵、清炒。
12. 所有做法都要适合 2 岁半宝宝：少油少盐、切小、煮软、鱼要确认无刺、豌豆玉米等圆粒要煮透压一压。
13. 菜名要具体，不要写“蔬菜”这种泛词。

输出 JSON，不能输出解释文字。结构必须是：
[
  {
    "name": "周一",
    "date": "7/6",
    "focus": "鲜菜先吃",
    "meals": {
      "breakfast": "主食：...｜搭配：...",
      "lunch": "主食：...｜肉菜：...｜素菜：...",
      "dinner": "主食：...｜蛋菜/素菜：...｜素菜：..."
    },
    "notes": {
      "breakfast": "一句具体做法提示。",
      "lunch": "一句具体做法提示。",
      "dinner": "一句具体做法提示。"
    }
  }
]
"""


def next_monday(today: dt.date) -> dt.date:
    days_until_monday = (0 - today.weekday()) % 7
    if days_until_monday == 0:
        return today
    return today + dt.timedelta(days=days_until_monday)


def date_range_text(start: dt.date) -> str:
    end = start + dt.timedelta(days=6)
    return f"{start:%Y.%m.%d}-{end:%m.%d}"


def build_prompt(start: dt.date) -> str:
    dates = [
        f"{['周一','周二','周三','周四','周五','周六','周日'][i]} { (start + dt.timedelta(days=i)).month }/{ (start + dt.timedelta(days=i)).day }"
        for i in range(7)
    ]
    return (
        RULES
        + "\n下一周日期是："
        + "，".join(dates)
        + "\n请只输出 JSON 数组，日期必须对应上面这 7 天。"
    )


def call_openai(prompt: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY. Add it as a GitHub Actions secret.")

    payload = {
        "model": MODEL,
        "input": prompt,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API request failed: {exc.code} {error_body}") from exc

    if "output_text" in body:
        return body["output_text"]

    chunks: list[str] = []
    for item in body.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and "text" in content:
                chunks.append(content["text"])
    if chunks:
        return "\n".join(chunks)

    raise RuntimeError("OpenAI response did not contain output_text.")


def extract_json(text: str) -> list[dict]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON array found in model output:\n{cleaned}")
    data = json.loads(cleaned[start : end + 1])
    if not isinstance(data, list) or len(data) != 7:
        raise ValueError("Menu JSON must be a list of 7 days.")
    return data


def validate_menu(days: list[dict]) -> None:
    banned = ["蒜", "蒜蓉", "蒜末", "秋葵", "清炒", "蔬菜"]
    meat_words = ["牛肉", "鸡肉", "猪肉", "肉末", "肉丁", "鲜肉", "鱼", "虾", "三文鱼", "鳕鱼", "丸子"]
    for day in days:
        meals = day.get("meals", {})
        notes = day.get("notes", {})
        if set(meals) != {"breakfast", "lunch", "dinner"}:
            raise ValueError(f"Bad meals keys for {day.get('name')}: {meals.keys()}")
        if set(notes) != {"breakfast", "lunch", "dinner"}:
            raise ValueError(f"Bad notes keys for {day.get('name')}: {notes.keys()}")
        all_text = json.dumps(day, ensure_ascii=False)
        for word in banned:
            if word in all_text:
                raise ValueError(f"Banned word {word!r} found in {day.get('name')}: {all_text}")
        egg_count = sum(1 for meal in meals.values() if "蛋" in meal)
        if egg_count > 1:
            raise ValueError(f"Too many egg meals in {day.get('name')}: {meals}")
        if not any(word in meals["lunch"] for word in meat_words):
            raise ValueError(f"Lunch must contain meat/fish/shrimp in {day.get('name')}: {meals['lunch']}")
        if any(word in meals["dinner"] for word in meat_words):
            raise ValueError(f"Dinner contains meat/fish/shrimp in {day.get('name')}: {meals['dinner']}")


def to_js_array(days: list[dict]) -> str:
    return json.dumps(days, ensure_ascii=False, indent=6)


def update_html(start: dt.date, days: list[dict]) -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    week_start = f'{start:%Y-%m-%d}T00:00:00+08:00'
    html = re.sub(
        r'const weekStart = new Date\("[^"]+"\);',
        f'const weekStart = new Date("{week_start}");',
        html,
    )
    html = re.sub(
        r"2 岁半宝宝 · \d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}",
        f"2 岁半宝宝 · {date_range_text(start)}",
        html,
    )
    html = re.sub(
        r"const days = \[[\s\S]*?\n    \];",
        "const days = " + to_js_array(days).replace("\n", "\n    ") + ";",
        html,
        count=1,
    )
    HTML_PATH.write_text(html, encoding="utf-8")


def main() -> None:
    today = dt.datetime.now(TIMEZONE).date()
    start = next_monday(today)
    prompt = build_prompt(start)
    raw = call_openai(prompt)
    days = extract_json(raw)
    validate_menu(days)
    update_html(start, days)
    print(f"Updated baby menu for {date_range_text(start)} using {MODEL}.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
