import time

class PluginMonitor:
    def __init__(self):
        self.execution_times = {}

    async def measure_execution_time(self, plugin_name, coroutine):
        start_time = time.time()
        result = await coroutine
        end_time = time.time()
        execution_time = end_time - start_time
        
        if plugin_name not in self.execution_times:
            self.execution_times[plugin_name] = []
        self.execution_times[plugin_name].append(execution_time)
        
        return result

    def get_average_execution_time(self, plugin_name):
        times = self.execution_times.get(plugin_name, [])
        if times:
            return sum(times) / len(times)
        return 0
