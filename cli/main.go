package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
)

const banner = `
 ██████╗  █████╗ ███╗   ██╗ ██████╗██╗  ██╗ ██████╗
 ██╔══██╗██╔══██╗████╗  ██║██╔════╝██║  ██║██╔═══██╗
 ██████╔╝███████║██╔██╗ ██║██║     ███████║██║   ██║
 ██╔══██╗██╔══██║██║╚██╗██║██║     ██╔══██║██║   ██║
 ██║  ██║██║  ██║██║ ╚████║╚██████╗██║  ██║╚██████╔╝
 ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝
          ██████╗ ███╗   ██╗     ██████╗██╗      ██████╗ ██╗   ██╗██████╗
         ██╔═══██╗████╗  ██║    ██╔════╝██║     ██╔═══██╗██║   ██║██╔══██╗
         ██║   ██║██╔██╗ ██║    ██║     ██║     ██║   ██║██║   ██║██║  ██║
         ██║   ██║██║╚██╗██║    ██║     ██║     ██║   ██║██║   ██║██║  ██║
         ╚██████╔╝██║ ╚████║    ╚██████╗███████╗╚██████╔╝╚██████╔╝██████╔╝
          ╚═════╝ ╚═╝  ╚═══╝     ╚═════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝
 🤖 Intelligent Infrastructure Cost Optimizer  |  FinOps AI Agent
`

const defaultURL = "http://localhost:8000"

var baseURL string

func init() {
	baseURL = os.Getenv("FINOPS_API_URL")
	if baseURL == "" {
		baseURL = defaultURL
	}
}

// ── HTTP helpers ──────────────────────────────────────────────────────────────

func post(path string, body any) (map[string]any, error) {
	var r io.Reader
	if body != nil {
		b, _ := json.Marshal(body)
		r = bytes.NewReader(b)
	}
	resp, err := http.Post(baseURL+path, "application/json", r)
	if err != nil {
		return nil, fmt.Errorf("cannot reach API at %s — is the server running?\n  uvicorn api.server:app --port 8000", baseURL)
	}
	defer resp.Body.Close()
	var result map[string]any
	json.NewDecoder(resp.Body).Decode(&result)
	return result, nil
}

func get(path string) (map[string]any, error) {
	resp, err := http.Get(baseURL + path)
	if err != nil {
		return nil, fmt.Errorf("cannot reach API at %s — is the server running?\n  uvicorn api.server:app --port 8000", baseURL)
	}
	defer resp.Body.Close()
	var result map[string]any
	json.NewDecoder(resp.Body).Decode(&result)
	return result, nil
}

// ── Commands ──────────────────────────────────────────────────────────────────

func cmdRun(autoApprove bool) {
	fmt.Println("🚀 Running optimization cycle...")
	data, err := post("/run", nil)
	if err != nil {
		fmt.Println("❌", err)
		return
	}

	// Print agent trace
	if trace, ok := data["trace"].([]any); ok {
		agents := []string{"📡 Monitor", "🔍 Analyst", "⚙️  Optimizer", "⚖️  Trade-off", "🧪 Simulator", "🛡️  Risk", "🚪 Gate"}
		for i, t := range trace {
			prefix := "   "
			if i < len(agents) {
				prefix = agents[i]
			}
			fmt.Printf("  %s → %s\n", prefix, t)
		}
	}

	fmt.Println()

	// Print executed actions
	if executed, ok := data["executed"].([]any); ok && len(executed) > 0 {
		fmt.Printf("✅ Auto-executed %d actions:\n", len(executed))
		for _, e := range executed {
			if rec, ok := e.(map[string]any); ok {
				fmt.Printf("   %-30s %-12s → $%.0f/month saved\n",
					rec["resource_id"], rec["action"], rec["actual_savings"])
			}
		}
		fmt.Println()
	}

	// Print approval queue
	if queue, ok := data["approval_queue"].([]any); ok && len(queue) > 0 {
		if autoApprove {
			var ids []string
			for _, item := range queue {
				if m, ok := item.(map[string]any); ok {
					ids = append(ids, m["resource_id"].(string))
				}
			}
			fmt.Printf("⚡ Auto-approving %d high-risk actions...\n", len(ids))
			cmdApproveIDs(ids)
		} else {
			fmt.Printf("⚠️  %d actions require approval → run: rancho approve\n", len(queue))
			for _, item := range queue {
				if m, ok := item.(map[string]any); ok {
					fmt.Printf("   %-30s %-12s  risk=%-6s  $%.0f/month\n",
						m["resource_id"], m["action"], m["risk_tier"], m["projected_savings"])
				}
			}
		}
	} else {
		fmt.Println("✨ No pending approvals.")
	}
}

func cmdApprove() {
	data, err := get("/run/queue")
	if err != nil {
		fmt.Println("❌", err)
		return
	}
	queue, _ := data["approval_queue"].([]any)
	if len(queue) == 0 {
		fmt.Println("✨ No pending approvals.")
		return
	}

	scanner := bufio.NewScanner(os.Stdin)
	var approvedIDs []string

	for i, item := range queue {
		m, ok := item.(map[string]any)
		if !ok {
			continue
		}
		fmt.Printf("\n[%d/%d] %s %s\n", i+1, len(queue), m["action"], m["resource_id"])
		if factors, ok := m["risk_factors"].([]any); ok {
			for _, f := range factors {
				fmt.Printf("      ⚠️  %s\n", f)
			}
		}
		fmt.Printf("      Savings: $%.0f/month | Confidence: %.0f%%\n",
			m["projected_savings"], m["confidence"].(float64)*100)
		fmt.Print("      Approve? [y/n/s(skip)]: ")
		scanner.Scan()
		switch strings.ToLower(strings.TrimSpace(scanner.Text())) {
		case "y", "yes":
			approvedIDs = append(approvedIDs, m["resource_id"].(string))
			fmt.Println("      ✅ Approved")
		case "n", "no":
			fmt.Println("      ❌ Rejected")
		default:
			fmt.Println("      ⏭️  Skipped")
		}
	}

	if len(approvedIDs) == 0 {
		fmt.Println("\nNo actions approved.")
		return
	}
	fmt.Printf("\nResuming execution for %d approved actions...\n", len(approvedIDs))
	cmdApproveIDs(approvedIDs)
}

func cmdApproveIDs(ids []string) {
	data, err := post("/approve", map[string]any{"approved_ids": ids})
	if err != nil {
		fmt.Println("❌", err)
		return
	}
	if executed, ok := data["executed"].([]any); ok {
		for _, e := range executed {
			if rec, ok := e.(map[string]any); ok {
				fmt.Printf("  ✅ %-30s %-12s → $%.0f/month saved\n",
					rec["resource_id"], rec["action"], rec["actual_savings"])
			}
		}
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
	cycleRun := data["cycle_run"].(bool)
	if !cycleRun {
		fmt.Println("No cycle run yet. Use: rancho run")
		return
	}
	fmt.Printf("Findings:         %.0f\n", data["findings"].(float64))
	fmt.Printf("Pending approval: %.0f\n", data["pending_approval"].(float64))
	fmt.Printf("Executed:         %.0f\n", data["executed"].(float64))
}

// ── Main ──────────────────────────────────────────────────────────────────────

func usage() {
	fmt.Println(banner)
	fmt.Println(`Usage:
  rancho run [--auto-approve]   Run full optimization cycle
  rancho approve                Interactively approve/reject high-risk actions
  rancho log                    Show action log
  rancho chat [query]           Chat with the agent
  rancho status                 Show current cycle status
  rancho reset                  Reset demo state

Environment:
  FINOPS_API_URL   API base URL (default: http://localhost:8000)
                   e.g. export FINOPS_API_URL=https://hackoasis-26.onrender.com`)
}

func main() {
	if len(os.Args) < 2 {
		usage()
		return
	}

	switch os.Args[1] {
	case "run":
		fmt.Println(banner)
		autoApprove := len(os.Args) > 2 && os.Args[2] == "--auto-approve"
		cmdRun(autoApprove)
	case "approve":
		fmt.Println(banner)
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
	default:
		fmt.Printf("Unknown command: %s\n\n", os.Args[1])
		usage()
	}
}
