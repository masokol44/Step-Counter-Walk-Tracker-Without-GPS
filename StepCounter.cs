# StepCounter.cs
/**
 * 🚶 Step Counter – Walk Tracker Without GPS (C# Edition)
 * Features: manual step log, daily goal, history chart, auto-simulation, statistics
 * Requires: .NET 6.0+
 */

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;

class StepCounter
{
    // ─── Colors ────────────────────────────────────────────────────────────

    private static readonly string Reset = "\u001B[0m";
    private static readonly string Bright = "\u001B[1m";
    private static readonly string Dim = "\u001B[2m";
    private static readonly string Red = "\u001B[31m";
    private static readonly string Green = "\u001B[32m";
    private static readonly string Yellow = "\u001B[33m";
    private static readonly string Blue = "\u001B[34m";
    private static readonly string Magenta = "\u001B[35m";
    private static readonly string Cyan = "\u001B[36m";

    private static string C(string text, string color) => color + text + Reset;

    // ─── Data Model ──────────────────────────────────────────────────────

    public class Entry
    {
        [JsonPropertyName("date")]
        public string Date { get; set; } = "";
        [JsonPropertyName("steps")]
        public int Steps { get; set; }
        [JsonPropertyName("timestamp")]
        public string Timestamp { get; set; } = "";
    }

    public class Data
    {
        [JsonPropertyName("goal")]
        public int Goal { get; set; } = 10000;
        [JsonPropertyName("entries")]
        public List<Entry> Entries { get; set; } = new();
    }

    // ─── Config ────────────────────────────────────────────────────────────

    private static readonly string DataDir = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
        ".step_counter"
    );
    private static readonly string DataFile = Path.Combine(DataDir, "data.json");

    // ─── Step Counter ──────────────────────────────────────────────────

    private readonly Data data = new();
    private Timer autoTimer;
    private bool autoRunning = false;
    private readonly Random random = new();

    public StepCounter()
    {
        Directory.CreateDirectory(DataDir);
        Load();
    }

    private void Load()
    {
        if (!File.Exists(DataFile)) return;
        try
        {
            string json = File.ReadAllText(DataFile);
            var loaded = JsonSerializer.Deserialize<Data>(json);
            if (loaded != null)
            {
                data.Goal = loaded.Goal > 0 ? loaded.Goal : 10000;
                data.Entries = loaded.Entries ?? new List<Entry>();
            }
        }
        catch { /* ignore */ }
    }

    private void Save()
    {
        string json = JsonSerializer.Serialize(data, new JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(DataFile, json);
    }

    private string Today() => DateTime.Now.ToString("yyyy-MM-dd");
    private string Timestamp() => DateTime.Now.ToString("yyyy-MM-ddTHH:mm:ss");

    private Entry GetTodayEntry()
    {
        string today = Today();
        return data.Entries.FirstOrDefault(e => e.Date == today);
    }

    private int GetTodaySteps() => GetTodayEntry()?.Steps ?? 0;

    private List<(string Date, int Steps)> GetLastNDays(int n)
    {
        var now = DateTime.Now;
        var result = new List<(string, int)>();
        for (int i = n - 1; i >= 0; i--)
        {
            var d = now.AddDays(-i);
            string dateStr = d.ToString("yyyy-MM-dd");
            int steps = data.Entries.FirstOrDefault(e => e.Date == dateStr)?.Steps ?? 0;
            result.Add((dateStr, steps));
        }
        return result;
    }

    private string ProgressBar(int current, int goal, int width = 20)
    {
        if (goal <= 0) return "⚠️  Goal not set";
        double ratio = Math.Min((double)current / goal, 1.0);
        int filled = (int)(ratio * width);
        string bar = new string('█', filled) + new string('░', width - filled);
        return $"[{bar}] {ratio * 100.0:F1}%";
    }

    // ─── Core Actions ──────────────────────────────────────────────────────

    private void AddSteps(int steps)
    {
        if (steps <= 0)
        {
            Console.WriteLine(C("❌ Steps must be positive!", Red));
            return;
        }
        string today = Today();
        var entry = GetTodayEntry();
        if (entry != null)
        {
            entry.Steps += steps;
        }
        else
        {
            data.Entries.Add(new Entry { Date = today, Steps = steps, Timestamp = Timestamp() });
        }
        Save();
        int total = GetTodaySteps();
        Console.WriteLine(C($"✅ Added {steps} steps (Total today: {total})", Green));
        if (total >= data.Goal)
        {
            Console.WriteLine(C("🎉 Goal achieved! Keep walking! 💪", Cyan));
        }
    }

    private void ShowToday()
    {
        int steps = GetTodaySteps();
        Console.WriteLine("\n" + C(new string('═', 50), Dim));
        Console.WriteLine(C("🚶 TODAY'S STEPS", Bright + Cyan));
        Console.WriteLine(C(new string('═', 50), Dim));
        Console.WriteLine($"  Goal:      {C($"{data.Goal}", Cyan)}");
        Console.WriteLine($"  Steps:     {C($"{steps}", Green)}");
        int remaining = Math.Max(data.Goal - steps, 0);
        Console.WriteLine($"  Remaining: {C($"{remaining}", Yellow)}");
        Console.WriteLine($"  Progress:  {ProgressBar(steps, data.Goal)}");
    }

    private void ShowChart(int days)
    {
        var history = GetLastNDays(days);
        int maxVal = history.Count > 0 ? history.Max(h => h.Steps) : 0;
        if (maxVal == 0)
        {
            Console.WriteLine(C("No data to chart.", Yellow));
            return;
        }
        int chartWidth = Math.Min(40, Math.Max(10, maxVal / 100 + 1));
        double scale = (double)maxVal / chartWidth;
        Console.WriteLine($"\n{C($"📊 Step History (last {days} days)", Bright + Cyan)}");
        foreach (var (date, steps) in history)
        {
            int barLen = (int)(steps / scale);
            string bar = new string('█', barLen) + new string('░', chartWidth - barLen);
            string dateStr = date[5..10];
            string stepsStr = $"{steps,8}";
            Console.WriteLine($"  {dateStr} {bar} {stepsStr}");
        }
    }

    private void ShowStats()
    {
        if (data.Entries.Count == 0)
        {
            Console.WriteLine(C("📭 No data yet. Start walking!", Yellow));
            return;
        }
        int total = data.Entries.Sum(e => e.Steps);
        int days = data.Entries.Count;
        double avg = (double)total / days;
        var best = data.Entries.OrderByDescending(e => e.Steps).First();
        Console.WriteLine("\n📊 STATISTICS");
        Console.WriteLine(C(new string('─', 30), Dim));
        Console.WriteLine($"  Total Steps:  {total}");
        Console.WriteLine($"  Days Tracked: {days}");
        Console.WriteLine($"  Average per Day: {Math.Round(avg)}");
        Console.WriteLine($"  Best Day:     {best.Date} ({best.Steps})");
        Console.WriteLine($"  Daily Goal:   {data.Goal}");
    }

    private void SetGoal(int goal)
    {
        if (goal <= 0)
        {
            Console.WriteLine(C("❌ Goal must be positive!", Red));
            return;
        }
        data.Goal = goal;
        Save();
        Console.WriteLine(C($"✅ Daily goal set to {goal} steps", Green));
    }

    private void ClearData()
    {
        Console.Write("⚠️  Delete ALL data? (yes/no): ");
        string ans = Console.ReadLine()?.Trim() ?? "";
        if (!ans.Equals("yes", StringComparison.OrdinalIgnoreCase)) return;
        data.Entries.Clear();
        data.Goal = 10000;
        Save();
        Console.WriteLine(C("🗑️  All data cleared.", Yellow));
    }

    private void AutoSimulate()
    {
        if (autoRunning)
        {
            Console.WriteLine(C("Auto-simulation already running.", Yellow));
            return;
        }
        autoRunning = true;
        Console.WriteLine(C("🔄 Auto-simulation started (adding random steps every 60s)", Cyan));
        Console.WriteLine(C("   Press Enter to stop.", Dim));
        autoTimer = new Timer(_ =>
        {
            if (!autoRunning) return;
            int steps = random.Next(50, 301);
            AddSteps(steps);
            Console.WriteLine(C($"Auto: +{steps} steps", Dim));
        }, null, 0, 60000);
        // Wait for user to stop
        Console.ReadLine();
        autoRunning = false;
        autoTimer?.Dispose();
        Console.WriteLine(C("⏹️  Auto-simulation stopped.", Yellow));
    }

    // ─── Menu ──────────────────────────────────────────────────────────────

    private string Ask(string prompt)
    {
        Console.Write(prompt);
        return Console.ReadLine()?.Trim() ?? "";
    }

    private int AskInt(string prompt)
    {
        while (true)
        {
            if (int.TryParse(Ask(prompt), out int val)) return val;
            Console.WriteLine(C("❌ Please enter a number.", Red));
        }
    }

    private void ShowMenu()
    {
        int steps = GetTodaySteps();
        string progress = ProgressBar(steps, data.Goal);
        Console.WriteLine("\n" + C(new string('═', 50), Cyan));
        Console.WriteLine(C("🚶 STEP COUNTER", Bright + Cyan));
        Console.WriteLine(C(new string('═', 50), Cyan));
        Console.WriteLine($"  Today: {steps} / {data.Goal}  {progress}");
        Console.WriteLine(C(new string('─', 50), Dim));
        Console.WriteLine("  1. 🦶 Add steps manually");
        Console.WriteLine("  2. 📊 Today's progress");
        Console.WriteLine("  3. 📈 Show history chart");
        Console.WriteLine("  4. 📊 Statistics");
        Console.WriteLine($"  5. 🎯 Set daily goal (current: {data.Goal})");
        Console.WriteLine("  6. 🔄 Auto-simulation (random steps)");
        Console.WriteLine("  7. 🗑️  Clear all data");
        Console.WriteLine("  0. 🚪 Exit");
        Console.WriteLine(C(new string('═', 50), Cyan));
    }

    public void Run()
    {
        Console.Clear();
        Console.WriteLine(C("\n🚶 Step Counter – Walk Tracker Without GPS", Bright + Cyan));
        Console.WriteLine(C("Track your steps, set goals, and stay active!", Dim));

        while (true)
        {
            ShowMenu();
            string choice = Ask("Your choice: ");
            switch (choice)
            {
                case "1":
                    int steps = AskInt("Steps: ");
                    AddSteps(steps);
                    break;
                case "2":
                    ShowToday();
                    break;
                case "3":
                    ShowChart(7);
                    break;
                case "4":
                    ShowStats();
                    break;
                case "5":
                    int goal = AskInt("New daily goal: ");
                    SetGoal(goal);
                    break;
                case "6":
                    AutoSimulate();
                    break;
                case "7":
                    ClearData();
                    break;
                case "0":
                    Console.WriteLine(C("👋 Keep walking! Goodbye!", Cyan));
                    return;
                default:
                    Console.WriteLine(C("❌ Invalid choice.", Red));
                    break;
            }
            if (choice != "0")
            {
                Console.Write("\nPress Enter to continue...");
                Console.ReadLine();
            }
        }
    }

    public static void Main()
    {
        try
        {
            new StepCounter().Run();
        }
        catch (Exception ex)
        {
            Console.WriteLine(C($"❌ Unexpected error: {ex.Message}", Red));
            Environment.Exit(1);
        }
    }
}
