package main

import (
	"fmt"
	"log"
	"math"

	ui "github.com/gizak/termui/v3"
	"github.com/gizak/termui/v3/widgets"
)

// ── Dashboard Command ─────────────────────────────────────────────────────────

func cmdDashboard() {
	if err := ui.Init(); err != nil {
		log.Fatalf("failed to initialize termui: %v", err)
	}
	defer ui.Close()

	// Fetch data
	statusData, err := get("/api/v1/status")
	var opportunities float64
	if err == nil {
		if opps, ok := statusData["opportunities"].(float64); ok {
			opportunities = opps
		}
	}

	resData, err := get("/api/v1/resources")
	if err != nil {
		ui.Close()
		fmt.Println("❌ Failed to fetch data for dashboard. Is the API server running?")
		fmt.Println("Error:", err)
		return
	}

	resources, ok := resData["resources"].([]interface{})
	if !ok {
		resources = []interface{}{}
	}

	// Calculate metrics
	var totalCost float64
	cloudCosts := map[string]float64{"aws": 0, "gcp": 0, "azure": 0}
	
	for _, r := range resources {
		res, ok := r.(map[string]interface{})
		if !ok {
			continue
		}
		
		cost, _ := res["monthly_cost"].(float64)
		totalCost += cost
		
		cloud, _ := res["cloud"].(string)
		if cloud != "" {
			cloudCosts[cloud] += cost
		}
	}

	// 1. KPI Widget
	p := widgets.NewParagraph()
	p.Title = " Baburao FinOps AI "
	p.Text = fmt.Sprintf("\n  [Total Monthly Run Rate](fg:white,mod:bold): [$%.2f/mo](fg:red)\n\n", totalCost)
	if opportunities > 0 {
		p.Text += fmt.Sprintf("  [Optimization Opportunities](fg:white,mod:bold): [%.0f identified](fg:green)\n", opportunities)
		p.Text += "  [Status](fg:white,mod:bold): [Cycle complete. Run 'baburao decide' for debates.](fg:yellow)"
	} else {
		p.Text += "  [Optimization Opportunities](fg:white,mod:bold): [None yet](fg:yellow)\n"
		p.Text += "  [Status](fg:white,mod:bold): [Run 'baburao run' to analyze infrastructure.](fg:white)"
	}
	p.SetRect(0, 0, 50, 8)
	p.BorderStyle.Fg = ui.ColorCyan

	// 2. Cloud Spend Bar Chart
	bc := widgets.NewBarChart()
	bc.Title = " Cloud Spend Breakdown ($/mo) "
	bc.Data = []float64{cloudCosts["aws"], cloudCosts["gcp"], cloudCosts["azure"]}
	bc.Labels = []string{"AWS", "GCP", "Azure"}
	bc.BarWidth = 10
	bc.BarColors = []ui.Color{ui.ColorYellow, ui.ColorRed, ui.ColorBlue}
	bc.LabelStyles = []ui.Style{ui.NewStyle(ui.ColorWhite)}
	bc.NumStyles = []ui.Style{ui.NewStyle(ui.ColorBlack)}
	bc.SetRect(50, 0, 100, 8)

	// 3. Savings Prediction Line Chart
	lc := widgets.NewPlot()
	lc.Title = " 12-Month Spend Projection "
	
	// Create projection data
	statusQuo := make([]float64, 12)
	optimized := make([]float64, 12)
	
	currentVal := totalCost
	optVal := totalCost * 0.75 // Assume 25% savings if they optimize
	
	for i := 0; i < 12; i++ {
		// Add slight 2% MoM growth
		statusQuo[i] = currentVal * math.Pow(1.02, float64(i))
		optimized[i] = optVal * math.Pow(1.015, float64(i))
	}

	lc.Data = make([][]float64, 2)
	lc.Data[0] = statusQuo
	lc.Data[1] = optimized
	lc.LineColors[0] = ui.ColorRed
	lc.LineColors[1] = ui.ColorGreen
	lc.AxesColor = ui.ColorWhite
	lc.SetRect(0, 8, 100, 20)

	// 4. Instructions
	inst := widgets.NewParagraph()
	inst.Text = "  Press [q](fg:yellow,mod:bold) to quit. Red Line: Status Quo, Green Line: Optimized."
	inst.Border = false
	inst.SetRect(0, 20, 100, 22)

	// Render
	ui.Render(p, bc, lc, inst)

	// Event loop
	uiEvents := ui.PollEvents()
	for {
		e := <-uiEvents
		switch e.ID {
		case "q", "<C-c>":
			return
		case "<Resize>":
			payload := e.Payload.(ui.Resize)
			
			// Responsive logic
			p.SetRect(0, 0, payload.Width/2, 8)
			bc.SetRect(payload.Width/2, 0, payload.Width, 8)
			lc.SetRect(0, 8, payload.Width, 20)
			inst.SetRect(0, 20, payload.Width, 22)
			
			ui.Clear()
			ui.Render(p, bc, lc, inst)
		}
	}
}
