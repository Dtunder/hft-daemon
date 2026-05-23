import os
import sys
import argparse
import subprocess

# Sys.path Bootstrapping:
# Calculate workspace root (2 levels up from this file)
# cli.py is in src/cli.py -> __file__ is /workspace/src/cli.py
# parent is /workspace/src, parent of parent is /workspace
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

def parse_args():
    parser = argparse.ArgumentParser(description="HFT Sovereign System CLI")

    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=["paper", "backtest", "optimize", "montecarlo", "report"],
        help="Betriebsmodus: paper, backtest, optimize, montecarlo, report"
    )

    parser.add_argument(
        "--symbol",
        type=str,
        default="BTCUSDT",
        help="Handelssymbol (default: BTCUSDT)"
    )

    parser.add_argument(
        "--capital",
        type=float,
        default=50.0,
        help="Startkapital (default: 50.0)"
    )

    parser.add_argument(
        "--runtime",
        type=int,
        default=0,
        help="Laufzeit in Sekunden (0=unendlich, default: 0)"
    )

    parser.add_argument(
        "--steps",
        type=int,
        default=1000,
        help="Anzahl der Schritte für backtest/montecarlo (default: 1000)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="report.html",
        help="Pfad für HTML-Report (default: report.html)"
    )

    return parser.parse_args()

def main():
    args = parse_args()

    if args.mode == "paper":
        print(f"Starting paper trading mode for {args.symbol} with capital {args.capital}...")
        main_daemon_path = os.path.join(WORKSPACE_ROOT, "main_daemon.py")
        if not os.path.exists(main_daemon_path):
            print(f"Error: Could not find {main_daemon_path}")
            sys.exit(1)
        # Assuming main_daemon.py can be called. We just use subprocess to execute it.
        # Alternatively, we could try to import and run it if it had a main() function.
        # But subprocess is safer given we don't know the exact args main_daemon.py takes.
        cmd = [sys.executable, main_daemon_path]
        # In a real implementation we might pass args to main_daemon,
        # but the spec doesn't say main_daemon takes them, it just says "Startet main_daemon.py im Paper-Trading-Modus"
        # We will set an env var or pass args as needed if known, for now just execute it.
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    elif args.mode == "backtest":
        print(f"Running backtest for {args.symbol} with {args.steps} steps...")
        backtester_path = os.path.join(WORKSPACE_ROOT, "src", "backtester.py")
        if not os.path.exists(backtester_path):
            print(f"Error: Could not find {backtester_path}")
            sys.exit(1)
        cmd = [sys.executable, backtester_path, "--symbol", args.symbol, "--capital", str(args.capital), "--steps", str(args.steps)]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    elif args.mode == "optimize":
        print("Running walk-forward optimization (Grid Search OBI-Thresholds)...")
        optimizer_path = os.path.join(WORKSPACE_ROOT, "src", "walk_forward.py")
        if not os.path.exists(optimizer_path):
            print(f"Error: Could not find {optimizer_path}")
            sys.exit(1)
        cmd = [sys.executable, optimizer_path, "--symbol", args.symbol]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    elif args.mode == "montecarlo":
        print(f"Running Monte Carlo simulation for Risk of Ruin with {args.steps} steps...")
        mc_path = os.path.join(WORKSPACE_ROOT, "src", "monte_carlo.py")
        if not os.path.exists(mc_path):
            print(f"Error: Could not find {mc_path}")
            sys.exit(1)
        cmd = [sys.executable, mc_path, "--symbol", args.symbol, "--capital", str(args.capital), "--steps", str(args.steps)]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    elif args.mode == "report":
        print(f"Generating HTML report at {args.output}...")
        report_path = os.path.join(WORKSPACE_ROOT, "src", "report_generator.py")
        if not os.path.exists(report_path):
            print(f"Warning: Could not find {report_path}, fallback to generating dummy report.")
            # For this MVP/CLI, we might just write out a dummy if the script doesn't exist
            with open(args.output, "w") as f:
                f.write(f"<html><body><h1>Report for {args.symbol}</h1></body></html>")
            print(f"Report written to {args.output}")
        else:
            cmd = [sys.executable, report_path, "--output", args.output]
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                sys.exit(e.returncode)

if __name__ == "__main__":
    main()
