"use client"

import { AlertTriangle } from "lucide-react"

const alerts = [
  {
    id: 1,
    budgetName: "Data Team GCP",
    threshold: "100% Exceeded",
    thresholdColor: "bg-red-500/20 text-red-400",
    date: "Oct 24, 2023",
  },
  {
    id: 2,
    budgetName: "Production AWS",
    threshold: "85% Reached",
    thresholdColor: "bg-yellow-500/20 text-yellow-400",
    date: "Oct 22, 2023",
  },
  {
    id: 3,
    budgetName: "Production AWS",
    threshold: "75% Reached",
    thresholdColor: "bg-yellow-500/20 text-yellow-400",
    date: "Oct 18, 2023",
  },
]

export function BudgetAlerts() {
  return (
    <div className="bg-card border border-border rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-4 h-4 text-yellow-500" />
        <h3 className="text-sm font-medium text-foreground">Budget alerts</h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider py-3 pr-4">
                Budget Name
              </th>
              <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider py-3 pr-4">
                Threshold Triggered
              </th>
              <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider py-3 pr-4">
                Date
              </th>
              <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider py-3">
                Action
              </th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((alert) => (
              <tr key={alert.id} className="border-b border-border/50 last:border-0">
                <td className="py-3 pr-4">
                  <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
                    <span className="text-sm text-foreground">{alert.budgetName}</span>
                  </div>
                </td>
                <td className="py-3 pr-4">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium ${alert.thresholdColor}`}
                  >
                    {alert.threshold}
                  </span>
                </td>
                <td className="py-3 pr-4">
                  <span className="text-sm text-muted-foreground">{alert.date}</span>
                </td>
                <td className="py-3">
                  <button className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors">
                    Dismiss
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
