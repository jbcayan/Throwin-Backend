import random
from typing import Dict
from gacha.choices import GachaKind

class Gacha:
    # Default probabilities for each gacha kind
    DEFAULT_PROBABILITIES: Dict[GachaKind, float] = {
        GachaKind.GOLD: 0.05,    # 5%
        GachaKind.SILVER: 0.20,  # 20%
        GachaKind.BRONZE: 0.75   # 75%
    }

    def __init__(self, probabilities: Dict[GachaKind, float] = None):
        """
        Initialize the Gacha class with probabilities.
        If no probabilities are provided, use the default probabilities.
        """
        self.probabilities = probabilities or self.DEFAULT_PROBABILITIES
        self._validate_probabilities()

    def _validate_probabilities(self):
        """
        Ensure that the probabilities sum to 1 (or 100%).
        Raises a ValueError if the probabilities are invalid.
        """
        total_probability = sum(self.probabilities.values())
        if not abs(total_probability - 1.0) < 1e-6:  # Account for floating-point inaccuracies
            raise ValueError("Probabilities must sum to 1.")

    def get_random_gacha_kind(self) -> GachaKind:
        """
        Returns a random gacha kind based on the defined probabilities.
        """
        return random.choices(
            list(self.probabilities.keys()),
            weights=list(self.probabilities.values()),
            k=1
        )[0]

    def play(self) -> GachaKind:
        """
        Simulates playing the gacha and returns the result.
        """
        return self.get_random_gacha_kind()