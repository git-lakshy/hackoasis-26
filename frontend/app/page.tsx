import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { MetricCards } from "@/components/metric-cards"
import { CostForecastChart } from "@/components/cost-forecast-chart"
import { TopRecommendations } from "@/components/top-recommendations"
import { CloudCostByService } from "@/components/cloud-cost-by-service"
import { BottomCharts } from "@/components/bottom-charts"

export default function Dashboard() {
  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          <MetricCards />
          <CostForecastChart />
          <TopRecommendations />
          <CloudCostByService />
          <BottomCharts />
        </main>
      </div>
    </div>
  )
}
