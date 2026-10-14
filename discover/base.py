
from abc import ABC, abstractmethod


class PublisherAdapter(ABC):

    @abstractmethod
    def discover(self, doi: str) -> dict:
        """
        Discover article full text and supplementary files.
        """
        pass