from dataclasses import dataclass


@dataclass
class AsyncBatchConfig:
    """
    异步批量推理的全局配置。

    所有可调参数集中管理，便于子类化或从配置文件/环境变量读取。
    """

    api_key: str
    """OpenAI 兼容 API 的密钥"""

    base_url: str
    """API 服务地址（如 https://yxai-api.nanfu.com/v1）"""

    model: str
    """使用的模型名称（如 deepseek-chat, gpt-4o-mini）"""

    max_concurrency: int = 10
    """最大并发请求数，控制同时发起的 HTTP 请求上限"""

    timeout: float = 120.0
    """单次请求超时时间，单位秒"""

    max_retries: int = 3
    """请求失败时的最大重试次数"""
