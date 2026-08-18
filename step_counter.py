# step_counter.py
#!/usr/bin/env python3
"""
🚶 Step Counter – Walk Tracker Without GPS (Python Edition)
Features: manual step log, daily goal, history chart, auto-simulation, statistics
"""

import json
import os
import sys
import random
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, IntPrompt, Confirm
    from rich import box
    from rich.progress import Progress, BarColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Install 'rich' for enhanced UI: pip install rich")


# ─── Colors ──────────────────────────────────────────────────────────────────

def c(text: str, color: str) -> str:
    colors = {
        "reset": "\033[0m", "bright": "\033[1m", "dim": "\033[2m",
        "red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m",
        "blue": "\033[34m", "magenta": "\033[35m", "cyan": "\033[36m"
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"


# ─── Data Manager ──────────────────────────────────────────────────────────

class StepCounter:
    DATA_DIR = Path.home() / ".step_counter"
    DATA_FILE = DATA_DIR / "data.json"
    DEFAULT_GOAL = 10000

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.data = self._load()
        self.goal = self.data.get("goal", self.DEFAULT_GOAL)
        self.entries: List[Dict] = self.data.get("entries", [])
        self._auto_running = False

    def _load(self) -> Dict:
        if self.DATA_FILE.exists():
            try:
                with open(self.DATA_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self) -> None:
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        data = {"goal": self.goal, "entries": self.entries}
        with open(self.DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def _today(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def _get_today_entry(self) -> Optional[Dict]:
        today = self._today()
        for e in self.entries:
            if e.get("date") == today:
                return e
        return None

    def _get_today_steps(self) -> int:
        entry = self._get_today_entry()
        return entry.get("steps", 0) if entry else 0

    def _get_last_n_days(self, n: int = 7) -> List[Dict]:
        today = datetime.now().date()
        result = []
        for i in range(n):
            d = today - timedelta(days=i)
            date_str = d.strftime("%Y-%m-%d")
            steps = 0
            for e in self.entries:
                if e.get("date") == date_str:
                    steps = e.get("steps", 0)
                    break
            result.append({"date": date_str, "steps": steps})
        result.reverse()
        return result

    def _progress_bar(self, current: int, goal: int, width: int = 20) -> str:
        if goal <= 0:
            return "⚠️  Goal not set"
        ratio = min(current / goal, 1.0)
        filled = int(ratio * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {ratio*100:.1f}%"

    def add_steps(self, steps: int) -> None:
        if steps <= 0:
            print(c("❌ Steps must be positive!", "red"))
            return
        today = self._today()
        entry = self._get_today_entry()
        if entry:
            entry["steps"] += steps
        else:
            self.entries.append({
                "date": today,
                "steps": steps,
                "timestamp": datetime.now().isoformat()
            })
        self._save()
        total = self._get_today_steps()
        if self.console:
            self.console.print(f"[green]✅ Added {steps} steps (Total today: {total})[/green]")
            if total >= self.goal:
                self.console.print("[bold cyan]🎉 Goal achieved! Keep walking! 💪[/bold cyan]")
        else:
            print(c(f"✅ Added {steps} steps (Total today: {total})", "green"))
            if total >= self.goal:
                print(c("🎉 Goal achieved! Keep walking! 💪", "cyan"))

    def show_today(self) -> None:
        steps = self._get_today_steps()
        if self.console:
            panel = Panel(
                f"[bold]🚶 Today's Steps[/bold]\n"
                f"  Goal: {self.goal}\n"
                f"  Steps: {steps}\n"
                f"  Remaining: {max(self.goal - steps, 0)}\n"
                f"  Progress: {self._progress_bar(steps, self.goal)}",
                title="📊 Daily Progress",
                border_style="cyan"
            )
            self.console.print(panel)
        else:
            print("\n" + "="*50)
            print(c("🚶 TODAY'S STEPS", "bright"))
            print("="*50)
            print(f"  Goal:      {self.goal}")
            print(f"  Steps:     {steps}")
            print(f"  Remaining: {max(self.goal - steps, 0)}")
            print(f"  Progress:  {self._progress_bar(steps, self.goal)}")
            print("="*50)

    def show_chart(self, days: int = 7) -> None:
        history = self._get_last_n_days(days)
        max_val = max((h["steps"] for h in history), default=0)
        if max_val == 0:
            print(c("No data to chart.", "yellow"))
            return
        chart_width = min(40, max(10, max_val // 100 + 1))
        scale = max_val / chart_width

        if self.console:
            self.console.print(f"\n[bold cyan]📊 Step History (last {days} days)[/bold cyan]")
            for item in history:
                bar_len = int(item["steps"] / scale)
                bar = "█" * bar_len + "░" * (chart_width - bar_len)
                date_str = item["date"][5:10]  # MM-DD
                steps_str = f"{item['steps']:,}"
                self.console.print(f"  {date_str} {bar} {steps_str:>8}")
        else:
            print(f"\n📊 Step History (last {days} days)")
            for item in history:
                bar_len = int(item["steps"] / scale)
                bar = "█" * bar_len + "░" * (chart_width - bar_len)
                date_str = item["date"][5:10]
                steps_str = f"{item['steps']:,}"
                print(f"  {date_str} {bar} {steps_str:>8}")

    def show_stats(self) -> None:
        if not self.entries:
            print(c("📭 No data yet. Start walking!", "yellow"))
            return
        total = sum(e.get("steps", 0) for e in self.entries)
        days = len(self.entries)
        avg = total / days if days else 0
        max_day = max((e.get("steps", 0) for e in self.entries), default=0)
        # best day
        best = max(self.entries, key=lambda e: e.get("steps", 0)) if self.entries else None

        if self.console:
            table = Table(title="📊 Statistics", box=box.ROUNDED)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Total Steps", f"{total:,}")
            table.add_row("Days Tracked", str(days))
            table.add_row("Average per Day", f"{avg:.0f}")
            table.add_row("Best Day", f"{best['date']} ({best['steps']:,})" if best else "—")
            table.add_row("Daily Goal", f"{self.goal:,}")
            self.console.print(table)
        else:
            print("\n📊 STATISTICS")
            print(c("─"*30, "dim"))
            print(f"  Total Steps:  {total:,}")
            print(f"  Days Tracked: {days}")
            print(f"  Average per Day: {avg:.0f}")
            print(f"  Best Day:     {best['date']} ({best['steps']:,})" if best else "  Best Day: —")
            print(f"  Daily Goal:   {self.goal:,}")

    def set_goal(self, goal: int) -> None:
        if goal <= 0:
            print(c("❌ Goal must be positive!", "red"))
            return
        self.goal = goal
        self._save()
        print(c(f"✅ Daily goal set to {goal:,} steps", "green"))

    def clear_data(self) -> None:
        if self.console:
            if not Confirm.ask("⚠️  Delete ALL data? This cannot be undone!"):
                return
        else:
            if input("⚠️  Delete ALL data? (yes/no): ").strip().lower() != "yes":
                return
        self.entries = []
        self.goal = self.DEFAULT_GOAL
        self._save()
        print(c("🗑️  All data cleared.", "yellow"))

    def auto_simulate(self, interval: int = 60) -> None:
        """Simulate step counting by adding random steps every interval seconds."""
        if self._auto_running:
            print(c("Auto-simulation already running.", "yellow"))
            return
        self._auto_running = True
        print(c(f"🔄 Auto-simulation started (adding random steps every {interval}s)", "cyan"))
        print(c("   Press Ctrl+C to stop.", "dim"))

        def sim_loop():
            while self._auto_running:
                steps = random.randint(50, 300)
                self.add_steps(steps)
                if self.console:
                    self.console.print(f"[dim]Auto: +{steps} steps[/dim]")
                else:
                    print(c(f"Auto: +{steps} steps", "dim"))
                time.sleep(interval)

        thread = threading.Thread(target=sim_loop, daemon=True)
        thread.start()
        # Wait for user to stop
        try:
            input(c("Press Enter to stop auto-simulation...\n", "dim"))
        except KeyboardInterrupt:
            pass
        self._auto_running = False
        print(c("⏹️  Auto-simulation stopped.", "yellow"))

    # ─── Menu ──────────────────────────────────────────────────────────────

    def _show_menu(self) -> None:
        steps = self._get_today_steps()
        progress = self._progress_bar(steps, self.goal)
        if self.console:
            menu = f"""
[bold cyan]🚶 Step Counter[/bold cyan]
  Today: {steps:,} / {self.goal:,}  {progress}

  [1] 🦶 Add steps manually
  [2] 📊 Today's progress
  [3] 📈 Show history chart
  [4] 📊 Statistics
  [5] 🎯 Set daily goal (current: {self.goal:,})
  [6] 🔄 Auto-simulation (random steps)
  [7] 🗑️  Clear all data
  [0] 🚪 Exit
"""
            self.console.print(Panel(menu, border_style="blue"))
        else:
            print("\n" + "-"*50)
            print(f"🚶 Today: {steps:,} / {self.goal:,}  {progress}")
            print("-"*50)
            print("  1. 🦶 Add steps manually")
            print("  2. 📊 Today's progress")
            print("  3. 📈 Show history chart")
            print("  4. 📊 Statistics")
            print(f"  5. 🎯 Set daily goal (current: {self.goal:,})")
            print("  6. 🔄 Auto-simulation (random steps)")
            print("  7. 🗑️  Clear all data")
            print("  0. 🚪 Exit")
            print("-"*50)

    def _get_choice(self) -> str:
        if self.console:
            return Prompt.ask("Your choice", choices=["0","1","2","3","4","5","6","7"])
        return input("Your choice: ").strip()

    def _get_steps(self) -> Optional[int]:
        if self.console:
            return IntPrompt.ask("Number of steps")
        try:
            return int(input("Steps: ").strip())
        except ValueError:
            print(c("❌ Please enter a number.", "red"))
            return None

    def _get_goal(self) -> Optional[int]:
        if self.console:
            return IntPrompt.ask("New daily goal")
        try:
            return int(input("New daily goal: ").strip())
        except ValueError:
            print(c("❌ Please enter a number.", "red"))
            return None

    def run(self) -> None:
        if self.console:
            self.console.print(Panel.fit("[bold cyan]🚶 Step Counter – Walk Tracker Without GPS[/bold cyan]", border_style="cyan"))
        else:
            print(c("\n🚶 Step Counter – Walk Tracker Without GPS", "bright"))
            print(c("Track your steps, set goals, and stay active!", "dim"))

        while True:
            self._show_menu()
            choice = self._get_choice()
            if choice == "1":
                steps = self._get_steps()
                if steps:
                    self.add_steps(steps)
            elif choice == "2":
                self.show_today()
            elif choice == "3":
                self.show_chart()
            elif choice == "4":
                self.show_stats()
            elif choice == "5":
                goal = self._get_goal()
                if goal:
                    self.set_goal(goal)
            elif choice == "6":
                self.auto_simulate()
            elif choice == "7":
                self.clear_data()
            elif choice == "0":
                print(c("👋 Keep walking! Goodbye!", "cyan"))
                break
            else:
                print(c("❌ Invalid choice.", "red"))

            if choice != "0":
                if self.console:
                    self.console.print("\n[dim]Press Enter to continue...[/dim]")
                    input()
                else:
                    input("\nPress Enter to continue...")


def main():
    try:
        app = StepCounter()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(c(f"❌ Unexpected error: {e}", "red"))
        sys.exit(1)

if __name__ == "__main__":
    main()
