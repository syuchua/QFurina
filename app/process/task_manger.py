import asyncio
from ..logger import logger

class TaskManager:
    def __init__(self, num_workers=10):
        self.task_queue = asyncio.Queue()
        self.num_workers = num_workers
        self.workers = []

    async def start(self):
        self.workers = [asyncio.create_task(self._worker()) for _ in range(self.num_workers)]
        # logger.info(f"Task manager started with {self.num_workers} workers")

    async def stop(self):
        await self.task_queue.join()
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)

    async def _worker(self):
        while True:
            task = await self.task_queue.get()
            try:
                await task
            except Exception as e:
                logger.error(f"Error processing task: {e}")
            finally:
                self.task_queue.task_done()

    async def add_task(self, task):
        await self.task_queue.put(task)

task_manager = TaskManager()