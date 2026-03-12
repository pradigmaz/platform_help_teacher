'use client'

import { Suspense } from 'react'
import { Loader2 } from 'lucide-react'
import { useAutoLogin } from '@/hooks/useAutoLogin'

function LoginForm() {
  const { otp, setOtp, rememberDevice, setRememberDevice, loading, checkingAuth, login, devLogin, canUseDevLogin } = useAutoLogin()

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
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600">
          Авторизация
        </h1>
        <p className="text-gray-400">Введите код из Telegram-бота</p>
      </div>

      <div className="space-y-4">
        <input
          type="text"
          maxLength={6}
          value={otp}
          onChange={(e) => setOtp(e.target.value)}
          placeholder="000000"
          className="w-full text-center text-4xl tracking-[0.5em] font-mono bg-transparent border-b-2 border-gray-700 focus:border-blue-500 outline-none py-4 transition-colors text-white placeholder-gray-800"
          disabled={loading}
        />

        <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={rememberDevice}
            onChange={(e) => setRememberDevice(e.target.checked)}
            className="w-4 h-4 rounded border-gray-600 bg-transparent text-blue-500 focus:ring-blue-500 focus:ring-offset-0"
            disabled={loading}
          />
          Запомнить устройство
        </label>

        <button
          onClick={() => login()}
          disabled={otp.length !== 6 || loading}
          className="w-full py-3 px-4 bg-white text-black font-bold rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading && <Loader2 className="animate-spin" size={20} />}
          {loading ? 'Проверка...' : 'Войти'}
        </button>

        {canUseDevLogin && (
          <button
            onClick={() => devLogin()}
            disabled={loading}
            className="w-full py-3 px-4 rounded-lg border border-emerald-500/40 bg-emerald-500/10 text-emerald-200 font-semibold hover:bg-emerald-500/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Войти как dev admin
          </button>
        )}
      </div>

      <div className="text-center text-sm text-gray-500">
        {canUseDevLogin ? 'Или используйте dev-вход выше.' : <>Нет кода? Напишите <span className="font-mono text-blue-400">/start</span> боту</>}
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-black text-white relative overflow-hidden">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />
      
      <Suspense fallback={<div className="text-white">Загрузка...</div>}>
        <LoginForm />
      </Suspense>
    </div>
  )
}
