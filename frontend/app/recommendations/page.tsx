"use client"

import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { RecommendationCards } from "@/components/recommendation-cards"
import { HistoricalSavings } from "@/components/historical-savings"
import { AutomatedGovernance } from "@/components/automated-governance"
import { Sparkles } from "lucide-react"

export default function RecommendationsPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar activePage="recommendations" userName="Alex Sterling" userRole="Cloud Admin" />
      <div className="flex-1 flex flex-col">
        <Header title="Recommendations Engine" subtitle="AI-Driven Findings" />
        <main className="flex-1 p-6 overflow-auto">
          {/* Header Section */}
          <div className="flex items-start justify-between mb-8">
            <div>
              <h1 className="text-2xl font-semibold text-foreground mb-2">Cost Optimization</h1>
              <p className="text-muted-foreground text-sm max-w-md">
                AI-driven insights to trim waste and maximize efficiency across your multi-cloud environment.
              </p>
            </div>
            <div className="flex gap-6">
              <div className="text-right">
                <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Total Savings Estimated</p>
                <p className="text-2xl font-bold text-emerald-400">$42,850.00</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Active</p>
                <p className="text-2xl font-bold text-cyan-400">14</p>
              </div>
            </div>
          </div>

          {/* Recommendation Cards */}
          <RecommendationCards />

          {/* Bottom Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            <HistoricalSavings />
            <AutomatedGovernance />
          </div>
        </main>
      </div>
    </div>
  )
}
