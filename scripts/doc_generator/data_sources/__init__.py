"""Data source adapters for documentation generator"""
from data_sources.db_adapter import DbAdapter
from data_sources.git_adapter import GitAdapter


def get_adapters(source_names):
    """
    Get adapter instances for specified sources

    Args:
        source_names: List of source names ('db', 'git', 'memory', 'user')

    Returns:
        list: List of adapter instances
    """
    adapter_map = {
        'db': DbAdapter,
        'git': GitAdapter,
        # 'memory': MemoryAdapter,  # Future
        # 'user': UserAdapter,      # Future
    }

    adapters = []
    for name in source_names:
        if name in adapter_map:
            adapters.append(adapter_map[name]())

    return adapters
