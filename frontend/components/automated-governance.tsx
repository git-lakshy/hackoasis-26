"use client"

import { useState } from "react"
import { Switch } from "@/components/ui/switch"

export function AutomatedGovernance() {
  const [enabled, setEnabled] = useState(false)

  return (
    <div className="bg-card border border-border rounded-xl p-5 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute right-0 bottom-0 w-48 h-48 opacity-20">
        <svg viewBox="0 0 200 200" className="w-full h-full">
          <defs>
            <linearGradient id="govGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#22d3ee" />
              <stop offset="100%" stopColor="#0891b2" />
            </linearGradient>
          </defs>
          <circle cx="100" cy="100" r="80" fill="none" stroke="url(#govGradient)" strokeWidth="1" opacity="0.3" />
          <circle cx="100" cy="100" r="60" fill="none" stroke="url(#govGradient)" strokeWidth="1" opacity="0.4" />
          <circle cx="100" cy="100" r="40" fill="none" stroke="url(#govGradient)" strokeWidth="1" opacity="0.5" />
          {/* Data points */}
          {[...Array(12)].map((_, i) => {
            const angle = (i * 30 * Math.PI) / 180
            const x = 100 + Math.cos(angle) * 70
            const y = 100 + Math.sin(angle) * 70
            return <circle key={i} cx={x} cy={y} r="2" fill="#22d3ee" opacity="0.6" />
          })}
        </svg>
      </div>

      <div className="relative z-10">
        <h3 className="text-lg font-semibold text-foreground mb-3">Automated Governance</h3>
        <p className="text-sm text-muted-foreground mb-6 max-w-xs">
          Enable auto-approval for &quot;Safe&quot; tier recommendations to maintain efficiency without manual oversight.
        </p>

        <div className="flex items-center gap-3">
          <Switch 
            checked={enabled}
            onCheckedChange={setEnabled}
            className="data-[state=checked]:bg-cyan-500"
          />
          <span className="text-sm text-muted-foreground">
            {enabled ? "Enabled" : "Disabled"}
          </span>
        </div>
      </div>
    </div>
  )
}
