import math
from dataclasses import dataclass

LOT_SIZE = 100  # IDX trades in lots of 100 shares


@dataclass(frozen=True)
class CostModel:
    """Trading costs as fractions (0.0015 = 0.15%).
       Sample values
    """

    buy_fee: float = 0.0015
    sell_fee: float = 0.0015
    sell_tax: float = 0.001
    slippage: float = 0.0005

    def buy_price(self, price: float) -> float:
        """Price actually paid per share: slippage makes buys slightly worse."""
        return price * (1 + self.slippage)

    def sell_price(self, price: float) -> float:
        """Price actually received per share: slippage makes sells slightly worse."""
        return price * (1 - self.slippage)

    def buy_cost(self, value: float) -> float:
        return value * self.buy_fee

    def sell_cost(self, value: float) -> float:
        return value * (self.sell_fee + self.sell_tax)

NO_COSTS = CostModel(0.0, 0.0, 0.0, 0.0)
DEFAULT_COSTS = CostModel()


def max_affordable_lots(cash: float, price: float, costs: CostModel) -> int:
    """Largest whole number of lots that cash covers, including slippage and buy fee."""
    cost_per_lot = LOT_SIZE * costs.buy_price(price) * (1 + costs.buy_fee)
    if cost_per_lot <= 0 or math.isnan(cost_per_lot):
        return 0
    return max(int(cash / cost_per_lot + 1e-9), 0)