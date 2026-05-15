import { TrendingUp, TrendingDown, Server, HardDrive, Cpu } from "lucide-react"

const opportunities = [
  {
    id: 1,
    title: "Right-size RDS instances in us-east-1",
    savings: "$4,350/mo",
    icon: Server,
  },
  {
    id: 2,
    title: "Terminate unattached EBS volumes",
    savings: "$2,100/mo",
    icon: HardDrive,
  },
  {
    id: 3,
    title: "Purchase Compute Savings Plan",
    savings: "$3,800/mo",
    icon: Cpu,
  },
]

export function SavingsSummary() {
  return (
    <div className="bg-card rounded-xl border border-border p-5">
      <h3 className="text-sm font-medium text-foreground mb-4">Savings summary</h3>
      
      {/* Metrics */}
      <div className="space-y-4 mb-6">
        <div>
          <p className="text-xs text-muted-foreground mb-1">Total waste found this month</p>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-foreground">$14,250</span>
            <span className="flex items-center gap-0.5 text-xs text-red-400">
              <TrendingUp className="w-3 h-3" />
              +14%
            </span>
          </div>
        </div>
        
        <div>
          <p className="text-xs text-muted-foreground mb-1">Total savings applied</p>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-cyan-400">$8,940</span>
            <span className="text-xs text-muted-foreground">86%</span>
          </div>
        </div>
      </div>

      {/* Top opportunities */}
      <div>
        <p className="text-xs text-muted-foreground mb-3">Top 3 opportunities</p>
        <div className="space-y-3">
          {opportunities.map((opportunity, index) => (
            <div key={opportunity.id} className="flex items-start gap-3">
              <div className="w-6 h-6 rounded bg-cyan-950/50 flex items-center justify-center flex-shrink-0 mt-0.5">
                <opportunity.icon className="w-3.5 h-3.5 text-cyan-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-foreground leading-tight">{opportunity.title}</p>
                <p className="text-xs text-cyan-400 mt-0.5">{opportunity.savings}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
