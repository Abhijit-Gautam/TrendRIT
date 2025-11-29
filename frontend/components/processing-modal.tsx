"use client"

import { useState, useEffect } from "react"
import { Loader2, CheckCircle2 } from "lucide-react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"

export default function ProcessingModal({
  memeId,
  onComplete,
}: {
  memeId: string
  onComplete: (memeId: string) => void
}) {
  const [step, setStep] = useState(0)
  const [isComplete, setIsComplete] = useState(false)

  const steps = [
    "Uploading meme...",
    "Analyzing segments...",
    "Generating depth maps...",
    "Creating 3D mesh...",
    "Processing complete!",
  ]

  useEffect(() => {
    const interval = setInterval(() => {
      setStep((prev) => {
        if (prev >= steps.length - 1) {
          setIsComplete(true)
          clearInterval(interval)
          setTimeout(() => onComplete(memeId), 2000)
          return prev
        }
        return prev + 1
      })
    }, 1200)

    return () => clearInterval(interval)
  }, [memeId, onComplete])

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-2xl p-8 max-w-md w-full space-y-6 shadow-2xl">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold">Creating Magic</h2>
          <p className="text-sm text-muted-foreground">Transforming your meme into 3D...</p>
        </div>

        <div className="space-y-3">
          {steps.map((stepName, idx) => (
            <div key={idx} className="flex items-center gap-3">
              <div className="flex-shrink-0">
                {idx < step ? (
                  <CheckCircle2 className="w-5 h-5 text-primary" />
                ) : idx === step ? (
                  <Loader2 className="w-5 h-5 text-primary animate-spin" />
                ) : (
                  <div className="w-5 h-5 rounded-full border-2 border-border" />
                )}
              </div>
              <p
                className={`text-sm font-medium transition-colors ${
                  idx <= step ? "text-foreground" : "text-muted-foreground"
                }`}
              >
                {stepName}
              </p>
            </div>
          ))}
        </div>

        <div className="w-full h-1 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary to-secondary transition-all duration-500"
            style={{ width: `${((step + 1) / steps.length) * 100}%` }}
          />
        </div>

        {isComplete && (
          <div className="text-center p-4 rounded-lg bg-primary/10 border border-primary/30 text-primary font-medium text-sm">
            ✨ Your meme is ready for export!
          </div>
        )}
      </div>
    </div>
  )
}
