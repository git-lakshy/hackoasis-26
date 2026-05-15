"use client"

import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from "recharts"

const data = [
  { month: "Jan", savings: 45000 },
  { month: "Feb", savings: 52000 },
  { month: "Mar", savings: 48000 },
  { month: "Apr", savings: 61000 },
  { month: "May", savings: 58000 },
  { month: "Jun", savings: 72000 },
  { month: "Jul", savings: 68000 },
  { month: "Aug", savings: 85000 },
  { month: "Sep", savings: 92000 },
  { month: "Oct", savings: 88000 },
  { month: "Nov", savings: 95000 },
  { month: "Dec", savings: 86000 },
]

export function HistoricalSavings() {
  return (
    <div className="bg-card border border-border rounded-xl p-5">
      <h3 className="text-sm font-medium text-muted-foreground mb-4">HISTORICAL SAVINGS</h3>
      
      <div className="h-40 mb-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barSize={20}>
            <XAxis 
              dataKey="month" 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748b', fontSize: 10 }}
            />
            <YAxis 
              hide
            />
            <Bar 
              dataKey="savings" 
              radius={[4, 4, 0, 0]}
            >
              {data.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={index === data.length - 1 ? "#22d3ee" : "#1e3a5f"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between pt-3 border-t border-border">
        <span className="text-sm text-muted-foreground">Year to Date</span>
        <span className="text-lg font-semibold text-emerald-400">+$850,000</span>
      </div>
    </div>
  )
}
