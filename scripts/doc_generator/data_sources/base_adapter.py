"""Base adapter class for data sources"""
from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    """Abstract base class for data source adapters"""

    @abstractmethod
    def gather(self, project, args):
        """
        Gather data from this source

        Args:
            project: Project dict from workspace.items
            args: Command-line arguments

        Returns:
            dict: Data gathered from this source
                  Format: {source_name: data_dict}
        """
        pass

    def is_available(self, project, args):
        """
        Check if this data source is available

        Args:
            project: Project dict from workspace.items
            args: Command-line arguments

        Returns:
            bool: True if source is available
        """
        return True
