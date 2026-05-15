"use client"

import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { SpendByProvider } from "@/components/spend-by-provider"
import { DailySpendTrend } from "@/components/daily-spend-trend"
import { ServiceBreakdown } from "@/components/service-breakdown"
import { useState } from "react"

export default function CloudSpendPage() {
  const [timeRange, setTimeRange] = useState("90d")
  const [provider, setProvider] = useState("All")

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar activePage="cloud-spend" />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 p-6 overflow-auto">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-2xl font-semibold text-foreground">Cloud Spend Breakdown</h1>
              <p className="text-muted-foreground text-sm mt-1">
                Analyze your multi-cloud expenditure across providers and services.
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1 bg-card rounded-lg p-1">
                {["7d", "30d", "90d"].map((range) => (
                  <button
                    key={range}
                    onClick={() => setTimeRange(range)}
                    className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                      timeRange === range
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {range}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-1">
                {["All", "AWS", "GCP", "Azure"].map((p) => (
                  <button
                    key={p}
                    onClick={() => setProvider(p)}
                    className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                      provider === p
                        ? "bg-card text-foreground border border-border"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <SpendByProvider />
            <DailySpendTrend />
          </div>

          <ServiceBreakdown />
        </main>
      </div>
    </div>
  )
}
