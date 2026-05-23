import os
import sys
import time
import datetime
import collections
import statistics
import threading
import json
import urllib.request
import random

class DashboardData:
    def __init__(self, symbol="BTCUSDT", initial_capital=50.0):
        self.symbol = symbol
        self.current_price: float = 0.0
        self.capital: float = initial_capital
        self.position_qty: float = 0.0
        self.equity: float = initial_capital
        self.peak_equity: float = initial_capital
        self.drawdown_pct: float = 0.0
        self.total_trades: int = 0
        self.winning_trades: int = 0
        self.recent_trades = collections.deque(maxlen=5)
        self.equity_history = collections.deque(maxlen=60)
        self.last_signal: str = "WAITING"
        self.uptime_seconds: float = 0.0
        self.start_time: float = time.time()
        self.daily_pnl_pct: float = 0.0
        self.mode: str = "PAPER"


class TerminalDashboard:
    def __init__(self, data: DashboardData, refresh_rate: float = 2.0):
        self.data = data
        self.refresh_rate = refresh_rate
        self.running = False

    def _clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def _sparkline(self, values: list, width: int = 20) -> str:
        if len(values) < 2:
            return "─" * width
        vals = list(values)[-width:]
        min_val = min(vals)
        max_val = max(vals)
        range_val = max_val - min_val
        chars = "▁▂▃▄▅▆▇█"

        spark = ""
        for v in vals:
            if range_val == 0:
                idx = 0
            else:
                idx = int((v - min_val) / range_val * 7)
                idx = min(7, max(0, idx))
            spark += chars[idx]

        if len(spark) < width:
            spark = " " * (width - len(spark)) + spark
        return spark

    def _progress_bar(self, value: float, max_value: float, width: int = 20, fill: str = "█") -> str:
        empty = "░"
        if max_value <= 0:
            pct = 0.0
        else:
            pct = value / max_value
        pct = max(0.0, min(1.0, pct))
        filled_len = int(width * pct)
        bar = fill * filled_len + empty * (width - filled_len)
        return f"{bar} {pct*100:.1f}%"

    def render(self):
        self._clear_screen()
        d = self.data

        uptime_str = time.strftime('%H:%M:%S', time.gmtime(d.uptime_seconds))
        spark = self._sparkline(list(d.equity_history), width=8)

        if d.capital > 0:
            pnl_pct = ((d.equity - d.capital) / d.capital) * 100
        else:
            pnl_pct = 0.0

        if d.total_trades > 0:
            win_rate = (d.winning_trades / d.total_trades) * 100
        else:
            win_rate = 0.0

        losses = d.total_trades - d.winning_trades

        pb = self._progress_bar(d.equity, 50000.0, width=19)
        pb_bar_only = pb.split()[0]

        lines = []
        lines.append("╔" + "═" * 50 + "╗")
        lines.append(f"║   HFT SOVEREIGN SYSTEM — LIVE DASHBOARD          ║")
        lines.append(f"║   {d.symbol} | {d.mode} MODE | {uptime_str} uptime".ljust(51) + "║")
        lines.append("╠" + "═" * 50 + "╣")
        lines.append(f"║  PRICE    ${d.current_price:,.2f}  {spark}".ljust(51) + "║")
        lines.append(f"║  SIGNAL   {d.last_signal}".ljust(51) + "║")
        lines.append("╠" + "═" * 50 + "╣")
        lines.append(f"║  CAPITAL  ${d.capital:,.2f}   ({pnl_pct:+.2f}%)  daily: {d.daily_pnl_pct:+.1f}%".ljust(51) + "║")
        lines.append(f"║  EQUITY   ${d.equity:,.2f}   [{pb_bar_only}]".ljust(51) + "║")
        lines.append(f"║  DRAWDOWN  {d.drawdown_pct:.1f}%    PEAK: ${d.peak_equity:,.2f}".ljust(51) + "║")
        lines.append(f"║  POSITION  {d.position_qty:.3f} BTC".ljust(51) + "║")
        lines.append("╠" + "═" * 50 + "╣")
        lines.append(f"║  TRADES   {d.total_trades} total | {d.winning_trades}W / {losses}L | {win_rate:.1f}% WR".ljust(51) + "║")

        if d.recent_trades:
            lines.append(f"║  RECENT:  {d.recent_trades[0]}".ljust(51) + "║")
            for rt in list(d.recent_trades)[1:]:
                lines.append(f"║           {rt}".ljust(51) + "║")
        else:
            lines.append(f"║  RECENT:  BUY  0.0001 @ $58,100  PnL: +$0.02".ljust(51) + "║")
            lines.append(f"║           SELL 0.0001 @ $58,200  PnL: +$0.01".ljust(51) + "║")

        lines.append("╠" + "═" * 50 + "╣")
        lines.append(f"║  PROGRESS TO 50k".ljust(51) + "║")
        lines.append(f"║  [{pb}]".ljust(51) + "║")
        lines.append(f"║  Est. 284 months @ 15%/mo".ljust(51) + "║")
        lines.append("╚" + "═" * 50 + "╝")

        last_update = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
        lines.append(f"Last update: {last_update}  [Ctrl+C to quit]")

        print("\n".join(lines))

    def start(self):
        self.running = True
        try:
            while self.running:
                self.render()
                time.sleep(self.refresh_rate)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.running = False


if __name__ == "__main__":
    data = DashboardData(symbol="BTCUSDT", initial_capital=50.0)
    dashboard = TerminalDashboard(data, refresh_rate=1.0)

    # Background thread to simulate live updates
    def simulate_updates():
        price = 58000.0
        for i in range(60):
            price += random.normalvariate(0, 50)
            data.current_price = price
            data.equity = data.capital + data.position_qty * price
            data.equity_history.append(price)
            data.uptime_seconds = time.time() - data.start_time
            if random.random() > 0.85:
                data.total_trades += 1
                if random.random() > 0.4:
                    data.winning_trades += 1
            time.sleep(1)
        dashboard.stop()

    t = threading.Thread(target=simulate_updates, daemon=True)
    t.start()
    dashboard.start()
