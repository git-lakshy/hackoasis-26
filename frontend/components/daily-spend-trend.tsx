"use client"

import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts"

const data = [
  { day: "1", value: 2800 },
  { day: "10", value: 2600 },
  { day: "20", value: 3200 },
  { day: "30", value: 2900 },
  { day: "40", value: 3400 },
  { day: "50", value: 3100 },
  { day: "60", value: 2800 },
  { day: "70", value: 3500 },
  { day: "80", value: 3200 },
  { day: "90", value: 3000 },
]

export function DailySpendTrend() {
  return (
    <div className="bg-card rounded-xl p-6 border border-border">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-medium text-muted-foreground">Daily Spend Trend</h3>
        <span className="text-xs text-muted-foreground">Last 90 Days</span>
      </div>
      
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis 
              dataKey="day" 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748b', fontSize: 12 }}
            />
            <YAxis 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748b', fontSize: 12 }}
              tickFormatter={(value) => `$${value / 1000}k`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#f8fafc'
              }}
              formatter={(value: number) => [`$${value.toLocaleString()}`, 'Spend']}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#06b6d4"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
