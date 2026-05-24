from PyQt5.QtCore import QThread, pyqtSignal


class AIWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    chunk = pyqtSignal(str, str)

    def __init__(self, ai_client, system_prompt, user_prompt, is_stream=True):
        super().__init__()
        self.ai_client = ai_client
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.is_stream = is_stream

    def run(self):
        try:
            if self.is_stream:
                full = ""
                for chunk in self.ai_client.chat_stream(
                    self.system_prompt, self.user_prompt
                ):
                    full += chunk
                    self.chunk.emit(chunk, full)
                self.finished.emit(full)
            else:
                response = self.ai_client.chat(
                    self.system_prompt, self.user_prompt
                )
                self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))
