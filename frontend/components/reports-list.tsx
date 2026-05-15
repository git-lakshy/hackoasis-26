"use client"

import { useState } from "react"
import { FileText, Calendar, Eye, MoreHorizontal } from "lucide-react"

const reports = [
  {
    id: 1,
    title: "Weekly FinOps Digest — May 12",
    date: "Generated on May 12, 2024 • 09:00 AM",
    icon: "purple",
    badge: null,
  },
  {
    id: 2,
    title: "April Cost Allocation & Chargeback",
    date: "Generated on May 1, 2024 • 00:15 AM",
    icon: "pink",
    badge: null,
  },
  {
    id: 3,
    title: "Idle EC2 Instance Analysis [Q1]",
    date: "Generated on Apr 15, 2024 • 14:30 PM",
    icon: "red",
    badge: "01",
  },
]

export function ReportsList() {
  const [activeTab, setActiveTab] = useState<"generated" | "scheduled">("generated")

  const getIconColor = (color: string) => {
    switch (color) {
      case "purple":
        return "bg-purple-900/50 text-purple-400"
      case "pink":
        return "bg-pink-900/50 text-pink-400"
      case "red":
        return "bg-red-900/50 text-red-400"
      default:
        return "bg-gray-900/50 text-gray-400"
    }
  }

  return (
    <div>
      {/* Tabs */}
      <div className="flex gap-1 mb-6">
        <button
          onClick={() => setActiveTab("generated")}
          className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
            activeTab === "generated"
              ? "bg-card text-foreground"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Generated reports
        </button>
        <button
          onClick={() => setActiveTab("scheduled")}
          className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
            activeTab === "scheduled"
              ? "bg-card text-foreground"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Schedule a report
        </button>
      </div>

      {/* Reports list */}
      <div className="space-y-3">
        {reports.map((report) => (
          <div
            key={report.id}
            className="flex items-center gap-4 p-4 bg-card rounded-xl border border-border hover:border-border/80 transition-colors"
          >
            {/* Icon */}
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${getIconColor(report.icon)}`}>
              <FileText className="w-5 h-5" />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-medium text-foreground">{report.title}</h3>
                {report.badge && (
                  <span className="px-1.5 py-0.5 text-[10px] font-medium bg-pink-900/50 text-pink-400 rounded">
                    {report.badge}
                  </span>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">{report.date}</p>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-cyan-400 bg-cyan-950/50 rounded-lg border border-cyan-800/30 hover:bg-cyan-900/50 transition-colors">
                <Eye className="w-3.5 h-3.5" />
                View
              </button>
              <button className="p-1.5 text-muted-foreground hover:text-foreground transition-colors">
                <MoreHorizontal className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Load more */}
      <button className="mt-4 text-sm text-muted-foreground hover:text-foreground transition-colors">
        ↓ Load older reports
      </button>
    </div>
  )
}
