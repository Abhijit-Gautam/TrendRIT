"use client"

import { useState } from "react"
import { Upload, Wand2, Zap } from "lucide-react"
import Header from "@/components/header"
import UploadSection from "@/components/upload-section"
import MemeGallery from "@/components/meme-gallery"
import TrendingSection from "@/components/trending-section"
import ProcessingModal from "@/components/processing-modal"

export default function Home() {
  const [userId, setUserId] = useState("user-" + Math.random().toString(36).substr(2, 9))
  const [memes, setMemes] = useState<any[]>([])
  const [trending, setTrending] = useState<any[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [currentMemeId, setCurrentMemeId] = useState<string | null>(null)

  const handleUploadSuccess = (memeId: string, imageUrl: string) => {
    setMemes((prev) => [
      {
        id: memeId,
        image_url: imageUrl,
        status: "processing",
        created_at: new Date().toISOString(),
      },
      ...prev,
    ])
    setIsProcessing(true)
    setCurrentMemeId(memeId)
  }

  const handleProcessingComplete = (memeId: string) => {
    setIsProcessing(false)
    setCurrentMemeId(null)
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-background via-muted to-background">
      <Header userId={userId} />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-20">
        {/* Hero Section */}
        <section className="text-center space-y-6 py-12">
          <div className="space-y-4">
            <h1 className="text-5xl md:text-6xl font-bold text-balance">
              Meme to{" "}
              <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">3D Magic</span>
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto text-pretty">
              Transform your favorite memes into stunning 3D experiences. Upload, generate, and export like never
              before.
            </p>
          </div>
        </section>

        {/* Upload Section */}
        <UploadSection onUploadSuccess={handleUploadSuccess} userId={userId} />

        {/* Features Grid */}
        <section className="grid md:grid-cols-3 gap-6">
          <div className="group relative overflow-hidden rounded-xl bg-card border border-border p-6 hover:border-primary/50 transition-all duration-300 hover:shadow-lg">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative space-y-4">
              <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                <Upload className="w-6 h-6 text-primary-foreground" />
              </div>
              <h3 className="text-lg font-semibold">Easy Upload</h3>
              <p className="text-sm text-muted-foreground">Drop your meme images in any format - JPG, PNG, or GIF</p>
            </div>
          </div>

          <div className="group relative overflow-hidden rounded-xl bg-card border border-border p-6 hover:border-primary/50 transition-all duration-300 hover:shadow-lg">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative space-y-4">
              <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                <Wand2 className="w-6 h-6 text-primary-foreground" />
              </div>
              <h3 className="text-lg font-semibold">AI Generation</h3>
              <p className="text-sm text-muted-foreground">
                Smart AI segments subjects and creates depth maps automatically
              </p>
            </div>
          </div>

          <div className="group relative overflow-hidden rounded-xl bg-card border border-border p-6 hover:border-primary/50 transition-all duration-300 hover:shadow-lg">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative space-y-4">
              <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                <Zap className="w-6 h-6 text-primary-foreground" />
              </div>
              <h3 className="text-lg font-semibold">Export Magic</h3>
              <p className="text-sm text-muted-foreground">Export as stunning GIFs or videos with custom scenes</p>
            </div>
          </div>
        </section>

        {/* Meme Gallery */}
        {memes.length > 0 && <MemeGallery memes={memes} userId={userId} />}

        {/* Trending Section */}
        <TrendingSection />

        {/* Processing Modal */}
        {isProcessing && currentMemeId && (
          <ProcessingModal memeId={currentMemeId} onComplete={handleProcessingComplete} />
        )}
      </div>
    </main>
  )
}
