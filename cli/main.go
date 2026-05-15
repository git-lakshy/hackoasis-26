package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

const version = "1.0.0"

// ANSI color codes
const (
	colorReset   = "\033[0m"
	colorRed     = "\033[31m"
	colorGreen   = "\033[32m"
	colorYellow  = "\033[33m"
	colorBlue    = "\033[34m"
	colorMagenta = "\033[35m"
	colorCyan    = "\033[36m"
	colorWhite   = "\033[37m"
	colorBold    = "\033[1m"
	colorDim     = "\033[2m"
)

const bannerText = ` ██████╗  █████╗ ██████╗ ██╗   ██╗██████╗  █████╗  ██████╗ 
 ██╔══██╗██╔══██╗██╔══██╗██║   ██║██╔══██╗██╔══██╗██╔═══██╗
 ██████╔╝███████║██████╔╝██║   ██║██████╔╝███████║██║   ██║
 ██╔══██╗██╔══██║██╔══██╗██║   ██║██╔══██╗██╔══██║██║   ██║
 ██████╔╝██║  ██║██████╔╝╚██████╔╝██║  ██║██║  ██║╚██████╔╝
 ╚═════╝ ╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝
 🤖 Intelligent Infrastructure Cost Optimizer  |  Baburao AI Agent`

const defaultURL = "https://hackoasis-26.onrender.com"

// Global configuration
type Config struct {
	BaseURL      string
	Debug        bool
	OutputFormat string
	Profile      string
	NoColor      bool
	CloudFilter  string
	EnvFilter    string
	RiskFilter   string
}

var (
	config     Config
	debugLog   bool
	exitCode   = 0
	homeDir, _ = os.UserHomeDir()
	configPath = filepath.Join(homeDir, ".baburao", "config.yaml")
)

// Exit codes
const (
	ExitSuccess       = 0
	ExitError         = 1
	ExitUsageError    = 2
	ExitNetworkError  = 3
	ExitAPIError      = 4
	ExitConfigError   = 5
	ExitUserCancelled = 130
)

func init() {
	// Load configuration from environment and config file
	config.BaseURL = os.Getenv("BABURAO_API_URL")
	if config.BaseURL == "" {
		config.BaseURL = defaultURL
	}
	config.Profile = os.Getenv("BABURAO_PROFILE")
	if config.Profile == "" {
		config.Profile = "default"
	}

	// Try to load config file
	loadConfigFile()
}

// ── Configuration file support ────────────────────────────────────────────────

func loadConfigFile() {
	// Check if config file exists
	if _, err := os.Stat(configPath); os.IsNotExist(err) {
		return
	}

	data, err := os.ReadFile(configPath)
	if err != nil {
		return
	}

	// Simple YAML-like parsing for basic key-value pairs
	lines := strings.Split(string(data), "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.SplitN(line, ":", 2)
		if len(parts) != 2 {
			continue
		}
		key := strings.TrimSpace(parts[0])
		value := strings.TrimSpace(parts[1])

		switch key {
		case "api_url":
			if config.BaseURL == defaultURL {
				config.BaseURL = value
			}
		case "default_profile":
			if config.Profile == "default" {
				config.Profile = value
			}
		case "output_format":
			config.OutputFormat = value
		case "no_color":
			config.NoColor = value == "true"
		}
	}
}

func createDefaultConfig() error {
	configDir := filepath.Dir(configPath)
	if err := os.MkdirAll(configDir, 0755); err != nil {
		return err
	}

	defaultConfig := `# Baburao CLI Configuration
# API endpoint
api_url: https://hackoasis-26.onrender.com

# Default profile (dev, staging, prod)
default_profile: default

# Output format (table, json, yaml)
output_format: table

# Disable colors
no_color: false
`

	return os.WriteFile(configPath, []byte(defaultConfig), 0644)
}

// ── Color and formatting helpers ──────────────────────────────────────────────

func colorize(color, text string) string {
	if config.NoColor {
		return text
	}
	return color + text + colorReset
}

func printBanner() {
	fmt.Println(colorize(colorGreen, bannerText))
}

func printSuccess(msg string) {
	fmt.Println(colorize(colorGreen, "✅ "+msg))
}

func printError(msg string) {
	fmt.Fprintln(os.Stderr, colorize(colorRed, "❌ "+msg))
}

func printWarning(msg string) {
	fmt.Println(colorize(colorYellow, "⚠️  "+msg))
}

func printInfo(msg string) {
	fmt.Println(colorize(colorCyan, "ℹ️  "+msg))
}

func printDebug(msg string) {
	if debugLog {
		fmt.Println(colorize(colorDim, "[DEBUG] "+msg))
	}
}

func printProgress(msg string) {
	fmt.Print(colorize(colorBlue, "⏳ "+msg))
}

func clearProgress() {
	fmt.Print("\r" + strings.Repeat(" ", 80) + "\r")
}

// ── Table formatting ──────────────────────────────────────────────────────────

func printTable(headers []string, rows [][]string) {
	if config.OutputFormat == "json" {
		printTableJSON(headers, rows)
		return
	}
	if config.OutputFormat == "yaml" {
		printTableYAML(headers, rows)
		return
	}

	// Calculate column widths
	widths := make([]int, len(headers))
	for i, h := range headers {
		widths[i] = len(h)
	}
	for _, row := range rows {
		for i, cell := range row {
			if i < len(widths) && len(cell) > widths[i] {
				widths[i] = len(cell)
			}
		}
	}

	// Print header
	fmt.Print(colorize(colorBold, ""))
	for i, h := range headers {
		fmt.Printf("%-*s  ", widths[i], h)
	}
	fmt.Println(colorize(colorReset, ""))

	// Print separator
	for _, w := range widths {
		fmt.Print(strings.Repeat("─", w+2))
	}
	fmt.Println()

	// Print rows
	for _, row := range rows {
		for i, cell := range row {
			if i < len(widths) {
				fmt.Printf("%-*s  ", widths[i], cell)
			}
		}
		fmt.Println()
	}
}

func printTableJSON(headers []string, rows [][]string) {
	var result []map[string]string
	for _, row := range rows {
		item := make(map[string]string)
		for i, cell := range row {
			if i < len(headers) {
				item[headers[i]] = cell
			}
		}
		result = append(result, item)
	}
	data, _ := json.MarshalIndent(result, "", "  ")
	fmt.Println(string(data))
}

func printTableYAML(headers []string, rows [][]string) {
	for idx, row := range rows {
		fmt.Printf("- item_%d:\n", idx+1)
		for i, cell := range row {
			if i < len(headers) {
				fmt.Printf("    %s: %s\n", headers[i], cell)
			}
		}
	}
}

// ── HTTP helpers ──────────────────────────────────────────────────────────────

func post(path string, body any) (map[string]any, error) {
	printDebug(fmt.Sprintf("POST %s%s", config.BaseURL, path))

	var r io.Reader
	if body != nil {
		b, _ := json.Marshal(body)
		r = bytes.NewReader(b)
		printDebug(fmt.Sprintf("Request body: %s", string(b)))
	}

	resp, err := http.Post(config.BaseURL+path, "application/json", r)
	if err != nil {
		printDebug(fmt.Sprintf("HTTP error: %v", err))
		return nil, fmt.Errorf("cannot reach API at %s — is the server running?\n  uvicorn api.server:app --port 8000", config.BaseURL)
	}
	defer resp.Body.Close()

	printDebug(fmt.Sprintf("Response status: %d", resp.StatusCode))

	var result map[string]any
	json.NewDecoder(resp.Body).Decode(&result)
	return result, nil
}

func get(path string) (map[string]any, error) {
	printDebug(fmt.Sprintf("GET %s%s", config.BaseURL, path))

	resp, err := http.Get(config.BaseURL + path)
	if err != nil {
		printDebug(fmt.Sprintf("HTTP error: %v", err))
		return nil, fmt.Errorf("cannot reach API at %s — is the server running?\n  uvicorn api.server:app --port 8000", config.BaseURL)
	}
	defer resp.Body.Close()

	printDebug(fmt.Sprintf("Response status: %d", resp.StatusCode))

	var result map[string]any
	json.NewDecoder(resp.Body).Decode(&result)
	return result, nil
}

// ── Filter helpers ────────────────────────────────────────────────────────────

func applyFilters(items []any) []any {
	if config.CloudFilter == "" && config.EnvFilter == "" && config.RiskFilter == "" {
		return items
	}

	var filtered []any
	for _, item := range items {
		m, ok := item.(map[string]any)
		if !ok {
			continue
		}

		// Cloud filter
		if config.CloudFilter != "" {
			if cloud, ok := m["cloud"].(string); ok {
				if !strings.EqualFold(cloud, config.CloudFilter) {
					continue
				}
			}
		}

		// Environment filter
		if config.EnvFilter != "" {
			if env, ok := m["environment"].(string); ok {
				if !strings.EqualFold(env, config.EnvFilter) {
					continue
				}
			}
		}

		// Risk filter
		if config.RiskFilter != "" {
			if risk, ok := m["risk_tier"].(string); ok {
				if !strings.EqualFold(risk, config.RiskFilter) {
					continue
				}
			}
		}

		filtered = append(filtered, item)
	}

	return filtered
}

// ── Core commands ─────────────────────────────────────────────────────────────

// cmdScan calls the API to run the optimization cycle, streaming agent progress.
func cmdScan() (map[string]any, error) {
	agentNames := map[string]string{
		"MonitorAgent":     "📡 Monitor",
		"AnalystAgent":     "🔍 Analyst",
		"OptimizerAgent":   "⚙️  Optimizer",
		"TradeoffAgent":    "⚖️  Trade-off",
		"SimulatorAgent":   "🧪 Simulator",
		"RiskAgent":        "🛡️  Risk",
		"GateAgent":        "🚪 Gate",
	}

	fmt.Println()
	fmt.Println(colorize(colorBold, "  🤖 Supervisor spawning analysis agents..."))
	fmt.Println(colorize(colorDim, "  "+strings.Repeat("─", 55)))

	data, err := post("/api/v1/run", nil)
	if err != nil {
		return nil, err
	}

	if trace, ok := data["trace"].([]any); ok {
		for _, t := range trace {
			s, ok := t.(string)
			if !ok {
				continue
			}
			for key, icon := range agentNames {
				if strings.Contains(s, strings.Split(key, "Agent")[0]) {
					fmt.Printf("    %s → %s\n", colorize(colorCyan, icon), s)
					break
				}
			}
		}
	}
	fmt.Println()
	return data, nil
}

func cmdRun(autoApprove bool) {
	data, err := cmdScan()
	if err != nil {
		printError(err.Error())
		exitCode = ExitNetworkError
		return
	}

	if executed, ok := data["executed"].([]any); ok && len(executed) > 0 {
		executed = applyFilters(executed)
		if len(executed) > 0 {
			printSuccess(fmt.Sprintf("Auto-executed %d actions:", len(executed)))
			headers := []string{"Resource ID", "Action", "Savings ($/mo)"}
			var rows [][]string
			for _, e := range executed {
				if rec, ok := e.(map[string]any); ok {
					rows = append(rows, []string{
						fmt.Sprintf("%v", rec["resource_id"]),
						fmt.Sprintf("%v", rec["action"]),
						fmt.Sprintf("%.0f", rec["actual_savings"]),
					})
				}
			}
			printTable(headers, rows)
			fmt.Println()
		}
	}

	if queue, ok := data["approval_queue"].([]any); ok && len(queue) > 0 {
		queue = applyFilters(queue)
		if len(queue) > 0 {
			if autoApprove {
				var ids []string
				for _, item := range queue {
					if m, ok := item.(map[string]any); ok {
						ids = append(ids, m["resource_id"].(string))
					}
				}
				printInfo(fmt.Sprintf("Auto-approving %d high-risk actions...", len(ids)))
				cmdApproveIDs(ids)
			} else {
				printWarning(fmt.Sprintf("%d actions require approval → run: baburao approve", len(queue)))

				headers := []string{"Resource ID", "Action", "Risk", "Savings ($/mo)"}
				var rows [][]string
				for _, item := range queue {
					if m, ok := item.(map[string]any); ok {
						rows = append(rows, []string{
							fmt.Sprintf("%v", m["resource_id"]),
							fmt.Sprintf("%v", m["action"]),
							fmt.Sprintf("%v", m["risk_tier"]),
							fmt.Sprintf("%.0f", m["projected_savings"]),
						})
					}
				}
				printTable(headers, rows)
			}
		}
	} else {
		printSuccess("No pending approvals.")
	}
}

func cmdApprove() {
	data, err := get("/run/queue")
	if err != nil {
		printError(err.Error())
		exitCode = ExitNetworkError
		return
	}
	queue, _ := data["approval_queue"].([]any)
	queue = applyFilters(queue)

	if len(queue) == 0 {
		printSuccess("No pending approvals.")
		return
	}

	scanner := bufio.NewScanner(os.Stdin)
	var approvedIDs []string

	for i, item := range queue {
		m, ok := item.(map[string]any)
		if !ok {
			continue
		}
		fmt.Printf("\n%s[%d/%d]%s %s %s\n",
			colorBold, i+1, len(queue), colorReset,
			colorize(colorYellow, fmt.Sprintf("%v", m["action"])),
			colorize(colorCyan, fmt.Sprintf("%v", m["resource_id"])))

		if factors, ok := m["risk_factors"].([]any); ok {
			for _, f := range factors {
				printWarning(fmt.Sprintf("  %s", f))
			}
		}

		confidence := 0.0
		if c, ok := m["confidence"].(float64); ok {
			confidence = c * 100
		}

		fmt.Printf("      %s: $%.0f/month | %s: %.0f%%\n",
			colorize(colorGreen, "Savings"),
			m["projected_savings"],
			colorize(colorBlue, "Confidence"),
			confidence)

		fmt.Print("      Approve? [y/n/s(skip)]: ")
		scanner.Scan()
		response := strings.ToLower(strings.TrimSpace(scanner.Text()))

		switch response {
		case "y", "yes":
			approvedIDs = append(approvedIDs, m["resource_id"].(string))
			printSuccess("      Approved")
		case "n", "no":
			printError("      Rejected")
		default:
			printInfo("      Skipped")
		}
	}

	if len(approvedIDs) == 0 {
		printInfo("No actions approved.")
		return
	}

	printInfo(fmt.Sprintf("Resuming execution for %d approved actions...", len(approvedIDs)))
	cmdApproveIDs(approvedIDs)
}

func cmdApproveIDs(ids []string) {
	data, err := post("/approve", map[string]any{"approved_ids": ids})
	if err != nil {
		printError(err.Error())
		exitCode = ExitNetworkError
		return
	}

	if executed, ok := data["executed"].([]any); ok {
		headers := []string{"Resource ID", "Action", "Savings ($/mo)"}
		var rows [][]string
		for _, e := range executed {
			if rec, ok := e.(map[string]any); ok {
				rows = append(rows, []string{
					fmt.Sprintf("%v", rec["resource_id"]),
					fmt.Sprintf("%v", rec["action"]),
					fmt.Sprintf("%.0f", rec["actual_savings"]),
				})
			}
		}
		printTable(headers, rows)
	}
}

func cmdLog() {
	data, err := get("/log")
	if err != nil {
		fmt.Println("❌", err)
		return
	}
	log, ok := data["log"].([]any)
	if !ok || len(log) == 0 {
		fmt.Println("No actions logged yet.")
		return
	}
	fmt.Printf("%-10s %-30s %-12s %-8s %-14s %-10s\n",
		"ID", "Resource", "Action", "Risk", "Saved ($/mo)", "Accuracy")
	fmt.Println(strings.Repeat("─", 90))
	for _, entry := range log {
		r, ok := entry.(map[string]any)
		if !ok {
			continue
		}
		accuracy := "N/A"
		if a, ok := r["accuracy"].(float64); ok {
			accuracy = fmt.Sprintf("%.0f%%", a*100)
		}
		saved := 0.0
		if s, ok := r["actual_savings"].(float64); ok {
			saved = s
		}
		fmt.Printf("%-10s %-30s %-12s %-8s $%-13.0f %-10s\n",
			r["action_id"], r["resource_id"], r["action"], r["risk_tier"], saved, accuracy)
	}
}

func cmdChat(query string) {
	if query == "" {
		scanner := bufio.NewScanner(os.Stdin)
		fmt.Print("💬 Ask: ")
		scanner.Scan()
		query = scanner.Text()
	}
	data, err := post("/chat", map[string]any{"query": query})
	if err != nil {
		fmt.Println("❌", err)
		return
	}
	fmt.Println(data["response"])
}

func cmdReset() {
	_, err := post("/reset", nil)
	if err != nil {
		fmt.Println("❌", err)
		return
	}
	fmt.Println("✅ Demo state reset.")
}

func cmdStatus() {
	data, err := get("/status")
	if err != nil {
		fmt.Println("❌", err)
		return
	}
	cycleRun, _ := data["cycle_run"].(bool)
	if !cycleRun {
		fmt.Println("No cycle run yet. Use: baburao run")
		return
	}
	fmt.Printf("Findings:         %.0f\n", data["findings"].(float64))
	fmt.Printf("Pending approval: %.0f\n", data["pending_approval"].(float64))
	fmt.Printf("Executed:         %.0f\n", data["executed"].(float64))
}

// ── Decide command (Multi-Agent Debate) ──────────────────────────────────────

func cmdDecide() {
	printInfo("Running multi-agent debate for optimization decisions...")
	printProgress("Agents are arguing...")

	data, err := post("/api/v1/decide", nil)
	if err != nil {
		clearProgress()
		printError(err.Error())
		exitCode = ExitNetworkError
		return
	}
	clearProgress()

	debates, ok := data["debates"].([]any)
	if !ok || len(debates) == 0 {
		printWarning("No debates to show. Run 'baburao run' first.")
		return
	}

	printSuccess(fmt.Sprintf("Completed %d agent debates", len(debates)))
	fmt.Println()

	for i, debate := range debates {
		d, ok := debate.(map[string]any)
		if !ok {
			continue
		}

		fmt.Printf("%s═══ Debate #%d: %s ═══%s\n",
			colorBold, i+1, d["resource_id"], colorReset)
		fmt.Printf("Proposed Action: %s\n", colorize(colorCyan, fmt.Sprintf("%v", d["original_action"])))
		fmt.Println()

		// Show agent arguments
		if rounds, ok := d["debate_rounds"].([]any); ok && len(rounds) > 0 {
			if round1, ok := rounds[0].([]any); ok {
				for _, arg := range round1 {
					if a, ok := arg.(map[string]any); ok {
						position := fmt.Sprintf("%v", a["position"])
						emoji := "✅"
						color := colorGreen
						if position == "oppose" {
							emoji = "❌"
							color = colorRed
						} else if position == "compromise" {
							emoji = "⚖️"
							color = colorYellow
						}

						fmt.Printf("%s [%s] %s\n",
							emoji,
							colorize(colorBold, fmt.Sprintf("%v", a["agent_name"])),
							position)
						fmt.Printf("  %s\n", colorize(color, fmt.Sprintf("%v", a["reasoning"])))

						if alt, ok := a["alternative"].(string); ok && alt != "" {
							fmt.Printf("  %s %s\n", colorize(colorCyan, "Alternative:"), alt)
						}

						if conf, ok := a["confidence"].(float64); ok {
							fmt.Printf("  Confidence: %.0f%%\n", conf*100)
						}
						fmt.Println()
					}
				}
			}
		}

		// Show consensus decision
		decision := fmt.Sprintf("%v", d["final_decision"])
		decisionColor := colorGreen
		decisionEmoji := "🤝"
		if decision == "rejected" {
			decisionColor = colorRed
			decisionEmoji = "🚫"
		} else if decision == "modified" {
			decisionColor = colorYellow
			decisionEmoji = "🔄"
		}

		fmt.Printf("%s %s Decision: %s\n",
			decisionEmoji,
			colorize(colorBold, "[ConsensusAgent]"),
			colorize(decisionColor, strings.ToUpper(decision)))
		fmt.Printf("  Action: %s\n", colorize(colorCyan, fmt.Sprintf("%v", d["consensus_action"])))
		fmt.Printf("  Reasoning: %s\n", d["consensus_reasoning"])

		if conf, ok := d["confidence"].(float64); ok {
			fmt.Printf("  Confidence: %.0f%%\n", conf*100)
		}

		fmt.Println()
		fmt.Println(strings.Repeat("─", 80))
		fmt.Println()
	}

	// Summary
	approved := 0
	rejected := 0
	modified := 0
	for _, debate := range debates {
		if d, ok := debate.(map[string]any); ok {
			decision := fmt.Sprintf("%v", d["final_decision"])
			switch decision {
			case "approved":
				approved++
			case "rejected":
				rejected++
			case "modified":
				modified++
			}
		}
	}

	fmt.Println(colorize(colorBold, "Summary:"))
	fmt.Printf("  %s Approved: %d\n", colorize(colorGreen, "✅"), approved)
	fmt.Printf("  %s Modified: %d\n", colorize(colorYellow, "🔄"), modified)
	fmt.Printf("  %s Rejected: %d\n", colorize(colorRed, "🚫"), rejected)
}

// ── Demo command ──────────────────────────────────────────────────────────────

func cmdDemo() {
	printBanner()
	fmt.Println(colorize(colorBold, "\n  🚀 Starting Baburao Demo Cycle"))
	fmt.Println(colorize(colorDim, "  Mock cloud data with real Groq LLM agent debate"))

	// Step 1: Scan
	fmt.Println(colorize(colorBold, "\n  ─── Step 1: Infrastructure Scan ───────────────────"))
	data, err := cmdScan()
	if err != nil {
		printError(err.Error())
		return
	}
	showScanSummary(data)
	showApprovalQueue(data, false)

	// Step 2: LLM Debate
	fmt.Println(colorize(colorBold, "\n  ─── Step 2: Multi-Agent LLM Debate ────────────────"))
	fmt.Println(colorize(colorDim, "  Spawning debate agents (powered by Groq LLaMA-3.3-70b)..."))
	cmdDecide()

	fmt.Println(colorize(colorBold, "\n  ✨ Demo Cycle Complete!"))
	fmt.Println(colorize(colorDim, "  Run 'baburao agent' for the full interactive experience."))
}

// ── Interactive Agent command ─────────────────────────────────────────────────

func cmdAgent() {
	printBanner()
	fmt.Println(colorize(colorBold, "\n  🤖 Baburao Interactive Agent"))
	fmt.Println(colorize(colorDim, "  Supervisor ready. Choose an action to begin."))

	reader := bufio.NewReader(os.Stdin)

	for {
		fmt.Println()
		fmt.Println(colorize(colorBold, "  What would you like to do?"))
		fmt.Println(colorize(colorDim, "  "+strings.Repeat("─", 48)))
		fmt.Println("  " + colorize(colorCyan, "[1]") + " 🔍 Scan infrastructure & identify waste")
		fmt.Println("  " + colorize(colorCyan, "[2]") + " 📈 Scan + Run simulation & cost forecast")
		fmt.Println("  " + colorize(colorCyan, "[3]") + " 🗣️  Scan + Multi-agent LLM debate")
		fmt.Println("  " + colorize(colorCyan, "[4]") + " 🚀 Full cycle (scan + debate + approve)")
		fmt.Println("  " + colorize(colorCyan, "[5]") + " ✅ Review & approve pending actions")
		fmt.Println("  " + colorize(colorCyan, "[6]") + " 📊 Open TUI dashboard")
		fmt.Println("  " + colorize(colorCyan, "[7]") + " 💬 Chat with agent")
		fmt.Println("  " + colorize(colorCyan, "[q]") + " Exit")
		fmt.Println()
		fmt.Print(colorize(colorYellow, "  Choice: "))

		choice, _ := reader.ReadString('\n')
		choice = strings.TrimSpace(choice)

		switch choice {
		case "1":
			data, err := cmdScan()
			if err != nil {
				printError(err.Error())
				continue
			}
			showScanSummary(data)
			showApprovalQueue(data, false)

		case "2":
			data, err := cmdScan()
			if err != nil {
				printError(err.Error())
				continue
			}
			showScanSummary(data)
			fmt.Println(colorize(colorBold, "\n  📈 Simulation & Forecast"))
			fmt.Println(colorize(colorDim, "  Opening 12-month savings projection..."))
			cmdDashboard()

		case "3":
			data, err := cmdScan()
			if err != nil {
				printError(err.Error())
				continue
			}
			showScanSummary(data)
			showApprovalQueue(data, false)
			fmt.Println()
			cmdDecide()

		case "4":
			data, err := cmdScan()
			if err != nil {
				printError(err.Error())
				continue
			}
			showScanSummary(data)
			showApprovalQueue(data, false)
			fmt.Println()
			cmdDecide()
			fmt.Println()
			cmdApprove()

		case "5":
			cmdApprove()

		case "6":
			cmdDashboard()

		case "7":
			fmt.Print(colorize(colorCyan, "\n  You: "))
			q, _ := reader.ReadString('\n')
			q = strings.TrimSpace(q)
			if q != "" {
				cmdChat(q)
			}

		case "q", "Q", "exit", "quit":
			fmt.Println(colorize(colorDim, "\n  Goodbye! 👋"))
			return

		default:
			fmt.Println(colorize(colorYellow, "  Invalid choice. Enter 1-7 or q."))
		}
	}
}

func showScanSummary(data map[string]any) {
	findings, _ := data["findings_count"].(float64)
	opps, _ := data["opportunities_count"].(float64)
	pending, _ := data["pending_approval"].(float64)
	fmt.Printf("\n  %s Found %s%d%s issues | %s%d%s optimizable | %s%d%s need approval\n",
		colorize(colorGreen, "✓"),
		colorize(colorBold, ""), int(findings), colorize(colorReset, ""),
		colorize(colorBold, ""), int(opps), colorize(colorReset, ""),
		colorize(colorYellow, ""), int(pending), colorize(colorReset, ""),
	)
}

func showApprovalQueue(data map[string]any, autoApprove bool) {
	queue, ok := data["approval_queue"].([]any)
	if !ok || len(queue) == 0 {
		printSuccess("  No pending approvals.")
		return
	}
	queue = applyFilters(queue)
	if len(queue) == 0 {
		return
	}
	if autoApprove {
		var ids []string
		for _, item := range queue {
			if m, ok := item.(map[string]any); ok {
				ids = append(ids, fmt.Sprintf("%v", m["resource_id"]))
			}
		}
		cmdApproveIDs(ids)
		return
	}
	printWarning(fmt.Sprintf("  %d high-risk actions need approval:", len(queue)))
	headers := []string{"Resource ID", "Action", "Risk", "Savings ($/mo)"}
	var rows [][]string
	for _, item := range queue {
		if m, ok := item.(map[string]any); ok {
			rows = append(rows, []string{
				fmt.Sprintf("%v", m["resource_id"]),
				fmt.Sprintf("%v", m["action"]),
				fmt.Sprintf("%v", m["risk_tier"]),
				fmt.Sprintf("%.0f", m["projected_savings"]),
			})
		}
	}
	printTable(headers, rows)
}

// ── Kubernetes command ────────────────────────────────────────────────────────

func cmdK8s(sub string) {
	switch sub {
	case "scan", "":
		fmt.Println("☸️  Scanning Kubernetes cluster for waste...")
		data, err := get("/k8s/scan")
		if err != nil {
			fmt.Println("❌", err)
			return
		}
		findings, _ := data["findings"].([]any)
		if len(findings) == 0 {
			fmt.Println("✨ No Kubernetes waste found.")
			return
		}
		fmt.Printf("Found %d findings:\n", len(findings))
		for _, f := range findings {
			if m, ok := f.(map[string]any); ok {
				fmt.Printf("  %-40s %-12s  $%.0f/mo  %s\n",
					m["resource_id"], m["waste_type"], m["monthly_cost"], m["recommendation"])
			}
		}
	case "nodes":
		fmt.Println("☸️  Kubernetes node summary:")
		data, err := get("/k8s/nodes")
		if err != nil {
			fmt.Println("❌", err)
			return
		}
		nodes, _ := data["nodes"].([]any)
		fmt.Printf("%-30s %-12s %-12s %-8s\n", "Node", "CPU Cap", "Mem (MB)", "Ready")
		fmt.Println(strings.Repeat("─", 70))
		for _, n := range nodes {
			if m, ok := n.(map[string]any); ok {
				ready := "✅"
				if r, ok := m["ready"].(bool); ok && !r {
					ready = "❌"
				}
				fmt.Printf("%-30s %-12s %-12.0f %-8s\n",
					m["name"], m["cpu_capacity"], m["mem_capacity_mb"], ready)
			}
		}
	default:
		fmt.Printf("Unknown k8s subcommand: %s\n", sub)
		fmt.Println("Usage: baburao k8s [scan|nodes]")
	}
}

// ── Prometheus command ────────────────────────────────────────────────────────

func cmdPrometheus(sub string) {
	switch sub {
	case "idle", "":
		fmt.Println("📊 Querying Prometheus for idle instances...")
		data, err := get("/prometheus/idle")
		if err != nil {
			fmt.Println("❌", err)
			return
		}
		instances, _ := data["idle_instances"].([]any)
		if len(instances) == 0 {
			fmt.Println("✨ No idle instances found in Prometheus.")
			return
		}
		fmt.Printf("%-40s %-12s\n", "Instance", "CPU Avg")
		fmt.Println(strings.Repeat("─", 55))
		for _, inst := range instances {
			if m, ok := inst.(map[string]any); ok {
				fmt.Printf("%-40s %.4f\n", m["instance"], m["cpu_avg"])
			}
		}
	case "status":
		data, err := get("/prometheus/status")
		if err != nil {
			fmt.Println("❌", err)
			return
		}
		if avail, ok := data["available"].(bool); ok && avail {
			fmt.Printf("✅ Prometheus reachable at %s\n", data["url"])
		} else {
			fmt.Printf("❌ Prometheus not reachable at %s\n", data["url"])
		}
	default:
		fmt.Printf("Unknown prometheus subcommand: %s\n", sub)
		fmt.Println("Usage: baburao prometheus [idle|status]")
	}
}

// ── Terraform command ─────────────────────────────────────────────────────────

func cmdTerraform(args []string) {
	if len(args) == 0 {
		fmt.Println("Usage: baburao terraform <plan|apply> <resource_id> <action> [--apply]")
		return
	}

	sub := args[0]
	switch sub {
	case "plan":
		if len(args) < 3 {
			fmt.Println("Usage: baburao terraform plan <resource_id> <action>")
			return
		}
		resourceID, action := args[1], args[2]
		fmt.Printf("🏗️  Generating Terraform plan for %s (%s)...\n", resourceID, action)
		data, err := post("/terraform/plan", map[string]any{
			"resource_id": resourceID,
			"action":      action,
			"dry_run":     true,
		})
		if err != nil {
			fmt.Println("❌", err)
			return
		}
		if errMsg, ok := data["error"].(string); ok {
			fmt.Println("❌", errMsg)
			return
		}
		fmt.Println("📋 Terraform Plan:")
		fmt.Println(data["plan"])

	case "apply":
		if len(args) < 3 {
			fmt.Println("Usage: baburao terraform apply <resource_id> <action>")
			return
		}
		resourceID, action := args[1], args[2]
		fmt.Printf("⚡ Applying Terraform for %s (%s)...\n", resourceID, action)
		scanner := bufio.NewScanner(os.Stdin)
		fmt.Print("This will make real infrastructure changes. Confirm? [yes/no]: ")
		scanner.Scan()
		if strings.ToLower(strings.TrimSpace(scanner.Text())) != "yes" {
			fmt.Println("Aborted.")
			return
		}
		data, err := post("/terraform/plan", map[string]any{
			"resource_id": resourceID,
			"action":      action,
			"dry_run":     false,
		})
		if err != nil {
			fmt.Println("❌", err)
			return
		}
		if errMsg, ok := data["error"].(string); ok {
			fmt.Println("❌", errMsg)
			return
		}
		if success, ok := data["success"].(bool); ok && success {
			fmt.Println("✅ Terraform apply succeeded.")
			fmt.Println(data["output"])
		} else {
			fmt.Println("❌ Terraform apply failed:", data["error"])
		}

	case "version":
		out, err := exec.Command("terraform", "version").Output()
		if err != nil {
			fmt.Println("❌ terraform not found in PATH")
			return
		}
		fmt.Print(string(out))

	default:
		fmt.Printf("Unknown terraform subcommand: %s\n", sub)
		fmt.Println("Usage: baburao terraform [plan|apply|version]")
	}
}

// ── Usage ─────────────────────────────────────────────────────────────────────

func usage() {
	printBanner()
	fmt.Println(`Usage:
  baburao dashboard                         Open interactive TUI dashboard
  baburao login                             Interactive authentication setup
  baburao demo                              Run full demo (run cycle + agent debate)
  baburao agent                             🤖 Interactive AI agent (recommended)
  baburao dashboard                         Open interactive TUI dashboard
  baburao login                             Configure cloud credentials & notifications
  baburao demo                              Full demo: scan + LLM debate
  baburao run [--auto-approve]              Run full optimization cycle
  baburao decide                            Multi-agent LLM debate for decisions
  baburao approve                           Interactively approve/reject high-risk actions
  baburao log                               Show action log
  baburao chat [query]                      Chat with the agent
  baburao status                            Show current cycle status
  baburao reset                             Reset demo state

  baburao k8s [scan|nodes]                  Kubernetes waste scan / node summary
  baburao prometheus [idle|status]          Prometheus idle instance query
  baburao terraform plan <id> <action>      Generate Terraform plan (dry-run)
  baburao terraform apply <id> <action>     Apply Terraform plan (real changes)
  baburao terraform version                 Show Terraform version

  baburao version                           Show version information
  baburao config [init]                     Show or initialize configuration

Environment:
  BABURAO_API_URL         Override API URL (default: https://hackoasis-26.onrender.com)
  AWS_ACCESS_KEY_ID       AWS credentials
  GROQ_API_KEY            Groq API key for LLM agent debate
  SLACK_WEBHOOK_URL       Slack webhook for alerts
  TWILIO_ACCOUNT_SID      Twilio SID for SMS notifications`)
}

// ── Main ──────────────────────────────────────────────────────────────────────

func main() {
	if len(os.Args) < 2 {
		usage()
		return
	}

	switch os.Args[1] {
	case "dashboard":
		cmdDashboard()
	case "login":
		cmdLogin()
	case "agent":
		cmdAgent()
	case "demo":
		cmdDemo()
	case "run":
		printBanner()
		autoApprove := len(os.Args) > 2 && os.Args[2] == "--auto-approve"
		cmdRun(autoApprove)
	case "approve":
		printBanner()
		cmdApprove()
	case "log":
		cmdLog()
	case "chat":
		query := ""
		if len(os.Args) > 2 {
			query = strings.Join(os.Args[2:], " ")
		}
		cmdChat(query)
	case "status":
		cmdStatus()
	case "reset":
		cmdReset()
	case "k8s":
		sub := ""
		if len(os.Args) > 2 {
			sub = os.Args[2]
		}
		cmdK8s(sub)
	case "prometheus":
		sub := ""
		if len(os.Args) > 2 {
			sub = os.Args[2]
		}
		cmdPrometheus(sub)
	case "terraform":
		args := []string{}
		if len(os.Args) > 2 {
			args = os.Args[2:]
		}
		cmdTerraform(args)
	case "version", "--version", "-v":
		fmt.Printf("Baburao CLI v%s\n", version)
		fmt.Printf("API: %s\n", config.BaseURL)
	case "decide":
		printBanner()
		cmdDecide()
	case "config":
		if len(os.Args) > 2 && os.Args[2] == "init" {
			if err := createDefaultConfig(); err != nil {
				printError(fmt.Sprintf("Failed to create config: %v", err))
				exitCode = ExitConfigError
			} else {
				printSuccess(fmt.Sprintf("Config created at %s", configPath))
			}
		} else {
			fmt.Printf("Config file: %s\n", configPath)
			fmt.Printf("API URL: %s\n", config.BaseURL)
			fmt.Printf("Profile: %s\n", config.Profile)
			fmt.Printf("Output format: %s\n", config.OutputFormat)
		}
	default:
		fmt.Printf("Unknown command: %s\n\n", os.Args[1])
		usage()
	}

	os.Exit(exitCode)
}
