import logging
from typing import Optional

class EconomyHandler:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.api = None
        try:
            from jweconomy.api.economy_api import EconomyAPI
            self.api = EconomyAPI
        except ImportError:
            self.logger.warning("JWEconomy not found. Economy features will not work.")

    def get_balance(self, player_name: str, currency: str = "coins") -> float:
        if not self.api:
            return 0.0
        return self.api.get_balance(player_name, currency)

    def withdraw(self, player_name: str, amount: float, currency: str = "coins") -> bool:
        if not self.api:
            return False
        return self.api.withdraw(player_name, amount, currency)

    def deposit(self, player_name: str, amount: float, currency: str = "coins") -> bool:
        if not self.api:
            return False
        return self.api.deposit(player_name, amount, currency)
