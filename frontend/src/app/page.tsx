'use client'

import { useState, useEffect, Suspense, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Loader2, MessageCircle } from 'lucide-react'
import { toast } from 'sonner'
import { AuthAPI, ApiError } from '@/lib/api'
import { ZodError } from 'zod'
import { AxiosError } from 'axios'

const TG_BOT_URL = process.env.NEXT_PUBLIC_TG_BOT_URL || process.env.NEXT_PUBLIC_BOT_URL || ''
const VK_BOT_URL = process.env.NEXT_PUBLIC_VK_BOT_URL || ''

function LoginForm() {
  const [otp, setOtp] = useState('')
  const [loading, setLoading] = useState(false)
  const [checkingAuth, setCheckingAuth] = useState(true)
  const router = useRouter()
  const searchParams = useSearchParams()
  const loginAttemptedRef = useRef(false)

  // Проверка авторизации при загрузке
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const res = await fetch('/api/v1/users/me', { credentials: 'include' })
        if (res.ok) {
          const user = await res.json()
          if (user.role === 'admin' || user.role === 'teacher') {
            router.replace('/admin')
            return
          } else if (user.role === 'student') {
            router.replace('/dashboard')
            return
          }
        }
      } catch {
        // Не залогинен - показываем форму
      }
      setCheckingAuth(false)
    }
    checkAuth()
  }, [router])

  useEffect(() => {
    if (checkingAuth) return
    const codeFromUrl = searchParams.get('code')
    if (codeFromUrl && codeFromUrl.length === 6 && !loginAttemptedRef.current) {
      setOtp(codeFromUrl)
      loginAttemptedRef.current = true
      const timer = setTimeout(() => handleLogin(codeFromUrl), 100)
      return () => clearTimeout(timer)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, checkingAuth])

  const handleLogin = async (code: string) => {
    if (code.length !== 6) return
    setLoading(true)

    try {
      const data = await AuthAPI.login(code)
      
      const redirectParam = searchParams.get('redirect')
      let targetPath = '/dashboard'

      if (redirectParam) {
        targetPath = redirectParam
      } else if (data.user?.role === 'admin' || data.user?.role === 'teacher') {
        targetPath = '/admin'
      }

      toast.success('Вход выполнен успешно')
      router.push(targetPath)
      router.refresh()
    } catch (err: unknown) {
      let message = 'Ошибка входа'
      
      if (err instanceof ApiError) {
        message = err.message
      } else if (err instanceof ZodError) {
        message = 'Ошибка валидации данных'
      } else if (err instanceof AxiosError) {
        message = err.response?.data?.detail || err.message
      } else if (err instanceof Error) {
        message = err.message
      }

      if (message === 'Invalid or expired code') {
        message = 'Неверный или истёкший код'
      }
      
      toast.error(message)
      setLoading(false)
    }
  }

  if (checkingAuth) {
    return (
      <div className="flex items-center justify-center">
        <Loader2 className="animate-spin text-white" size={32} />
      </div>
    )
  }

  return (
    <div className="w-full max-w-md p-8 space-y-6 bg-black/50 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl">
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-b from-white to-gray-500">
          EDU PLATFORM
        </h1>
        <p className="text-gray-400">Введите код из Telegram-бота</p>
      </div>

      <div className="space-y-4">
        <input
          type="text"
          maxLength={6}
          value={otp}
          onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
          placeholder="000000"
          className="w-full text-center text-4xl tracking-[0.5em] font-mono bg-transparent border-b-2 border-gray-700 focus:border-blue-500 outline-none py-4 transition-colors text-white placeholder-gray-800"
          disabled={loading}
        />

        <button
          onClick={() => handleLogin(otp)}
          disabled={otp.length !== 6 || loading}
          className="w-full py-3 px-4 bg-white text-black font-bold rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading && <Loader2 className="animate-spin" size={20} />}
          {loading ? 'Проверка...' : 'Войти'}
        </button>
      </div>

      {/* Выбор соц.сети */}
      <div className="space-y-3">
        <p className="text-center text-sm text-gray-500">Нет кода? Получите в боте:</p>
        <div className="flex gap-3">
          <a
            href={TG_BOT_URL || '#'}
            target="_blank"
            rel="noopener noreferrer"
            className={`flex-1 py-2.5 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${
              TG_BOT_URL 
                ? 'bg-white/10 hover:bg-white/20 text-white border border-white/10' 
                : 'bg-gray-800 text-gray-600 cursor-not-allowed pointer-events-none'
            }`}
          >
            <MessageCircle size={18} />
            Telegram
          </a>
          <a
            href={VK_BOT_URL || '#'}
            target="_blank"
            rel="noopener noreferrer"
            className={`flex-1 py-2.5 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${
              VK_BOT_URL 
                ? 'bg-white/10 hover:bg-white/20 text-white border border-white/10' 
                : 'bg-gray-800 text-gray-600 cursor-not-allowed pointer-events-none'
            }`}
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15.684 0H8.316C1.592 0 0 1.592 0 8.316v7.368C0 22.408 1.592 24 8.316 24h7.368C22.408 24 24 22.408 24 15.684V8.316C24 1.592 22.408 0 15.684 0zm3.692 17.123h-1.744c-.66 0-.864-.525-2.05-1.727-1.033-1-1.49-1.135-1.744-1.135-.356 0-.458.102-.458.593v1.575c0 .424-.135.678-1.253.678-1.846 0-3.896-1.118-5.335-3.202C4.624 10.857 4 8.684 4 8.245c0-.254.102-.491.593-.491h1.744c.44 0 .61.203.78.678.847 2.455 2.27 4.607 2.862 4.607.22 0 .322-.102.322-.66V9.721c-.068-1.186-.695-1.287-.695-1.71 0-.203.17-.407.44-.407h2.744c.373 0 .508.203.508.643v3.473c0 .372.17.508.271.508.22 0 .407-.136.813-.542 1.254-1.406 2.151-3.574 2.151-3.574.119-.254.322-.491.763-.491h1.744c.525 0 .644.27.525.643-.22 1.017-2.354 4.031-2.354 4.031-.186.305-.254.44 0 .78.186.254.796.779 1.203 1.253.745.847 1.32 1.558 1.473 2.05.17.49-.085.744-.576.744z"/>
            </svg>
            VK
          </a>
        </div>
      </div>
    </div>
  )
}

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-black text-white relative overflow-hidden">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />
      
      <Suspense fallback={<Loader2 className="animate-spin text-white" />}>
        <LoginForm />
      </Suspense>
    </div>
  )
}
