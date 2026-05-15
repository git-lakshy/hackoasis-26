"use client"

import { TrendingDown, TrendingUp, AlertCircle, Sparkles } from "lucide-react"
import { Card } from "@/components/ui/card"

const metrics = [
  {
    title: "TOTAL MONTHLY SPEND",
    value: "$124,300",
    change: "+2.3% vs last month",
    trend: "up",
    color: "text-emerald-400",
    borderColor: "border-l-emerald-400",
    bgGlow: "bg-emerald-500/10",
  },
  {
    title: "MONTH TO DATE ACTUAL",
    value: "$18,200",
    change: "Within budget expectations",
    trend: "neutral",
    color: "text-orange-400",
    borderColor: "border-l-orange-400",
    bgGlow: "bg-orange-500/10",
  },
  {
    title: "AVERAGE DAILY RUN RATE",
    value: "$4,100",
    change: "Policy auto-optimized at 2.4%",
    trend: "info",
    color: "text-cyan-400",
    borderColor: "border-l-cyan-400",
    bgGlow: "bg-cyan-500/10",
  },
  {
    title: "PROJECTED SAVINGS",
    value: "$14,100",
    change: "Pending approvals at 5 weeks",
    trend: "savings",
    color: "text-red-400",
    borderColor: "border-l-red-400",
    bgGlow: "bg-red-500/10",
  },
]

export function MetricCards() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric) => (
        <Card 
          key={metric.title} 
          className={`relative overflow-hidden bg-card border-l-4 ${metric.borderColor} p-4`}
        >
          <div className={`absolute inset-0 ${metric.bgGlow} opacity-20`} />
          <div className="relative">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">
              {metric.title}
            </p>
            <p className={`text-2xl font-bold ${metric.color}`}>
              {metric.value}
            </p>
            <div className="flex items-center gap-1 mt-2">
              {metric.trend === "up" && <TrendingUp className="w-3 h-3 text-emerald-400" />}
              {metric.trend === "neutral" && <TrendingDown className="w-3 h-3 text-orange-400" />}
              {metric.trend === "info" && <AlertCircle className="w-3 h-3 text-cyan-400" />}
              {metric.trend === "savings" && <Sparkles className="w-3 h-3 text-red-400" />}
              <p className="text-xs text-muted-foreground">{metric.change}</p>
            </div>
          </div>
        </Card>
      ))}
    </div>
  )
}
