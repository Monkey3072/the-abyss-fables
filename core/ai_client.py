"""
DeepSeek AI 客户端模块
管理API连接、模型调用、流式输出等功能
"""
import json
from openai import OpenAI


class AIClient:
    def __init__(self, api_key: str = "", base_url: str = "https://api.deepseek.com", model: str = "deepseek-v4-flash"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not self.api_key:
                raise ValueError("API密钥未设置，请在设置中配置")
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def reset_client(self):
        self._client = None

    def update_config(self, api_key: str = "", base_url: str = "", model: str = ""):
        if api_key:
            self.api_key = api_key
        if base_url:
            self.base_url = base_url
        if model:
            self.model = model
        self.reset_client()

    def chat(self, system_prompt: str, user_prompt: str, stream: bool = False):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                stream=stream,
            )
            if stream:
                return self._stream_response(response)
            else:
                return response.choices[0].message.content
        except Exception as e:
            raise AIRequestError(f"AI请求失败: {str(e)}")

    def chat_stream(self, system_prompt: str, user_prompt: str):
        return self.chat(system_prompt, user_prompt, stream=True)

    def _stream_response(self, response):
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def test_connection(self):
        try:
            resp = self.chat(
                system_prompt="你是一个测试助手",
                user_prompt="回复'连接成功'",
                stream=False,
            )
            return True, resp
        except Exception as e:
            return False, str(e)


class AIRequestError(Exception):
    pass
