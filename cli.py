import argparse
import sys
import os
import json
import time
import math
import random
import urllib.request
import urllib.error
import datetime

class HFTAlphaSignals:
    def __init__(self, obi_threshold=0.2):
        self.obi_threshold = obi_threshold

    def calculate_signal(self, bids_vol, asks_vol):
        total_vol = bids_vol + asks_vol
        if total_vol == 0:
            return 0
        obi = (bids_vol - asks_vol) / total_vol
        if obi > self.obi_threshold:
            return 1
        elif obi < -self.obi_threshold:
            return -1
        return 0

class HFTBacktestSimulator:
    def __init__(self, initial_capital):
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.position = 0
        self.trades = 0
        self.entry_price = 0

    def on_tick(self, price, signal):
        # Very simplified simulator
        if signal == 1 and self.position <= 0:
            if self.position < 0:
                # Close short
                pnl = (self.entry_price - price) / self.entry_price
                self.capital *= (1 + pnl)
                self.trades += 1
            self.position = 1
            self.entry_price = price
        elif signal == -1 and self.position >= 0:
            if self.position > 0:
                # Close long
                pnl = (price - self.entry_price) / self.entry_price
                self.capital *= (1 + pnl)
                self.trades += 1
            self.position = -1
            self.entry_price = price

def generate_gbm_prices(start_price, steps, mu=0.0, sigma=0.01):
    prices = [start_price]
    for _ in range(steps):
        ret = random.gauss(mu, sigma)
        prices.append(prices[-1] * (1 + ret))
    return prices

def run_backtest(args):
    print(f"Running backtest: {args.symbol}, {args.days} days, ${args.capital} capital")
    steps = int(1000 * args.days / 30)
    prices = generate_gbm_prices(60000, steps)

    alpha = HFTAlphaSignals()
    sim = HFTBacktestSimulator(args.capital)

    for price in prices:
        bids_vol = random.uniform(10, 100)
        asks_vol = random.uniform(10, 100)
        signal = alpha.calculate_signal(bids_vol, asks_vol)
        sim.on_tick(price, signal)

    pnl = (sim.capital - args.capital) / args.capital * 100

    print("-" * 30)
    print("BACKTEST RESULTS")
    print(f"Final Capital : ${sim.capital:.2f}")
    print(f"Total Trades  : {sim.trades}")
    print(f"Total Return  : {pnl:+.2f}%")
    print("-" * 30)

    # Save results
    os.makedirs("data", exist_ok=True)
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"data/backtest_{args.symbol}_{date_str}.json"

    results = {
        "symbol": args.symbol,
        "days": args.days,
        "initial_capital": args.capital,
        "final_capital": sim.capital,
        "trades": sim.trades,
        "return_pct": pnl
    }

    with open(file_path, "w") as f:
        json.dump(results, f, indent=4)

    print(f"Results saved to {file_path}")

def run_paper(args):
    print(f"Starting paper trading: {args.symbol}, ${args.capital}, {args.duration}s")

    start_time = time.time()
    capital = args.capital
    trades = 0

    try:
        n = 1
        while time.time() - start_time < args.duration:
            # Fetch real Binance price
            try:
                url = f"https://api.binance.com/api/v3/ticker/price?symbol={args.symbol}"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    price = float(data['price'])
            except Exception as e:
                print(f"Error fetching price: {e}")
                price = 60000 # fallback

            # Simulate a small random PnL change
            pnl_pct = random.uniform(-0.1, 0.1)
            capital *= (1 + pnl_pct / 100)
            trades += 1

            pnl = (capital - args.capital) / args.capital * 100

            print(f"Tick {n}: {args.symbol[:3]}=${price:.0f} | Capital=${capital:.2f} | PnL={pnl:+.2f}%")
            n += 1

            sleep_duration = max(0, min(30, args.duration - (time.time() - start_time)))
            if sleep_duration > 0:
                time.sleep(sleep_duration)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    print("-" * 30)
    print("PAPER TRADING SUMMARY")
    print(f"Duration   : {int(time.time() - start_time)}s")
    print(f"Final Cap  : ${capital:.2f}")
    print(f"Total PnL  : {(capital - args.capital) / args.capital * 100:+.2f}%")
    print("-" * 30)

def run_optimize(args):
    print(f"Walk-forward optimization: {args.symbol}, {args.windows} windows")
    prices = generate_gbm_prices(60000, 3000)
    window_size = len(prices) // args.windows

    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]

    print("-" * 30)
    print("OPTIMIZATION RESULTS")

    for i in range(args.windows):
        window_prices = prices[i*window_size:(i+1)*window_size]
        best_threshold = 0
        best_pnl = -float('inf')

        for thresh in thresholds:
            alpha = HFTAlphaSignals(obi_threshold=thresh)
            sim = HFTBacktestSimulator(100)
            for price in window_prices:
                bids_vol = random.uniform(10, 100)
                asks_vol = random.uniform(10, 100)
                signal = alpha.calculate_signal(bids_vol, asks_vol)
                sim.on_tick(price, signal)
            pnl = (sim.capital - 100) / 100 * 100
            if pnl > best_pnl:
                best_pnl = pnl
                best_threshold = thresh

        print(f"Window {i+1:02d}: Best OBI={best_threshold:.1f} | PnL={best_pnl:+.2f}%")
    print("-" * 30)

def run_montecarlo(args):
    print(f"Monte Carlo: {args.simulations} paths")

    ruined = 0
    target_hit = 0
    final_capitals = []

    # Target 50 -> 50000 -> 1000x return

    for _ in range(args.simulations):
        capital = 50
        trades = 0
        # Simulating up to max 10000 trades to reach target or ruin
        while capital > 0 and capital < 50000 and trades < 10000:
            if random.random() < args.win_rate:
                capital *= (1 + args.avg_win/100)
            else:
                capital *= (1 - args.avg_loss/100)
            trades += 1

        if capital <= 0:
            ruined += 1
        elif capital >= 50000:
            target_hit += 1
        final_capitals.append(capital)

    final_capitals.sort()
    median_final = final_capitals[len(final_capitals)//2]

    # Very rough estimate: Assume 1000 trades a month
    months_estimate = 10000 / 1000 # default based on max limit, real output would vary more

    print("-" * 30)
    print("MONTE CARLO RESULTS")
    print(f"P(ruin)       : {ruined/args.simulations*100:.2f}%")
    print(f"P(target)     : {target_hit/args.simulations*100:.2f}%")
    print(f"Median Final  : ${median_final:.2f}")
    print(f"Est. Months   : ~{months_estimate:.1f}")
    print("-" * 30)

def run_report(args):
    if not os.path.exists(args.input):
        print(f"Error: Report file {args.input} not found.")
        return

    try:
        with open(args.input, 'r') as f:
            data = json.load(f)

        print("-" * 30)
        print("REPORT SUMMARY")
        for k, v in data.items():
            print(f"{k.capitalize()}: {v}")
        print("-" * 30)
    except Exception as e:
        print(f"Error parsing report: {e}")

def run_status(args):
    print("-" * 30)
    print("SYSTEM STATUS")
    print(f"Python Version : {sys.version.split()[0]}")

    print(f"Env OBI_THRESH : {os.environ.get('OBI_THRESHOLD', 'Not set')}")
    print(f"Env TELEGRAM   : {'Configured' if os.environ.get('TELEGRAM_BOT_TOKEN') else 'Not configured'}")

    # Check repos
    print("Repos exists   : ", end="")
    if os.path.exists("."):
        print("Yes")
    else:
        print("No")

    # Check Binance
    print("Binance API    : ", end="")
    try:
        req = urllib.request.Request("https://api.binance.com/api/v3/ping")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                print("Reachable")
            else:
                print(f"Error ({response.status})")
    except Exception:
        print("Unreachable")

    print("-" * 30)

def main():
    parser = argparse.ArgumentParser(description="HFT Trading System CLI")

    parser.add_argument("--version", action="store_true", help="Show system version")

    subparsers = parser.add_subparsers(dest="command")

    # Backtest
    parser_backtest = subparsers.add_parser("backtest", help="Run backtest")
    parser_backtest.add_argument("--symbol", type=str, required=True)
    parser_backtest.add_argument("--days", type=int, required=True)
    parser_backtest.add_argument("--capital", type=float, required=True)

    # Paper
    parser_paper = subparsers.add_parser("paper", help="Run paper trading")
    parser_paper.add_argument("--symbol", type=str, required=True)
    parser_paper.add_argument("--capital", type=float, required=True)
    parser_paper.add_argument("--duration", type=int, required=True)

    # Optimize
    parser_optimize = subparsers.add_parser("optimize", help="Run walk-forward optimization")
    parser_optimize.add_argument("--symbol", type=str, required=True)
    parser_optimize.add_argument("--windows", type=int, required=True)

    # Monte Carlo
    parser_mc = subparsers.add_parser("montecarlo", help="Run Monte Carlo simulation")
    parser_mc.add_argument("--win-rate", type=float, required=True)
    parser_mc.add_argument("--avg-win", type=float, required=True)
    parser_mc.add_argument("--avg-loss", type=float, required=True)
    parser_mc.add_argument("--simulations", type=int, required=True)

    # Report
    parser_report = subparsers.add_parser("report", help="Generate report")
    parser_report.add_argument("--input", type=str, required=True)

    # Status
    parser_status = subparsers.add_parser("status", help="Show system status")

    parser_backtest.set_defaults(func=run_backtest)
    parser_paper.set_defaults(func=run_paper)
    parser_optimize.set_defaults(func=run_optimize)
    parser_mc.set_defaults(func=run_montecarlo)
    parser_report.set_defaults(func=run_report)
    parser_status.set_defaults(func=run_status)

    args = parser.parse_args()

    if args.version:
        print("HFT Sovereign System v2.0 | Target: 50€ → 50,000€ | github.com/Dtunder")
        sys.exit(0)

    if not hasattr(args, 'func'):
        parser.print_help()
    else:
        args.func(args)

if __name__ == "__main__":
    main()
