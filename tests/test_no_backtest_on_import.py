"""Regression test: importing tradingbot must not launch a backtest.

tradingbot.py calls strategy.backtest(...) at module level. As a result any
`import tradingbot` -- test collection, a REPL, another program -- starts a
multi-year Yahoo Finance backtest with the placeholder Alpaca credentials.
The backtest must only run when the file is executed as a script.
"""

import importlib.util
import sys
import types
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_tradingbot_with_stubs():
    """Execute tradingbot.py with its heavy dependencies stubbed out.

    The stub Strategy.backtest records calls, so the returned list tells us
    whether importing the module started a backtest.
    """
    backtest_calls = []

    class Alpaca:
        def __init__(self, *args, **kwargs):
            pass

    class YahooDataBacktesting:
        pass

    class Strategy:
        def __init__(self, *args, **kwargs):
            pass

        def backtest(self, *args, **kwargs):
            backtest_calls.append((args, kwargs))

    class Trader:
        pass

    class REST:
        def __init__(self, *args, **kwargs):
            pass

    stubs = {
        "lumibot": types.ModuleType("lumibot"),
        "lumibot.brokers": types.ModuleType("lumibot.brokers"),
        "lumibot.backtesting": types.ModuleType("lumibot.backtesting"),
        "lumibot.strategies": types.ModuleType("lumibot.strategies"),
        "lumibot.strategies.strategy": types.ModuleType("lumibot.strategies.strategy"),
        "lumibot.traders": types.ModuleType("lumibot.traders"),
        "alpaca_trade_api": types.ModuleType("alpaca_trade_api"),
        "finbert_utils": types.ModuleType("finbert_utils"),
    }
    stubs["lumibot.brokers"].Alpaca = Alpaca
    stubs["lumibot.backtesting"].YahooDataBacktesting = YahooDataBacktesting
    stubs["lumibot.strategies.strategy"].Strategy = Strategy
    stubs["lumibot.strategies"].strategy = stubs["lumibot.strategies.strategy"]
    stubs["lumibot.traders"].Trader = Trader
    stubs["lumibot"].brokers = stubs["lumibot.brokers"]
    stubs["lumibot"].backtesting = stubs["lumibot.backtesting"]
    stubs["lumibot"].strategies = stubs["lumibot.strategies"]
    stubs["lumibot"].traders = stubs["lumibot.traders"]
    stubs["alpaca_trade_api"].REST = REST
    stubs["finbert_utils"].estimate_sentiment = lambda news: (0, "neutral")

    spec = importlib.util.spec_from_file_location(
        "tradingbot_under_test", REPO_ROOT / "tradingbot.py"
    )
    module = importlib.util.module_from_spec(spec)
    saved = {name: sys.modules.get(name) for name in stubs}
    sys.modules.update(stubs)
    try:
        spec.loader.exec_module(module)
    finally:
        for name, value in saved.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value
    return backtest_calls


def test_importing_tradingbot_does_not_start_a_backtest():
    assert _load_tradingbot_with_stubs() == []
