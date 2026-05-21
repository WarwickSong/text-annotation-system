import asyncio


class BatchHandle:
    """
    后台批处理的任务句柄。

    通过 async_batch() 启动后台任务后立即返回此句柄，
    调用方可随时查询进度、已完成的中间结果和最终完成状态。

    支持 wait() 等待全部完成后获取结果列表。
    """

    def __init__(self, total: int):
        self._total = total
        self._results: list[dict] = []
        self._errors: list[dict] = []
        self._completed = 0
        self._done = False
        self._lock = asyncio.Lock()
        self._done_event = asyncio.Event()

    @property
    def is_done(self) -> bool:
        return self._done

    @property
    def results(self) -> list[dict]:
        return list(self._results)

    @property
    def errors(self) -> list[dict]:
        return list(self._errors)

    def progress(self) -> tuple[int, int]:
        return self._completed, self._total

    def to_dict(self) -> dict:
        return {
            "is_done": self._done,
            "completed": self._completed,
            "total": self._total,
            "results": list(self._results),
            "errors": list(self._errors),
        }

    async def wait(self) -> list[dict]:
        """
        阻塞等待全部任务完成。

        :return: 所有成功结果的列表
        """
        await self._done_event.wait()
        return list(self._results)

    async def _add(self, index: int, messages: list[dict],
                   answer: str | None = None, error: Exception | None = None):
        """统一的内部入口：写入一条结果（成功或失败），更新计数和完成状态。"""
        async with self._lock:
            if answer is not None:
                self._results.append({"messages": messages, "answer": answer})
            if error is not None:
                self._errors.append({"index": index, "error": str(error)})
            self._completed += 1
            if self._completed >= self._total:
                self._done = True
                self._done_event.set()
