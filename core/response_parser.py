"""
AI响应解析器
解析AI返回的JSON格式内容，提取故事、选项、角色状态等
"""
import json
import re
from models.validators import AIResponseValidator
from pydantic import ValidationError


def extract_json_from_response(response: str) -> dict:
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    tank = response.split("```json")
    if len(tank) >= 2:
        json_str = tank[1].split("```")[0].strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    match = re.search(r"\{[\s\S]*\"story\"[\s\S]*\}", response)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return _fallback_parse(response)


def _sanitize_story_text(text: str) -> str:
    text = re.sub(r"^```(?:json|markdown|yaml)?\s*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n?```\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n?\s*```\s*\n?", "\n", text)
    text = re.sub(r'^\s*\{?\s*"(?:story|choices|character_status|items_changed|events|meta|npc_updates)"\s*[:：]', "", text, flags=re.MULTILINE)
    json_kv_pattern = re.compile(r'^\s*"[^"]+"\s*:\s*("[^"]*"|\d+|true|false|null|\[[\s\S]*?\]|\{[\s\S]*?\}),?\s*$', re.MULTILINE)
    text = json_kv_pattern.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _fallback_parse(response: str) -> dict:
    clean_story = _sanitize_story_text(response)
    if len(clean_story) < 10:
        clean_story = response.replace("{", "").replace("}", "").strip()
    result = {
        "story": clean_story,
        "character_status": {},
        "choices": [{"type": "free", "text": "请输入你的行动"}],
        "items_changed": {"added": [], "removed": []},
        "events": [],
        "meta": {"location": "未知", "time_of_day": "未知", "weather": "未知"},
    }

    choice_pattern = re.findall(r"选项\s*[：:]\s*(.+)", response)
    if choice_pattern:
        result["choices"] = []
        for line in choice_pattern:
            parts = re.split(r"[；;，,]", line)
            for p in parts:
                p = p.strip()
                if p and len(p) > 1:
                    result["choices"].append({"type": "choice", "text": p})

    return result


def parse_ai_response(response: str) -> dict:
    parsed = extract_json_from_response(response)
    raw_story = parsed.get("story", response)
    story = _sanitize_story_text(raw_story) if raw_story else raw_story
    result = {
        "story": story,
        "choices": parsed.get("choices", [{"type": "free", "text": "请输入你的行动"}]),
        "character_status": parsed.get("character_status", {}),
        "items_changed": parsed.get("items_changed", {"added": [], "removed": []}),
        "events": parsed.get("events", []),
        "npc_updates": parsed.get("npc_updates", []),
        "meta": parsed.get("meta", {
            "location": "未知",
            "time_of_day": "未知",
            "weather": "未知",
            "should_end": False,
            "ending_reason": "",
        }),
    }
    try:
        AIResponseValidator(**result)
    except ValidationError:
        pass
    return result
