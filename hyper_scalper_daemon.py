"""
===============================================================
   HFT HYPER-SCALPER DAEMON v1.0
   [DEGEN SNIPER EDITION: From $0.50 to $50,000]
   
   Features:
     1. 100x Leverage Margin Trading Simulation.
     2. 100% Exponential Reinvestment (Full Compound).
     3. Micro-second Order Flow Imbalance (OFI) Sniping.
     4. Real-time Liquidation & Margin Call Risk Engine.
     5. Advanced High-Frequency Spreads Hunting.
     
   This script simulates the extreme, high-risk compounding
   math required to scale pocket change into a massive fortune,
   showcasing the exact mathematical threshold between extreme
   success and instant ruin (Gambler's Ruin theorem).
===============================================================
"""

import sys
import os
import time
import random
import statistics

# ── Path bootstrap ────────────────────────────────────────────────────────────
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE, "hft_market_data_feed"))
sys.path.insert(0, os.path.join(WORKSPACE, "hft_alpha_signals"))
sys.path.insert(0, os.path.join(WORKSPACE, "hft_risk_guard"))
sys.path.insert(0, os.path.join(WORKSPACE, "hft_execution_engine"))

from src.alpha_brain   import HFTAlphaSignals
from src.risk_barrier  import HFTRiskGuard
from src.executor      import HFTExecutionEngine

# ── Hyper-Scalper Config ──────────────────────────────────────────────────────
START_CAPITAL     = 50.0          # Starting with 50 dollars!
TARGET_CAPITAL    = 50000.0       # Target: $50,000!
LEVERAGE          = 100.0         # 100x Leverage!
TICK_INTERVAL_MS  = 1             # Hyper-speed ticks (1ms)
OBI_THRESHOLD     = 0.60          # Hyper-sensitive OBI signals
MAKER_REBATE_MODE = True          # Capture rebates to offset high leverage costs
MAX_TICKS         = 50000         # Maximum ticks for the run

class HyperScalperDaemon:
    def __init__(self):
        print("\n" + "🔥" * 31)
        print("   ⚔️  HFT HYPER-SCALPER DAEMON — DEGEN SNIPER 100X")
        print("🔥" * 31)

        self.alpha = HFTAlphaSignals(obi_threshold=OBI_THRESHOLD)
        self.engine = HFTExecutionEngine(latency_buffer_ms=0.01) # Sub-millisecond latency
        
        # Portfolio State
        self.capital = START_CAPITAL
        self.position = 0.0          # Active position in BTC
        self.avg_entry_price = 0.0
        self.trades_executed = 0
        self.wins = 0
        self.losses = 0
        
        self.price = 60000.0         # Starting mid-price
        self.peak_capital = START_CAPITAL
        self.liquidated = False

    def get_leverage_tier(self):
        """Dynamic De-leveraging (DDL): Reduces leverage as capital grows to avoid Gambler's Ruin."""
        if self.capital < 10.0:
            return 100.0   # Degen bootstrap phase
        elif self.capital < 100.0:
            return 50.0    # Growth phase
        elif self.capital < 1000.0:
            return 25.0    # Scale-up phase
        elif self.capital < 10000.0:
            return 10.0    # Institutional phase
        else:
            return 3.0     # Wealth protection phase

    def get_liquidation_price(self, side, leverage):
        """Calculates liquidation price based on dynamic leverage tier."""
        maintenance_margin = 0.005 # 0.5%
        if side == "BUY":
            return self.avg_entry_price * (1 - (1/leverage) + maintenance_margin)
        else:
            return self.avg_entry_price * (1 + (1/leverage) - maintenance_margin)

    def _next_tick(self):
        """Simulates realistic HFT market microstructure: Order Book Imbalance drives price changes!"""
        if not hasattr(self, 'current_bias'):
            self.current_bias = 0.0
            
        # Simulate high-frequency institutional block orders driving imbalances
        if random.random() < 0.18:
            self.current_bias = random.choice([-3.0, 3.0])
        else:
            self.current_bias *= 0.75  # Decay bias towards equilibrium
            
        bid_skew = random.uniform(0.5, 1.8) + max(0, self.current_bias)
        ask_skew = random.uniform(0.5, 1.8) + max(0, -self.current_bias)
        
        # High-density book levels
        bids = [[self.price - i*0.1, random.uniform(2, 8) * bid_skew] for i in range(5)]
        asks = [[self.price + i*0.1, random.uniform(2, 8) * ask_skew] for i in range(5)]
        
        # Price impact model: Order book pressure directly causes price movement
        total_bids = sum(b[1] for b in bids)
        total_asks = sum(a[1] for a in asks)
        obi = (total_bids - total_asks) / (total_bids + total_asks + 1e-9)
        
        vol = 0.00045  # Standard tick volatility
        change = self.price * vol * (obi + random.gauss(0, 0.1))
        self.price += change
        self.price = max(self.price, 1.0)
        
        return bids, asks

    def run(self):
        print(f"\n   🚀 Starting with        : ${self.capital:.2f}")
        print(f"   🎯 Target Capital        : ${TARGET_CAPITAL:,.2f}")
        print(f"   🛡️ Risk Management Active: Dynamic De-leveraging (DDL) + Trailing Stop-Loss\n")
        
        tick = 0
        trailing_stop_pct = 0.0035  # 0.35% trailing stop to protect profits
        peak_trade_price = 0.0
        lowest_trade_price = 999999.0
        
        while self.capital > 0.01 and self.capital < TARGET_CAPITAL and tick < MAX_TICKS:
            tick += 1
            bids, asks = self._next_tick()
            
            # Determine dynamic leverage tier for this tick
            leverage = self.get_leverage_tier()
            
            # 1. Check Trailing Stop-Loss & Liquidation Risk
            if self.position > 0:
                # Update peak price for trailing stop
                if self.price > peak_trade_price:
                    peak_trade_price = self.price
                
                # Check Trailing Stop
                stop_price = peak_trade_price * (1 - trailing_stop_pct)
                liq_price = self.get_liquidation_price("BUY", leverage)
                
                if self.price <= stop_price:
                    pnl = (stop_price - self.avg_entry_price) * self.position
                    self.capital += pnl
                    self.position = 0.0
                    if pnl > 0: self.wins += 1
                    else: self.losses += 1
                    print(f"🛡️ [TRAILING STOP] Triggered Long Stop-Loss at ${stop_price:,.2f}! Locked PnL: ${pnl:+.4f} | Capital: ${self.capital:,.2f}")
                elif self.price <= liq_price:
                    print(f"💀 [LIQUIDATION] Price dropped to ${self.price:,.2f}! Liquidated 100x Long at ${liq_price:,.2f}!")
                    self.capital = 0.0
                    self.position = 0.0
                    self.liquidated = True
                    break
                    
            elif self.position < 0:
                # Update lowest price for trailing stop
                if self.price < lowest_trade_price:
                    lowest_trade_price = self.price
                
                # Check Trailing Stop
                stop_price = lowest_trade_price * (1 + trailing_stop_pct)
                liq_price = self.get_liquidation_price("SELL", leverage)
                
                if self.price >= stop_price:
                    pnl = (self.avg_entry_price - stop_price) * abs(self.position)
                    self.capital += pnl
                    self.position = 0.0
                    if pnl > 0: self.wins += 1
                    else: self.losses += 1
                    print(f"🛡️ [TRAILING STOP] Triggered Short Stop-Loss at ${stop_price:,.2f}! Locked PnL: ${pnl:+.4f} | Capital: ${self.capital:,.2f}")
                elif self.price >= liq_price:
                    print(f"💀 [LIQUIDATION] Price spiked to ${self.price:,.2f}! Liquidated 100x Short at ${liq_price:,.2f}!")
                    self.capital = 0.0
                    self.position = 0.0
                    self.liquidated = True
                    break

            # 2. Analyze Alpha signals
            signal, obi = self.alpha.check_signals(bids, asks)
            
            # Reinvest 100% of capital using dynamic leverage tier
            margin_qty = (self.capital * leverage) / self.price
            
            if signal == "BUY" and self.position <= 0:
                # Close Short first
                if self.position < 0:
                    fee = abs(self.position) * self.price * 0.00055
                    self.capital -= fee
                    pnl = (self.avg_entry_price - self.price) * abs(self.position)
                    self.capital += pnl
                    self.position = 0.0
                    if pnl > 0: self.wins += 1
                    else: self.losses += 1
                
                # Open Long
                if self.capital > 0.01:
                    fee = margin_qty * self.price * 0.00055
                    self.capital -= fee
                    self.avg_entry_price = self.price
                    self.position = margin_qty
                    self.trades_executed += 1
                    peak_trade_price = self.price
                    print(f"🔥 [{leverage:.0f}X LONG] Sniped {margin_qty:.6f} BTC @ ${self.price:,.2f} | Fee: ${fee:.2f} | Margin: ${self.capital:.4f}")
            
            elif signal == "SELL" and self.position >= 0:
                # Close Long first
                if self.position > 0:
                    fee = self.position * self.price * 0.00055
                    self.capital -= fee
                    pnl = (self.price - self.avg_entry_price) * self.position
                    self.capital += pnl
                    self.position = 0.0
                    if pnl > 0: self.wins += 1
                    else: self.losses += 1
                
                # Open Short
                if self.capital > 0.01:
                    fee = margin_qty * self.price * 0.00055
                    self.capital -= fee
                    self.avg_entry_price = self.price
                    self.position = -margin_qty
                    self.trades_executed += 1
                    lowest_trade_price = self.price
                    print(f"🔥 [{leverage:.0f}X SHORT] Sniped {margin_qty:.6f} BTC @ ${self.price:,.2f} | Fee: ${fee:.2f} | Margin: ${self.capital:.4f}")
            
            
            # Print milestones
            if self.capital > self.peak_capital:
                self.peak_capital = self.capital
                if self.capital > 10.0 and self.capital < 50000.0:
                    print(f"🏆 [MILESTONE] scaled account to: ${self.capital:,.2f}!")

            time.sleep(TICK_INTERVAL_MS / 1000.0)

        # Session End Report
        print("\n" + "═" * 62)
        print("   📊  HYPER-SCALPER 100X — DEGEN SESSION REPORT")
        print("═" * 62)
        print(f"   Starting Capital : ${START_CAPITAL:.2f}")
        print(f"   Final Capital    : ${self.capital:,.2f}")
        print(f"   Trades Executed  : {self.trades_executed}")
        print(f"   Wins / Losses    : {self.wins} Wins / {self.losses} Losses")
        print(f"   Win Rate         : {(self.wins / (self.wins + self.losses + 1e-9)) * 100:.2f}%")
        print(f"   Status           : {'💀 LIQUIDATED (RECKT)' if self.liquidated else '🏆 SUCCESSFUL COMPUTE'}")
        print("═" * 62 + "\n")

if __name__ == "__main__":
    scalper = HyperScalperDaemon()
    scalper.run()
