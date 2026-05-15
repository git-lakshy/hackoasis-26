"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Server, Database, Loader2 } from "lucide-react"

const recommendations = [
  {
    icon: Server,
    label: "Low",
    labelColor: "bg-emerald-500/20 text-emerald-400",
    title: "m5a.4xlarge → R5X",
    savings: "+$413/mo",
    savingsColor: "text-emerald-400",
    description: "Instance is underutilized (avg CPU < 10%), Migrate to Savings Plan Flex Instance at lower cost",
    details: "4 days of data",
    borderColor: "border-l-emerald-500",
  },
  {
    icon: Database,
    label: "Medium",
    labelColor: "bg-orange-500/20 text-orange-400",
    title: "Unused RDS Volumes",
    savings: "+$2,100/mo",
    savingsColor: "text-orange-400",
    description: "14 orphan volumes detected (no uses > 5 days). Recommend deletion or archival and recovery.",
    details: "14 Idle / 76 attached",
    borderColor: "border-l-orange-500",
  },
  {
    icon: Loader2,
    label: "Critical",
    labelColor: "bg-red-500/20 text-red-400",
    title: "Idle Load Balancer",
    savings: "+$1,521/mo",
    savingsColor: "text-red-400",
    description: "Application Load Balancers 'alb-by-42-tsu' alb-x-alpha-api-lb idle (0 targets, 0 hits) for 30+ consecutive days. Delete or terminate.",
    details: "3 Meeting 0 Decision",
    borderColor: "border-l-red-500",
  },
]

export function TopRecommendations() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-foreground">Top recommendations</h3>
        <Button variant="link" className="text-cyan-400 text-sm p-0 h-auto">
          View all 24 Insights
        </Button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {recommendations.map((rec, index) => (
          <Card 
            key={index} 
            className={`relative overflow-hidden bg-card border-l-4 ${rec.borderColor} p-4`}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${rec.labelColor}`}>
                  {rec.label}
                </span>
                <span className={`text-sm font-semibold ${rec.savingsColor}`}>
                  {rec.savings}
                </span>
              </div>
              
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-secondary flex items-center justify-center">
                  <rec.icon className="w-4 h-4 text-muted-foreground" />
                </div>
                <h4 className="text-sm font-medium text-foreground">{rec.title}</h4>
              </div>
              
              <p className="text-xs text-muted-foreground leading-relaxed">
                {rec.description}
              </p>
              
              <div className="flex items-center justify-between pt-2 border-t border-border">
                <span className="text-[10px] text-muted-foreground">{rec.details}</span>
                <Button size="sm" className="h-7 text-xs bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30 border-0">
                  Optimize Now
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
