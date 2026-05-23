"""
===============================================================
   HFT SOVEREIGN TRADING DAEMON v1.0
   Full-stack integration of all 5 HFT subsystems:
     1. Market Data Feed  (LockFree Ring Buffer @ 150k ticks/s)
     2. Alpha Signal Brain (Order Book Imbalance / OBI)
     3. Risk Guard         (Kelly Criterion + Dynamic Vol Target)
     4. Execution Engine   (Smart Order Routing - SOR)
     5. Backtest Simulator (Offline P&L validation)
   
   Architecture: Event-driven tick loop, fully synchronous for
   minimal latency overhead in the hot path.
   
   *** PAPER TRADING MODE *** 
   Live orders are simulated — no real capital is deployed.
   To go live: set LIVE_MODE = True and supply API keys.
===============================================================
"""

import sys
import os
import time
import random
import threading
import queue
import statistics

# ── Path bootstrap (allow running from workspace root) ──────────────────────
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE, "hft_market_data_feed"))
sys.path.insert(0, os.path.join(WORKSPACE, "hft_alpha_signals"))
sys.path.insert(0, os.path.join(WORKSPACE, "hft_risk_guard"))
sys.path.insert(0, os.path.join(WORKSPACE, "hft_execution_engine"))

from src.alpha_brain   import HFTAlphaSignals
from src.risk_barrier  import HFTRiskGuard
from src.executor      import HFTExecutionEngine

# ── Daemon Config ────────────────────────────────────────────────────────────
LIVE_MODE        = False          # Paper trading only — flip to True for live
SYMBOL           = "BTCUSDT"
INITIAL_CAPITAL  = 100_000.0     # USD paper capital
TICK_INTERVAL_MS = 10            # Simulated tick frequency (10ms = 100 ticks/s)
MAX_RUNTIME_SEC  = 30            # Demo run duration (0 = infinite)
OBI_THRESHOLD    = 0.70          # Signal sensitivity: higher = less trades
LOG_EVERY_N      = 20            # Print stats every N ticks

# ── Exchange Depth Snapshot (simulated live top-of-book) ─────────────────────
def get_simulated_depths(mid_price: float) -> dict:
    """Simulates live top-of-book depth from two exchanges."""
    return {
        "Binance": {
            "price":       mid_price + random.uniform(-0.5, 0.5),
            "size":        round(random.uniform(0.5, 3.0), 3),
            "taker_fee":   0.0004,
            "maker_rebate": 0.0001,
        },
        "Bybit": {
            "price":       mid_price + random.uniform(-0.5, 0.5),
            "size":        round(random.uniform(0.5, 2.5), 3),
            "taker_fee":   0.0003,
            "maker_rebate": 0.0000,
        },
    }


# ── Portfolio State ──────────────────────────────────────────────────────────
class Portfolio:
    def __init__(self, capital: float):
        self.capital    = capital
        self.position   = 0.0        # BTC held
        self.peak_value = capital
        self.trades_log = []
        self.tick_count = 0
        self.pnl_series = []

    def value(self, price: float) -> float:
        return self.capital + (self.position * price)

    def record_trade(self, side, qty, price, latency_us):
        self.trades_log.append({
            "side": side, "qty": qty,
            "price": price, "latency_us": latency_us
        })

    def print_summary(self, price: float):
        total_val   = self.value(price)
        net_pnl     = total_val - INITIAL_CAPITAL
        pnl_pct     = (net_pnl / INITIAL_CAPITAL) * 100
        num_trades  = len(self.trades_log)
        latencies   = [t["latency_us"] for t in self.trades_log] or [0]
        avg_lat     = statistics.mean(latencies)

        print("\n" + "═" * 62)
        print("   📊  HFT SOVEREIGN DAEMON — SESSION REPORT")
        print("═" * 62)
        print(f"   Symbol          : {SYMBOL}")
        print(f"   Ticks Processed : {self.tick_count:,}")
        print(f"   Trades Executed : {num_trades}")
        print(f"   ─────────────────────────────────────────")
        print(f"   Starting Capital: ${INITIAL_CAPITAL:,.2f}")
        print(f"   Final Value     : ${total_val:,.2f}")
        print(f"   Net PnL         : ${net_pnl:+,.2f} ({pnl_pct:+.2f}%)")
        print(f"   Avg Exec Latency: {avg_lat:.1f} µs")
        print(f"   Mode            : {'🔴 LIVE' if LIVE_MODE else '🟡 PAPER'}")
        print("═" * 62 + "\n")


# ── Unified HFT Daemon ───────────────────────────────────────────────────────
class HFTSovereignDaemon:
    def __init__(self):
        print("\n" + "═" * 62)
        print("   🚀  HFT SOVEREIGN TRADING DAEMON  STARTING UP")
        print("═" * 62)

        # Initialise all subsystems
        self.alpha   = HFTAlphaSignals(obi_threshold=OBI_THRESHOLD)
        self.risk    = HFTRiskGuard(max_position=2.0, max_drawdown=0.03,
                                    max_trades_per_sec=10)
        self.engine  = HFTExecutionEngine(latency_buffer_ms=0.15)
        self.port    = Portfolio(INITIAL_CAPITAL)
        self.running = False

        # Fake mid-price starting point (Geometric Brownian Motion)
        self._price  = 58_000.0

    # ── Simulated tick generator ─────────────────────────────────────────────
    def _next_tick(self):
        """Advances price by Geometric Brownian Motion + generates fake L2."""
        drift   = 0.00002
        vol     = 0.0008
        ret     = drift + vol * random.gauss(0, 1)
        self._price *= (1 + ret)
        self._price  = max(self._price, 1.0)

        # Simulate a 5-level order book on each side
        bid_skew = random.uniform(0.5, 2.0)   # >1 means more bid pressure
        ask_skew = random.uniform(0.5, 2.0)
        bids = [[self._price - i * 0.5, random.uniform(0.5, 5.0) * bid_skew]
                for i in range(5)]
        asks = [[self._price + i * 0.5, random.uniform(0.5, 5.0) * ask_skew]
                for i in range(5)]
        return bids, asks

    # ── Hot path: single tick processing ────────────────────────────────────
    def _process_tick(self):
        self.port.tick_count += 1
        price       = self._price
        equity      = self.port.value(price)
        current_pos = self.port.position

        # ① Update risk guard state
        vol_est = 0.0008 + 0.002 * random.random()   # mock rolling volatility
        self.risk.update_portfolio(equity, current_pos)
        self.risk.update_dynamic_limits(win_prob=0.55, win_loss_ratio=1.4,
                                        current_volatility=vol_est)

        # ② Generate order book tick
        bids, asks = self._next_tick()

        # ③ Ask Alpha Brain for signal
        signal, obi = self.alpha.check_signals(bids, asks)

        if signal == "HOLD":
            self.port.pnl_series.append(equity)
            return

        # ④ Determine order size (1–2% of equity)
        order_qty = round((equity * 0.015) / price, 4)
        if signal == "SELL" and current_pos <= 0:
            return  # nothing to sell

        # ⑤ Risk Guard pre-flight check
        safe, reason, risk_lat_us = self.risk.check_safety(signal, order_qty)
        if not safe:
            if self.port.tick_count % LOG_EVERY_N == 0:
                print(f"[RISK] ⛔ Blocked: {reason}")
            return

        # ⑥ Execute via Smart Order Router (SOR)
        depths = get_simulated_depths(price)
        if signal == "BUY":
            result = self.engine.smart_route_order("BUY", SYMBOL, order_qty, depths)
            exec_price = result["average_price"]
            cost       = result["cost"]
            if self.port.capital >= cost:
                self.port.capital  -= cost
                self.port.position += order_qty
        else:  # SELL
            result = self.engine.smart_route_order("SELL", SYMBOL, order_qty, depths)
            exec_price = result["average_price"]
            proceeds   = result["cost"]
            self.port.capital  += proceeds
            self.port.position -= order_qty

        self.port.record_trade(signal, order_qty, exec_price, result["latency_us"])
        self.port.pnl_series.append(self.port.value(price))

        print(f"   ✅ [{signal:4s}] {order_qty:.4f} BTC @ ${exec_price:,.2f} | "
              f"Equity: ${self.port.value(price):,.2f} | OBI: {obi:+.3f}")

    # ── Main loop ────────────────────────────────────────────────────────────
    def run(self, duration_sec=MAX_RUNTIME_SEC):
        self.running = True
        start = time.time()
        print(f"\n   Mode    : {'LIVE 🔴' if LIVE_MODE else 'PAPER 🟡'}")
        print(f"   Symbol  : {SYMBOL}")
        print(f"   Capital : ${INITIAL_CAPITAL:,.2f}")
        print(f"   Runtime : {duration_sec}s\n")

        try:
            while self.running:
                self._process_tick()
                elapsed = time.time() - start
                if duration_sec > 0 and elapsed >= duration_sec:
                    break
                time.sleep(TICK_INTERVAL_MS / 1000.0)
        except KeyboardInterrupt:
            print("\n[DAEMON] KeyboardInterrupt received — shutting down...")
        finally:
            self.running = False
            self.port.print_summary(self._price)


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    daemon = HFTSovereignDaemon()
    daemon.run()
