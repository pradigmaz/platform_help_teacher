'use client';

import { useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Lock, AlertCircle, Clock, ShieldCheck } from 'lucide-react';
import { PublicReportAPI, ApiError } from '@/lib/api';

interface PinDialogProps {
  code: string;
  open: boolean;
  onSuccess: () => void;
}

export function PinDialog({ code, open, onSuccess }: PinDialogProps) {
  const [pin, setPin] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [attemptsLeft, setAttemptsLeft] = useState<number | null>(null);
  const [retryAfter, setRetryAfter] = useState<number | null>(null);

  useEffect(() => {
    if (!retryAfter || retryAfter <= 0) {
      return;
    }

    const timer = window.setInterval(() => {
      setRetryAfter((current) => {
        if (!current || current <= 1) {
          window.clearInterval(timer);
          return null;
        }

        return current - 1;
      });
    }, 1000);

    return () => window.clearInterval(timer);
  }, [retryAfter]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pin || pin.length < 4) {
      setError('PIN должен содержать минимум 4 цифры');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await PublicReportAPI.verifyPin(code, pin);
      if (result.success) {
        onSuccess();
      } else {
        setError(result.message || 'Неверный PIN-код');
        if (result.attempts_left !== undefined) {
          setAttemptsLeft(result.attempts_left);
        }
        if (result.retry_after !== undefined) {
          setRetryAfter(result.retry_after);
        }
      }
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 429) {
          setRetryAfter(900); // 15 minutes
          setError('Слишком много попыток. Попробуйте позже.');
        } else {
          setError(err.message);
        }
      } else {
        setError('Ошибка проверки PIN-кода');
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePinChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 6);
    setPin(value);
    setError(null);
  };

  const isBlocked = retryAfter !== null && retryAfter > 0;
  const retryMinutes = retryAfter ? Math.floor(retryAfter / 60) : 0;
  const retrySeconds = retryAfter ? retryAfter % 60 : 0;

  return (
    <Dialog open={open}>
      <DialogContent
        className="overflow-hidden rounded-3xl border-border/60 p-0 shadow-xl sm:max-w-md"
        onPointerDownOutside={(e) => e.preventDefault()}
      >
        <DialogHeader className="border-b border-border/60 bg-muted/30 px-6 py-6">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
            <ShieldCheck className="h-7 w-7 text-primary" />
          </div>
          <DialogTitle className="text-center text-2xl">Защищённый отчёт</DialogTitle>
          <DialogDescription className="text-center">
            Для просмотра отчёта введите PIN-код, полученный от преподавателя
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-5 px-6 py-6">
          <div className="rounded-2xl border border-border/60 bg-background/70 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm text-muted-foreground">
              <Lock className="h-4 w-4" />
              <span>PIN нужен только для этого отчёта</span>
            </div>
            <div className="space-y-2">
              <Label htmlFor="public-report-pin">PIN-код</Label>
              <p className="text-sm text-muted-foreground">
                Введите от 4 до 6 цифр. Данные отчёта не изменятся, вы просто подтвердите доступ.
              </p>
            </div>
          </div>

          <div className="space-y-3">
            <Input
              id="public-report-pin"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              autoComplete="one-time-code"
              placeholder="0000"
              value={pin}
              onChange={handlePinChange}
              disabled={loading || isBlocked}
              className="h-14 text-center font-mono text-2xl tracking-[0.35em]"
              autoFocus
            />

            {error && (
              <div className="flex items-start gap-2 rounded-2xl border border-destructive/20 bg-destructive/5 px-3 py-2 text-sm text-destructive">
                <AlertCircle className="h-4 w-4" />
                <span>{error}</span>
              </div>
            )}

            {attemptsLeft !== null && attemptsLeft > 0 && (
              <p className="text-center text-sm text-muted-foreground">
                Осталось попыток: {attemptsLeft}
              </p>
            )}

            {isBlocked && (
              <div className="flex items-center justify-center gap-2 rounded-2xl border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-sm text-amber-700 dark:text-amber-300">
                <Clock className="h-4 w-4" />
                <span>
                  Повторите через {retryMinutes}:{String(retrySeconds).padStart(2, '0')}
                </span>
              </div>
            )}
          </div>

          <Button
            type="submit"
            className="h-11 w-full"
            disabled={loading || isBlocked || pin.length < 4}
          >
            {loading ? 'Проверка...' : 'Войти'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
