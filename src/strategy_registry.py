import json
import datetime
import os
import hashlib
import copy

DEFAULT_STRATEGIES = {
    "obi_conservative": {
        "description": "Low-risk OBI with tight threshold",
        "signals": ["obi"],
        "params": {"obi_threshold": 0.80, "momentum_window": 4},
        "risk": {"max_drawdown": 0.10, "daily_loss_limit": 0.03,
                 "position_size_pct": 0.01, "leverage": 1.0},
        "target_sharpe": 1.5,
        "min_capital": 50.0
    },
    "obi_aggressive": {
        "description": "Standard OBI momentum strategy",
        "signals": ["obi"],
        "params": {"obi_threshold": 0.70, "momentum_window": 3},
        "risk": {"max_drawdown": 0.20, "daily_loss_limit": 0.05,
                 "position_size_pct": 0.02, "leverage": 1.5},
        "target_sharpe": 1.2,
        "min_capital": 250.0
    },
    "multi_signal": {
        "description": "OBI + VWAP + Funding Rate ensemble",
        "signals": ["obi", "vwap", "funding_rate"],
        "params": {"obi_threshold": 0.72, "vwap_window": 100,
                   "required_votes": 2},
        "risk": {"max_drawdown": 0.15, "daily_loss_limit": 0.04,
                 "position_size_pct": 0.015, "leverage": 2.0},
        "target_sharpe": 1.8,
        "min_capital": 1000.0
    },
    "technical_ensemble": {
        "description": "RSI + MACD + Bollinger Bands",
        "signals": ["rsi", "macd", "bollinger"],
        "params": {"rsi_period": 14, "macd_fast": 12, "macd_slow": 26,
                   "bb_period": 20},
        "risk": {"max_drawdown": 0.12, "daily_loss_limit": 0.04,
                 "position_size_pct": 0.015, "leverage": 1.5},
        "target_sharpe": 1.6,
        "min_capital": 500.0
    },
    "ddl_full": {
        "description": "Full DDL ladder with all signals \u2014 production strategy",
        "signals": ["obi", "vwap", "funding_rate", "rsi", "macd"],
        "params": {"obi_threshold": 0.72, "vwap_window": 100,
                   "rsi_period": 14, "required_votes": 3},
        "risk": {"max_drawdown": 0.20, "daily_loss_limit": 0.05,
                 "position_size_pct": "ddl", "leverage": "ddl"},
        "target_sharpe": 2.0,
        "min_capital": 50.0
    }
}

class StrategyRegistry:
    def __init__(self, registry_file: str = "data/strategy_registry.json"):
        self.registry_file = registry_file
        os.makedirs("data", exist_ok=True)
        self.active_strategy = None
        self.strategies = {}
        self.load()

    def load(self):
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f:
                self.strategies = json.load(f)
        else:
            self.strategies = copy.deepcopy(DEFAULT_STRATEGIES)

    def save(self):
        with open(self.registry_file, 'w') as f:
            json.dump(self.strategies, f, indent=2)

    def list_strategies(self) -> list:
        return [
            {
                "name": name,
                "description": s.get("description", ""),
                "min_capital": s.get("min_capital", 0.0),
                "target_sharpe": s.get("target_sharpe", 0.0),
                "signals": s.get("signals", [])
            }
            for name, s in self.strategies.items()
        ]

    def get_strategy(self, name: str) -> dict:
        if name not in self.strategies:
            raise KeyError(f"Strategy {name} not found.")
        return copy.deepcopy(self.strategies[name])

    def activate_strategy(self, name: str, current_capital: float) -> dict:
        strat = self.get_strategy(name)
        if current_capital < strat.get("min_capital", 0.0):
            raise ValueError(f"Insufficient capital for strategy {name}. Minimum required is {strat.get('min_capital')}")
        self.active_strategy = name
        return strat

    def recommend_strategy(self, capital: float) -> str:
        if capital < 250:
            return "obi_conservative"
        elif capital < 1000:
            return "obi_aggressive"
        elif capital < 5000:
            return "multi_signal"
        elif capital < 15000:
            return "technical_ensemble"
        else:
            return "ddl_full"

    def save_backtest_result(self, strategy_name: str, result: dict):
        if strategy_name not in self.strategies:
            raise KeyError(f"Strategy {strategy_name} not found.")

        today = datetime.date.today().isoformat()
        if "backtest_history" not in self.strategies[strategy_name]:
            self.strategies[strategy_name]["backtest_history"] = []

        history_entry = {
            "date": today,
            "sharpe": result.get("sharpe"),
            "return_pct": result.get("return_pct"),
            "max_dd": result.get("max_dd")
        }
        self.strategies[strategy_name]["backtest_history"].append(history_entry)
        self.save()

    def get_active_config(self) -> dict:
        if self.active_strategy:
            return self.get_strategy(self.active_strategy)
        rec = self.recommend_strategy(50)
        return self.get_strategy(rec)

    def export_for_daemon(self) -> dict:
        config = self.get_active_config()
        flat_config = {
            "strategy": self.active_strategy or self.recommend_strategy(50),
            "signals": config.get("signals", [])
        }
        if "params" in config:
            flat_config.update(config["params"])
        if "risk" in config:
            flat_config.update(config["risk"])
        return flat_config

if __name__ == "__main__":
    reg = StrategyRegistry()
    print("Available strategies:")
    for s in reg.list_strategies():
        print(f"  {s['name']}: {s['description']} | min: \u20ac{s['min_capital']}")

    for capital in [50, 300, 1200, 6000, 20000]:
        rec = reg.recommend_strategy(capital)
        print(f"Capital \u20ac{capital}: \u2192 {rec}")

    config = reg.export_for_daemon()
    print("Active daemon config:", config)
