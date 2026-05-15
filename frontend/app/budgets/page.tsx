"use client"

import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { BudgetCards } from "@/components/budget-cards"
import { BudgetAlerts } from "@/components/budget-alerts"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function BudgetsPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar 
        activePage="budgets" 
        userName="Admin User" 
        userRole="admin@glacier.cloud"
        variant="enterprise"
      />
      <div className="flex-1 flex flex-col">
        <Header title="Budgets" hideLastSync />
        <main className="flex-1 p-6 overflow-auto">
          {/* Page Header */}
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-2xl font-semibold text-foreground mb-1">Budgets</h1>
              <p className="text-sm text-muted-foreground">
                Monitor and control your cloud spending across environments.
              </p>
            </div>
            <Button className="bg-cyan-600 hover:bg-cyan-700 text-white gap-2">
              <Plus className="w-4 h-4" />
              Create budget
            </Button>
          </div>

          {/* Budget Cards */}
          <BudgetCards />

          {/* Budget Alerts */}
          <BudgetAlerts />
        </main>
      </div>
    </div>
  )
}
