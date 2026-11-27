import pytest

from idxlab.backtest.costs import NO_COSTS, CostModel, max_affordable_lots


def test_slippage_makes_prices_worse():
    c = CostModel(slippage=0.01)
    assert c.buy_price(1000) == pytest.approx(1010)
    assert c.sell_price(1000) == pytest.approx(990)


def test_sell_cost_includes_fee_and_tax():
    c = CostModel(buy_fee=0.001, sell_fee=0.002, sell_tax=0.001, slippage=0)
    assert c.buy_cost(100_000) == pytest.approx(100)
    assert c.sell_cost(100_000) == pytest.approx(300)


def test_lots_round_down_and_leave_cash():
    # 250,000 buys 2.5 lots at 1,000 per share -> 2 lots
    assert max_affordable_lots(250_000, 1000, NO_COSTS) == 2
    assert max_affordable_lots(99_999, 1000, NO_COSTS) == 0


def test_lots_account_for_buy_fee():
    c = CostModel(buy_fee=0.01, sell_fee=0, sell_tax=0, slippage=0)
    # 1 lot costs 100,000 * 1.01 = 101,000, so 100,500 only buys 0 lots
    assert max_affordable_lots(100_500, 1000, c) == 0
    assert max_affordable_lots(101_000, 1000, c) == 1