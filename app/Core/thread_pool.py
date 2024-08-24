from concurrent.futures import ThreadPoolExecutor

_thread_pool = None

def get_thread_pool():
    global _thread_pool
    if _thread_pool is None:
        _thread_pool = ThreadPoolExecutor(max_workers=12)
    return _thread_pool