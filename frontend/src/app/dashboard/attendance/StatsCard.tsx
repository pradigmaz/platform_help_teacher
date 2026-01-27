import { IconAlertCircle, IconCheck, IconClock, IconX } from '@tabler/icons-react';
import { motion } from 'motion/react';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { NumberTicker } from '@/components/ui/number-ticker';
import type { NormalizedStats } from './types';
import type React from 'react';

type StatMiniProps = {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: 'green' | 'yellow' | 'blue' | 'red';
};

export function AttendanceStatsRow({ stats }: { stats: NormalizedStats }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
      <CardSpotlight className="p-4 text-center">
        <p className="text-3xl font-bold text-green-500">
          <NumberTicker value={Math.round(stats.attendance_rate)} />%
        </p>
        <p className="text-xs text-muted-foreground">Посещаемость</p>
      </CardSpotlight>
      <StatMini icon={<IconCheck className="h-4 w-4" />} label="Был" value={stats.present} color="green" />
      <StatMini icon={<IconClock className="h-4 w-4" />} label="Опоздал" value={stats.late} color="yellow" />
      <StatMini icon={<IconAlertCircle className="h-4 w-4" />} label="Уваж." value={stats.excused} color="blue" />
      <StatMini icon={<IconX className="h-4 w-4" />} label="Пропуск" value={stats.absent} color="red" />
    </div>
  );
}

function StatMini({ icon, label, value, color }: StatMiniProps) {
  const colorClasses = {
    green: 'text-green-500',
    yellow: 'text-yellow-500',
    blue: 'text-blue-500',
    red: 'text-red-500',
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="p-3 rounded-xl border border-border bg-card flex items-center gap-2"
    >
      <span className={colorClasses[color]}>{icon}</span>
      <div>
        <p className="text-lg font-bold text-foreground">{value}</p>
        <p className="text-[10px] text-muted-foreground">{label}</p>
      </div>
    </motion.div>
  );
}
