"""
Token 预估工具
使用 tiktoken 估算 API 调用消耗的 token 数量和费用
回退到字符数/4 的粗略估算
"""
try:
    import tiktoken
    _HAS_TIKTOKEN = True
except ImportError:
    _HAS_TIKTOKEN = False

MODEL_PRICING = {
    "deepseek-v4-flash": {"input": 0.14, "output": 0.28},
    "deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek-reasoner": {"input": 0.55, "output": 2.19},
}


def _get_encoder(model: str):
    if not _HAS_TIKTOKEN:
        return None
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        try:
            return tiktoken.get_encoding("cl100k_base")
        except Exception:
            return None


def estimate_tokens(text: str, model: str = "deepseek-v4-flash") -> int:
    encoder = _get_encoder(model)
    if encoder:
        return len(encoder.encode(text))
    return max(1, len(text) // 4)


def estimate_cost(prompt_tokens: int, expected_output_tokens: int = 500,
                  model: str = "deepseek-v4-flash") -> float:
    pricing = MODEL_PRICING.get(model, {"input": 0.14, "output": 0.28})
    input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
    output_cost = (expected_output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


def format_token_info(prompt_text: str, model: str = "deepseek-v4-flash") -> str:
    tokens = estimate_tokens(prompt_text, model)
    cost = estimate_cost(tokens, model=model)
    source = "tiktoken" if _HAS_TIKTOKEN else "估算"
    return f"预计消耗 ~{tokens} tokens ({source})，约 ¥{cost:.4f}"
