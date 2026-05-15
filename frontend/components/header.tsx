"use client"

import { Search, Bell, RefreshCw } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export function Header() {
  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-border">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-semibold text-foreground">Command Center</h1>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <RefreshCw className="w-3 h-3" />
          <span>Last synced: 4 min ago</span>
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input 
            placeholder="Search clusters, services..." 
            className="w-64 pl-9 bg-secondary border-border text-sm"
          />
        </div>
        
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-cyan-400 rounded-full" />
        </Button>
        
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500" />
      </div>
    </header>
  )
}
