"use client"

import { 
  LayoutDashboard, 
  Cloud, 
  Lightbulb, 
  FileOutput, 
  Bell, 
  Settings,
  ChevronDown
} from "lucide-react"
import { cn } from "@/lib/utils"
import Link from "next/link"

const navigation = [
  { name: "Dashboard", icon: LayoutDashboard, href: "/" },
  { name: "Cloud Spend", icon: Cloud, href: "/cloud-spend" },
  { name: "Recommendations", icon: Lightbulb, href: "/recommendations" },
  { name: "Budgets", icon: FileOutput, href: "/budgets" },
  { name: "Reports", icon: Bell, href: "/reports" },
]

interface SidebarProps {
  activePage?: string
  userName?: string
  userRole?: string
  variant?: "default" | "enterprise"
}

export function Sidebar({ activePage = "dashboard", userName = "Alice Chen", userRole, variant = "default" }: SidebarProps) {
  const isActive = (name: string) => {
    const normalized = name.toLowerCase().replace(" ", "-")
    return normalized === activePage || (activePage === "dashboard" && name === "Dashboard")
  }

  return (
    <div className="flex flex-col h-screen w-56 bg-sidebar border-r border-sidebar-border sticky top-0">
      {/* Logo */}
      <div className="p-4 border-b border-sidebar-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-teal-500 flex items-center justify-center">
            <span className="text-white font-bold text-sm">G</span>
          </div>
          <div>
            <span className="text-lg font-semibold text-foreground">
              {variant === "enterprise" ? "Glacier Cloud" : "Glacier"}
            </span>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
              {variant === "enterprise" ? "Enterprise Tier" : "Cloud Savings Engine"}
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {navigation.map((item) => (
          <Link
            key={item.name}
            href={item.href}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors",
              isActive(item.name)
                ? "bg-sidebar-accent text-cyan-400 border-l-2 border-cyan-400" 
                : "text-muted-foreground hover:text-foreground hover:bg-sidebar-accent/50"
            )}
          >
            <item.icon className="w-4 h-4" />
            {item.name}
          </Link>
        ))}
      </nav>

      {/* Monthly Savings Card */}
      {(activePage === "cloud-spend" || activePage === "recommendations") && (
        <div className="mx-3 mb-3 p-4 bg-gradient-to-br from-cyan-950/50 to-teal-950/50 rounded-xl border border-cyan-800/30">
          <p className="text-xs text-muted-foreground mb-1">Est. Monthly Savings</p>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold text-cyan-400">$12,450</span>
            <ChevronDown className="w-4 h-4 text-cyan-400 rotate-[-90deg]" />
          </div>
        </div>
      )}

      {/* Upgrade Plan Button - Enterprise variant */}
      {variant === "enterprise" && (
        <div className="mx-3 mb-3">
          <button className="w-full py-2.5 px-4 bg-cyan-600 hover:bg-cyan-700 text-white text-sm font-medium rounded-lg transition-colors">
            Upgrade Plan
          </button>
        </div>
      )}

      {/* Bottom section */}
      <div className="p-3 space-y-1 border-t border-sidebar-border">
        <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-sidebar-accent/50 transition-colors">
          <Settings className="w-4 h-4" />
          Settings
        </button>
        
        {/* User profile */}
        <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-sidebar-accent/50 cursor-pointer transition-colors">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <span className="text-white text-xs font-medium">{userName.split(" ").map(n => n[0]).join("")}</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">{userName}</p>
            {userRole && <p className="text-[10px] text-muted-foreground">{userRole}</p>}
          </div>
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        </div>
      </div>
    </div>
  )
}
