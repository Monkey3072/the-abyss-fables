"""
种子管理模块
创建、编辑、导入、导出游戏种子文件（加密/明文）
"""
import json
import base64
import hashlib
import zlib
from pathlib import Path
from typing import Optional
from models.validators import validate_seed
from pydantic import ValidationError

SEED_FILE_EXTENSION = ".seed"
ENCRYPTED_MARKER = "ENCRYPTED_SEED:"


class SeedManager:
    @staticmethod
    def create_default_seed():
        return {
            "name": "新的故事",
            "background": "",
            "genre": "奇幻冒险",
            "style": "传统叙事",
            "tone": "中性",
            "elements": [],
            "protagonist_setting": {
                "name": "",
                "gender": "未知",
                "age": "",
                "personality": "",
                "background": "",
                "abilities": "",
                "appearance": "",
            },
            "world_setting": "",
            "moral_requirements": "无特别限制",
            "forbidden_content": "",
            "ai_tendency": "平衡",
            "expected_length": "中等",
            "difficulty": "普通",
            "custom_notes": "",
        }

    @staticmethod
    def export_seed(seed: dict, filepath: str, password: str = ""):
        data = json.dumps(seed, ensure_ascii=False, indent=2)
        if password:
            key = hashlib.sha256(password.encode()).digest()
            compressed = zlib.compress(data.encode("utf-8"))
            encrypted = bytearray()
            for i, b in enumerate(compressed):
                encrypted.append(b ^ key[i % len(key)])
            final = ENCRYPTED_MARKER + base64.b64encode(bytes(encrypted)).decode()
        else:
            final = data

        path = Path(filepath)
        if not path.suffix:
            path = path.with_suffix(SEED_FILE_EXTENSION)
        with open(path, "w", encoding="utf-8") as f:
            f.write(final)
        return str(path)

    @staticmethod
    def import_seed(filepath: str, password: str = "") -> Optional[dict]:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"种子文件不存在: {filepath}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if content.startswith(ENCRYPTED_MARKER):
            if not password:
                raise ValueError("此种子已加密，需要密码")
            try:
                b64_data = content[len(ENCRYPTED_MARKER):]
                encrypted = base64.b64decode(b64_data)
                key = hashlib.sha256(password.encode()).digest()
                decrypted = bytearray()
                for i, b in enumerate(encrypted):
                    decrypted.append(b ^ key[i % len(key)])
                decompressed = zlib.decompress(bytes(decrypted))
                seed = json.loads(decompressed.decode("utf-8"))
                return validate_seed(seed)
            except ValidationError:
                raise ValueError("种子文件格式不符合规范")
            except Exception:
                raise ValueError("密码错误或文件损坏")
        else:
            try:
                seed = json.loads(content)
                return validate_seed(seed)
            except ValidationError:
                raise ValueError("种子文件格式不符合规范")
            except json.JSONDecodeError:
                raise ValueError("无效的种子文件格式")

    @staticmethod
    def is_encrypted(filepath: str) -> bool:
        path = Path(filepath)
        if not path.exists():
            return False
        with open(path, "r", encoding="utf-8") as f:
            content = f.read(256)
        return content.startswith(ENCRYPTED_MARKER)

    @staticmethod
    def auto_generate_seed(ai_client, text_content: str) -> dict:
        prompt = _build_auto_gen_prompt(text_content)
        try:
            response = ai_client.chat(
                system_prompt="你是一个专业的游戏策划和故事分析AI，善于从文本中提取故事要素并生成游戏种子配置。",
                user_prompt=prompt,
            )
            tank = response.split("```json")
            if len(tank) >= 2:
                json_str = tank[1].split("```")[0].strip()
                return json.loads(json_str)
            return json.loads(response)
        except Exception as e:
            raise RuntimeError(f"AI自动生成种子失败: {str(e)}")


def _build_auto_gen_prompt(text_content: str):
    return f"""请分析以下文本内容，提取其中的故事要素，并生成一个游戏种子配置（JSON格式）。

文本内容：
{text_content[:8000]}

请返回如下结构的JSON：
{{
    "name": "故事名称",
    "background": "故事背景简述",
    "genre": "故事类型（如：奇幻、科幻、武侠、悬疑、校园等）",
    "style": "叙事风格",
    "tone": "语调（积极/中性/阴暗等）",
    "elements": ["关键剧情元素1", "关键剧情元素2"],
    "protagonist_setting": {{
        "name": "主角名",
        "gender": "性别",
        "age": "年龄",
        "personality": "性格描述",
        "background": "背景故事",
        "abilities": "能力",
        "appearance": "外貌描述"
    }},
    "world_setting": "世界观设定",
    "moral_requirements": "道德要求",
    "forbidden_content": "禁止内容",
    "ai_tendency": "AI倾向",
    "expected_length": "预期长度",
    "difficulty": "难度",
    "custom_notes": "备注"
}}

只返回JSON，不要其他内容。"""
