"use client"

import type React from "react"

import { useState, useRef } from "react"
import { Upload, Loader2 } from "lucide-react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"

export default function UploadSection({
  onUploadSuccess,
  userId,
}: {
  onUploadSuccess: (memeId: string, imageUrl: string) => void
  userId: string
}) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileUpload = async (file: File) => {
    if (!file.type.startsWith("image/")) {
      setError("Please select an image file")
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append("file", file)
      formData.append("user_id", userId)

      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error("Upload failed")
      }

      const data = await response.json()
      onUploadSuccess(data.meme_id, data.image_url)

      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }
    } catch (err) {
      setError("Failed to upload. Please try again.")
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDragAndDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()

    const files = e.dataTransfer.files
    if (files && files[0]) {
      handleFileUpload(files[0])
    }
  }

  return (
    <section className="w-full">
      <div onDragOver={(e) => e.preventDefault()} onDrop={handleDragAndDrop} className="relative group">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/20 via-secondary/20 to-primary/20 rounded-2xl blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

        <div className="relative bg-gradient-to-br from-card to-muted rounded-2xl border-2 border-dashed border-primary/30 hover:border-primary/60 transition-all duration-300 p-12">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
            className="hidden"
          />

          <div className="flex flex-col items-center justify-center gap-4 text-center">
            <div className="p-4 rounded-full bg-gradient-to-br from-primary/10 to-secondary/10">
              {isLoading ? (
                <Loader2 className="w-8 h-8 text-primary animate-spin" />
              ) : (
                <Upload className="w-8 h-8 text-primary" />
              )}
            </div>

            <div className="space-y-2">
              <h3 className="text-2xl font-bold text-balance">
                {isLoading ? "Uploading your meme..." : "Drop your meme here"}
              </h3>
              <p className="text-muted-foreground">or click below to browse. Supports JPG, PNG, GIF</p>
            </div>

            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              className="mt-4 px-8 py-3 rounded-lg font-semibold bg-gradient-to-r from-primary to-secondary text-primary-foreground hover:shadow-lg hover:shadow-primary/30 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? "Processing..." : "Select File"}
            </button>

            {error && <p className="text-sm text-destructive mt-2">{error}</p>}
          </div>
        </div>
      </div>
    </section>
  )
}
