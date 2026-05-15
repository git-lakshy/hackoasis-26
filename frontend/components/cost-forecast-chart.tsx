"use client"

import { Card } from "@/components/ui/card"
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  ResponsiveContainer,
  Tooltip,
  Legend,
  Area,
  ComposedChart
} from "recharts"

const data = [
  { day: 0, current: 124000, optimized: 124000 },
  { day: 10, current: 128000, optimized: 122000 },
  { day: 20, current: 132000, optimized: 120000 },
  { day: 30, current: 138000, optimized: 118000 },
  { day: 40, current: 145000, optimized: 116000 },
  { day: 50, current: 152000, optimized: 114000 },
  { day: 60, current: 160000, optimized: 113000 },
  { day: 70, current: 168000, optimized: 112000 },
  { day: 80, current: 176000, optimized: 111000 },
  { day: 90, current: 185000, optimized: 110000 },
]

export function CostForecastChart() {
  return (
    <Card className="p-6 bg-card">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-foreground">Cost forecast — next 90 days</h3>
          <p className="text-sm text-muted-foreground">Projected savings based on RUSP utilization and right-sizing</p>
        </div>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-cyan-400 rounded" />
            <span className="text-xs text-muted-foreground">Current Trajectory</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-pink-500 rounded" style={{ borderStyle: 'dashed' }} />
            <span className="text-xs text-muted-foreground">Optimized</span>
          </div>
        </div>
      </div>
      
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="currentGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#22d3ee" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <XAxis 
              dataKey="day" 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#6b7280', fontSize: 11 }}
              tickFormatter={(value) => `Day ${value}`}
            />
            <YAxis 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#6b7280', fontSize: 11 }}
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              domain={[100000, 200000]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#f1f5f9'
              }}
              formatter={(value: number) => [`$${value.toLocaleString()}`, '']}
              labelFormatter={(label) => `Day ${label}`}
            />
            <Area
              type="monotone"
              dataKey="current"
              stroke="transparent"
              fill="url(#currentGradient)"
            />
            <Line 
              type="monotone" 
              dataKey="current" 
              stroke="#22d3ee" 
              strokeWidth={2}
              dot={false}
              name="Current Trajectory"
            />
            <Line 
              type="monotone" 
              dataKey="optimized" 
              stroke="#ec4899" 
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              name="Optimized"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}
