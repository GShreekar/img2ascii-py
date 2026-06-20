from abc import ABC, abstractmethod
import numpy as np


class BaseRenderer(ABC):
    """Abstract base class for all renderers."""

    @abstractmethod
    def render(
        self, grid_rgb: np.ndarray, grid_luma: np.ndarray, grid_alpha: np.ndarray
    ) -> str:
        """Render the given sampled grid into a string representation."""
