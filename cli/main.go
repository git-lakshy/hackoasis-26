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
	"strings"
)

// ANSI green — only the banner is colored
const green = "\033[32m"
const reset = "\033[0m"

const bannerText = `
 ██████╗  █████╗ ██████╗ ██╗   ██╗██████╗  █████╗  ██████╗ 
 ██╔══██╗██╔══██╗██╔══██╗██║   ██║██╔══██╗██╔══██╗██╔═══██╗
 ██████╔╝███████║██████╔╝██║   ██║██████╔╝███████║██║   ██║
 ██╔══██╗██╔══██║██╔══██╗██║   ██║██╔══██╗██╔══██║██║   ██║
 ██████╔╝██║  ██║██████╔╝╚██████╔╝██║  ██║██║  ██║╚██████╔╝
 ╚═════╝ ╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝

 🤖 Intelligent Infrastructure Cost Optimizer  |  FinOps AI Agent
`

const defaultURL = "https://hackoasis-26.onrender.com"

var baseURL string

func init() {
	baseURL = os.Getenv("FINOPS_API_URL")
	if baseURL == "" {
		baseURL = defaultURL
	}
}

func printBanner() {
	fmt.Print(green + bannerText + reset)
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

// ── Core commands ─────────────────────────────────────────────────────────────

func cmdRun(autoApprove bool) {
	fmt.Println("🚀 Running optimization cycle...")
	data, err := post("/run", nil)
	if err != nil {
		fmt.Println("❌", err)
		return
	}

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
			fmt.Printf("⚠️  %d actions require approval → run: baburao approve\n", len(queue))
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
	cycleRun, _ := data["cycle_run"].(bool)
	if !cycleRun {
		fmt.Println("No cycle run yet. Use: baburao run")
		return
	}
	fmt.Printf("Findings:         %.0f\n", data["findings"].(float64))
	fmt.Printf("Pending approval: %.0f\n", data["pending_approval"].(float64))
	fmt.Printf("Executed:         %.0f\n", data["executed"].(float64))
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
  baburao run [--auto-approve]              Run full optimization cycle
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

Environment:
  FINOPS_API_URL          Override API URL (default: https://hackoasis-26.onrender.com)
  AWS_ACCESS_KEY_ID       AWS credentials
  AWS_SECRET_ACCESS_KEY
  AWS_REGION              (default: us-east-1)
  AZURE_SUBSCRIPTION_ID   Azure credentials
  GCP_PROJECT_ID          GCP project
  KUBECONFIG              Kubernetes config path
  PROMETHEUS_URL          Prometheus URL (default: http://localhost:9090)
  SLACK_WEBHOOK_URL       Slack webhook for alerts`)
}

// ── Main ──────────────────────────────────────────────────────────────────────

func main() {
	if len(os.Args) < 2 {
		usage()
		return
	}

	switch os.Args[1] {
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
	default:
		fmt.Printf("Unknown command: %s\n\n", os.Args[1])
		usage()
	}
}
