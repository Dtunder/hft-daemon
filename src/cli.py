import argparse
import sys
import os
import subprocess

# ── Path bootstrap (allow running from workspace root) ──────────────────────
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE, "hft_market_data_feed"))
sys.path.insert(0, os.path.join(WORKSPACE, "hft_alpha_signals"))
sys.path.insert(0, os.path.join(WORKSPACE, "hft_risk_guard"))
sys.path.insert(0, os.path.join(WORKSPACE, "hft_execution_engine"))
sys.path.insert(0, os.path.join(WORKSPACE, "hft_backtest_simulator"))
sys.path.insert(0, os.path.join(WORKSPACE, "hft_performance_metrics"))

def main():
    parser = argparse.ArgumentParser(description="HFT Sovereign Daemon CLI")
    parser.add_argument("mode", choices=["paper", "backtest", "optimize", "montecarlo", "report"], help="Execution mode")

    args = parser.parse_args()

    if args.mode == "paper":
        env = os.environ.copy()
        env["HFT_MODE"] = "paper"
        main_daemon_path = os.path.join(WORKSPACE, "main_daemon.py")
        subprocess.run([sys.executable, main_daemon_path], env=env)

    elif args.mode == "backtest":
        import hft_backtest_simulator
        hft_backtest_simulator.hft_backtest_simulator(steps=1000)

    elif args.mode == "optimize":
        import hft_backtest_simulator
        hft_backtest_simulator.WalkForwardOptimizer()

    elif args.mode == "montecarlo":
        import hft_backtest_simulator
        hft_backtest_simulator.MonteCarloSimulator()

    elif args.mode == "report":
        import hft_performance_metrics
        hft_performance_metrics.PerformanceMetrics.full_report()

if __name__ == "__main__":
    main()
