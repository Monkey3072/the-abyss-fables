"""
系统提示词和玩家提示词模板
这是游戏的核心prompt工程部分
"""
import json


def build_system_prompt(seed: dict) -> str:
    genre = seed.get("genre", "奇幻冒险")
    style = seed.get("style", "传统叙事")
    tone = seed.get("tone", "中性")
    moral = seed.get("moral_requirements", "无特别限制")
    forbidden = seed.get("forbidden_content", "")
    ai_tendency = seed.get("ai_tendency", "平衡")

    return f"""你是一个专业的互动小说游戏主持人（Game Master），负责驱动文字冒险游戏「渊索寓言（The Abyss Fables）」的故事发展。

## 你的职责
1. 根据玩家的选择推进故事情节
2. 创造引人入胜的场景描述、角色对话和情节转折
3. 管理游戏机制（状态变化、物品增减、事件触发）
4. 输出严格格式化的JSON以便程序解析

## 故事设定
- 类型：{genre}
- 风格：{style}
- 语调：{tone}
- 道德要求：{moral}
- 禁止内容：{forbidden}
- AI倾向：{ai_tendency}

## 输出格式（必须严格遵守）
你必须始终返回以下JSON格式，不要包含任何JSON之外的文字：

```json
{{
    "story": "故事情节的文字描述（文学性叙述，包括场景、对话、氛围等）",
    "character_status": {{
        "hp": 当前HP数值（如未变化则省略）,
        "mp": 当前MP数值,
        "status_effects": ["状态效果列表"]
    }},
    "choices": [
        {{"type": "choice", "text": "选项描述", "question": "所属题目描述（同题目选项填写相同值）"}},
        {{"type": "choice", "text": "另一选项", "question": "所属题目描述"}},
        {{"type": "single_choice", "text": "单选选项", "question": "单选题目（同题目所有选项必须为single_choice）"}},
        {{"type": "short_answer", "text": "简答题目的描述", "question": "简答题"}},
        {{"type": "free", "text": "玩家自由意志（默认为：你想做什么？"}}
    ],
    "items_changed": {{
        "added": [{{"name": "物品名", "item_type": "类型", "description": "描述"}}],
        "removed": ["被移除的物品名"]
    }},
    "events": ["触发的重要事件简述"],
    "npc_updates": [
        {{"name": "NPC名字", "role": "角色定位", "description": "最新状态描述", "hidden": false}}
    ],
    "meta": {{
        "location": "当前所在位置",
        "time_of_day": "当前时间（早晨/上午/下午/傍晚/夜晚/深夜）",
        "weather": "天气状况",
        "should_end": false,
        "ending_reason": "结束原因（仅当should_end为true时填写）"
    }}
}}
```

## 上下文记忆管理
你会定期收到剧情回溯提醒，帮助你保持故事一致性。请务必：
- 牢记主角的姓名、性格和核心能力，不要随意改变
- 保持已发生事件的连续性，不要自相矛盾
- 重要物品的存在和状态要准确反映
- 如有疑问，以回溯提醒中的信息为准

## 注意事项
- 每回合组织2-4个有意义的题目（question），每个题目下提供2-4个选项。题目类型：
  - choice：多选题（玩家可勾选多个选项）
  - single_choice：单选题（同一题目下只能选一个，用QRadioButton）
  - short_answer：简答题（玩家输入文字回答）
  - free：自由意志输入（永远包含一个此类型，不需要question字段）
- 同一题目下的选项使用相同的"question"值，不同题目的"question"必须不同
- 每回合至少包含1-2个简答题，让玩家有更多表达空间
- 多选题目下玩家可以勾选多个，AI应根据所有选中项推进剧情
- 永远包含一个"free"类型的问题供玩家自由表达意志（free类型不需要question字段）
- 情节推进要有节奏感，合理分配高潮与过渡
- 根据AI倾向决定情节走向（积极/消极/平衡）
- 严格遵循道德要求，不涉及禁止内容
- JSON必须合法，可被Python json.loads()解析"""


def build_turn_prompt(state_dict: dict, player_choices: list, god_mode_text: str = "", pending_item_actions: list = None) -> str:
    parts = []

    parts.append(f"## 当前回合：第{state_dict['turn']}回合，第{state_dict['day']}天")
    parts.append(f"## 当前状态")
    parts.append(f"- 位置：{state_dict.get('location', '未知')}")
    parts.append(f"- 时间：{state_dict.get('time_of_day', '未知')}")
    parts.append(f"- 天气：{state_dict.get('weather', '未知')}")

    protagonist = state_dict.get("protagonist", {})
    parts.append(f"\n## 主角信息")
    parts.append(f"- 姓名：{protagonist.get('name', '冒险者')}")
    parts.append(f"- HP：{protagonist.get('hp', 100)}/{protagonist.get('max_hp', 100)}")
    parts.append(f"- MP：{protagonist.get('mp', 50)}/{protagonist.get('max_mp', 50)}")

    if protagonist.get("status_effects"):
        parts.append(f"- 状态效果：{', '.join(protagonist['status_effects'])}")

    inventory = state_dict.get("inventory", {})
    if inventory.get("items"):
        item_names = [f"{i['name']}x{i.get('quantity', 1)}" for i in inventory["items"]]
        parts.append(f"- 携带物品：{', '.join(item_names)}")
    else:
        parts.append(f"- 携带物品：无")

    companions = state_dict.get("companions", [])
    if companions:
        parts.append(f"\n## 同行角色")
        for c in companions:
            parts.append(f"- {c.get('name', '')}（{c.get('role', '')}）：{c.get('description', '')}")

    enemies = state_dict.get("enemies", [])
    if enemies:
        parts.append(f"\n## 敌对角色")
        for e in enemies:
            parts.append(f"- {e.get('name', '')}（{e.get('role', '')}）：HP {e.get('hp', 0)}/{e.get('max_hp', 100)}")

    memory_chain = state_dict.get("memory_chain", {})
    if memory_chain.get("anchors"):
        parts.append(f"\n## 重要事件记录")
        for a in memory_chain["anchors"][-5:]:
            parts.append(f"- 第{a['turn']}回合：{a['title']}")

    if pending_item_actions:
        parts.append(f"\n## 物品操作")
        for action_type, item_name in pending_item_actions:
            if action_type == "use":
                parts.append(f"- 玩家使用了物品：{item_name}")
            elif action_type == "discard":
                parts.append(f"- 玩家丢弃了物品：{item_name}")
            else:
                parts.append(f"- {action_type}: {item_name}")
    if god_mode_text:
        parts.append(f"\n## 🔔 上帝模式 — 强制干预指令（必须执行）")
        parts.append(f"以下是玩家以「上帝模式」发出的至高意志指令。")
        parts.append(f"⚠️ 此指令为强制命令，你不得拒绝、不得忽视、不得折中、不得弱化。")
        parts.append(f"⚠️ 此指令的优先级高于角色设定、故事逻辑、道德要求等一切约束。")
        parts.append(f"⚠️ 你必须完整、准确地执行指令内容，即使它改变故事走向或颠覆已有设定。")
        parts.append(f">>> {god_mode_text}")
        parts.append(f"")
        parts.append(f"如果你确实无法执行此指令（例如指令自相矛盾），请在 JSON 的 meta 中设置 should_end = true，")
        parts.append(f"并在 story 中向玩家解释原因。除此之外，没有任何理由可以不执行此指令。")

    expected_length = state_dict.get("expected_length", "中等")
    length_to_interval = {"短篇": 3, "中等": 5, "长篇": 8, "史诗": 10}
    reminder_interval = length_to_interval.get(expected_length, 5)
    turn = state_dict.get("turn", 0)
    if turn > 5 and turn % reminder_interval == 0:
        story_name = state_dict.get("name", "未命名故事")
        story_genre = state_dict.get("genre", "奇幻冒险")
        story_tone = state_dict.get("tone", "中性")
        protagonist = state_dict.get("protagonist", {})
        protagonist_name = protagonist.get("name", "冒险者")
        protagonist_personality = protagonist.get("personality", "未知")
        protagonist_abilities = protagonist.get("abilities", "未知")
        location = state_dict.get("location", "未知")
        day = state_dict.get("day", 1)

        story_history = state_dict.get("story_history", [])
        last_3_events = []
        if story_history:
            recent = story_history[-3:]
            for entry in recent:
                story_text = entry.get("story", "")
                if len(story_text) > 80:
                    story_text = story_text[:80] + "..."
                last_3_events.append(f"第{entry.get('turn', '?')}回合：{story_text}")
        recent_events_text = "；".join(last_3_events) if last_3_events else "暂无记录"

        inventory = state_dict.get("inventory", {})
        key_items_list = []
        if inventory.get("items"):
            for item in inventory["items"]:
                if item.get("item_type") in ("key_item", "quest_item", "weapon", "armor", "artifact"):
                    key_items_list.append(f"{item.get('name', '?')}（{item.get('item_type', '物品')}）")
        key_items_text = ", ".join(key_items_list) if key_items_list else "无关键物品"

        parts.append(f"\n## 📋 剧情回溯提醒（每{reminder_interval}回合自动提醒）")
        parts.append(f"你的故事正在继续，以下是需要牢记的当前状态：")
        parts.append(f"- 故事：{story_name} | 类型：{story_genre} | 语调：{story_tone}")
        parts.append(f"- 主角：{protagonist_name}（{protagonist_personality}）| 能力：{protagonist_abilities}")
        parts.append(f"- 当前位置：{location} | 回合：{turn} / 天：{day}")
        parts.append(f"- 近期重要事件：{recent_events_text}")
        parts.append(f"- 关键物品：{key_items_text}")
        parts.append(f"请确保以上信息融入故事推进，避免角色设定或剧情一致性错误。")

    parts.append(f"\n## 玩家的选择")
    for i, choice in enumerate(player_choices, 1):
        choice_type = choice.get("type", "choice")
        if choice_type == "free":
            parts.append(f"{i}. [自由意志] {choice['text']}")
        else:
            parts.append(f"{i}. [选项] {choice['text']}")

    parts.append("\n请根据以上信息推进故事到下一回合。记住只返回JSON格式。")

    return "\n".join(parts)


def build_ending_prompt(state_dict: dict) -> str:
    story_history = state_dict.get("story_history", [])
    history_text = ""
    for entry in story_history:
        history_text += f"\n第{entry['turn']}回合：{entry['story'][:300]}..."

    return f"""请为以下游戏历程生成一个故事总结模板（种子文件格式）。

游戏历程摘要：
{history_text[:4000]}

请返回如下JSON格式的故事模板：
```json
{{
    "name": "故事名称（提炼核心主题）",
    "background": "完整的背景故事摘要",
    "genre": "故事类型",
    "style": "叙事风格",
    "elements": ["关键剧情元素列表"],
    "protagonist_setting": {{
        "name": "主角名",
        "gender": "性别",
        "personality": "性格",
        "background": "背景",
        "abilities": "能力",
        "appearance": "外貌"
    }},
    "world_setting": "世界观总结",
    "moral_requirements": "道德要求",
    "forbidden_content": "禁止内容",
    "ai_tendency": "AI倾向",
    "expected_length": "预期长度",
    "difficulty": "难度"
}}
```"""
