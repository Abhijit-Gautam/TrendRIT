"use client"

import { Sparkles, Menu } from "lucide-react"
import { useState } from "react"

export default function Header({ userId }: { userId: string }) {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-background/95 border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              TrendRIT
            </span>
          </div>

          <div className="hidden md:flex items-center gap-8">
            <nav className="flex gap-6 text-sm font-medium text-muted-foreground">
              <a href="#" className="hover:text-foreground transition-colors">
                Explore
              </a>
              <a href="#" className="hover:text-foreground transition-colors">
                Trending
              </a>
              <a href="#" className="hover:text-foreground transition-colors">
                Gallery
              </a>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-sm text-muted-foreground">
              <span className="font-mono text-xs px-3 py-1 rounded-full bg-muted text-foreground">
                {userId.slice(-6)}
              </span>
            </div>
            <button className="md:hidden p-2 hover:bg-muted rounded-lg transition-colors">
              <Menu className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
