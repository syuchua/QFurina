class PluginDependencyManager:
    def __init__(self):
        self.dependencies = {}

    def add_dependency(self, plugin_name, dependency):
        if plugin_name not in self.dependencies:
            self.dependencies[plugin_name] = set()
        self.dependencies[plugin_name].add(dependency)

    def get_dependencies(self, plugin_name):
        return self.dependencies.get(plugin_name, set())

    def resolve_dependencies(self, plugin_name):
        resolved = set()
        self._resolve_dependencies_recursive(plugin_name, resolved)
        return resolved

    def _resolve_dependencies_recursive(self, plugin_name, resolved):
        for dependency in self.get_dependencies(plugin_name):
            if dependency not in resolved:
                self._resolve_dependencies_recursive(dependency, resolved)
        resolved.add(plugin_name)