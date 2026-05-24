"""
异步 AI Worker（基于 qasync + asyncio）
替代 QThread 方案，使用原生 async/await 调用 DeepSeek API
"""
from PyQt5.QtCore import QObject, pyqtSignal
from core.token_counter import format_token_info


class AsyncAIWorker(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    chunk = pyqtSignal(str, str)
    token_info = pyqtSignal(str)

    def __init__(self, ai_client, system_prompt, user_prompt):
        super().__init__()
        self.ai_client = ai_client
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self._task = None

    def start(self, loop):
        self._task = loop.create_task(self._run())

    def cancel(self):
        if self._task:
            self._task.cancel()

    async def _run(self):
        try:
            model = self.ai_client.model
            info = format_token_info(
                self.system_prompt + self.user_prompt, model
            )
            self.token_info.emit(info)

            full = ""
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(
                    api_key=self.ai_client.api_key,
                    base_url=self.ai_client.base_url,
                )
                stream = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": self.user_prompt},
                    ],
                    stream=True,
                )
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        delta = chunk.choices[0].delta.content
                        full += delta
                        self.chunk.emit(delta, full)
            except ImportError:
                response = self.ai_client.chat(
                    self.system_prompt, self.user_prompt
                )
                self.finished.emit(response)
                return

            self.finished.emit(full)
        except Exception as e:
            self.error.emit(str(e))
