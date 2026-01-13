/**
 * Централизованный logger для фронтенда
 * В dev — console, в prod — можно подключить Sentry/аналитику
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogContext {
  component?: string;
  action?: string;
  [key: string]: unknown;
}

const isDev = process.env.NODE_ENV === 'development';

function formatMessage(level: LogLevel, message: string, context?: LogContext): string {
  const prefix = context?.component ? `[${context.component}]` : '';
  return `${prefix} ${message}`.trim();
}

export const logger = {
  debug(message: string, context?: LogContext) {
    if (isDev) {
      console.debug(formatMessage('debug', message, context), context);
    }
  },

  info(message: string, context?: LogContext) {
    if (isDev) {
      console.info(formatMessage('info', message, context), context);
    }
  },

  warn(message: string, context?: LogContext) {
    console.warn(formatMessage('warn', message, context), context);
    // TODO: В продакшене отправлять в Sentry
  },

  error(message: string, error?: unknown, context?: LogContext) {
    console.error(formatMessage('error', message, context), error, context);
    // TODO: В продакшене отправлять в Sentry
    // if (!isDev && typeof Sentry !== 'undefined') {
    //   Sentry.captureException(error, { extra: context });
    // }
  },
};

export default logger;
