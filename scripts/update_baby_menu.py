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
ACTIVE_PLAN_INDEXES = [1]
TRACKED_INGREDIENTS = [
    "白玉菇",
    "海鲜菇",
    "上海青",
    "油麦菜",
    "娃娃菜",
    "圆白菜",
    "紫甘蓝",
    "西兰花",
    "西葫芦",
    "白萝卜",
    "青萝卜",
    "玉米笋",
    "黄豆芽",
    "绿豆芽",
    "海带芽",
    "裙带菜",
    "四季豆",
    "豆腐",
    "油菜",
    "菜心",
    "茼蒿",
    "空心菜",
    "白菜",
    "大头菜",
    "冬瓜",
    "南瓜",
    "番茄",
    "花菜",
    "胡萝卜",
    "土豆",
    "山药",
    "芋头",
    "莴笋",
    "莲藕",
    "丝瓜",
    "芦笋",
    "黄瓜",
    "茄子",
    "口蘑",
    "香菇",
    "豌豆",
    "海带",
    "紫菜",
    "彩椒",
]


WEEK_PLANS = [
    {
        "days": [
            {
                "focus": "鲜菜先吃",
                "meals": {
                    "breakfast": "主食：油菜牛肉小包子｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：番茄鸡肉丁｜素菜：莴笋胡萝卜丁",
                    "dinner": "主食：小米馒头｜素菜：南瓜豆腐羹｜素菜：娃娃菜白玉菇汤",
                },
                "notes": {
                    "breakfast": "包子馅里加少量油菜碎，提前蒸好或冷冻，早上复热即可。",
                    "lunch": "鸡肉和番茄切小丁，莴笋胡萝卜都切小粒后煮软。",
                    "dinner": "南瓜和豆腐煮成软羹；娃娃菜白玉菇汤煮软后剪小。",
                },
            },
            {
                "focus": "鱼虾优先",
                "meals": {
                    "breakfast": "主食：上海青鲜肉小馄饨｜搭配：苹果片",
                    "lunch": "主食：软米饭｜肉菜：鳕鱼芦笋丁｜素菜：莲藕土豆泥",
                    "dinner": "主食：甜玉米软面｜蛋菜：西兰花鸡蛋碎｜素菜：冬瓜海带芽汤",
                },
                "notes": {
                    "breakfast": "小馄饨本身算一道菜，馅里放上海青碎；苹果切薄片或小丁。",
                    "lunch": "鳕鱼确认无刺后切丁，芦笋去老根切小；莲藕擦碎后和土豆蒸软压泥。",
                    "dinner": "今天鸡蛋放晚餐，只用一个；冬瓜海带芽汤煮软。",
                },
            },
            {
                "focus": "软烂好嚼",
                "meals": {
                    "breakfast": "主食：番茄油麦菜牛肉碎面｜搭配：蒸红薯",
                    "lunch": "主食：软米饭｜肉菜：虾仁南瓜丁｜素菜：茼蒿豆腐汤",
                    "dinner": "主食：山药小馒头｜素菜：胡萝卜豌豆丁｜素菜：茄子口蘑煲",
                },
                "notes": {
                    "breakfast": "牛肉碎提前分装，番茄煮软后下面；油麦菜最后剪碎烫熟。",
                    "lunch": "虾仁切小丁，南瓜蒸到软；茼蒿切碎后和豆腐一起煮软。",
                    "dinner": "茄子口蘑加水焖软；豌豆粒要煮透压一压。",
                },
            },
            {
                "focus": "换主食",
                "meals": {
                    "breakfast": "主食：西兰花鸡蛋饼｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：鸡肉土豆丁｜素菜：丝瓜黄豆芽汤",
                    "dinner": "主食：圆白菜素包子｜素菜：冬瓜紫菜汤",
                },
                "notes": {
                    "breakfast": "今天鸡蛋放早餐，只用一个；西兰花焯熟切碎再摊饼。",
                    "lunch": "鸡肉去皮切丁，土豆煮软；黄豆芽掐短一点，和丝瓜一起煮透。",
                    "dinner": "素包子本身算一道菜，所以只配冬瓜紫菜汤。",
                },
            },
            {
                "focus": "耐放菜",
                "meals": {
                    "breakfast": "主食：菠菜猪肉小馄饨｜搭配：苹果片",
                    "lunch": "主食：软米饭｜肉菜：三文鱼胡萝卜丁｜素菜：彩椒白玉菇",
                    "dinner": "主食：番茄疙瘩汤｜素菜：南瓜豆腐羹｜素菜：空心菜碎汤",
                },
                "notes": {
                    "breakfast": "小馄饨馅里加菠菜碎，煮到皮软馅熟；苹果切小块。",
                    "lunch": "三文鱼切小丁煎或蒸熟后拌胡萝卜；彩椒和白玉菇切小段煮软。",
                    "dinner": "疙瘩做小一点，番茄煮软；空心菜剪碎后最后下锅。",
                },
            },
            {
                "focus": "周末简单",
                "meals": {
                    "breakfast": "主食：菜心鸡肉小包子｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：牛肉西葫芦丁｜素菜：花菜裙带菜汤",
                    "dinner": "主食：山药小馒头｜蛋菜：娃娃菜鸡蛋碎｜素菜：茄子芋头煲",
                },
                "notes": {
                    "breakfast": "包子馅里加菜心碎；冷冻包子复热后掰开确认不烫。",
                    "lunch": "牛肉和西葫芦都切小丁，牛肉先做熟再混合。",
                    "dinner": "今天鸡蛋放晚餐，只用一个；茄子芋头加水焖软。",
                },
            },
            {
                "focus": "清库存",
                "meals": {
                    "breakfast": "主食：生菜鳕鱼小饼｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：虾仁番茄丁｜素菜：白萝卜豆腐汤",
                    "dinner": "主食：南瓜软面｜素菜：胡萝卜豌豆丁｜素菜：丝瓜绿豆芽汤",
                },
                "notes": {
                    "breakfast": "鳕鱼确认无刺，和生菜碎拌成小饼，烙到全熟。",
                    "lunch": "虾仁切丁，番茄煮软；白萝卜和豆腐切小块、煮透。",
                    "dinner": "软面煮久一点；豌豆粒煮透后压碎，绿豆芽切短煮透。",
                },
            },
        ],
        "shopping": [
            {"group": "肉蛋奶", "items": [["鸡蛋", "耐放"], ["牛肉碎或牛肉末", "分装"], ["鸡肉", "分装"], ["猪肉末", "分装"], ["鳕鱼", "前半周"], ["三文鱼小块", "冷冻"], ["虾仁", "前半周"], ["牛奶", "耐放"], ["豆腐", "前半周"]]},
            {"group": "青菜根茎", "items": [["油菜", "前半周"], ["上海青", "前半周"], ["油麦菜", "前半周"], ["茼蒿", "前半周"], ["菜心", "前半周"], ["娃娃菜", "耐放"], ["圆白菜", "耐放"], ["茄子", "前半周"], ["芦笋", "前半周"], ["莴笋", "前半周"], ["西葫芦", "前半周"], ["花菜", "耐放"], ["胡萝卜", "耐放"], ["南瓜", "耐放"], ["土豆", "耐放"], ["山药", "耐放"], ["芋头", "耐放"], ["冬瓜", "耐放"], ["丝瓜", "前半周"], ["白萝卜", "耐放"], ["莲藕", "耐放"], ["豌豆粒", "冷冻"], ["黄豆芽", "前半周"], ["绿豆芽", "前半周"], ["海带芽", "耐放"], ["裙带菜", "耐放"], ["紫菜", "耐放"], ["口蘑或白玉菇", "前半周"], ["番茄", "前半周"], ["彩椒", "少量"]]},
            {"group": "主食水果", "items": [["大米", "耐放"], ["小米馒头", "可冷冻"], ["小馄饨皮", "冷冻"], ["小包子", "可冷冻"], ["面条", "耐放"], ["面粉", "耐放"], ["红薯", "耐放"], ["苹果", "耐放"]]},
        ],
    },
    {
        "days": [
            {
                "focus": "先用鲜叶",
                "meals": {
                    "breakfast": "主食：油麦菜鸡蛋羹馒头块｜搭配：梨丁",
                    "lunch": "主食：软米饭｜肉菜：牛肉白萝卜丁｜素菜：番茄花菜碎",
                    "dinner": "主食：紫薯小馒头｜素菜：豆腐娃娃菜煲｜素菜：胡萝卜玉米笋汤",
                },
                "notes": {
                    "breakfast": "今天鸡蛋放早餐，只用一个；油麦菜焯软切碎放进蛋羹。",
                    "lunch": "牛肉切小丁或剁碎，白萝卜炖软；番茄花菜都切小。",
                    "dinner": "豆腐娃娃菜小火煮软，玉米笋切薄片。",
                },
            },
            {
                "focus": "补铁安排",
                "meals": {
                    "breakfast": "主食：上海青猪肉小饼｜搭配：牛奶",
                    "lunch": "主食：南瓜软饭｜肉菜：鳕鱼四季豆丁｜素菜：西兰花土豆泥",
                    "dinner": "主食：小米面片汤｜素菜：丝瓜海鲜菇｜素菜：芋头菜心汤",
                },
                "notes": {
                    "breakfast": "上海青焯软切碎，猪肉末做熟后拌进小饼。",
                    "lunch": "四季豆一定煮透切碎；西兰花土豆蒸软压泥。",
                    "dinner": "面片做小，丝瓜和海鲜菇煮软；菜心最后剪碎烫熟。",
                },
            },
            {
                "focus": "鱼肉换口味",
                "meals": {
                    "breakfast": "主食：油菜虾仁小馄饨｜搭配：香蕉块",
                    "lunch": "主食：软米饭｜肉菜：鲈鱼青萝卜丁｜素菜：莴笋口蘑汤",
                    "dinner": "主食：甜玉米小饼｜素菜：西葫芦圆白菜丁｜素菜：海带芽汤",
                },
                "notes": {
                    "breakfast": "小馄饨馅里加油菜碎和虾仁丁；香蕉切小块。",
                    "lunch": "鲈鱼确认无刺后切丁，青萝卜煮软。",
                    "dinner": "西葫芦和圆白菜都切细丝更好熟；海带芽少量煮软。",
                },
            },
            {
                "focus": "软饭日",
                "meals": {
                    "breakfast": "主食：番茄牛肉碎面｜搭配：苹果片",
                    "lunch": "主食：软米饭｜肉菜：鸡肉山药丁｜素菜：茼蒿黄豆芽汤",
                    "dinner": "主食：白菜素饺子｜素菜：豆腐彩椒羹",
                },
                "notes": {
                    "breakfast": "牛肉碎提前分装，番茄煮软后下进面里。",
                    "lunch": "鸡肉切丁，山药蒸软；黄豆芽切短后和茼蒿煮透。",
                    "dinner": "素饺子本身算一道菜，所以只配豆腐彩椒羹。",
                },
            },
            {
                "focus": "耐放搭配",
                "meals": {
                    "breakfast": "主食：娃娃菜鲜肉小包子｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：猪肉茄子丁｜素菜：紫甘蓝胡萝卜碎",
                    "dinner": "主食：小米疙瘩汤｜素菜：冬瓜裙带菜汤｜素菜：芋头豌豆泥",
                },
                "notes": {
                    "breakfast": "包子馅里加娃娃菜碎，早上复热后放温再吃。",
                    "lunch": "猪肉和茄子都切小，茄子焖软；紫甘蓝胡萝卜蒸软切碎。",
                    "dinner": "疙瘩做小；冬瓜切薄片，裙带菜少量；芋头蒸软后和豌豆压泥。",
                },
            },
            {
                "focus": "周末省心",
                "meals": {
                    "breakfast": "主食：油菜鸡蛋饼｜搭配：梨丁",
                    "lunch": "主食：软米饭｜肉菜：虾仁西葫芦丁｜素菜：莲藕土豆泥",
                    "dinner": "主食：红薯小馒头｜素菜：上海青口蘑汤｜素菜：莴笋玉米笋丁",
                },
                "notes": {
                    "breakfast": "今天鸡蛋放早餐，只用一个；油菜焯软切碎再摊饼。",
                    "lunch": "虾仁和西葫芦切小丁，莲藕擦碎后和土豆蒸软压泥。",
                    "dinner": "上海青和口蘑煮软；莴笋玉米笋都切小丁。",
                },
            },
            {
                "focus": "清淡收尾",
                "meals": {
                    "breakfast": "主食：菜心牛肉小包子｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：鳕鱼番茄丁｜素菜：青萝卜紫菜汤",
                    "dinner": "主食：小米软面｜素菜：西兰花豆腐羹｜素菜：丝瓜海鲜菇汤",
                },
                "notes": {
                    "breakfast": "包子馅里加菜心碎，复热后确认中间热透。",
                    "lunch": "鳕鱼确认无刺，番茄煮软后拌鱼丁。",
                    "dinner": "西兰花和豆腐煮成软羹，丝瓜海鲜菇汤煮软。",
                },
            },
        ],
        "shopping": [
            {"group": "肉蛋奶", "items": [["鸡蛋", "耐放"], ["牛肉碎", "分装"], ["猪肉末", "分装"], ["鸡肉", "分装"], ["鲈鱼或鳕鱼", "前半周"], ["虾仁", "前半周"], ["牛奶", "耐放"], ["豆腐", "前半周"]]},
            {"group": "青菜根茎", "items": [["油麦菜", "前半周"], ["上海青", "前半周"], ["油菜", "前半周"], ["菜心", "前半周"], ["空心菜", "前半周"], ["娃娃菜", "耐放"], ["圆白菜", "耐放"], ["白菜", "耐放"], ["西兰花", "前半周"], ["番茄", "前半周"], ["冬瓜", "耐放"], ["花菜", "耐放"], ["胡萝卜", "耐放"], ["玉米笋", "前半周"], ["四季豆", "前半周"], ["紫甘蓝", "少量"], ["白萝卜", "耐放"], ["青萝卜", "耐放"], ["莴笋", "前半周"], ["芋头", "耐放"], ["南瓜", "耐放"], ["西葫芦", "前半周"], ["丝瓜", "前半周"], ["山药", "耐放"], ["紫薯或红薯", "耐放"], ["豌豆粒", "冷冻"], ["白玉菇或海鲜菇", "前半周"], ["裙带菜", "耐放"], ["紫菜", "耐放"]]},
            {"group": "主食水果", "items": [["大米", "耐放"], ["馒头", "可冷冻"], ["小馄饨皮", "冷冻"], ["饺子皮", "冷冻"], ["面条", "耐放"], ["面粉", "耐放"], ["苹果", "耐放"], ["梨", "耐放"], ["香蕉", "前半周"]]},
        ],
    },
    {
        "days": [
            {
                "focus": "叶菜藏起来",
                "meals": {
                    "breakfast": "主食：油菜鳕鱼小饼｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：猪肉冬瓜丁｜素菜：番茄豆腐羹",
                    "dinner": "主食：南瓜小馒头｜蛋菜：上海青鸡蛋碎｜素菜：西葫芦白玉菇",
                },
                "notes": {
                    "breakfast": "鳕鱼确认无刺，油菜焯软切碎，和鱼肉拌成小饼。",
                    "lunch": "猪肉丁做熟后加冬瓜煮软；番茄豆腐羹切小块。",
                    "dinner": "今天鸡蛋放晚餐，只用一个；上海青切碎拌进鸡蛋里。",
                },
            },
            {
                "focus": "虾仁换味",
                "meals": {
                    "breakfast": "主食：娃娃菜牛肉小馄饨｜搭配：梨丁",
                    "lunch": "主食：软米饭｜肉菜：虾仁芦笋丁｜素菜：莲藕南瓜泥",
                    "dinner": "主食：山药软面｜素菜：圆白菜豆腐汤｜素菜：胡萝卜玉米笋丁",
                },
                "notes": {
                    "breakfast": "馄饨馅里加娃娃菜碎，煮软后放温再吃。",
                    "lunch": "虾仁和芦笋都切小；莲藕擦碎后和南瓜蒸软压泥。",
                    "dinner": "山药切小煮软后下面；玉米笋切薄片。",
                },
            },
            {
                "focus": "牛肉补铁",
                "meals": {
                    "breakfast": "主食：菜心鸡蛋羹小馒头｜搭配：苹果片",
                    "lunch": "主食：软米饭｜肉菜：牛肉胡萝卜丁｜素菜：丝瓜豆腐汤",
                    "dinner": "主食：番茄疙瘩汤｜素菜：土豆豌豆泥｜素菜：冬瓜海带芽汤",
                },
                "notes": {
                    "breakfast": "今天鸡蛋放早餐，只用一个；菜心切碎放进蛋羹。",
                    "lunch": "牛肉和胡萝卜切小丁，胡萝卜要煮软。",
                    "dinner": "疙瘩做小一点；豌豆煮透后和土豆一起压泥。",
                },
            },
            {
                "focus": "鱼肉安排",
                "meals": {
                    "breakfast": "主食：油麦菜猪肉小包子｜搭配：牛奶",
                    "lunch": "主食：南瓜软饭｜肉菜：三文鱼西葫芦丁｜素菜：娃娃菜白玉菇汤",
                    "dinner": "主食：紫薯小馒头｜素菜：番茄花菜碎｜素菜：豆腐空心菜汤",
                },
                "notes": {
                    "breakfast": "包子馅里加油麦菜碎，复热后掰开看一下温度。",
                    "lunch": "三文鱼煎或蒸熟后切小，西葫芦煮软。",
                    "dinner": "番茄花菜切小煮软；空心菜剪碎后最后下进豆腐汤。",
                },
            },
            {
                "focus": "软烂耐嚼",
                "meals": {
                    "breakfast": "主食：茼蒿鸡肉碎面｜搭配：香蕉块",
                    "lunch": "主食：软米饭｜肉菜：鸡肉土豆丁｜素菜：莴笋胡萝卜丁",
                    "dinner": "主食：圆白菜素包子｜素菜：南瓜豆腐羹",
                },
                "notes": {
                    "breakfast": "鸡肉碎提前做熟，茼蒿焯软切碎后下进面里。",
                    "lunch": "鸡肉土豆都切小，土豆煮软；莴笋去老皮切小丁。",
                    "dinner": "素包子本身算一道菜，只配南瓜豆腐羹。",
                },
            },
            {
                "focus": "周末快手",
                "meals": {
                    "breakfast": "主食：上海青鸡蛋饼｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：鳕鱼番茄丁｜素菜：白萝卜玉米笋汤",
                    "dinner": "主食：小米馒头｜素菜：茄子芋头煲｜素菜：西兰花豆腐汤",
                },
                "notes": {
                    "breakfast": "今天鸡蛋放早餐，只用一个；上海青切碎摊进饼里。",
                    "lunch": "鳕鱼确认无刺，番茄煮软；白萝卜玉米笋切小。",
                    "dinner": "茄子芋头加水焖软；西兰花切小再煮汤。",
                },
            },
            {
                "focus": "清库存",
                "meals": {
                    "breakfast": "主食：油菜牛肉小饼｜搭配：黄瓜软片",
                    "lunch": "主食：软米饭｜肉菜：虾仁山药丁｜素菜：胡萝卜花菜碎",
                    "dinner": "主食：丝瓜面片汤｜素菜：白菜豆腐丁｜素菜：南瓜豌豆泥",
                },
                "notes": {
                    "breakfast": "牛肉末和油菜碎拌成小饼，烙到全熟；黄瓜去皮切薄片。",
                    "lunch": "虾仁切丁，山药蒸软；胡萝卜花菜煮软切碎。",
                    "dinner": "面片煮软；豌豆煮透后和南瓜一起压泥。",
                },
            },
        ],
        "shopping": [
            {"group": "肉蛋奶", "items": [["鸡蛋", "耐放"], ["鳕鱼", "前半周"], ["猪肉末", "分装"], ["牛肉末", "分装"], ["鸡肉", "分装"], ["三文鱼小块", "冷冻"], ["虾仁", "前半周"], ["牛奶", "耐放"], ["豆腐", "前半周"]]},
            {"group": "青菜根茎", "items": [["油菜", "前半周"], ["上海青", "前半周"], ["菜心", "前半周"], ["油麦菜", "前半周"], ["茼蒿", "前半周"], ["空心菜", "前半周"], ["娃娃菜", "耐放"], ["圆白菜", "耐放"], ["白菜", "耐放"], ["西兰花", "前半周"], ["西葫芦", "前半周"], ["冬瓜", "耐放"], ["白萝卜", "耐放"], ["番茄", "前半周"], ["胡萝卜", "耐放"], ["花菜", "耐放"], ["南瓜", "耐放"], ["土豆", "耐放"], ["山药", "耐放"], ["芋头", "耐放"], ["莲藕", "耐放"], ["莴笋", "前半周"], ["丝瓜", "前半周"], ["芦笋", "前半周"], ["玉米笋", "前半周"], ["黄瓜", "前半周"], ["茄子", "前半周"], ["白玉菇", "前半周"], ["豌豆粒", "冷冻"], ["海带芽", "耐放"], ["紫菜", "耐放"]]},
            {"group": "主食水果", "items": [["大米", "耐放"], ["小馒头", "可冷冻"], ["小馄饨皮", "冷冻"], ["小包子", "可冷冻"], ["面条", "耐放"], ["面粉", "耐放"], ["紫薯", "耐放"], ["苹果", "耐放"], ["梨", "耐放"], ["香蕉", "前半周"]]},
        ],
    },
    {
        "days": [
            {
                "focus": "清爽开周",
                "meals": {
                    "breakfast": "主食：菜心鸡肉小包子｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：牛肉番茄丁｜素菜：青萝卜豆腐汤",
                    "dinner": "主食：山药小馒头｜素菜：娃娃菜香菇煲｜素菜：胡萝卜豌豆丁",
                },
                "notes": {
                    "breakfast": "包子馅里加菜心碎，复热后放温再吃。",
                    "lunch": "牛肉和番茄切小，青萝卜切薄片后煮软。",
                    "dinner": "香菇切小片，白菜煮软；豌豆煮透压一压。",
                },
            },
            {
                "focus": "叶菜藏馅",
                "meals": {
                    "breakfast": "主食：上海青猪肉小馄饨｜搭配：梨丁",
                    "lunch": "主食：软米饭｜肉菜：鸡肉南瓜丁｜素菜：西葫芦白玉菇",
                    "dinner": "主食：番茄软面｜蛋菜：油菜鸡蛋碎｜素菜：丝瓜豆腐汤",
                },
                "notes": {
                    "breakfast": "馄饨馅里加上海青碎，煮到皮软馅熟。",
                    "lunch": "鸡肉切丁，南瓜蒸软；西葫芦白玉菇煮软。",
                    "dinner": "今天鸡蛋放晚餐，只用一个；油菜切碎拌进鸡蛋。",
                },
            },
            {
                "focus": "鱼虾轮换",
                "meals": {
                    "breakfast": "主食：油麦菜牛肉碎面｜搭配：苹果片",
                    "lunch": "主食：软米饭｜肉菜：虾仁土豆丁｜素菜：花菜胡萝卜碎",
                    "dinner": "主食：紫薯小馒头｜素菜：南瓜豆腐羹｜素菜：冬瓜海带汤",
                },
                "notes": {
                    "breakfast": "油麦菜剪碎最后下锅，牛肉碎提前做熟。",
                    "lunch": "虾仁切丁，土豆煮软；花菜胡萝卜切碎煮软。",
                    "dinner": "南瓜豆腐煮成软羹，冬瓜切薄片。",
                },
            },
            {
                "focus": "蛋放早餐",
                "meals": {
                    "breakfast": "主食：茼蒿鸡蛋饼｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：鳕鱼芦笋丁｜素菜：大头菜豆腐汤",
                    "dinner": "主食：圆白菜素包子｜素菜：番茄花菜碎",
                },
                "notes": {
                    "breakfast": "今天鸡蛋放早餐，只用一个；茼蒿焯软切碎再摊饼。",
                    "lunch": "鳕鱼确认无刺，芦笋去老根切小。",
                    "dinner": "素包子本身算一道菜，只配番茄花菜碎。",
                },
            },
            {
                "focus": "根茎耐放",
                "meals": {
                    "breakfast": "主食：娃娃菜鲜肉小饼｜搭配：香蕉块",
                    "lunch": "主食：软米饭｜肉菜：猪肉胡萝卜丁｜素菜：茄子芋头煲",
                    "dinner": "主食：甜玉米疙瘩汤｜素菜：西兰花豆腐丁｜素菜：空心菜碎汤",
                },
                "notes": {
                    "breakfast": "娃娃菜切碎拌进鲜肉馅，小饼烙到全熟。",
                    "lunch": "猪肉和胡萝卜都切小丁；茄子芋头加水焖软。",
                    "dinner": "疙瘩做小一点；空心菜碎最后下锅烫熟。",
                },
            },
            {
                "focus": "周末省心",
                "meals": {
                    "breakfast": "主食：油菜鳕鱼小饼｜搭配：牛奶",
                    "lunch": "主食：软米饭｜肉菜：鸡肉山药丁｜素菜：丝瓜绿豆芽汤",
                    "dinner": "主食：南瓜软面｜素菜：娃娃菜白玉菇汤｜素菜：胡萝卜豌豆泥",
                },
                "notes": {
                    "breakfast": "鳕鱼确认无刺，油菜切碎后拌成小饼。",
                    "lunch": "鸡肉和山药切丁，山药蒸软；绿豆芽切短后和丝瓜煮透。",
                    "dinner": "软面煮久一点；胡萝卜豌豆煮透压泥。",
                },
            },
            {
                "focus": "收尾清淡",
                "meals": {
                    "breakfast": "主食：油麦菜牛肉小馄饨｜搭配：梨丁",
                    "lunch": "主食：软米饭｜肉菜：三文鱼西葫芦丁｜素菜：白萝卜豆腐汤",
                    "dinner": "主食：红薯小馒头｜蛋菜：番茄鸡蛋碎｜素菜：花菜紫菜汤",
                },
                "notes": {
                    "breakfast": "馄饨馅里加油麦菜碎，煮软后放温。",
                    "lunch": "三文鱼煎或蒸熟后切小，西葫芦煮软。",
                    "dinner": "今天鸡蛋放晚餐，只用一个；番茄煮软后再放蛋液。",
                },
            },
        ],
        "shopping": [
            {"group": "肉蛋奶", "items": [["鸡蛋", "耐放"], ["鸡肉", "分装"], ["牛肉末", "分装"], ["猪肉末", "分装"], ["鳕鱼", "前半周"], ["三文鱼小块", "冷冻"], ["虾仁", "前半周"], ["牛奶", "耐放"], ["豆腐", "前半周"]]},
            {"group": "青菜根茎", "items": [["菜心", "前半周"], ["上海青", "前半周"], ["油菜", "前半周"], ["油麦菜", "前半周"], ["茼蒿", "前半周"], ["空心菜", "前半周"], ["娃娃菜", "耐放"], ["圆白菜或大头菜", "耐放"], ["番茄", "前半周"], ["冬瓜", "耐放"], ["白萝卜", "耐放"], ["青萝卜", "耐放"], ["西葫芦", "前半周"], ["白玉菇", "前半周"], ["香菇", "前半周"], ["南瓜", "耐放"], ["土豆", "耐放"], ["花菜", "耐放"], ["胡萝卜", "耐放"], ["芦笋", "前半周"], ["茄子", "前半周"], ["山药", "耐放"], ["芋头", "耐放"], ["丝瓜", "前半周"], ["玉米笋", "前半周"], ["豌豆粒", "冷冻"], ["绿豆芽", "前半周"], ["海带", "耐放"], ["紫菜", "耐放"]]},
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
    plan_index = ACTIVE_PLAN_INDEXES[week_number % len(ACTIVE_PLAN_INDEXES)]
    return WEEK_PLANS[plan_index]


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


def extract_ingredients(text: str) -> set[str]:
    found: set[str] = set()
    remaining = text
    for ingredient in sorted(TRACKED_INGREDIENTS, key=len, reverse=True):
        if ingredient in remaining:
            found.add(ingredient)
            remaining = remaining.replace(ingredient, "")
    return found


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
    ]
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

    day_ingredients = []
    for day in days:
        day_sets = {meal_name: extract_ingredients(meal_text) for meal_name, meal_text in day["meals"].items()}
        seen: dict[str, str] = {}
        for meal_name, ingredients in day_sets.items():
            for ingredient in ingredients:
                if ingredient in seen:
                    raise ValueError(
                        f"Ingredient {ingredient!r} repeats in one day: {day.get('name')} "
                        f"{seen[ingredient]} and {meal_name}"
                    )
                seen[ingredient] = meal_name
        day_ingredients.append(set().union(*day_sets.values()))

    for start_index in range(len(day_ingredients) - 2):
        window = day_ingredients[start_index : start_index + 3]
        for ingredient in TRACKED_INGREDIENTS:
            hit_days = [DAY_NAMES[start_index + offset] for offset, ingredients in enumerate(window) if ingredient in ingredients]
            if len(hit_days) > 1:
                raise ValueError(f"Ingredient {ingredient!r} repeats within 3 days: {', '.join(hit_days)}")


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
