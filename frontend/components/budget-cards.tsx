"use client"

import { MoreHorizontal } from "lucide-react"

const budgets = [
  {
    name: "ML Infrastructure",
    status: "On Track",
    statusColor: "bg-emerald-500",
    spent: 18400,
    total: 30000,
    percentage: 61,
    forecast: 6000,
    progressColor: "bg-emerald-500",
  },
  {
    name: "Production AWS",
    status: "At Risk",
    statusColor: "bg-yellow-500",
    spent: 43500,
    total: 50000,
    percentage: 87,
    forecast: 7200,
    progressColor: "bg-yellow-500",
  },
  {
    name: "Data Team GCP",
    status: "Over budget",
    statusColor: "bg-red-500",
    spent: 19800,
    total: 15000,
    percentage: 132,
    forecast: 8200,
    progressColor: "bg-red-500",
  },
  {
    name: "Marketing Sandbox",
    status: "On Track",
    statusColor: "bg-emerald-500",
    spent: 3200,
    total: 8000,
    percentage: 40,
    forecast: 2800,
    progressColor: "bg-emerald-500",
  },
]

export function BudgetCards() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
      {budgets.map((budget) => (
        <div
          key={budget.name}
          className="bg-card border border-border rounded-xl p-5"
        >
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-sm font-medium text-foreground mb-2">{budget.name}</h3>
              <span
                className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium text-white ${budget.statusColor}`}
              >
                {budget.status}
              </span>
            </div>
            <button className="text-muted-foreground hover:text-foreground transition-colors">
              <MoreHorizontal className="w-5 h-5" />
            </button>
          </div>

          <div className="mb-3">
            <div className="flex items-baseline gap-1 mb-2">
              <span className="text-xs text-muted-foreground">Spent:</span>
              <span className="text-sm font-semibold text-foreground">
                ${budget.spent.toLocaleString()}
              </span>
              <span className="text-xs text-muted-foreground">
                of ${budget.total.toLocaleString()}
              </span>
              <span className="text-xs text-muted-foreground ml-auto">
                {budget.percentage}%
              </span>
            </div>
            <div className="h-1.5 bg-muted rounded-full overflow-hidden">
              <div
                className={`h-full ${budget.progressColor} rounded-full transition-all`}
                style={{ width: `${Math.min(budget.percentage, 100)}%` }}
              />
            </div>
          </div>

          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <span>Forecasted end-of-month:</span>
            <span className="text-cyan-400 font-medium">${budget.forecast.toLocaleString()}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
