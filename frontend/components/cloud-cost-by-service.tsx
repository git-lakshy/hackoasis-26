"use client"

import { Card } from "@/components/ui/card"
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  ResponsiveContainer, 
  Cell,
  Tooltip
} from "recharts"

const data = [
  { name: "Compute", value: 65, color: "#3b82f6" },
  { name: "Storage", value: 38, color: "#8b5cf6" },
  { name: "Database", value: 52, color: "#a855f7" },
  { name: "Networking", value: 31, color: "#ec4899" },
  { name: "Security", value: 44, color: "#14b8a6" },
]

export function CloudCostByService() {
  return (
    <Card className="p-6 bg-card">
      <h3 className="text-lg font-semibold text-foreground mb-6">Cloud Cost by Service</h3>
      
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <XAxis 
              dataKey="name" 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#6b7280', fontSize: 11 }}
            />
            <YAxis 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#6b7280', fontSize: 11 }}
              tickFormatter={(value) => `$${value}k`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#f1f5f9'
              }}
              formatter={(value: number) => [`$${value}k`, 'Cost']}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      
      <div className="flex items-center justify-center gap-4 mt-4 flex-wrap">
        {data.map((item) => (
          <div key={item.name} className="flex items-center gap-1.5">
            <div 
              className="w-2.5 h-2.5 rounded-full" 
              style={{ backgroundColor: item.color }}
            />
            <span className="text-xs text-muted-foreground">{item.name}</span>
            <span className="text-xs font-medium text-foreground">${item.value}k</span>
          </div>
        ))}
      </div>
    </Card>
  )
}
