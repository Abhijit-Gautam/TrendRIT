"use client"

import { useState, useEffect } from "react"
import { TrendingUp, Loader2 } from "lucide-react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"

interface Trend {
  title: string
  description: string
  reason: string
  scene_ideas: string[]
}

export default function TrendingSection() {
  const [trends, setTrends] = useState<Trend[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState("memes")

  useEffect(() => {
    const fetchTrending = async () => {
      setIsLoading(true)
      try {
        const response = await fetch(`${API_BASE_URL}/trending?category=${selectedCategory}`)
        const data = await response.json()
        setTrends(data.trends || [])
      } catch (err) {
        console.error("Failed to fetch trending:", err)
        setTrends([])
      } finally {
        setIsLoading(false)
      }
    }

    fetchTrending()
  }, [selectedCategory])

  const categories = ["memes", "news", "pop_culture", "music"]

  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold flex items-center gap-2">
          <TrendingUp className="w-8 h-8 text-primary" />
          Trending Now
        </h2>
        <p className="text-muted-foreground">Discover what's hot and get inspired</p>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-2">
        {categories.map((category) => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={`px-4 py-2 rounded-full font-medium transition-all duration-300 whitespace-nowrap capitalize ${
              selectedCategory === category
                ? "bg-gradient-to-r from-primary to-secondary text-primary-foreground shadow-lg shadow-primary/30"
                : "border border-border text-muted-foreground hover:border-primary/50"
            }`}
          >
            {category.replace("_", " ")}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          {trends.map((trend, idx) => (
            <div
              key={idx}
              className="group relative overflow-hidden rounded-xl bg-gradient-to-br from-card to-muted border border-border hover:border-primary/50 transition-all duration-300 hover:shadow-lg hover:shadow-primary/20 p-6"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-secondary/5 opacity-0 group-hover:opacity-100 transition-opacity" />

              <div className="relative space-y-3">
                <h3 className="text-xl font-bold text-balance">{trend.title}</h3>
                <p className="text-sm text-muted-foreground">{trend.description}</p>

                <div className="flex items-center gap-2 pt-2">
                  <span className="text-xs font-semibold text-primary bg-primary/10 px-2 py-1 rounded-full">
                    {trend.reason}
                  </span>
                </div>

                {trend.scene_ideas && trend.scene_ideas.length > 0 && (
                  <div className="pt-3 border-t border-border">
                    <p className="text-xs font-medium text-muted-foreground mb-2">Scene ideas:</p>
                    <div className="flex flex-wrap gap-2">
                      {trend.scene_ideas.map((idea, i) => (
                        <span
                          key={i}
                          className="text-xs px-2 py-1 rounded-lg bg-secondary/20 text-secondary-foreground border border-secondary/30"
                        >
                          {idea}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
