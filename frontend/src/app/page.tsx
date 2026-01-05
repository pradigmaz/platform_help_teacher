'use client'

import { useState, useEffect, Suspense, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { AuthAPI, ApiError } from '@/lib/api'
import { ZodError } from 'zod'
import { AxiosError } from 'axios'

const BOT_URL = process.env.NEXT_PUBLIC_BOT_URL || ''

function LoginForm() {
  const [otp, setOtp] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const searchParams = useSearchParams()
  const loginAttemptedRef = useRef(false)

  useEffect(() => {
    const codeFromUrl = searchParams.get('code')
    if (codeFromUrl && codeFromUrl.length === 6 && !loginAttemptedRef.current) {
      setOtp(codeFromUrl)
      loginAttemptedRef.current = true
      const timer = setTimeout(() => handleLogin(codeFromUrl), 100)
      return () => clearTimeout(timer)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams])

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

      <div className="text-center text-sm text-gray-500">
        Нет кода? Напишите{' '}
        {BOT_URL ? (
          <a 
            href={BOT_URL} 
            target="_blank" 
            rel="noopener noreferrer"
            className="font-mono text-blue-400 hover:text-blue-300 transition underline"
          >
            /start
          </a>
        ) : (
          <span className="font-mono text-blue-400">/start</span>
        )}
        {' '}боту
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
