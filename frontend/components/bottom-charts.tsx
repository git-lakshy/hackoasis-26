"use client"

import { Card } from "@/components/ui/card"
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts"

const distributionData = [
  { name: "Compute", value: 55, color: "#3b82f6" },
  { name: "Storage", value: 30, color: "#14b8a6" },
  { name: "Other", value: 15, color: "#8b5cf6" },
]

const regionData = [
  { name: "US East 1", value: 44, color: "#22d3ee" },
  { name: "EU West 1", value: 35, color: "#3b82f6" },
  { name: "AP South 1", value: 21, color: "#ec4899" },
]

export function BottomCharts() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Service Distribution */}
      <Card className="p-4 bg-card">
        <h4 className="text-sm font-semibold text-foreground mb-4">Service Distribution</h4>
        <div className="flex items-center gap-4">
          <div className="w-24 h-24">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={distributionData}
                  cx="50%"
                  cy="50%"
                  innerRadius={25}
                  outerRadius={40}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {distributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-2">
            {distributionData.map((item) => (
              <div key={item.name} className="flex items-center gap-2">
                <div 
                  className="w-2 h-2 rounded-full" 
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-xs text-muted-foreground">{item.name}</span>
                <span className="text-xs font-medium text-foreground">{item.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Spend by Region */}
      <Card className="p-4 bg-card">
        <h4 className="text-sm font-semibold text-foreground mb-4">Spend by Region</h4>
        <div className="flex items-center gap-4">
          <div className="w-24 h-24">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={regionData}
                  cx="50%"
                  cy="50%"
                  innerRadius={25}
                  outerRadius={40}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {regionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-2">
            {regionData.map((item) => (
              <div key={item.name} className="flex items-center gap-2">
                <div 
                  className="w-2 h-2 rounded-full" 
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-xs text-muted-foreground">{item.name}</span>
                <span className="text-xs font-medium text-foreground">{item.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Automated Savings */}
      <Card className="p-4 bg-gradient-to-br from-purple-900/50 to-pink-900/50 border-purple-500/30">
        <h4 className="text-sm font-semibold text-foreground mb-2">Automated Savings</h4>
        <p className="text-xs text-muted-foreground mb-4">
          Enable AI-optimized for autonomous cost optimization
        </p>
        <button className="w-full py-2 px-4 rounded-lg bg-cyan-500/20 text-cyan-400 text-sm font-medium hover:bg-cyan-500/30 transition-colors">
          Automate Now
        </button>
      </Card>
    </div>
  )
}
