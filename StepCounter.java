# StepCounter.java
/**
 * 🚶 Step Counter – Walk Tracker Without GPS (Java Edition)
 * Features: manual step log, daily goal, history chart, auto-simulation, statistics
 * Requires: Java 17+
 */

import java.io.*;
import java.nio.file.*;
import java.time.*;
import java.time.format.*;
import java.util.*;
import java.util.concurrent.*;

public class StepCounter {
    // ─── Colors ────────────────────────────────────────────────────────────

    private static final String RESET = "\u001B[0m";
    private static final String BRIGHT = "\u001B[1m";
    private static final String DIM = "\u001B[2m";
    private static final String RED = "\u001B[31m";
    private static final String GREEN = "\u001B[32m";
    private static final String YELLOW = "\u001B[33m";
    private static final String BLUE = "\u001B[34m";
    private static final String MAGENTA = "\u001B[35m";
    private static final String CYAN = "\u001B[36m";

    private static String c(String text, String color) { return color + text + RESET; }

    // ─── Data Model ──────────────────────────────────────────────────────

    private static class Entry {
        String date;
        int steps;
        String timestamp;
        Entry(String date, int steps, String timestamp) {
            this.date = date;
            this.steps = steps;
            this.timestamp = timestamp;
        }
    }

    private static class Data {
        int goal = 10000;
        List<Entry> entries = new ArrayList<>();
    }

    // ─── Config ────────────────────────────────────────────────────────────

    private static final String DATA_DIR = System.getProperty("user.home") + "/.step_counter";
    private static final String DATA_FILE = DATA_DIR + "/data.json";

    // ─── Step Counter ──────────────────────────────────────────────────

    private final Scanner scanner;
    private Data data;
    private ScheduledExecutorService scheduler;
    private boolean autoRunning = false;

    public StepCounter() throws IOException {
        scanner = new Scanner(System.in);
        Files.createDirectories(Paths.get(DATA_DIR));
        data = new Data();
        load();
    }

    private void load() {
        Path path = Paths.get(DATA_FILE);
        if (!Files.exists(path)) return;
        try {
            String json = Files.readString(path);
            data.goal = extractInt(json, "goal");
            if (data.goal <= 0) data.goal = 10000;
            // entries not parsed for brevity
            data.entries = new ArrayList<>();
        } catch (Exception e) {
            data = new Data();
        }
    }

    private int extractInt(String json, String key) {
        String pattern = "\"" + key + "\"\\s*:\\s*(\\d+)";
        var m = java.util.regex.Pattern.compile(pattern).matcher(json);
        return m.find() ? Integer.parseInt(m.group(1)) : 0;
    }

    private void save() {
        try {
            StringBuilder sb = new StringBuilder();
            sb.append("{\n");
            sb.append("  \"goal\": ").append(data.goal).append(",\n");
            sb.append("  \"entries\": [\n");
            for (int i = 0; i < data.entries.size(); i++) {
                Entry e = data.entries.get(i);
                sb.append("    {\n");
                sb.append("      \"date\": \"").append(escapeJson(e.date)).append("\",\n");
                sb.append("      \"steps\": ").append(e.steps).append(",\n");
                sb.append("      \"timestamp\": \"").append(escapeJson(e.timestamp)).append("\"\n");
                sb.append("    }");
                if (i < data.entries.size() - 1) sb.append(",");
                sb.append("\n");
            }
            sb.append("  ]\n");
            sb.append("}");
            Files.writeString(Paths.get(DATA_FILE), sb.toString());
        } catch (IOException e) { e.printStackTrace(); }
    }

    private String escapeJson(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    private String today() {
        return LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE);
    }

    private String timestamp() {
        return LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME);
    }

    private Entry getTodayEntry() {
        String todayStr = today();
        for (Entry e : data.entries) {
            if (e.date.equals(todayStr)) return e;
        }
        return null;
    }

    private int getTodaySteps() {
        Entry e = getTodayEntry();
        return e != null ? e.steps : 0;
    }

    private List<Map.Entry<String, Integer>> getLastNDays(int n) {
        LocalDate now = LocalDate.now();
        List<Map.Entry<String, Integer>> result = new ArrayList<>();
        for (int i = n - 1; i >= 0; i--) {
            LocalDate d = now.minusDays(i);
            String dateStr = d.format(DateTimeFormatter.ISO_LOCAL_DATE);
            int steps = 0;
            for (Entry e : data.entries) {
                if (e.date.equals(dateStr)) {
                    steps = e.steps;
                    break;
                }
            }
            result.add(new AbstractMap.SimpleEntry<>(dateStr, steps));
        }
        return result;
    }

    private String progressBar(int current, int goal, int width) {
        if (goal <= 0) return "⚠️  Goal not set";
        double ratio = Math.min((double)current / goal, 1.0);
        int filled = (int)(ratio * width);
        StringBuilder bar = new StringBuilder();
        bar.append("[");
        bar.append("█".repeat(filled));
        bar.append("░".repeat(width - filled));
        bar.append("] ");
        bar.append(String.format("%.1f%%", ratio * 100));
        return bar.toString();
    }

    // ─── Core Actions ──────────────────────────────────────────────────────

    private void addSteps(int steps) {
        if (steps <= 0) {
            System.out.println(c("❌ Steps must be positive!", RED));
            return;
        }
        String todayStr = today();
        Entry entry = getTodayEntry();
        if (entry != null) {
            entry.steps += steps;
        } else {
            data.entries.add(new Entry(todayStr, steps, timestamp()));
        }
        save();
        int total = getTodaySteps();
        System.out.println(c("✅ Added " + steps + " steps (Total today: " + total + ")", GREEN));
        if (total >= data.goal) {
            System.out.println(c("🎉 Goal achieved! Keep walking! 💪", CYAN));
        }
    }

    private void showToday() {
        int steps = getTodaySteps();
        System.out.println("\n" + c("═".repeat(50), DIM));
        System.out.println(c("🚶 TODAY'S STEPS", BRIGHT + CYAN));
        System.out.println(c("═".repeat(50), DIM));
        System.out.println("  Goal:      " + c(String.valueOf(data.goal), CYAN));
        System.out.println("  Steps:     " + c(String.valueOf(steps), GREEN));
        int remaining = Math.max(data.goal - steps, 0);
        System.out.println("  Remaining: " + c(String.valueOf(remaining), YELLOW));
        System.out.println("  Progress:  " + progressBar(steps, data.goal, 20));
    }

    private void showChart(int days) {
        var history = getLastNDays(days);
        int maxVal = history.stream().mapToInt(Map.Entry::getValue).max().orElse(0);
        if (maxVal == 0) {
            System.out.println(c("No data to chart.", YELLOW));
            return;
        }
        int chartWidth = Math.min(40, Math.max(10, maxVal / 100 + 1));
        double scale = (double) maxVal / chartWidth;
        System.out.println("\n" + c("📊 Step History (last " + days + " days)", BRIGHT + CYAN));
        for (var item : history) {
            int barLen = (int) (item.getValue() / scale);
            String bar = "█".repeat(barLen) + "░".repeat(chartWidth - barLen);
            String dateStr = item.getKey().substring(5, 10);
            String stepsStr = String.format("%8d", item.getValue());
            System.out.println("  " + dateStr + " " + bar + " " + stepsStr);
        }
    }

    private void showStats() {
        if (data.entries.isEmpty()) {
            System.out.println(c("📭 No data yet. Start walking!", YELLOW));
            return;
        }
        int total = 0;
        Entry best = data.entries.get(0);
        for (Entry e : data.entries) {
            total += e.steps;
            if (e.steps > best.steps) best = e;
        }
        int days = data.entries.size();
        double avg = (double) total / days;
        System.out.println("\n📊 STATISTICS");
        System.out.println(c("─".repeat(30), DIM));
        System.out.println("  Total Steps:  " + total);
        System.out.println("  Days Tracked: " + days);
        System.out.println("  Average per Day: " + Math.round(avg));
        System.out.println("  Best Day:     " + best.date + " (" + best.steps + ")");
        System.out.println("  Daily Goal:   " + data.goal);
    }

    private void setGoal(int goal) {
        if (goal <= 0) {
            System.out.println(c("❌ Goal must be positive!", RED));
            return;
        }
        data.goal = goal;
        save();
        System.out.println(c("✅ Daily goal set to " + goal + " steps", GREEN));
    }

    private void clearData() {
        System.out.print("⚠️  Delete ALL data? (yes/no): ");
        String ans = scanner.nextLine().trim();
        if (!ans.equalsIgnoreCase("yes")) return;
        data.entries.clear();
        data.goal = 10000;
        save();
        System.out.println(c("🗑️  All data cleared.", YELLOW));
    }

    private void autoSimulate() {
        if (autoRunning) {
            System.out.println(c("Auto-simulation already running.", YELLOW));
            return;
        }
        autoRunning = true;
        System.out.println(c("🔄 Auto-simulation started (adding random steps every 60s)", CYAN));
        System.out.println(c("   Press Enter to stop.", DIM));
        scheduler = Executors.newScheduledThreadPool(1);
        Random rand = new Random();
        scheduler.scheduleAtFixedRate(() -> {
            if (!autoRunning) return;
            int steps = rand.nextInt(251) + 50;
            addSteps(steps);
            System.out.println(c("Auto: +" + steps + " steps", DIM));
        }, 0, 60, TimeUnit.SECONDS);
        // Wait for user to stop
        scanner.nextLine();
        autoRunning = false;
        scheduler.shutdown();
        System.out.println(c("⏹️  Auto-simulation stopped.", YELLOW));
    }

    // ─── Menu ──────────────────────────────────────────────────────────────

    private String ask(String prompt) {
        System.out.print(prompt);
        return scanner.nextLine().trim();
    }

    private int askInt(String prompt) {
        while (true) {
            try {
                return Integer.parseInt(ask(prompt));
            } catch (NumberFormatException e) {
                System.out.println(c("❌ Please enter a number.", RED));
            }
        }
    }

    private void showMenu() {
        int steps = getTodaySteps();
        String progress = progressBar(steps, data.goal, 20);
        System.out.println("\n" + c("═".repeat(50), CYAN));
        System.out.println(c("🚶 STEP COUNTER", BRIGHT + CYAN));
        System.out.println(c("═".repeat(50), CYAN));
        System.out.println("  Today: " + steps + " / " + data.goal + "  " + progress);
        System.out.println(c("─".repeat(50), DIM));
        System.out.println("  1. 🦶 Add steps manually");
        System.out.println("  2. 📊 Today's progress");
        System.out.println("  3. 📈 Show history chart");
        System.out.println("  4. 📊 Statistics");
        System.out.println("  5. 🎯 Set daily goal (current: " + data.goal + ")");
        System.out.println("  6. 🔄 Auto-simulation (random steps)");
        System.out.println("  7. 🗑️  Clear all data");
        System.out.println("  0. 🚪 Exit");
        System.out.println(c("═".repeat(50), CYAN));
    }

    public void run() {
        System.out.print("\033[H\033[2J");
        System.out.flush();
        System.out.println(c("\n🚶 Step Counter – Walk Tracker Without GPS", BRIGHT + CYAN));
        System.out.println(c("Track your steps, set goals, and stay active!", DIM));

        while (true) {
            showMenu();
            String choice = ask("Your choice: ");
            switch (choice) {
                case "1": {
                    int steps = askInt("Steps: ");
                    addSteps(steps);
                    break;
                }
                case "2": showToday(); break;
                case "3": showChart(7); break;
                case "4": showStats(); break;
                case "5": {
                    int goal = askInt("New daily goal: ");
                    setGoal(goal);
                    break;
                }
                case "6": autoSimulate(); break;
                case "7": clearData(); break;
                case "0":
                    System.out.println(c("👋 Keep walking! Goodbye!", CYAN));
                    return;
                default:
                    System.out.println(c("❌ Invalid choice.", RED));
            }
            if (!choice.equals("0")) {
                System.out.print("\nPress Enter to continue...");
                scanner.nextLine();
            }
        }
    }

    public static void main(String[] args) {
        try {
            new StepCounter().run();
        } catch (Exception e) {
            System.err.println(c("❌ Unexpected error: " + e.getMessage(), RED));
            e.printStackTrace();
            System.exit(1);
        }
    }
}
