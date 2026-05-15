package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// ── Auth / Login command ──────────────────────────────────────────────────────

func promptLine(reader *bufio.Reader, prompt string) string {
	fmt.Print(colorize(colorCyan, "  → ")+prompt+" ")
	text, _ := reader.ReadString('\n')
	return strings.TrimSpace(text)
}

func promptSection(title string) {
	fmt.Println()
	fmt.Println(colorize(colorBold, "  "+title))
	fmt.Println(colorize(colorDim, "  "+strings.Repeat("─", 48)))
}

func askProviderBlock(reader *bufio.Reader, providerName string, fields []struct{ key, label, def string }) map[string]string {
	result := map[string]string{}
	fmt.Print(colorize(colorYellow, "\n  Configure "+providerName+"? [y/N] "))
	ans, _ := reader.ReadString('\n')
	if !strings.HasPrefix(strings.ToLower(strings.TrimSpace(ans)), "y") {
		fmt.Println(colorize(colorDim, "  Skipped "+providerName+"."))
		return result
	}
	for _, f := range fields {
		label := f.label
		if f.def != "" {
			label = fmt.Sprintf("%s (default: %s)", label, f.def)
		}
		val := promptLine(reader, label+":")
		if val == "" {
			val = f.def
		}
		if val != "" {
			result[f.key] = val
		}
	}
	return result
}

func cmdLogin() {
	printBanner()
	fmt.Println(colorize(colorBold, "\n  🔐 Baburao Credential Setup"))
	fmt.Println(colorize(colorDim, "  Configure your cloud & notification credentials."))
	fmt.Println(colorize(colorDim, "  Press Enter to skip any provider you don't use."))

	reader := bufio.NewReader(os.Stdin)
	config := map[string]string{}

	// Load existing config to merge
	home, _ := os.UserHomeDir()
	configPath := filepath.Join(home, ".baburao", "config.json")
	if data, err := os.ReadFile(configPath); err == nil {
		var existing map[string]string
		if json.Unmarshal(data, &existing) == nil {
			for k, v := range existing {
				config[k] = v
			}
		}
	}

	// ── AWS
	promptSection("☁️  AWS")
	awsFields := []struct{ key, label, def string }{
		{"AWS_ACCESS_KEY_ID", "Access Key ID", ""},
		{"AWS_SECRET_ACCESS_KEY", "Secret Access Key", ""},
		{"AWS_REGION", "Region", "us-east-1"},
	}
	for k, v := range askProviderBlock(reader, "AWS", awsFields) {
		config[k] = v
	}

	// ── GCP
	promptSection("☁️  Google Cloud")
	gcpFields := []struct{ key, label, def string }{
		{"GCP_PROJECT_ID", "Project ID", ""},
		{"GOOGLE_APPLICATION_CREDENTIALS", "Service Account JSON path", ""},
	}
	for k, v := range askProviderBlock(reader, "Google Cloud", gcpFields) {
		config[k] = v
	}

	// ── Azure
	promptSection("☁️  Azure")
	azureFields := []struct{ key, label, def string }{
		{"AZURE_SUBSCRIPTION_ID", "Subscription ID", ""},
		{"AZURE_TENANT_ID", "Tenant ID", ""},
		{"AZURE_CLIENT_ID", "Client ID (App ID)", ""},
		{"AZURE_CLIENT_SECRET", "Client Secret", ""},
	}
	for k, v := range askProviderBlock(reader, "Azure", azureFields) {
		config[k] = v
	}

	// ── Kubernetes
	promptSection("☸️  Kubernetes")
	k8sFields := []struct{ key, label, def string }{
		{"KUBECONFIG", "Kubeconfig path", "~/.kube/config"},
	}
	for k, v := range askProviderBlock(reader, "Kubernetes", k8sFields) {
		config[k] = v
	}

	// ── Slack
	promptSection("💬 Slack Notifications")
	slackFields := []struct{ key, label, def string }{
		{"SLACK_WEBHOOK_URL", "Webhook URL (from api.slack.com/apps)", ""},
		{"SLACK_CHANNEL", "Channel", "#finops-alerts"},
	}
	for k, v := range askProviderBlock(reader, "Slack", slackFields) {
		config[k] = v
	}

	// ── Twilio
	promptSection("📱 Twilio SMS Notifications")
	twilioFields := []struct{ key, label, def string }{
		{"TWILIO_ACCOUNT_SID", "Account SID (from twilio.com/console)", ""},
		{"TWILIO_AUTH_TOKEN", "Auth Token", ""},
		{"TWILIO_FROM_NUMBER", "Twilio Phone Number (e.g. +15551234567)", ""},
		{"TWILIO_TO_NUMBER", "Your Phone Number to receive SMS", ""},
	}
	for k, v := range askProviderBlock(reader, "Twilio", twilioFields) {
		config[k] = v
	}

	// ── Email
	promptSection("📧 Email Notifications")
	emailFields := []struct{ key, label, def string }{
		{"NOTIFY_EMAIL", "Recipient email", ""},
		{"SMTP_HOST", "SMTP host", "smtp.gmail.com"},
		{"SMTP_PORT", "SMTP port", "587"},
		{"SMTP_USER", "SMTP username", ""},
		{"SMTP_PASS", "SMTP password", ""},
	}
	for k, v := range askProviderBlock(reader, "Email", emailFields) {
		config[k] = v
	}

	// ── Cloud Mode
	fmt.Println()
	fmt.Println(colorize(colorBold, "  🌐 Cloud Mode"))
	fmt.Println(colorize(colorDim, "  "+strings.Repeat("─", 48)))
	fmt.Println(colorize(colorDim, "  Options: mock | aws | azure | gcp | all"))
	mode := promptLine(reader, "Cloud mode (default: mock):")
	if mode == "" {
		mode = "mock"
	}
	config["CLOUD_MODE"] = mode

	// Save
	if err := os.MkdirAll(filepath.Dir(configPath), 0755); err != nil {
		printError("Failed to create config directory: " + err.Error())
		return
	}

	data, _ := json.MarshalIndent(config, "", "  ")
	if err := os.WriteFile(configPath, data, 0600); err != nil {
		printError("Failed to save configuration: " + err.Error())
		return
	}

	fmt.Println()
	printSuccess("Credentials saved to " + configPath)
	fmt.Println(colorize(colorDim, "  Restart the API server to apply changes."))
	fmt.Println()

	// Show summary of what was configured
	configured := []string{}
	if config["AWS_ACCESS_KEY_ID"] != "" {
		configured = append(configured, "AWS")
	}
	if config["GCP_PROJECT_ID"] != "" {
		configured = append(configured, "GCP")
	}
	if config["AZURE_SUBSCRIPTION_ID"] != "" {
		configured = append(configured, "Azure")
	}
	if config["KUBECONFIG"] != "" {
		configured = append(configured, "Kubernetes")
	}
	if config["SLACK_WEBHOOK_URL"] != "" {
		configured = append(configured, "Slack")
	}
	if config["TWILIO_ACCOUNT_SID"] != "" {
		configured = append(configured, "Twilio SMS")
	}
	if config["NOTIFY_EMAIL"] != "" {
		configured = append(configured, "Email")
	}

	if len(configured) > 0 {
		fmt.Printf("  Configured: %s\n\n", colorize(colorGreen, strings.Join(configured, ", ")))
	}
}
