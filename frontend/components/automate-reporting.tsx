import { Sparkles } from "lucide-react"

export function AutomateReporting() {
  return (
    <div className="bg-gradient-to-br from-purple-950/40 to-indigo-950/40 rounded-xl border border-purple-800/30 p-5">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-lg bg-purple-900/50 flex items-center justify-center flex-shrink-0">
          <Sparkles className="w-4 h-4 text-purple-400" />
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-medium text-foreground mb-1">Automate your reporting</h3>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Have insights delivered directly to your team in Slack or via email.
          </p>
          <button className="mt-3 text-xs font-medium text-purple-400 hover:text-purple-300 transition-colors">
            Configure Slack integration →
          </button>
        </div>
      </div>
    </div>
  )
}
