"use client"

import { useState } from "react"
import Image from "next/image"
import { Loader2, Download, Sparkles } from "lucide-react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"

interface Meme {
  id: string
  image_url: string
  status: string
  created_at: string
}

export default function MemeGallery({ memes, userId }: { memes: Meme[]; userId: string }) {
  const [generatingId, setGeneratingId] = useState<string | null>(null)
  const [exportingId, setExportingId] = useState<string | null>(null)

  const handleGenerate3D = async (memeId: string) => {
    setGeneratingId(memeId)
    try {
      const response = await fetch(`${API_BASE_URL}/generate-3d/${memeId}`, {
        method: "POST",
      })

      if (response.ok) {
        const data = await response.json()
        console.log("3D generation started:", data)
      }
    } catch (err) {
      console.error("Failed to generate 3D:", err)
    } finally {
      setGeneratingId(null)
    }
  }

  const handleExport = async (memeId: string) => {
    setExportingId(memeId)
    try {
      const response = await fetch(`${API_BASE_URL}/export/${memeId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ format: "gif" }),
      })

      if (response.ok) {
        const data = await response.json()
        window.open(data.url, "_blank")
      }
    } catch (err) {
      console.error("Failed to export:", err)
    } finally {
      setExportingId(null)
    }
  }

  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold">Your Memes</h2>
        <p className="text-muted-foreground">Transform your uploads into 3D masterpieces</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {memes.map((meme) => (
          <div
            key={meme.id}
            className="group relative overflow-hidden rounded-xl border border-border hover:border-primary/50 transition-all duration-300 hover:shadow-lg hover:shadow-primary/20 bg-card"
          >
            <div className="relative h-64 w-full bg-muted overflow-hidden">
              <Image
                src={meme.image_url || "/placeholder.svg"}
                alt="Meme"
                fill
                className="object-cover group-hover:scale-105 transition-transform duration-300"
              />

              {meme.status === "processing" && (
                <div className="absolute inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center">
                  <div className="text-center">
                    <Loader2 className="w-8 h-8 text-white animate-spin mx-auto mb-2" />
                    <p className="text-white text-sm font-medium">Processing...</p>
                  </div>
                </div>
              )}
            </div>

            <div className="p-4 space-y-4">
              <div className="text-sm text-muted-foreground">{new Date(meme.created_at).toLocaleDateString()}</div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleGenerate3D(meme.id)}
                  disabled={generatingId === meme.id || meme.status === "processing"}
                  className="flex-1 px-4 py-2 rounded-lg font-medium bg-gradient-to-r from-primary to-secondary text-primary-foreground hover:shadow-lg hover:shadow-primary/30 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {generatingId === meme.id ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="text-sm">Generating...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      <span className="text-sm">Generate 3D</span>
                    </>
                  )}
                </button>

                <button
                  onClick={() => handleExport(meme.id)}
                  disabled={exportingId === meme.id}
                  className="px-4 py-2 rounded-lg font-medium border border-primary/30 text-primary hover:bg-primary/10 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {exportingId === meme.id ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Download className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
