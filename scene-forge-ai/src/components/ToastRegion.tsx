import { useEffect } from 'react'
import { CheckCircle2, CircleAlert, Info, X } from 'lucide-react'

export interface ToastMessage {
  id: number
  message: string
  tone: 'success' | 'error' | 'info'
}

interface ToastRegionProps {
  toasts: ToastMessage[]
  onDismiss: (id: number) => void
}

const icons = {
  success: CheckCircle2,
  error: CircleAlert,
  info: Info,
}

export default function ToastRegion({ toasts, onDismiss }: ToastRegionProps) {
  useEffect(() => {
    const timers = toasts.map((toast) =>
      window.setTimeout(() => onDismiss(toast.id), toast.tone === 'error' ? 6500 : 4200),
    )
    return () => timers.forEach((timer) => window.clearTimeout(timer))
  }, [onDismiss, toasts])

  return (
    <div className="toast-region" aria-live="polite" aria-label="操作通知">
      {toasts.map((toast) => {
        const Icon = icons[toast.tone]
        return (
          <div className={`toast toast-${toast.tone}`} key={toast.id}>
            <Icon size={18} aria-hidden="true" />
            <p>{toast.message}</p>
            <button type="button" aria-label="关闭通知" onClick={() => onDismiss(toast.id)}>
              <X size={16} />
            </button>
          </div>
        )
      })}
    </div>
  )
}
