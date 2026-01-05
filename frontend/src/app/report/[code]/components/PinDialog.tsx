'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Lock, AlertCircle, Clock } from 'lucide-react';
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

  return (
    <Dialog open={open}>
      <DialogContent className="sm:max-w-md" onPointerDownOutside={(e) => e.preventDefault()}>
        <DialogHeader>
          <div className="mx-auto mb-4 p-3 rounded-full bg-primary/10">
            <Lock className="h-6 w-6 text-primary" />
          </div>
          <DialogTitle className="text-center">Защищённый отчёт</DialogTitle>
          <DialogDescription className="text-center">
            Для просмотра отчёта введите PIN-код, полученный от преподавателя
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Input
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              placeholder="Введите PIN-код"
              value={pin}
              onChange={handlePinChange}
              disabled={loading || isBlocked}
              className="text-center text-2xl tracking-widest font-mono"
              autoFocus
            />
            
            {error && (
              <div className="flex items-center gap-2 text-sm text-destructive">
                <AlertCircle className="h-4 w-4" />
                <span>{error}</span>
              </div>
            )}

            {attemptsLeft !== null && attemptsLeft > 0 && (
              <p className="text-sm text-muted-foreground text-center">
                Осталось попыток: {attemptsLeft}
              </p>
            )}

            {isBlocked && (
              <div className="flex items-center justify-center gap-2 text-sm text-amber-600">
                <Clock className="h-4 w-4" />
                <span>Повторите через {Math.ceil(retryAfter! / 60)} мин.</span>
              </div>
            )}
          </div>

          <Button 
            type="submit" 
            className="w-full" 
            disabled={loading || isBlocked || pin.length < 4}
          >
            {loading ? 'Проверка...' : 'Войти'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
