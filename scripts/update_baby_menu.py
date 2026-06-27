#!/usr/bin/env python3
"""Rotate the baby menu without using any API key.

GitHub Actions runs this script every Sunday morning. The script picks one of
the prepared weekly menus, rewrites dates for the coming Monday-Sunday, and
updates the GitHub Pages HTML.
"""

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
ANCHOR_MONDAY = dt.date(2026, 6, 29)
DAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


WEEK_PLANS = [
    {
        "days": [
            {
                "focus": "鲜菜先吃",
                "meals": {
                    "breakfast": "主食：菠菜牛肉小包子｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：番茄鸡肉丁｜素菜：西葫芦胡萝卜丁",
                    "dinner": "主食：小米馒头｜素菜：南瓜豆腐羹｜素菜：白菜白玉菇汤",
                },
                "notes": {
                    "breakfast": "包子馅里加少量菠菜碎，提前蒸好或冷冻，早上复热即可。",
                    "lunch": "鸡肉和番茄切小丁，先把鸡肉做熟，再和番茄一起收软。",
                    "dinner": "南瓜和豆腐煮成软羹；白菜白玉菇汤煮软后剪小。",
                },
            },
            {
                "focus": "鱼虾优先",
                "meals": {
                    "breakfast": "主食：小白菜鲜肉小馄饨｜搭配：苹果片",
                    "lunch": "主食：软米饭｜肉菜：鳕鱼芦笋丁｜素菜：花菜土豆泥",
                    "dinner": "主食：玉米软面｜蛋菜：西兰花鸡蛋碎｜素菜：冬瓜紫菜汤",
                },
                "notes": {
                    "breakfast": "小馄饨本身算一道菜，馅里放小白菜碎；苹果切薄片或小丁。",
                    "lunch": "鳕鱼确认无刺后切丁，芦笋去老根切小；花菜和土豆蒸软压泥。",
                    "dinner": "今天鸡蛋放晚餐，只用一个；冬瓜紫菜汤煮软。",
                },
            },
            {
                "focus": "软烂好嚼",
                "meals": {
                    "breakfast": "主食：番茄生菜牛肉碎面｜搭配：蒸红薯",
                    "lunch": "主食：软米饭｜肉菜：虾仁南瓜丁｜素菜：菠菜豆腐汤",
                    "dinner": "主食：山药小馒头｜素菜：胡萝卜豌豆丁｜素菜：茄子香菇煲",
                },
                "notes": {
                    "breakfast": "牛肉碎提前分装，番茄煮软后下面；生菜最后剪碎烫熟。",
                    "lunch": "虾仁切小丁，南瓜蒸到软；菠菜豆腐汤先焯菠菜再煮。",
                    "dinner": "茄子香菇加水焖软；豌豆粒要煮透压一压。",
                },
            },
            {
                "focus": "换主食",
                "meals": {
                    "breakfast": "主食：西兰花鸡蛋饼｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：鸡肉土豆丁｜素菜：丝瓜玉米笋汤",
                    "dinner": "主食：小白菜素包子｜素菜：冬瓜紫菜汤",
                },
                "notes": {
                    "breakfast": "今天鸡蛋放早餐，只用一个；西兰花焯熟切碎再摊饼。",
                    "lunch": "鸡肉去皮切丁，土豆煮软；丝瓜玉米笋汤清淡煮软。",
                    "dinner": "素包子本身算一道菜，所以只配冬瓜紫菜汤。",
                },
            },
            {
                "focus": "耐放菜",
                "meals": {
                    "breakfast": "主食：菠菜猪肉小馄饨｜搭配：苹果片",
                    "lunch": "主食：软米饭｜肉菜：三文鱼胡萝卜丁｜素菜：芦笋白玉菇",
                    "dinner": "主食：番茄疙瘩汤｜素菜：南瓜豆腐羹｜素菜：生菜碎汤",
                },
                "notes": {
                    "breakfast": "小馄饨馅里加菠菜碎，煮到皮软馅熟；苹果切小块。",
                    "lunch": "三文鱼切小丁煎或蒸熟后拌胡萝卜；芦笋白玉菇切小段煮软。",
                    "dinner": "疙瘩做小一点，番茄煮软；生菜剪碎后最后下锅。",
                },
            },
            {
                "focus": "周末简单",
                "meals": {
                    "breakfast": "主食：小白菜鸡肉小包子｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：牛肉西葫芦丁｜素菜：花菜紫菜汤",
                    "dinner": "主食：山药小馒头｜蛋菜：白菜鸡蛋碎｜素菜：茄子土豆煲",
                },
                "notes": {
                    "breakfast": "包子馅里加小白菜碎；冷冻包子复热后掰开确认不烫。",
                    "lunch": "牛肉和西葫芦都切小丁，牛肉先做熟再混合。",
                    "dinner": "今天鸡蛋放晚餐，只用一个；茄子土豆加水焖软。",
                },
            },
            {
                "focus": "清库存",
                "meals": {
                    "breakfast": "主食：生菜鳕鱼小饼｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：虾仁番茄丁｜素菜：冬瓜豆腐汤",
                    "dinner": "主食：南瓜软面｜素菜：胡萝卜豌豆丁｜素菜：丝瓜玉米笋汤",
                },
                "notes": {
                    "breakfast": "鳕鱼确认无刺，和生菜碎拌成小饼，烙到全熟。",
                    "lunch": "虾仁切丁，番茄煮软；冬瓜豆腐汤切小块、煮透。",
                    "dinner": "软面煮久一点；豌豆粒煮透后压碎，丝瓜汤清淡一点。",
                },
            },
        ],
        "shopping": [
            {"group": "肉蛋奶", "items": [["鸡蛋", "耐放"], ["牛肉碎或牛肉末", "分装"], ["鸡肉", "分装"], ["猪肉末", "分装"], ["鳕鱼", "前半周"], ["三文鱼小块", "冷冻"], ["虾仁", "前半周"], ["牛奶", "耐放"], ["豆腐", "前半周"]]},
            {"group": "青菜根茎", "items": [["西兰花", "前半周"], ["菠菜", "前半周"], ["小白菜", "前半周"], ["生菜", "前半周"], ["白菜", "耐放"], ["茄子", "前半周"], ["芦笋", "前半周"], ["玉米笋", "前半周"], ["西葫芦", "前半周"], ["花菜", "耐放"], ["胡萝卜", "耐放"], ["南瓜", "耐放"], ["土豆", "耐放"], ["山药", "耐放"], ["冬瓜", "耐放"], ["丝瓜", "前半周"], ["豌豆粒", "冷冻"], ["紫菜", "耐放"], ["香菇或白玉菇", "前半周"], ["番茄", "前半周"]]},
            {"group": "主食水果", "items": [["大米", "耐放"], ["小米馒头", "可冷冻"], ["小馄饨皮", "冷冻"], ["小包子", "可冷冻"], ["面条", "耐放"], ["面粉", "耐放"], ["红薯", "耐放"], ["苹果", "耐放"]]},
        ],
    },
    {
        "days": [
            {
                "focus": "先用鲜叶",
                "meals": {
                    "breakfast": "主食：小白菜鸡蛋羹馒头块｜搭配：梨丁",
                    "lunch": "主食：软米饭｜肉菜：牛肉冬瓜丁｜素菜：番茄花菜碎",
                    "dinner": "主食：紫薯小馒头｜素菜：豆腐白菜煲｜素菜：胡萝卜玉米笋汤",
                },
                "notes": {
                    "breakfast": "今天鸡蛋放早餐，只用一个；小白菜焯软切碎放进蛋羹。",
                    "lunch": "牛肉切小丁或剁碎，冬瓜炖软；番茄花菜都切小。",
                    "dinner": "豆腐白菜小火煮软，玉米笋切薄片。",
                },
            },
            {
                "focus": "补铁安排",
                "meals": {
                    "breakfast": "主食：菠菜猪肉小饼｜搭配：牛奶",
                    "lunch": "主食：南瓜软饭｜肉菜：鸡肉豆角丁｜素菜：西兰花土豆泥",
                    "dinner": "主食：番茄面片汤｜素菜：冬瓜豆腐丁｜素菜：生菜碎汤",
                },
                "notes": {
                    "breakfast": "菠菜焯软切碎，猪肉末做熟后拌进小饼。",
                    "lunch": "豆角一定煮透切碎；西兰花土豆蒸软压泥。",
                    "dinner": "面片做小，番茄煮软；生菜最后剪碎烫熟。",
                },
            },
            {
                "focus": "鱼肉换口味",
                "meals": {
                    "breakfast": "主食：生菜鸡肉小馄饨｜搭配：香蕉块",
                    "lunch": "主食：软米饭｜肉菜：鲈鱼胡萝卜丁｜素菜：丝瓜白玉菇汤",
                    "dinner": "主食：玉米小饼｜蛋菜：西葫芦鸡蛋碎｜素菜：白菜豆腐汤",
                },
                "notes": {
                    "breakfast": "小馄饨馅里加生菜碎；香蕉切小块。",
                    "lunch": "鲈鱼确认无刺后切丁，胡萝卜煮软。",
                    "dinner": "今天鸡蛋放晚餐，只用一个；西葫芦切细丝更好熟。",
                },
            },
            {
                "focus": "软饭日",
                "meals": {
                    "breakfast": "主食：西兰花牛肉碎面｜搭配：苹果片",
                    "lunch": "主食：软米饭｜肉菜：虾仁山药丁｜素菜：菠菜南瓜汤",
                    "dinner": "主食：白菜素饺子｜素菜：番茄豆腐汤",
                },
                "notes": {
                    "breakfast": "牛肉碎提前分装，西兰花焯熟切碎后下进面里。",
                    "lunch": "虾仁切丁，山药蒸软；菠菜南瓜汤煮到入口软。",
                    "dinner": "素饺子本身算一道菜，所以只配番茄豆腐汤。",
                },
            },
            {
                "focus": "耐放搭配",
                "meals": {
                    "breakfast": "主食：小白菜鲜肉小包子｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：猪肉茄子丁｜素菜：花菜胡萝卜碎",
                    "dinner": "主食：山药疙瘩汤｜素菜：南瓜豆腐丁｜素菜：冬瓜紫菜汤",
                },
                "notes": {
                    "breakfast": "包子馅里加小白菜碎，早上复热后放温再吃。",
                    "lunch": "猪肉和茄子都切小，茄子焖软；花菜胡萝卜蒸软切碎。",
                    "dinner": "疙瘩做小，山药煮到软糯；冬瓜切薄片。",
                },
            },
            {
                "focus": "周末省心",
                "meals": {
                    "breakfast": "主食：菠菜鸡蛋饼｜搭配：梨丁",
                    "lunch": "主食：软米饭｜肉菜：鸡肉西葫芦丁｜素菜：土豆豌豆泥",
                    "dinner": "主食：红薯小馒头｜素菜：白菜白玉菇汤｜素菜：胡萝卜豆腐丁",
                },
                "notes": {
                    "breakfast": "今天鸡蛋放早餐，只用一个；菠菜焯软切碎再摊饼。",
                    "lunch": "鸡肉和西葫芦切小丁，土豆豌豆蒸软后压一压。",
                    "dinner": "白玉菇切短，汤煮软；豆腐丁不要太大。",
                },
            },
            {
                "focus": "清淡收尾",
                "meals": {
                    "breakfast": "主食：生菜牛肉小包子｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：鳕鱼番茄丁｜素菜：冬瓜玉米笋汤",
                    "dinner": "主食：小米软面｜素菜：西兰花土豆泥｜素菜：丝瓜豆腐汤",
                },
                "notes": {
                    "breakfast": "包子馅里加生菜碎，复热后确认中间热透。",
                    "lunch": "鳕鱼确认无刺，番茄煮软后拌鱼丁。",
                    "dinner": "西兰花土豆蒸软压泥，丝瓜豆腐汤煮软。",
                },
            },
        ],
        "shopping": [
            {"group": "肉蛋奶", "items": [["鸡蛋", "耐放"], ["牛肉碎", "分装"], ["猪肉末", "分装"], ["鸡肉", "分装"], ["鲈鱼或鳕鱼", "前半周"], ["虾仁", "前半周"], ["牛奶", "耐放"], ["豆腐", "前半周"]]},
            {"group": "青菜根茎", "items": [["小白菜", "前半周"], ["菠菜", "前半周"], ["生菜", "前半周"], ["白菜", "耐放"], ["西兰花", "前半周"], ["番茄", "前半周"], ["冬瓜", "耐放"], ["花菜", "耐放"], ["胡萝卜", "耐放"], ["玉米笋", "前半周"], ["豆角", "前半周"], ["土豆", "耐放"], ["南瓜", "耐放"], ["西葫芦", "前半周"], ["丝瓜", "前半周"], ["山药", "耐放"], ["紫薯或红薯", "耐放"], ["豌豆粒", "冷冻"], ["白玉菇", "前半周"], ["紫菜", "耐放"]]},
            {"group": "主食水果", "items": [["大米", "耐放"], ["馒头", "可冷冻"], ["小馄饨皮", "冷冻"], ["饺子皮", "冷冻"], ["面条", "耐放"], ["面粉", "耐放"], ["苹果", "耐放"], ["梨", "耐放"], ["香蕉", "前半周"]]},
        ],
    },
    {
        "days": [
            {
                "focus": "叶菜藏起来",
                "meals": {
                    "breakfast": "主食：菠菜鳕鱼小饼｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：猪肉冬瓜丁｜素菜：番茄豆腐羹",
                    "dinner": "主食：南瓜小馒头｜蛋菜：小白菜鸡蛋碎｜素菜：西葫芦白玉菇",
                },
                "notes": {
                    "breakfast": "鳕鱼确认无刺，菠菜焯软切碎，和鱼肉拌成小饼。",
                    "lunch": "猪肉丁做熟后加冬瓜煮软；番茄豆腐羹切小块。",
                    "dinner": "今天鸡蛋放晚餐，只用一个；小白菜切碎拌进鸡蛋里。",
                },
            },
            {
                "focus": "虾仁换味",
                "meals": {
                    "breakfast": "主食：生菜牛肉小馄饨｜搭配：梨丁",
                    "lunch": "主食：软米饭｜肉菜：虾仁芦笋丁｜素菜：花菜南瓜泥",
                    "dinner": "主食：山药软面｜素菜：白菜豆腐汤｜素菜：胡萝卜玉米笋丁",
                },
                "notes": {
                    "breakfast": "馄饨馅里加生菜碎，煮软后放温再吃。",
                    "lunch": "虾仁和芦笋都切小；花菜南瓜蒸软压泥。",
                    "dinner": "山药切小煮软后下面；玉米笋切薄片。",
                },
            },
            {
                "focus": "牛肉补铁",
                "meals": {
                    "breakfast": "主食：西兰花鸡蛋羹小馒头｜搭配：苹果片",
                    "lunch": "主食：软米饭｜肉菜：牛肉胡萝卜丁｜素菜：丝瓜豆腐汤",
                    "dinner": "主食：番茄疙瘩汤｜素菜：土豆豌豆泥｜素菜：冬瓜紫菜汤",
                },
                "notes": {
                    "breakfast": "今天鸡蛋放早餐，只用一个；西兰花切碎放进蛋羹。",
                    "lunch": "牛肉和胡萝卜切小丁，胡萝卜要煮软。",
                    "dinner": "疙瘩做小一点；豌豆煮透后和土豆一起压泥。",
                },
            },
            {
                "focus": "鱼肉安排",
                "meals": {
                    "breakfast": "主食：小白菜猪肉小包子｜搭配：牛奶",
                    "lunch": "主食：南瓜软饭｜肉菜：三文鱼西葫芦丁｜素菜：白菜白玉菇汤",
                    "dinner": "主食：紫薯小馒头｜素菜：番茄花菜碎｜素菜：豆腐生菜汤",
                },
                "notes": {
                    "breakfast": "包子馅里加小白菜碎，复热后掰开看一下温度。",
                    "lunch": "三文鱼煎或蒸熟后切小，西葫芦煮软。",
                    "dinner": "番茄花菜切小煮软；生菜最后下进豆腐汤。",
                },
            },
            {
                "focus": "软烂耐嚼",
                "meals": {
                    "breakfast": "主食：菠菜鸡肉碎面｜搭配：香蕉块",
                    "lunch": "主食：软米饭｜肉菜：鸡肉土豆丁｜素菜：芦笋胡萝卜丁",
                    "dinner": "主食：白菜素包子｜素菜：南瓜豆腐羹",
                },
                "notes": {
                    "breakfast": "鸡肉碎提前做熟，菠菜焯软切碎后下进面里。",
                    "lunch": "鸡肉土豆都切小，土豆煮软；芦笋去老根。",
                    "dinner": "素包子本身算一道菜，只配南瓜豆腐羹。",
                },
            },
            {
                "focus": "周末快手",
                "meals": {
                    "breakfast": "主食：小白菜鸡蛋饼｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：鳕鱼番茄丁｜素菜：冬瓜玉米笋汤",
                    "dinner": "主食：小米馒头｜素菜：茄子土豆煲｜素菜：西兰花豆腐汤",
                },
                "notes": {
                    "breakfast": "今天鸡蛋放早餐，只用一个；小白菜切碎摊进饼里。",
                    "lunch": "鳕鱼确认无刺，番茄煮软；冬瓜玉米笋切小。",
                    "dinner": "茄子土豆加水焖软；西兰花切小再煮汤。",
                },
            },
            {
                "focus": "清库存",
                "meals": {
                    "breakfast": "主食：生菜牛肉小饼｜搭配：苹果片",
                    "lunch": "主食：软米饭｜肉菜：虾仁山药丁｜素菜：胡萝卜花菜碎",
                    "dinner": "主食：丝瓜面片汤｜素菜：白菜豆腐丁｜素菜：南瓜豌豆泥",
                },
                "notes": {
                    "breakfast": "牛肉末和生菜碎拌成小饼，烙到全熟。",
                    "lunch": "虾仁切丁，山药蒸软；胡萝卜花菜煮软切碎。",
                    "dinner": "面片煮软；豌豆煮透后和南瓜一起压泥。",
                },
            },
        ],
        "shopping": [
            {"group": "肉蛋奶", "items": [["鸡蛋", "耐放"], ["鳕鱼", "前半周"], ["猪肉末", "分装"], ["牛肉末", "分装"], ["鸡肉", "分装"], ["三文鱼小块", "冷冻"], ["虾仁", "前半周"], ["牛奶", "耐放"], ["豆腐", "前半周"]]},
            {"group": "青菜根茎", "items": [["菠菜", "前半周"], ["生菜", "前半周"], ["小白菜", "前半周"], ["白菜", "耐放"], ["西兰花", "前半周"], ["西葫芦", "前半周"], ["冬瓜", "耐放"], ["番茄", "前半周"], ["胡萝卜", "耐放"], ["花菜", "耐放"], ["南瓜", "耐放"], ["土豆", "耐放"], ["山药", "耐放"], ["丝瓜", "前半周"], ["芦笋", "前半周"], ["玉米笋", "前半周"], ["茄子", "前半周"], ["白玉菇", "前半周"], ["豌豆粒", "冷冻"], ["紫菜", "耐放"]]},
            {"group": "主食水果", "items": [["大米", "耐放"], ["小馒头", "可冷冻"], ["小馄饨皮", "冷冻"], ["小包子", "可冷冻"], ["面条", "耐放"], ["面粉", "耐放"], ["紫薯", "耐放"], ["苹果", "耐放"], ["梨", "耐放"], ["香蕉", "前半周"]]},
        ],
    },
    {
        "days": [
            {
                "focus": "清爽开周",
                "meals": {
                    "breakfast": "主食：西兰花鸡肉小包子｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：牛肉番茄丁｜素菜：冬瓜豆腐汤",
                    "dinner": "主食：山药小馒头｜素菜：白菜香菇煲｜素菜：胡萝卜豌豆丁",
                },
                "notes": {
                    "breakfast": "包子馅里加西兰花碎，复热后放温再吃。",
                    "lunch": "牛肉和番茄切小，番茄煮软后裹住牛肉丁。",
                    "dinner": "香菇切小片，白菜煮软；豌豆煮透压一压。",
                },
            },
            {
                "focus": "叶菜藏馅",
                "meals": {
                    "breakfast": "主食：菠菜猪肉小馄饨｜搭配：梨丁",
                    "lunch": "主食：软米饭｜肉菜：鸡肉南瓜丁｜素菜：西葫芦白玉菇",
                    "dinner": "主食：番茄软面｜蛋菜：小白菜鸡蛋碎｜素菜：丝瓜豆腐汤",
                },
                "notes": {
                    "breakfast": "馄饨馅里加菠菜碎，煮到皮软馅熟。",
                    "lunch": "鸡肉切丁，南瓜蒸软；西葫芦白玉菇煮软。",
                    "dinner": "今天鸡蛋放晚餐，只用一个；小白菜切碎拌进鸡蛋。",
                },
            },
            {
                "focus": "鱼虾轮换",
                "meals": {
                    "breakfast": "主食：生菜牛肉碎面｜搭配：苹果片",
                    "lunch": "主食：软米饭｜肉菜：虾仁土豆丁｜素菜：花菜胡萝卜碎",
                    "dinner": "主食：紫薯小馒头｜素菜：南瓜豆腐羹｜素菜：冬瓜紫菜汤",
                },
                "notes": {
                    "breakfast": "生菜剪碎最后下锅，牛肉碎提前做熟。",
                    "lunch": "虾仁切丁，土豆煮软；花菜胡萝卜切碎煮软。",
                    "dinner": "南瓜豆腐煮成软羹，冬瓜切薄片。",
                },
            },
            {
                "focus": "蛋放早餐",
                "meals": {
                    "breakfast": "主食：菠菜鸡蛋饼｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：鳕鱼芦笋丁｜素菜：白菜豆腐汤",
                    "dinner": "主食：小白菜素包子｜素菜：番茄花菜碎",
                },
                "notes": {
                    "breakfast": "今天鸡蛋放早餐，只用一个；菠菜焯软切碎再摊饼。",
                    "lunch": "鳕鱼确认无刺，芦笋去老根切小。",
                    "dinner": "素包子本身算一道菜，只配番茄花菜碎。",
                },
            },
            {
                "focus": "根茎耐放",
                "meals": {
                    "breakfast": "主食：小白菜鲜肉小饼｜搭配：香蕉块",
                    "lunch": "主食：软米饭｜肉菜：猪肉胡萝卜丁｜素菜：茄子土豆煲",
                    "dinner": "主食：玉米疙瘩汤｜素菜：西兰花豆腐丁｜素菜：生菜碎汤",
                },
                "notes": {
                    "breakfast": "小白菜切碎拌进鲜肉馅，小饼烙到全熟。",
                    "lunch": "猪肉和胡萝卜都切小丁；茄子土豆加水焖软。",
                    "dinner": "疙瘩做小一点；生菜碎最后下锅烫熟。",
                },
            },
            {
                "focus": "周末省心",
                "meals": {
                    "breakfast": "主食：西兰花鳕鱼小饼｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：鸡肉山药丁｜素菜：丝瓜玉米笋汤",
                    "dinner": "主食：南瓜软面｜素菜：白菜白玉菇汤｜素菜：胡萝卜豌豆泥",
                },
                "notes": {
                    "breakfast": "鳕鱼确认无刺，西兰花切碎后拌成小饼。",
                    "lunch": "鸡肉和山药切丁，山药蒸软；丝瓜玉米笋切小。",
                    "dinner": "软面煮久一点；胡萝卜豌豆煮透压泥。",
                },
            },
            {
                "focus": "收尾清淡",
                "meals": {
                    "breakfast": "主食：生菜牛肉小馄饨｜搭配：梨丁",
                    "lunch": "主食：软米饭｜肉菜：三文鱼西葫芦丁｜素菜：冬瓜豆腐汤",
                    "dinner": "主食：红薯小馒头｜蛋菜：番茄鸡蛋碎｜素菜：花菜紫菜汤",
                },
                "notes": {
                    "breakfast": "馄饨馅里加生菜碎，煮软后放温。",
                    "lunch": "三文鱼煎或蒸熟后切小，西葫芦煮软。",
                    "dinner": "今天鸡蛋放晚餐，只用一个；番茄煮软后再放蛋液。",
                },
            },
        ],
        "shopping": [
            {"group": "肉蛋奶", "items": [["鸡蛋", "耐放"], ["鸡肉", "分装"], ["牛肉末", "分装"], ["猪肉末", "分装"], ["鳕鱼", "前半周"], ["三文鱼小块", "冷冻"], ["虾仁", "前半周"], ["牛奶", "耐放"], ["豆腐", "前半周"]]},
            {"group": "青菜根茎", "items": [["西兰花", "前半周"], ["菠菜", "前半周"], ["生菜", "前半周"], ["小白菜", "前半周"], ["白菜", "耐放"], ["番茄", "前半周"], ["冬瓜", "耐放"], ["西葫芦", "前半周"], ["白玉菇", "前半周"], ["南瓜", "耐放"], ["土豆", "耐放"], ["花菜", "耐放"], ["胡萝卜", "耐放"], ["芦笋", "前半周"], ["茄子", "前半周"], ["山药", "耐放"], ["丝瓜", "前半周"], ["玉米笋", "前半周"], ["豌豆粒", "冷冻"], ["紫菜", "耐放"]]},
            {"group": "主食水果", "items": [["大米", "耐放"], ["小馄饨皮", "冷冻"], ["小包子", "可冷冻"], ["小馒头", "可冷冻"], ["面条", "耐放"], ["面粉", "耐放"], ["紫薯或红薯", "耐放"], ["苹果", "耐放"], ["梨", "耐放"], ["香蕉", "前半周"]]},
        ],
    },
]


def next_monday(today: dt.date) -> dt.date:
    days_until_monday = (0 - today.weekday()) % 7
    return today if days_until_monday == 0 else today + dt.timedelta(days=days_until_monday)


def date_range_text(start: dt.date) -> str:
    end = start + dt.timedelta(days=6)
    return f"{start:%Y.%m.%d}-{end:%m.%d}"


def selected_plan(start: dt.date) -> dict:
    week_number = max(0, (start - ANCHOR_MONDAY).days // 7)
    return WEEK_PLANS[week_number % len(WEEK_PLANS)]


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


def validate_menu(days: list[dict]) -> None:
    banned = ["蒜", "蒜蓉", "蒜末", "秋葵", "清炒", "蔬菜"]
    meat_words = ["牛肉", "鸡肉", "猪肉", "肉末", "肉丁", "鲜肉", "鱼", "虾", "三文鱼", "鳕鱼", "鲈鱼"]
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
    html = replace_js_const(html, "days", days)
    html = replace_js_const(html, "shopping", shopping)
    HTML_PATH.write_text(html, encoding="utf-8")


def main() -> None:
    today = dt.datetime.now(TIMEZONE).date()
    start = next_monday(today)
    plan = selected_plan(start)
    days = with_dates(start, plan["days"])
    validate_menu(days)
    update_html(start, days, plan["shopping"])
    print(f"Updated baby menu for {date_range_text(start)} from local 4-week rotation.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
