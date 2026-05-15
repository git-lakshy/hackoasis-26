"use client"

import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts"

const data = [
  { name: "AWS", value: 58, amount: "$48.8k", color: "#06b6d4" },
  { name: "GCP", value: 24, amount: "$20.2k", color: "#a855f7" },
  { name: "Azure", value: 18, amount: "$15.2k", color: "#3b82f6" },
]

export function SpendByProvider() {
  return (
    <div className="bg-card rounded-xl p-6 border border-border">
      <h3 className="text-sm font-medium text-muted-foreground mb-6">Spend by Provider</h3>
      
      <div className="flex items-center gap-8">
        <div className="relative w-48 h-48">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={2}
                dataKey="value"
                strokeWidth={0}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-xs text-muted-foreground">Total Spend</span>
            <span className="text-2xl font-bold text-foreground">$84.2k</span>
          </div>
        </div>

        <div className="flex flex-col gap-4">
          {data.map((item) => (
            <div key={item.name} className="flex items-center justify-between gap-8">
              <div className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-sm text-foreground">{item.name}</span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm text-muted-foreground">{item.value}%</span>
                <span className="text-sm font-medium text-foreground w-16 text-right">{item.amount}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
