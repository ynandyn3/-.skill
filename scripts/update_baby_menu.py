#!/usr/bin/env python3
"""Update the baby menu page from a curated weekly menu."""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "docs" / "baby-menu" / "index.html"
TIMEZONE = ZoneInfo("Asia/Shanghai")
DAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


WEEK_PLAN = {
    "days": [
        {
            "focus": "鸡蛋放早上",
            "tags": ["菠菜", "山药", "番茄", "牛肉", "西葫芦", "玉米", "冬瓜", "豆腐", "茄子", "土豆"],
            "meals": {
                "breakfast": "主食：菠菜鸡蛋羹 + 山药小馒头｜搭配：梨丁",
                "lunch": "主食：软米饭｜肉菜：番茄牛肉碎｜素菜：西葫芦玉米粒",
                "dinner": "主食：小米馒头｜素菜：冬瓜豆腐汤｜素菜：茄子土豆煲",
            },
            "notes": {
                "breakfast": "今天鸡蛋放早餐，只用一个；菠菜焯软切碎放进蛋羹，旁边配山药小馒头。",
                "lunch": "牛肉剁碎，番茄煮软后再收汁；西葫芦和玉米粒都煮到软烂。",
                "dinner": "早餐吃过蛋，晚餐不再用蛋；冬瓜豆腐切小块煮透，茄子土豆加水焖软。",
            },
        },
        {
            "focus": "馄饨配地瓜",
            "tags": ["小白菜", "虾仁", "地瓜", "南瓜", "鳕鱼", "西兰花", "白菜", "白玉菇", "紫薯", "花菜", "白萝卜", "紫菜"],
            "meals": {
                "breakfast": "主食：小白菜虾仁小馄饨｜搭配：蒸地瓜",
                "lunch": "主食：南瓜软饭｜肉菜：鳕鱼西兰花碎｜素菜：白菜白玉菇汤",
                "dinner": "主食：紫薯小馒头｜蛋菜：花菜鸡蛋碎｜素菜：白萝卜紫菜汤",
            },
            "notes": {
                "breakfast": "小馄饨馅里加小白菜碎，虾仁剁细；地瓜蒸软切小块。",
                "lunch": "鳕鱼确认无刺后切碎，西兰花焯软切小；白玉菇切短煮透。",
                "dinner": "早餐没吃蛋，晚餐用一个鸡蛋；花菜先焯软，再和蛋液一起做成碎碎菜。",
            },
        },
        {
            "focus": "面条配水果",
            "tags": ["油麦菜", "香菇", "苹果", "鸡肉", "莲藕", "莴笋", "胡萝卜", "丝瓜", "海鲜菇", "圆白菜"],
            "meals": {
                "breakfast": "主食：油麦菜香菇碎面｜搭配：苹果片",
                "lunch": "主食：软米饭｜肉菜：鸡肉莲藕丸｜素菜：莴笋胡萝卜丁",
                "dinner": "主食：玉米疙瘩汤｜素菜：丝瓜海鲜菇汤｜蛋菜：圆白菜鸡蛋碎",
            },
            "notes": {
                "breakfast": "油麦菜最后剪碎烫熟，香菇切薄片煮透；苹果切薄片或小丁。",
                "lunch": "鸡肉剁泥，莲藕擦碎后拌进肉泥做小丸子，煮熟再给宝宝吃。",
                "dinner": "早餐没吃蛋，晚餐用一个鸡蛋；圆白菜切碎后和蛋液一起炒成软碎。",
            },
        },
        {
            "focus": "包子配牛奶",
            "tags": ["菜心", "牛肉", "猪肉", "豆角", "茄子", "土豆", "山药", "油菜", "冬瓜", "海带"],
            "meals": {
                "breakfast": "主食：菜心牛肉小包子｜搭配：牛奶",
                "lunch": "主食：软米饭｜肉菜：猪肉豆角丁｜素菜：茄子土豆煲",
                "dinner": "主食：山药小馒头｜蛋菜：油菜鸡蛋碎｜素菜：冬瓜海带汤",
            },
            "notes": {
                "breakfast": "包子馅里加菜心碎，复热后掰开确认不烫，配牛奶可以。",
                "lunch": "豆角必须彻底煮熟再切碎；茄子和土豆加水焖到软烂。",
                "dinner": "早餐没吃蛋，晚餐用一个鸡蛋；油菜切碎后做成软软的鸡蛋碎。",
            },
        },
        {
            "focus": "鸡蛋饼配粥",
            "tags": ["生菜", "三文鱼", "西葫芦", "白萝卜", "杏鲍菇", "白菜", "豆腐", "南瓜", "豌豆"],
            "meals": {
                "breakfast": "主食：生菜鸡蛋饼｜搭配：小米粥",
                "lunch": "主食：软米饭｜肉菜：三文鱼西葫芦丁｜素菜：白萝卜杏鲍菇汤",
                "dinner": "主食：小米软饭｜素菜：白菜豆腐汤｜素菜：南瓜豌豆泥",
            },
            "notes": {
                "breakfast": "今天鸡蛋放早餐，只用一个；生菜切细碎摊进蛋饼，旁边配小米粥。",
                "lunch": "三文鱼蒸熟或煎熟后拆小块，西葫芦煮软；杏鲍菇切小丁煮透。",
                "dinner": "早餐吃过蛋，晚餐不再用蛋；南瓜和豌豆都蒸软后压一压。",
            },
        },
        {
            "focus": "馄饨配紫薯",
            "tags": ["西兰花", "虾仁", "紫薯", "鳕鱼", "芦笋", "番茄", "花菜", "玉米", "圆白菜", "胡萝卜", "莴笋", "白玉菇"],
            "meals": {
                "breakfast": "主食：西兰花虾仁小馄饨｜搭配：蒸紫薯",
                "lunch": "主食：软米饭｜肉菜：鳕鱼芦笋丁｜素菜：番茄花菜碎",
                "dinner": "主食：玉米疙瘩汤｜蛋菜：圆白菜胡萝卜鸡蛋碎｜素菜：莴笋白玉菇汤",
            },
            "notes": {
                "breakfast": "西兰花焯软后切碎拌进馅里，虾仁剁细；紫薯蒸软切小块。",
                "lunch": "鳕鱼确认无刺，芦笋去老根切小丁；番茄和花菜都煮软再剪小。",
                "dinner": "早餐没吃蛋，晚餐用一个鸡蛋；圆白菜和胡萝卜都切细碎。",
            },
        },
        {
            "focus": "周日清淡",
            "tags": ["上海青", "猪肉", "鸡肉", "山药", "丝瓜", "海鲜菇", "红薯", "油麦菜", "茄子", "土豆"],
            "meals": {
                "breakfast": "主食：上海青猪肉小饼｜搭配：牛奶",
                "lunch": "主食：软米饭｜肉菜：鸡肉山药丸｜素菜：丝瓜海鲜菇汤",
                "dinner": "主食：红薯小馒头｜蛋菜：油麦菜鸡蛋碎｜素菜：茄子土豆煲",
            },
            "notes": {
                "breakfast": "上海青焯软切碎，猪肉末先做熟后拌进小饼，配牛奶不干吃。",
                "lunch": "鸡肉剁泥，山药蒸软压泥后做小丸子，煮熟再给宝宝吃。",
                "dinner": "早餐没吃蛋，晚餐用一个鸡蛋；油麦菜切碎后拌进鸡蛋里。",
            },
        },
    ],
    "shopping": [
        {
            "group": "肉蛋奶",
            "items": [
                ["鸡蛋", "耐放"],
                ["牛肉末", "分装"],
                ["鸡肉", "分装"],
                ["猪肉末", "分装"],
                ["虾仁", "冷冻"],
                ["鳕鱼", "冷冻"],
                ["三文鱼小块", "冷冻"],
                ["牛奶", "耐放"],
                ["豆腐", "前半周"],
            ],
        },
        {
            "group": "青菜根茎",
            "items": [
                ["菠菜", "前半周"],
                ["小白菜", "前半周"],
                ["油麦菜", "前半周"],
                ["菜心", "前半周"],
                ["生菜", "前半周"],
                ["西兰花", "前半周"],
                ["上海青", "前半周"],
                ["油菜", "前半周"],
                ["番茄", "前半周"],
                ["西葫芦", "前半周"],
                ["胡萝卜", "耐放"],
                ["冬瓜", "耐放"],
                ["茄子", "前半周"],
                ["土豆", "耐放"],
                ["白菜", "耐放"],
                ["白萝卜", "耐放"],
                ["圆白菜", "耐放"],
                ["花菜", "耐放"],
                ["南瓜", "耐放"],
                ["山药", "耐放"],
                ["丝瓜", "前半周"],
                ["莴笋", "前半周"],
                ["莲藕", "耐放"],
                ["豆角", "前半周"],
                ["豌豆粒", "冷冻"],
                ["芦笋", "前半周"],
                ["香菇", "前半周"],
                ["白玉菇", "前半周"],
                ["海鲜菇", "前半周"],
                ["杏鲍菇", "前半周"],
                ["海带", "耐放"],
                ["紫菜", "耐放"],
            ],
        },
        {
            "group": "主食水果",
            "items": [
                ["大米", "耐放"],
                ["小米", "耐放"],
                ["面条", "耐放"],
                ["面粉", "耐放"],
                ["小馄饨皮", "冷冻"],
                ["小包子或包子皮", "可冷冻"],
                ["山药小馒头", "可冷冻"],
                ["紫薯小馒头", "可冷冻"],
                ["红薯小馒头", "可冷冻"],
                ["小米馒头", "可冷冻"],
                ["地瓜或红薯", "耐放"],
                ["紫薯", "耐放"],
                ["玉米粒", "冷冻"],
                ["梨", "耐放"],
                ["苹果", "耐放"],
            ],
        },
    ],
}


def next_monday(today: dt.date) -> dt.date:
    days_until_monday = (0 - today.weekday()) % 7
    return today if days_until_monday == 0 else today + dt.timedelta(days=days_until_monday)


def date_range_text(start: dt.date) -> str:
    end = start + dt.timedelta(days=6)
    return f"{start:%Y.%m.%d}-{end:%m.%d}"


def with_dates(start: dt.date, plan_days: list[dict]) -> list[dict]:
    dated = []
    for index, day in enumerate(plan_days):
        current = start + dt.timedelta(days=index)
        dated.append(
            {
                "name": DAY_NAMES[index],
                "date": f"{current.month}/{current.day}",
                "focus": day["focus"],
                "meals": day["meals"],
                "notes": day["notes"],
            }
        )
    return dated


def validate_spacing(plan_days: list[dict]) -> None:
    for start in range(len(plan_days) - 2):
        seen: dict[str, str] = {}
        for offset in range(3):
            day = plan_days[start + offset]
            for tag in day.get("tags", []):
                if tag in seen:
                    window = f"{DAY_NAMES[start]}-{DAY_NAMES[start + 2]}"
                    raise ValueError(f"{tag} repeats within {window}: {seen[tag]} and {DAY_NAMES[start + offset]}")
                seen[tag] = DAY_NAMES[start + offset]


def validate_menu(days: list[dict]) -> None:
    banned = [
        "蒜",
        "蒜蓉",
        "蒜末",
        "秋葵",
        "清炒",
        "蔬菜",
        "苦菊",
        "苋菜",
        "快菜",
        "尖椒",
        "心里美",
        "佛手瓜",
        "荷兰豆",
        "甜豆",
        "毛豆仁",
        "毛豆",
        "鲈鱼",
        "娃娃菜",
        "芋头",
        "鳕鱼白萝卜丁",
        "鸡肉山药丁",
    ]
    meat_words = ["牛肉", "鸡肉", "猪肉", "肉末", "肉丁", "鲜肉", "三文鱼", "鳕鱼", "虾仁"]
    breakfast_greens = ["菠菜", "小白菜", "油麦菜", "油菜", "菜心", "上海青", "西兰花", "生菜", "圆白菜"]

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

        breakfast = meals["breakfast"]
        dinner = meals["dinner"]
        if not any(green in breakfast for green in breakfast_greens):
            raise ValueError(f"Breakfast needs a specific green in {day.get('name')}: {breakfast}")
        if "鸡蛋羹" in breakfast and not any(staple in breakfast for staple in ["小馒头", "小包子", "馒头块"]):
            raise ValueError(f"Egg custard breakfast needs a bun/mantou in {day.get('name')}: {breakfast}")
        if "小馄饨" in breakfast and "牛奶" in breakfast:
            raise ValueError(f"Wonton breakfast should not pair with milk in {day.get('name')}: {breakfast}")
        if "面" in breakfast and "牛奶" in breakfast:
            raise ValueError(f"Noodle breakfast should not pair with milk in {day.get('name')}: {breakfast}")

        breakfast_has_egg = "蛋" in breakfast
        if breakfast_has_egg and "蛋" in dinner:
            raise ValueError(f"Dinner has egg after egg breakfast in {day.get('name')}: {dinner}")

        egg_count = sum(1 for meal in meals.values() if "蛋" in meal)
        if egg_count > 1:
            raise ValueError(f"Too many egg meals in {day.get('name')}: {meals}")
        if not any(word in meals["lunch"] for word in meat_words):
            raise ValueError(f"Lunch must contain meat/fish/shrimp in {day.get('name')}: {meals['lunch']}")
        if any(word in dinner for word in meat_words):
            raise ValueError(f"Dinner contains meat/fish/shrimp in {day.get('name')}: {dinner}")


def to_js(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=6)


def replace_js_const(html: str, name: str, value: object) -> str:
    pattern = rf"const {name} = \[[\s\S]*?\n    \];"
    replacement = f"const {name} = " + to_js(value).replace("\n", "\n    ") + ";"
    updated, count = re.subn(pattern, replacement, html, count=1)
    if count != 1:
        raise RuntimeError(f"Could not replace const {name}.")
    return updated


def update_html(start: dt.date, days: list[dict], shopping: list[dict]) -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    week_start = f"{start:%Y-%m-%d}T00:00:00+08:00"
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
    html = html.replace(
        "油麦菜、上海青、油菜、菜心、鲜鱼虾放前半周吃；带馅的小包子、小馄饨本身算一道菜，再配一道汤或素菜就够。",
        "叶菜、鲜鱼虾优先前半周吃；带馅的小包子、小馄饨本身算一道菜，再配一道汤或素菜就够。",
    )
    html = html.replace("牛肉碎、鸡腿丁、猪肉末", "牛肉末、鸡肉、猪肉末")
    html = html.replace(
        "<li><strong>鳕鱼或鲈鱼</strong> -> 虾仁 / 三文鱼 / 豆腐羹。</li>",
        "<li><strong>鳕鱼</strong> -> 三文鱼 / 虾仁 / 豆腐羹。</li>",
    )
    html = replace_js_const(html, "days", days)
    html = replace_js_const(html, "shopping", shopping)
    HTML_PATH.write_text(html, encoding="utf-8")


def main() -> None:
    today = dt.datetime.now(TIMEZONE).date()
    start = next_monday(today)
    validate_spacing(WEEK_PLAN["days"])
    days = with_dates(start, WEEK_PLAN["days"])
    validate_menu(days)
    update_html(start, days, WEEK_PLAN["shopping"])
    print(f"Updated baby menu for {date_range_text(start)} from curated weekly recipes.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
