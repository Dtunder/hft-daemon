import os
import json
import urllib.request
import urllib.parse
import threading
from datetime import datetime

class TelegramNotifier:
    def __init__(self, bot_token: str = None, chat_id: str = None, enabled: bool = True):
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")
        self.enabled = enabled and bool(self.bot_token) and bool(self.chat_id)
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.message_queue = []
        self._sent_count = 0

    def _send(self, text: str) -> bool:
        if not self.enabled:
            return False

        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get("ok"):
                    self._sent_count += 1
                    return True
                return False
        except Exception:
            return False

    def send_trade_alert(self, side: str, symbol: str, price: float, qty: float, pnl: float = None, capital_after: float = None):
        side_emoji = "📈" if side.upper() == "BUY" else "📉"
        lines = [
            "<b>HFT TRADE</b>",
            f"{side_emoji} {side} {qty:.6f} {symbol}",
            f"Price: <code>${price:,.2f}</code>"
        ]

        if pnl is not None:
            color_emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
            lines.append(f"{color_emoji} PnL: <code>${pnl:+.4f}</code>")

        if capital_after is not None:
            lines.append(f"Capital: <code>${capital_after:,.2f}</code>")

        return self._send("\n".join(lines))

    def send_daily_summary(self, date: str, starting_capital: float, ending_capital: float, total_trades: int, win_rate: float, best_trade_pnl: float, worst_trade_pnl: float):
        day_emoji = "✅" if ending_capital > starting_capital else "❌"
        lines = [
            f"{day_emoji} <b>Daily Summary: {date}</b>",
            f"Trades: {total_trades}",
            f"Win Rate: {win_rate:.1%}",
            f"Best Trade: <code>${best_trade_pnl:+.2f}</code>",
            f"Worst Trade: <code>${worst_trade_pnl:+.2f}</code>",
            f"Starting Capital: <code>${starting_capital:,.2f}</code>",
            f"Ending Capital: <code>${ending_capital:,.2f}</code>"
        ]
        return self._send("\n".join(lines))

    def send_risk_alert(self, reason: str, capital: float, drawdown_pct: float):
        message = f"⚠️ RISK ALERT\n{reason}\nCapital: ${capital:.2f}\nDrawdown: {drawdown_pct:.1f}%"
        return self._send(message)

    def send_system_message(self, message: str):
        return self._send(message)

    def send_startup_message(self, symbol: str, capital: float, mode: str):
        message = f"🚀 HFT Daemon Started\nSymbol: {symbol}\nCapital: ${capital:.2f}\nMode: {mode}"
        return self._send(message)

    def test_connection(self) -> bool:
        return self._send("🔧 Test message from HFT Daemon")

if __name__ == "__main__":
    notifier = TelegramNotifier()
    if notifier.enabled:
        notifier.test_connection()
        notifier.send_startup_message("BTCUSDT", 50.0, "PAPER")
        notifier.send_trade_alert("BUY", "BTCUSDT", 58000.0, 0.001, capital_after=50.58)
        notifier.send_daily_summary("2026-05-23", 50.0, 52.3, 15, 0.6, 1.2, -0.4)
    else:
        print("Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
        print("Bot would send: startup, trade alert, daily summary")
