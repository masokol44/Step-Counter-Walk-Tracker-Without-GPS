# step_counter.go
/**
 * 🚶 Step Counter – Walk Tracker Without GPS (Go Edition)
 * Features: manual step log, daily goal, history chart, auto-simulation, statistics
 */

package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"math"
	"math/rand"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

// ─── Data Model ─────────────────────────────────────────────────────────────

type Entry struct {
	Date      string `json:"date"`
	Steps     int    `json:"steps"`
	Timestamp string `json:"timestamp"`
}

type Data struct {
	Goal    int     `json:"goal"`
	Entries []Entry `json:"entries"`
}

// ─── Colors ──────────────────────────────────────────────────────────────────

const (
	reset  = "\x1b[0m"
	bright = "\x1b[1m"
	dim    = "\x1b[2m"
	red    = "\x1b[31m"
	green  = "\x1b[32m"
	yellow = "\x1b[33m"
	blue   = "\x1b[34m"
	magenta = "\x1b[35m"
	cyan   = "\x1b[36m"
)

func c(str, color string) string {
	return color + str + reset
}

// ─── Config ──────────────────────────────────────────────────────────────────

const (
	defaultGoal = 10000
)

// ─── Data Manager ──────────────────────────────────────────────────────────

type StepCounter struct {
	goal    int
	entries []Entry
	file    string
	reader  *bufio.Reader
}

func NewStepCounter() *StepCounter {
	home, _ := os.UserHomeDir()
	dir := filepath.Join(home, ".step_counter")
	os.MkdirAll(dir, 0755)
	file := filepath.Join(dir, "data.json")
	s := &StepCounter{file: file, reader: bufio.NewReader(os.Stdin)}
	s.load()
	return s
}

func (s *StepCounter) load() {
	if _, err := os.Stat(s.file); os.IsNotExist(err) {
		s.goal = defaultGoal
		s.entries = []Entry{}
		return
	}
	raw, err := os.ReadFile(s.file)
	if err != nil {
		s.goal = defaultGoal
		s.entries = []Entry{}
		return
	}
	var data Data
	if err := json.Unmarshal(raw, &data); err != nil {
		s.goal = defaultGoal
		s.entries = []Entry{}
		return
	}
	s.goal = data.Goal
	if s.goal <= 0 {
		s.goal = defaultGoal
	}
	s.entries = data.Entries
	if s.entries == nil {
		s.entries = []Entry{}
	}
}

func (s *StepCounter) save() {
	data := Data{Goal: s.goal, Entries: s.entries}
	raw, _ := json.MarshalIndent(data, "", "  ")
	os.WriteFile(s.file, raw, 0644)
}

func (s *StepCounter) today() string {
	return time.Now().Format("2006-01-02")
}

func (s *StepCounter) getTodayEntry() *Entry {
	today := s.today()
	for i := range s.entries {
		if s.entries[i].Date == today {
			return &s.entries[i]
		}
	}
	return nil
}

func (s *StepCounter) getTodaySteps() int {
	entry := s.getTodayEntry()
	if entry == nil {
		return 0
	}
	return entry.Steps
}

func (s *StepCounter) getLastNDays(n int) []struct{ Date string; Steps int } {
	now := time.Now()
	res := make([]struct{ Date string; Steps int }, n)
	for i := n - 1; i >= 0; i-- {
		d := now.AddDate(0, 0, -i)
		dateStr := d.Format("2006-01-02")
		steps := 0
		for _, e := range s.entries {
			if e.Date == dateStr {
				steps = e.Steps
				break
			}
		}
		res = append(res, struct{ Date string; Steps int }{dateStr, steps})
	}
	return res
}

func (s *StepCounter) progressBar(current, goal, width int) string {
	if goal <= 0 {
		return "⚠️  Goal not set"
	}
	ratio := float64(current) / float64(goal)
	if ratio > 1.0 {
		ratio = 1.0
	}
	filled := int(ratio * float64(width))
	bar := strings.Repeat("█", filled) + strings.Repeat("░", width-filled)
	return fmt.Sprintf("[%s] %.1f%%", bar, ratio*100)
}

// ─── Core Actions ──────────────────────────────────────────────────────────

func (s *StepCounter) addSteps(steps int) {
	if steps <= 0 {
		fmt.Println(c("❌ Steps must be positive!", red))
		return
	}
	today := s.today()
	entry := s.getTodayEntry()
	if entry != nil {
		entry.Steps += steps
	} else {
		s.entries = append(s.entries, Entry{
			Date:      today,
			Steps:     steps,
			Timestamp: time.Now().Format(time.RFC3339),
		})
	}
	s.save()
	total := s.getTodaySteps()
	fmt.Printf(c("✅ Added %d steps (Total today: %d)\n", green), steps, total)
	if total >= s.goal {
		fmt.Println(c("🎉 Goal achieved! Keep walking! 💪", cyan))
	}
}

func (s *StepCounter) showToday() {
	steps := s.getTodaySteps()
	fmt.Println("\n" + c(strings.Repeat("═", 50), dim))
	fmt.Println(c("🚶 TODAY'S STEPS", bright+cyan))
	fmt.Println(c(strings.Repeat("═", 50), dim))
	fmt.Printf("  Goal:      %s\n", c(fmt.Sprintf("%d", s.goal), cyan))
	fmt.Printf("  Steps:     %s\n", c(fmt.Sprintf("%d", steps), green))
	remaining := s.goal - steps
	if remaining < 0 {
		remaining = 0
	}
	fmt.Printf("  Remaining: %s\n", c(fmt.Sprintf("%d", remaining), yellow))
	fmt.Printf("  Progress:  %s\n", s.progressBar(steps, s.goal, 20))
}

func (s *StepCounter) showChart(days int) {
	history := s.getLastNDays(days)
	maxVal := 0
	for _, h := range history {
		if h.Steps > maxVal {
			maxVal = h.Steps
		}
	}
	if maxVal == 0 {
		fmt.Println(c("No data to chart.", yellow))
		return
	}
	chartWidth := 40
	if maxVal < 100 {
		chartWidth = 20
	} else if maxVal < 500 {
		chartWidth = 30
	}
	scale := float64(maxVal) / float64(chartWidth)
	fmt.Printf("\n%s\n", c(fmt.Sprintf("📊 Step History (last %d days)", days), bright+cyan))
	for _, h := range history {
		barLen := int(math.Floor(float64(h.Steps) / scale))
		bar := strings.Repeat("█", barLen) + strings.Repeat("░", chartWidth-barLen)
		dateStr := h.Date[5:10]
		stepsStr := fmt.Sprintf("%8d", h.Steps)
		fmt.Printf("  %s %s %s\n", dateStr, bar, stepsStr)
	}
}

func (s *StepCounter) showStats() {
	if len(s.entries) == 0 {
		fmt.Println(c("📭 No data yet. Start walking!", yellow))
		return
	}
	total := 0
	best := s.entries[0]
	for _, e := range s.entries {
		total += e.Steps
		if e.Steps > best.Steps {
			best = e
		}
	}
	days := len(s.entries)
	avg := float64(total) / float64(days)
	fmt.Println("\n📊 STATISTICS")
	fmt.Println(c(strings.Repeat("─", 30), dim))
	fmt.Printf("  Total Steps:  %d\n", total)
	fmt.Printf("  Days Tracked: %d\n", days)
	fmt.Printf("  Average per Day: %.0f\n", avg)
	fmt.Printf("  Best Day:     %s (%d)\n", best.Date, best.Steps)
	fmt.Printf("  Daily Goal:   %d\n", s.goal)
}

func (s *StepCounter) setGoal(goal int) {
	if goal <= 0 {
		fmt.Println(c("❌ Goal must be positive!", red))
		return
	}
	s.goal = goal
	s.save()
	fmt.Printf(c("✅ Daily goal set to %d steps\n", green), goal)
}

func (s *StepCounter) clearData() {
	fmt.Print("⚠️  Delete ALL data? (yes/no): ")
	ans, _ := s.reader.ReadString('\n')
	ans = strings.TrimSpace(strings.ToLower(ans))
	if ans != "yes" {
		return
	}
	s.entries = []Entry{}
	s.goal = defaultGoal
	s.save()
	fmt.Println(c("🗑️  All data cleared.", yellow))
}

func (s *StepCounter) autoSimulate() {
	fmt.Println(c("🔄 Auto-simulation started (adding random steps every 60s)", cyan))
	fmt.Println(c("   Press Ctrl+C to stop.", dim))
	ticker := time.NewTicker(60 * time.Second)
	go func() {
		for range ticker.C {
			steps := rand.Intn(250) + 50
			s.addSteps(steps)
			fmt.Printf(c("Auto: +%d steps\n", dim), steps)
		}
	}()
	// Wait for user to stop
	s.reader.ReadString('\n')
	ticker.Stop()
	fmt.Println(c("⏹️  Auto-simulation stopped.", yellow))
}

// ─── Menu ──────────────────────────────────────────────────────────────────

func (s *StepCounter) ask(prompt string) string {
	fmt.Print(prompt)
	line, _ := s.reader.ReadString('\n')
	return strings.TrimSpace(line)
}

func (s *StepCounter) askInt(prompt string) int {
	for {
		ans := s.ask(prompt)
		if val, err := strconv.Atoi(ans); err == nil {
			return val
		}
		fmt.Println(c("❌ Please enter a number.", red))
	}
}

func (s *StepCounter) showMenu() {
	steps := s.getTodaySteps()
	progress := s.progressBar(steps, s.goal, 20)
	fmt.Println("\n" + c(strings.Repeat("═", 50), cyan))
	fmt.Println(c("🚶 STEP COUNTER", bright+cyan))
	fmt.Println(c(strings.Repeat("═", 50), cyan))
	fmt.Printf("  Today: %d / %d  %s\n", steps, s.goal, progress)
	fmt.Println(c(strings.Repeat("─", 50), dim))
	fmt.Println("  1. 🦶 Add steps manually")
	fmt.Println("  2. 📊 Today's progress")
	fmt.Println("  3. 📈 Show history chart")
	fmt.Println("  4. 📊 Statistics")
	fmt.Printf("  5. 🎯 Set daily goal (current: %d)\n", s.goal)
	fmt.Println("  6. 🔄 Auto-simulation (random steps)")
	fmt.Println("  7. 🗑️  Clear all data")
	fmt.Println("  0. 🚪 Exit")
	fmt.Println(c(strings.Repeat("═", 50), cyan))
}

func (s *StepCounter) run() {
	fmt.Print("\033[H\033[2J")
	fmt.Println(c("\n🚶 Step Counter – Walk Tracker Without GPS", bright+cyan))
	fmt.Println(c("Track your steps, set goals, and stay active!", dim))

	for {
		s.showMenu()
		choice := s.ask("Your choice: ")
		switch choice {
		case "1":
			steps := s.askInt("Steps: ")
			s.addSteps(steps)
		case "2":
			s.showToday()
		case "3":
			s.showChart(7)
		case "4":
			s.showStats()
		case "5":
			goal := s.askInt("New daily goal: ")
			s.setGoal(goal)
		case "6":
			s.autoSimulate()
		case "7":
			s.clearData()
		case "0":
			fmt.Println(c("👋 Keep walking! Goodbye!", cyan))
			return
		default:
			fmt.Println(c("❌ Invalid choice.", red))
		}
		if choice != "0" {
			fmt.Print("\nPress Enter to continue...")
			s.reader.ReadString('\n')
		}
	}
}

func main() {
	rand.Seed(time.Now().UnixNano())
	app := NewStepCounter()
	app.run()
}
