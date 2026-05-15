"use client"

import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { ReportsList } from "@/components/reports-list"
import { SavingsSummary } from "@/components/savings-summary"
import { AutomateReporting } from "@/components/automate-reporting"

export default function ReportsPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar 
        activePage="reports" 
        userName="Alex Mercer"
        userRole="FinOps Lead"
      />
      
      <div className="flex-1 flex flex-col">
        <Header title="Reports" subtitle="Group / Heros" />
        
        <main className="flex-1 p-6">
          <div className="flex gap-6">
            {/* Left side - Reports list */}
            <div className="flex-1">
              <ReportsList />
            </div>
            
            {/* Right side - Savings summary */}
            <div className="w-80 space-y-4">
              <SavingsSummary />
              <AutomateReporting />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
