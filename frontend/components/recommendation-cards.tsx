"use client"

import { useState } from "react"
import { Sparkles, AlertTriangle, CheckCircle, XCircle } from "lucide-react"
import { Button } from "@/components/ui/button"

interface Recommendation {
  id: string
  title: string
  subtitle: string
  description: string
  currentCost: number
  projectedSavings: number
  isPositiveSavings: boolean
  aiReasoning: string
  badge?: {
    text: string
    variant: "warning" | "approval"
  }
  provider: "aws" | "azure" | "gcp"
}

const recommendations: Recommendation[] = [
  {
    id: "1",
    title: "i3.xlarge - Production DB",
    subtitle: "Underutilized instance with low CPU usage",
    description: "",
    currentCost: 1248.00,
    projectedSavings: 848.00,
    isPositiveSavings: true,
    aiReasoning: "Average CPU utilization over the last 30 days is 4.2%. Recommending a switch to t3.large which provides equivalent performance for your bursty traffic patterns without the overhead.",
    provider: "aws"
  },
  {
    id: "2",
    title: "Standard_D4s_v3 - Analytics",
    subtitle: "Stranded resource found outside of business hours",
    description: "",
    currentCost: 2856.00,
    projectedSavings: 1428.00,
    isPositiveSavings: false,
    aiReasoning: "This resource has 0% activity between 8 PM and 8 AM PST. Implementing a start/stop schedule could reduce your monthly spend by 80% without impacting operations.",
    badge: { text: "Warning", variant: "warning" },
    provider: "azure"
  },
  {
    id: "3",
    title: "n1-standard-16 - Kubernetes Cluster",
    subtitle: "High-cost instance with low memory pressure",
    description: "",
    currentCost: 4800.00,
    projectedSavings: 2208.00,
    isPositiveSavings: true,
    aiReasoning: "Cluster is consistently over-provisioned by 65%. Migrating to preemptible VMs for non-critical workloads or down-sizing nodes would yield massive efficiency gains.",
    badge: { text: "Approval Required", variant: "approval" },
    provider: "gcp"
  },
  {
    id: "4",
    title: "Unattached EBS Volumes",
    subtitle: "Orphaned storage not attached to any instances",
    description: "",
    currentCost: 429.00,
    projectedSavings: 429.00,
    isPositiveSavings: true,
    aiReasoning: "Detected 12 EBS volumes that haven&apos;t been attached to an EC2 instance for over 60 days. These volumes are still incurring costs without being utilized.",
    provider: "aws"
  }
]

const providerColors = {
  aws: "bg-orange-500",
  azure: "bg-blue-500",
  gcp: "bg-red-500"
}

export function RecommendationCards() {
  const [dismissed, setDismissed] = useState<string[]>([])

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {recommendations.filter(r => !dismissed.includes(r.id)).map((rec) => (
        <div
          key={rec.id}
          className="bg-card border border-border rounded-xl p-5 hover:border-border/80 transition-colors"
        >
          {/* Header */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className={`w-1 h-12 rounded-full ${providerColors[rec.provider]}`} />
              <div>
                <h3 className="font-medium text-foreground text-sm">{rec.title}</h3>
                <p className="text-xs text-muted-foreground mt-0.5">{rec.subtitle}</p>
              </div>
            </div>
            {rec.badge && (
              <span className={`text-xs px-2 py-1 rounded-full ${
                rec.badge.variant === "warning" 
                  ? "bg-amber-500/20 text-amber-400" 
                  : "bg-cyan-500/20 text-cyan-400"
              }`}>
                {rec.badge.text}
              </span>
            )}
          </div>

          {/* Cost Info */}
          <div className="flex gap-8 mb-4">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Current Monthly Cost</p>
              <p className="text-lg font-semibold text-foreground">${rec.currentCost.toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Projected Savings</p>
              <p className={`text-lg font-semibold ${rec.isPositiveSavings ? "text-emerald-400" : "text-red-400"}`}>
                {rec.isPositiveSavings ? "+" : "-"}${rec.projectedSavings.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </p>
            </div>
          </div>

          {/* AI Reasoning */}
          <div className="bg-background/50 rounded-lg p-3 mb-4">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              <span className="text-xs font-medium text-cyan-400">AI REASONING</span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              {rec.aiReasoning}
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <Button 
              size="sm" 
              className="flex-1 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 border-0"
            >
              Approve
            </Button>
            <Button 
              size="sm" 
              variant="outline"
              className="flex-1 border-border hover:bg-muted"
              onClick={() => setDismissed([...dismissed, rec.id])}
            >
              Dismiss
            </Button>
          </div>
        </div>
      ))}
    </div>
  )
}
