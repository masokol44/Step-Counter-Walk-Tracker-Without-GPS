# step_counter.js
/**
 * 🚶 Step Counter – Walk Tracker Without GPS (Node.js Edition)
 * Features: manual step log, daily goal, history chart, auto-simulation, statistics
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const readline = require('readline');

// ─── Colors ──────────────────────────────────────────────────────────────────

const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    dim: '\x1b[2m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m',
};

const c = (str, color) => `${color}${str}${colors.reset}`;

// ─── Config ──────────────────────────────────────────────────────────────────

const CONFIG = {
    dataDir: path.join(os.homedir(), '.step_counter'),
    dataFile: 'data.json',
    defaultGoal: 10000,
};

// ─── Data Manager ──────────────────────────────────────────────────────────

class StepCounter {
    constructor() {
        this.rl = readline.createInterface({ input: process.stdin, output: process.stdout });
        this.data = this._load();
        this.goal = this.data.goal || CONFIG.defaultGoal;
        this.entries = this.data.entries || [];
        this._autoRunning = false;
    }

    _getDataPath() {
        if (!fs.existsSync(CONFIG.dataDir)) fs.mkdirSync(CONFIG.dataDir, { recursive: true });
        return path.join(CONFIG.dataDir, CONFIG.dataFile);
    }

    _load() {
        const file = this._getDataPath();
        if (fs.existsSync(file)) {
            try {
                return JSON.parse(fs.readFileSync(file, 'utf8'));
            } catch (_) { return {}; }
        }
        return {};
    }

    _save() {
        const data = { goal: this.goal, entries: this.entries };
        fs.writeFileSync(this._getDataPath(), JSON.stringify(data, null, 2));
    }

    _today() {
        return new Date().toISOString().split('T')[0];
    }

    _getTodayEntry() {
        const today = this._today();
        return this.entries.find(e => e.date === today) || null;
    }

    _getTodaySteps() {
        const entry = this._getTodayEntry();
        return entry ? entry.steps : 0;
    }

    _getLastNDays(n = 7) {
        const today = new Date();
        const result = [];
        for (let i = n - 1; i >= 0; i--) {
            const d = new Date(today);
            d.setDate(d.getDate() - i);
            const dateStr = d.toISOString().split('T')[0];
            const entry = this.entries.find(e => e.date === dateStr);
            result.push({ date: dateStr, steps: entry ? entry.steps : 0 });
        }
        return result;
    }

    _progressBar(current, goal, width = 20) {
        if (goal <= 0) return '⚠️  Goal not set';
        const ratio = Math.min(current / goal, 1);
        const filled = Math.floor(ratio * width);
        return `[${'█'.repeat(filled)}${'░'.repeat(width - filled)}] ${(ratio * 100).toFixed(1)}%`;
    }

    // ─── Core Actions ──────────────────────────────────────────────────────

    addSteps(steps) {
        if (steps <= 0) {
            console.log(c('❌ Steps must be positive!', 'red'));
            return;
        }
        const today = this._today();
        let entry = this._getTodayEntry();
        if (entry) {
            entry.steps += steps;
        } else {
            this.entries.push({ date: today, steps, timestamp: new Date().toISOString() });
        }
        this._save();
        const total = this._getTodaySteps();
        console.log(c(`✅ Added ${steps} steps (Total today: ${total})`, 'green'));
        if (total >= this.goal) {
            console.log(c('🎉 Goal achieved! Keep walking! 💪', 'cyan'));
        }
    }

    showToday() {
        const steps = this._getTodaySteps();
        console.log('\n' + c('═'.repeat(50), 'dim'));
        console.log(c('🚶 TODAY\'S STEPS', 'bright') + c('', 'cyan'));
        console.log(c('═'.repeat(50), 'dim'));
        console.log(`  Goal:      ${c(this.goal.toLocaleString(), 'cyan')}`);
        console.log(`  Steps:     ${c(steps.toLocaleString(), 'green')}`);
        console.log(`  Remaining: ${c(Math.max(this.goal - steps, 0).toLocaleString(), 'yellow')}`);
        console.log(`  Progress:  ${this._progressBar(steps, this.goal)}`);
    }

    showChart(days = 7) {
        const history = this._getLastNDays(days);
        const maxVal = Math.max(...history.map(h => h.steps), 0);
        if (maxVal === 0) {
            console.log(c('No data to chart.', 'yellow'));
            return;
        }
        const chartWidth = Math.min(40, Math.max(10, Math.floor(maxVal / 100) + 1));
        const scale = maxVal / chartWidth;
        console.log(`\n${c(`📊 Step History (last ${days} days)`, 'bright') + c('', 'cyan')}`);
        history.forEach(item => {
            const barLen = Math.floor(item.steps / scale);
            const bar = '█'.repeat(barLen) + '░'.repeat(chartWidth - barLen);
            const dateStr = item.date.slice(5, 10);
            const stepsStr = item.steps.toLocaleString().padStart(8);
            console.log(`  ${dateStr} ${bar} ${stepsStr}`);
        });
    }

    showStats() {
        if (!this.entries.length) {
            console.log(c('📭 No data yet. Start walking!', 'yellow'));
            return;
        }
        const total = this.entries.reduce((s, e) => s + e.steps, 0);
        const days = this.entries.length;
        const avg = total / days;
        const best = this.entries.reduce((a, b) => a.steps > b.steps ? a : b, this.entries[0]);
        console.log('\n📊 STATISTICS');
        console.log(c('─'.repeat(30), 'dim'));
        console.log(`  Total Steps:  ${total.toLocaleString()}`);
        console.log(`  Days Tracked: ${days}`);
        console.log(`  Average per Day: ${Math.round(avg).toLocaleString()}`);
        console.log(`  Best Day:     ${best.date} (${best.steps.toLocaleString()})`);
        console.log(`  Daily Goal:   ${this.goal.toLocaleString()}`);
    }

    setGoal(goal) {
        if (goal <= 0) {
            console.log(c('❌ Goal must be positive!', 'red'));
            return;
        }
        this.goal = goal;
        this._save();
        console.log(c(`✅ Daily goal set to ${goal.toLocaleString()} steps`, 'green'));
    }

    clearData() {
        this.rl.question('⚠️  Delete ALL data? (yes/no): ', (ans) => {
            if (ans.toLowerCase() === 'yes') {
                this.entries = [];
                this.goal = CONFIG.defaultGoal;
                this._save();
                console.log(c('🗑️  All data cleared.', 'yellow'));
            }
            this.rl.close();
        });
    }

    autoSimulate() {
        if (this._autoRunning) {
            console.log(c('Auto-simulation already running.', 'yellow'));
            return;
        }
        this._autoRunning = true;
        console.log(c('🔄 Auto-simulation started (adding random steps every 60s)', 'cyan'));
        console.log(c('   Press Ctrl+C to stop.', 'dim'));
        const interval = setInterval(() => {
            if (!this._autoRunning) {
                clearInterval(interval);
                return;
            }
            const steps = Math.floor(Math.random() * 250) + 50;
            this.addSteps(steps);
            console.log(c(`Auto: +${steps} steps`, 'dim'));
        }, 60000);
        // Wait for user to stop
        this.rl.question(c('Press Enter to stop auto-simulation...\n', 'dim'), () => {
            this._autoRunning = false;
            clearInterval(interval);
            console.log(c('⏹️  Auto-simulation stopped.', 'yellow'));
        });
    }

    // ─── Menu ──────────────────────────────────────────────────────────────

    _ask(prompt) {
        return new Promise(resolve => this.rl.question(prompt, resolve));
    }

    async _askInt(prompt) {
        while (true) {
            const ans = await this._ask(prompt);
            const num = parseInt(ans.trim());
            if (!isNaN(num)) return num;
            console.log(c('❌ Please enter a number.', 'red'));
        }
    }

    async _showMenu() {
        const steps = this._getTodaySteps();
        const progress = this._progressBar(steps, this.goal);
        console.log('\n' + c('═'.repeat(50), 'cyan'));
        console.log(c('🚶 STEP COUNTER', 'bright') + c('', 'cyan'));
        console.log(c('═'.repeat(50), 'cyan'));
        console.log(`  Today: ${steps.toLocaleString()} / ${this.goal.toLocaleString()}  ${progress}`);
        console.log(c('─'.repeat(50), 'dim'));
        console.log('  1. 🦶 Add steps manually');
        console.log('  2. 📊 Today\'s progress');
        console.log('  3. 📈 Show history chart');
        console.log('  4. 📊 Statistics');
        console.log(`  5. 🎯 Set daily goal (current: ${this.goal.toLocaleString()})`);
        console.log('  6. 🔄 Auto-simulation (random steps)');
        console.log('  7. 🗑️  Clear all data');
        console.log('  0. 🚪 Exit');
        console.log(c('═'.repeat(50), 'cyan'));
    }

    async run() {
        console.clear();
        console.log(c('\n🚶 Step Counter – Walk Tracker Without GPS', 'bright') + c('', 'cyan'));
        console.log(c('Track your steps, set goals, and stay active!', 'dim'));

        while (true) {
            await this._showMenu();
            const choice = await this._ask('Your choice: ');
            switch (choice.trim()) {
                case '1': {
                    const steps = await this._askInt('Steps: ');
                    this.addSteps(steps);
                    break;
                }
                case '2': this.showToday(); break;
                case '3': this.showChart(); break;
                case '4': this.showStats(); break;
                case '5': {
                    const goal = await this._askInt('New daily goal: ');
                    this.setGoal(goal);
                    break;
                }
                case '6': this.autoSimulate(); break;
                case '7': this.clearData(); break;
                case '0':
                    console.log(c('👋 Keep walking! Goodbye!', 'cyan'));
                    this.rl.close();
                    return;
                default:
                    console.log(c('❌ Invalid choice.', 'red'));
            }
            if (choice !== '0') {
                console.log('\nPress Enter to continue...');
                await this._ask('');
            }
        }
    }
}

// ─── Main ────────────────────────────────────────────────────────────────────

const main = async () => {
    try {
        const app = new StepCounter();
        await app.run();
    } catch (e) {
        console.error(c(`❌ Unexpected error: ${e.message}`, 'red'));
        process.exit(1);
    }
};

main();
