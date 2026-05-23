import json
import datetime
import math
import os

DDL_STAGES = [
    {"stage": 0, "min": 0,     "max": 250,    "label": "Micro"},
    {"stage": 1, "min": 250,   "max": 1000,   "label": "Bootstrap"},
    {"stage": 2, "min": 1000,  "max": 5000,   "label": "Growth"},
    {"stage": 3, "min": 5000,  "max": 15000,  "label": "Scale"},
    {"stage": 4, "min": 15000, "max": 999999, "label": "Target"},
]

class CompoundingEngine:
    def __init__(self, initial_capital: float = 50.0,
                 target_capital: float = 50000.0,
                 state_file: str = "data/compound_state.json"):
        self.capital = initial_capital
        self.target = target_capital
        self.state_file = state_file
        self.stage = 0
        self.monthly_snapshots = []
        self.start_date = datetime.date.today().isoformat()
        self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.capital = data.get("capital", self.capital)
                    self.stage = data.get("stage", self.stage)
                    self.monthly_snapshots = data.get("monthly_snapshots", self.monthly_snapshots)
                    self.start_date = data.get("start_date", self.start_date)
            except Exception as e:
                print(f"Error loading state: {e}")

    def _save_state(self):
        data = {
            "capital": self.capital,
            "stage": self.stage,
            "monthly_snapshots": self.monthly_snapshots,
            "start_date": self.start_date
        }
        try:
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving state: {e}")

    def update_capital(self, new_capital: float) -> dict:
        self.capital = new_capital
        for s in DDL_STAGES:
            if s["min"] <= new_capital < s["max"]:
                self.stage = s["stage"]
                break
        self._save_state()
        return DDL_STAGES[self.stage]

    def record_monthly_snapshot(self):
        today = datetime.date.today().isoformat()
        self.monthly_snapshots.append({
            "date": today,
            "capital": self.capital,
            "stage": self.stage
        })
        self._save_state()

    def project_months_to_target(self, monthly_growth_rate: float = 0.15) -> int:
        if self.capital >= self.target:
            return 0
        if self.capital <= 0:
            return -1 # Avoid math domain error if capital is 0
        n = math.log(self.target / self.capital) / math.log(1 + monthly_growth_rate)
        return math.ceil(n)

    def get_progress_report(self) -> dict:
        next_stage_idx = min(self.stage + 1, len(DDL_STAGES) - 1)
        next_stage_at = DDL_STAGES[next_stage_idx]["min"]

        return {
            "current_capital": self.capital,
            "target_capital": self.target,
            "progress_pct": round(self.capital / self.target * 100, 2),
            "current_stage": self.stage,
            "stage_label": DDL_STAGES[self.stage]["label"],
            "next_stage_at": next_stage_at,
            "months_to_target_15pct": self.project_months_to_target(0.15),
            "months_to_target_20pct": self.project_months_to_target(0.20),
            "months_to_target_30pct": self.project_months_to_target(0.30),
            "snapshots": self.monthly_snapshots[-6:]
        }

    def print_dashboard(self):
        progress_pct = self.capital / self.target
        progress_pct_clamped = min(max(progress_pct, 0.0), 1.0)

        bar_length = 10
        filled_length = int(bar_length * progress_pct_clamped)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)

        pct_display = round(progress_pct * 100, 1)
        stage_label = DDL_STAGES[self.stage]["label"]
        months_to_target = self.project_months_to_target(0.15)

        print(f"{bar} {pct_display}% \u2014 Stage {self.stage} {stage_label} \u2014 {months_to_target} months @ 15%/mo")

if __name__ == "__main__":
    engine = CompoundingEngine(initial_capital=50.0)

    updates = [80, 130, 220, 380, 650, 1100]
    for update in updates:
        engine.update_capital(update)
        engine.record_monthly_snapshot()
        engine.print_dashboard()

    print("\nProgress Report:")
    report = engine.get_progress_report()
    print(json.dumps(report, indent=4))
