🚶 Step Counter – Walk Tracker Without GPS
"Track your steps, set goals, and stay active – all without GPS. Simple, smart, and effective!"

📋 Table of Contents
✨ Features

📁 Repository Structure

🚀 Quick Start

💻 Language Implementations

📊 Data Format

🤝 Contributing

📄 License

✨ Features
Feature	Description
🦶 Manual Step Log	Add steps manually at any time
🎯 Daily Goal	Set a daily step target (default 10,000)
📊 Progress View	See today's steps with a visual progress bar
📈 History Chart	Show steps for the last 7 days as an ASCII bar chart
🔄 Auto‑Simulation	Simulate step counting (random steps every minute) – great for testing
📉 Statistics	Total steps, average per day, best day, and more
💾 Persistence	All data saved locally in JSON
🎨 Colorful CLI	Beautiful terminal output with ANSI colors
⚡ Cross‑Platform	Works on Windows, macOS, and Linux
📁 Repository Structure
text
step-counter/
├── README.md
├── python/
│   └── step_counter.py
├── javascript/
│   └── step_counter.js
├── typescript/
│   └── step_counter.ts
├── go/
│   └── step_counter.go
├── rust/
│   └── step_counter.rs
├── cpp/
│   └── step_counter.cpp
├── java/
│   └── StepCounter.java
└── csharp/
    └── StepCounter.cs
🚀 Quick Start
Prerequisites
Each language requires its respective runtime/compiler (see individual sections)

Clone & Run
bash
git clone https://github.com/yourusername/step-counter.git
cd step-counter
# Navigate to your language folder and run
💻 Language Implementations
1. 🐍 Python
bash
cd python
pip install rich
python step_counter.py
Requires: Python 3.8+

2. 🟨 JavaScript (Node.js)
bash
cd javascript
node step_counter.js
Requires: Node.js 16+

3. 🟦 TypeScript
bash
cd typescript
npm install -g ts-node
ts-node step_counter.ts
Requires: Node.js 16+, TypeScript

4. 🟩 Go
bash
cd go
go run step_counter.go
Requires: Go 1.18+

5. 🦀 Rust
bash
cd rust
cargo run
Requires: Rust 1.70+ (dependencies: serde, serde_json, chrono, colored, rand)

6. ⚙️ C++
bash
cd cpp
g++ -std=c++17 step_counter.cpp -o step_counter
./step_counter
Requires: C++17 compiler

7. ☕ Java
bash
cd java
javac StepCounter.java
java StepCounter
Requires: JDK 17+

8. 🔷 C#
bash
cd csharp
dotnet run
Requires: .NET 6.0+

📊 Data Format
All implementations store data in ~/.step_counter/data.json:

json
{
  "goal": 10000,
  "entries": [
    {
      "date": "2026-08-18",
      "steps": 7345,
      "timestamp": "2026-08-18T08:15:00Z"
    }
  ]
}
🤝 Contributing
Contributions are welcome! Please:

Fork the repository

Create a feature branch

Commit your changes

Open a Pull Request

📄 License
MIT © 2026 Step Counter Team
