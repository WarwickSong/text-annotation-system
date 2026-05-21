# Async Batch Inference

基于 OpenAI SDK 的异步批量推理工具包。提供**阻塞式**（`batch`）和**非阻塞式**（`async_batch`）两套模式，配合信号量限流，适用于实时展示进度、对接外部系统等场景。

## 快速开始

```python
import asyncio
from async_batch_inference import AsyncBatchConfig, AsyncBatchInference

# 1. 配置
config = AsyncBatchConfig(
    api_key="sk-xxx",
    base_url="https://api.openai.com/v1",
    model="gpt-4o-mini",
)

# 2. 初始化引擎
engine = AsyncBatchInference(config)

# 3. 准备数据（每个元素是一个 messages 列表）
prompts = [
    [{"role": "user", "content": "What is the capital of France?"}],
    [{"role": "user", "content": "Explain Python in one sentence."}],
    [{"role": "user", "content": "What is 2+2?"}],
]

# 4. 阻塞式批量推理 — 等全部完成后返回结果
results = asyncio.run(engine.batch(prompts))
for r in results:
    print(r["answer"])

# 5. 非阻塞式批量推理 — 立即返回句柄，实时查进度
async def main():
    handle = await engine.async_batch(prompts)

    while not handle.is_done:
        done, total = handle.progress()
        print(f"进度: {done}/{total}, 已产出 {len(handle.results)} 条结果")
        await asyncio.sleep(1)

    for r in handle.results:
        print(r["answer"])

asyncio.run(main())
```

## 目录结构

```
async_batch_inference/
├── __init__.py          # 统一导出
├── config.py            # AsyncBatchConfig 配置类
├── inference.py         # AsyncBatchInference 核心引擎
├── handle.py            # BatchHandle 后台任务句柄
├── prompt_manager.py    # PromptManager 提示词模板工具
└── README.md
```

## API 参考

### AsyncBatchConfig

集中管理全部配置：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `api_key` | `str` | — | API 密钥 |
| `base_url` | `str` | — | API 地址（如 `https://yxai-api.nanfu.com/v1`） |
| `model` | `str` | — | 模型名称（如 `deepseek-chat`, `gpt-4o-mini`） |
| `max_concurrency` | `int` | `10` | 最大并发数 |
| `timeout` | `float` | `120.0` | 单次请求超时（秒） |
| `max_retries` | `int` | `3` | 失败重试次数 |

### AsyncBatchInference

核心引擎，方法分四个层次：

| 方法 | 返回值 | 说明 | 子类可重写 |
|------|--------|------|:---------:|
| `ask(messages, **kwargs)` | `ChatCompletion` | 发送原始请求（受并发限流） | ✅ |
| `parse_response(response)` | `str` | 从响应提取文本 | ✅ |
| `_build_client()` | `AsyncOpenAI` | 构建底层客户端（可注入代理/httpx） | ✅ |
| `single(messages, **kwargs)` | `dict` | 请求 + 解析 | — |
| `batch(prompts, **kwargs)` | `list[dict]` | 阻塞式批量请求 | — |
| `async_batch(prompts, **kwargs)` | `BatchHandle` | 非阻塞式后台批量请求 | — |

### BatchHandle

非阻塞模式返回的句柄，用于查询进度和结果：

| 属性/方法 | 类型 | 说明 |
|-----------|------|------|
| `is_done` | `property` | 是否全部处理完毕 |
| `results` | `property` | 已完成结果列表（返回副本） |
| `errors` | `property` | 错误列表（返回副本） |
| `progress()` | `(int, int)` | `(已完成, 总数)` |
| `to_dict()` | `dict` | 序列化为字典，用于外部系统对接 |
| `wait()` | `list[dict]` | 阻塞等待全部完成，返回结果列表 |

### PromptManager

独立工具类，用于管理提示词模板：

```python
from async_batch_inference import PromptManager

pm = PromptManager(template="用{language}回答：{question}")
prompt = pm.format_prompt(language="中文", question="What is AI?")
# → "用中文回答：What is AI?"
```

## 使用场景

### 阻塞式批量（`batch`）

最简单的方式，等全部完成拿到结果：

```python
results = await engine.batch(prompts)
```

内部实现 = `async_batch()` + `handle.wait()`，与下面等价：

```python
handle = await engine.async_batch(prompts)
results = await handle.wait()
```

### 非阻塞式批量（`async_batch`）

适合需要**实时展示进度**或**对接外部系统**的场景：

```python
handle = await engine.async_batch(prompts)

# 随时查询进度和中间结果
done, total = handle.progress()      # e.g. (3, 10)
partial = handle.results             # 已完成的 3 条
d = handle.to_dict()                 # 序列化为 JSON 响应

# 对接 REST API 轮询
@app.get("/batch/{task_id}")
async def status(task_id: str):
    return task_store[task_id].to_dict()

# 对接 WebSocket 推送
while not handle.is_done:
    await ws.send_json(handle.to_dict())
    await asyncio.sleep(1)
```

### 子类化扩展

通过重写 `ask()`、`parse_response()`、`_build_client()` 自定义行为：

```python
class MyEngine(AsyncBatchInference):
    def _build_client(self):
        # 自定义 httpx 配置（代理、证书等）
        import httpx
        return AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            http_client=httpx.AsyncClient(proxy="http://proxy:8080"),
        )

    async def ask(self, messages, **kwargs):
        # 统一注入 system prompt，固定 temperature
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            *messages,
        ]
        return await super().ask(messages, temperature=0.3, **kwargs)

    def parse_response(self, response):
        # 返回所有 choices 的文本
        return [c.message.content for c in response.choices]
```

### 透传 API 参数

所有 `**kwargs` 会透传到 OpenAI `chat.completions.create`：

```python
results = await engine.batch(prompts, temperature=0.8, top_p=0.9, max_tokens=200)
```

### 调整并发上限

```python
config = AsyncBatchConfig(
    ...,
    max_concurrency=5,  # 同时最多 5 个请求通过信号量
)
```

## 并发控制原理

通过 `asyncio.Semaphore` 实现令牌桶限流：

```
asyncio.gather 创建 N 个协程
         │
         ▼
每个协程进入 ask() → async with semaphore
         │
    ┌────┴────┐
    │ 有空位？   │
    └────┬────┘
     Yes │  No → 排队等待
         │
    chat.completions.create()
         │
    完成 → release() → 下一个进入
```

请求在 `ask()` 方法入口排队，确保同时只有 `max_concurrency` 个 HTTP 连接。

## 设计原则

- **单一入口** — `async_batch()` 是底层实现，`batch()` 是其阻塞包裹
- **Handle 自治** — `_add()` 是唯一的状态写入点，外部无需知道内部锁和计数逻辑
- **子类化优先** — 3 个 hooks（`ask`、`parse_response`、`_build_client`）覆盖主要定制场景
- **不可变出口** — `results`、`errors`、`to_dict()` 都返回副本，避免外部意外修改
