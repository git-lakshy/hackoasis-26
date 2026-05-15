"use client"

import { Download } from "lucide-react"

const services = [
  {
    name: "RDS Production Cluster",
    provider: "AWS",
    providerColor: "#f97316",
    region: "US-EAST-1",
    team: "Backend",
    monthlyCost: "$12,450.00",
    change: -9.2,
    wasteScore: 12,
  },
  {
    name: "AKS Dev Cluster",
    provider: "Azure",
    providerColor: "#3b82f6",
    region: "WestUS2",
    team: "Platform",
    monthlyCost: "$8,230.98",
    change: 5.5,
    wasteScore: 45,
  },
  {
    name: "BigQuery Analytics",
    provider: "GCP",
    providerColor: "#a855f7",
    region: "US-Central",
    team: "Data Sci",
    monthlyCost: "$6,920.20",
    change: -2.8,
    wasteScore: 8,
  },
  {
    name: "EC2 Worker Nodes",
    provider: "AWS",
    providerColor: "#f97316",
    region: "EU-West",
    team: "Backend",
    monthlyCost: "$4,860.00",
    change: 0,
    wasteScore: 78,
  },
  {
    name: "S3 Data Lake (us-east-west-1)",
    provider: "AWS",
    providerColor: "#f97316",
    region: "US-EAST-1",
    team: "Unknown",
    monthlyCost: "$3,200.00",
    change: 8.54,
    wasteScore: 22,
  },
]

function WasteScoreBar({ score }: { score: number }) {
  const getColor = () => {
    if (score <= 20) return "bg-emerald-500"
    if (score <= 50) return "bg-yellow-500"
    return "bg-red-500"
  }

  return (
    <div className="flex items-center gap-2">
      <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
        <div 
          className={`h-full rounded-full ${getColor()}`}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className="text-xs text-muted-foreground w-8">{score}%</span>
    </div>
  )
}

export function ServiceBreakdown() {
  return (
    <div className="bg-card rounded-xl p-6 border border-border">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-medium text-foreground">Service Breakdown</h3>
        <button className="flex items-center gap-2 text-sm text-cyan-400 hover:text-cyan-300 transition-colors">
          <Download className="w-4 h-4" />
          Export
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Service Name
              </th>
              <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Provider
              </th>
              <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Region
              </th>
              <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Team
              </th>
              <th className="text-right py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Monthly Cost
              </th>
              <th className="text-right py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                % vs Last Month
              </th>
              <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Waste Score
              </th>
            </tr>
          </thead>
          <tbody>
            {services.map((service, index) => (
              <tr key={index} className="border-b border-border/50 hover:bg-muted/20 transition-colors">
                <td className="py-4 px-4">
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-1 h-8 rounded-full"
                      style={{ backgroundColor: service.providerColor }}
                    />
                    <span className="text-sm font-medium text-foreground">{service.name}</span>
                  </div>
                </td>
                <td className="py-4 px-4">
                  <span className="text-sm text-muted-foreground">{service.provider}</span>
                </td>
                <td className="py-4 px-4">
                  <span className="text-sm text-muted-foreground">{service.region}</span>
                </td>
                <td className="py-4 px-4">
                  <span className="text-sm text-muted-foreground">{service.team}</span>
                </td>
                <td className="py-4 px-4 text-right">
                  <span className="text-sm font-medium text-foreground">{service.monthlyCost}</span>
                </td>
                <td className="py-4 px-4 text-right">
                  <span className={`text-sm font-medium ${
                    service.change < 0 
                      ? "text-emerald-400" 
                      : service.change > 0 
                        ? "text-red-400" 
                        : "text-muted-foreground"
                  }`}>
                    {service.change > 0 ? "+" : ""}{service.change}%
                  </span>
                </td>
                <td className="py-4 px-4">
                  <WasteScoreBar score={service.wasteScore} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
        <span className="text-sm text-muted-foreground">Showing 1-5 of 142 services</span>
        <div className="flex items-center gap-2">
          <button className="px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors">
            Previous
          </button>
          <span className="text-sm text-foreground">Page 1 of 29</span>
          <button className="px-3 py-1.5 text-sm text-cyan-400 hover:text-cyan-300 transition-colors">
            Next
          </button>
        </div>
      </div>
    </div>
  )
}
