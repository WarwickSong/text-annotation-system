import asyncio
from typing import Optional, List, Dict, Tuple


class BatchHandle:
    """
    后台批处理的任务句柄。

    通过 async_batch() 启动后台任务后立即返回此句柄，
    调用方可随时查询进度、已完成的中间结果和最终完成状态。

    支持 wait() 等待全部完成后获取结果列表。
    """

    def __init__(self, total: int):
        self._total = total
        self._results: List[Optional[Dict]] = [None] * total
        self._errors: List[Dict] = []
        self._completed = 0
        self._done = False
        self._lock = asyncio.Lock()
        self._done_event = asyncio.Event()

    @property
    def is_done(self) -> bool:
        return self._done

    @property
    def results(self) -> List[Dict]:
        return [r for r in self._results if r is not None]

    @property
    def errors(self) -> List[Dict]:
        return list(self._errors)

    def progress(self) -> Tuple[int, int]:
        return self._completed, self._total

    def to_dict(self) -> Dict:
        return {
            "is_done": self._done,
            "completed": self._completed,
            "total": self._total,
            "results": [r for r in self._results if r is not None],
            "errors": list(self._errors),
        }

    async def wait(self) -> List[Dict]:
        """
        阻塞等待全部任务完成。

        :return: 所有成功结果的列表，顺序与输入 prompts 一致
        """
        await self._done_event.wait()
        return [r for r in self._results if r is not None]

    async def _add(self, index: int, messages: List[Dict],
                   answer: Optional[str] = None, error: Optional[Exception] = None):
        """统一的内部入口：写入一条结果（成功或失败），更新计数和完成状态。"""
        async with self._lock:
            if answer is not None:
                self._results[index] = {"messages": messages, "answer": answer}
            if error is not None:
                self._errors.append({"index": index, "error": str(error)})
            self._completed += 1
            if self._completed >= self._total:
                self._done = True
                self._done_event.set()
