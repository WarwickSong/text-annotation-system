import asyncio
from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from .config import AsyncBatchConfig
from .handle import BatchHandle


class AsyncBatchInference:
    """
    异步批量推理引擎。

    子类可重写 ask() 和 parse_response() 来定制请求行为：
    - ask()：自定义参数（temperature、system prompt、stream 等）
    - parse_response()：自定义响应解析逻辑

    子类可重写 _build_client() 来定制 httpx 配置、代理等。
    """

    def __init__(self, config: AsyncBatchConfig):
        self.config = config
        self._client: AsyncOpenAI | None = None
        self._semaphore = asyncio.Semaphore(config.max_concurrency)

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def _build_client(self) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )

    async def ask(self, messages: list[dict], **kwargs: Any) -> ChatCompletion:
        async with self._semaphore:
            return await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                **kwargs,
            )

    def parse_response(self, response: ChatCompletion) -> str:
        return response.choices[0].message.content

    async def single(self, messages: list[dict], **kwargs: Any) -> dict:
        response = await self.ask(messages, **kwargs)
        return {
            "messages": messages,
            "answer": self.parse_response(response),
        }

    async def batch(self, prompts: list[list[dict]], **kwargs: Any) -> list[dict]:
        """
        批量并发请求（阻塞版）。

        等全部完成后返回结果列表。
        内部基于 async_batch() 实现。
        """
        handle = await self.async_batch(prompts, **kwargs)
        return await handle.wait()

    async def async_batch(self, prompts: list[list[dict]], **kwargs: Any) -> BatchHandle:
        """
        后台批量推理（非阻塞版）。

        启动后立即返回 BatchHandle，任务在后台逐条执行，
        结果实时写入 handle。调用方可通过 handle 查询进度和中间结果。

        :param prompts: 多个 messages 列表的列表
        :param kwargs: 透传给 single() 的额外参数
        :return: BatchHandle 句柄（可查进度、取结果、等待完成）
        """
        handle = BatchHandle(total=len(prompts))

        async def _run_one(index: int, prompt: list[dict]):
            try:
                result = await self.single(prompt, **kwargs)
                await handle._add(index, prompt, answer=result["answer"])
            except Exception as e:
                await handle._add(index, prompt, error=e)

        for i, prompt in enumerate(prompts):
            asyncio.create_task(_run_one(i, prompt))

        return handle
