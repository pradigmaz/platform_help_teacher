'use client';

import { Save, Loader2, Eye, EyeOff, Users, FileText, MessageSquare } from 'lucide-react';
import { IconBrandTelegram, IconBrandVk, IconMessage } from '@tabler/icons-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { ContactVisibility } from '@/lib/api';
import { cn } from '@/lib/utils';

const visibilityOptions: { value: ContactVisibility; label: string; icon: React.ReactNode; description: string }[] = [
  { value: 'student', label: 'Студентам', icon: <Users className="h-4 w-4" />, description: 'Видно в ЛК студента' },
  { value: 'report', label: 'В отчёте', icon: <FileText className="h-4 w-4" />, description: 'Видно в публичном отчёте' },
  { value: 'both', label: 'Везде', icon: <Eye className="h-4 w-4" />, description: 'Видно везде' },
  { value: 'none', label: 'Скрыто', icon: <EyeOff className="h-4 w-4" />, description: 'Не отображается' },
];

const contactFields = [
  { key: 'telegram', label: 'Telegram', icon: IconBrandTelegram, placeholder: '@username', color: 'text-blue-500', bgColor: 'bg-blue-500/10', description: 'Ваш Telegram для связи' },
  { key: 'vk', label: 'ВКонтакте', icon: IconBrandVk, placeholder: 'vk.com/id или @username', color: 'text-blue-600', bgColor: 'bg-blue-600/10', description: 'Страница или группа ВК' },
  { key: 'max', label: 'MAX', icon: IconMessage, placeholder: '@username или ссылка', color: 'text-green-500', bgColor: 'bg-green-500/10', description: 'Мессенджер MAX' },
] as const;

export type ContactFieldKey = typeof contactFields[number]['key'];

interface ContactsCardProps {
  contacts: Record<ContactFieldKey, string>;
  visibility: Record<ContactFieldKey, ContactVisibility>;
  isSaving: boolean;
  onContactChange: (key: ContactFieldKey, value: string) => void;
  onVisibilityChange: (key: ContactFieldKey, value: ContactVisibility) => void;
  onSave: () => void;
}

export function ContactsCard({
  contacts, visibility, isSaving,
  onContactChange, onVisibilityChange, onSave
}: ContactsCardProps) {
  const getVisibilityBadge = (vis: ContactVisibility) => {
    const option = visibilityOptions.find(o => o.value === vis);
    if (!option || vis === 'none') return null;
    return (
      <Badge variant="secondary" className="text-xs gap-1">
        {option.icon}
        {option.label}
      </Badge>
    );
  };

  return (
    <Card className="border-border/50">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-blue-500/10">
            <MessageSquare className="h-5 w-5 text-blue-500" />
          </div>
          <div>
            <CardTitle className="text-lg">Контакты для связи</CardTitle>
            <CardDescription>Укажите мессенджеры, через которые студенты смогут с вами связаться</CardDescription>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {contactFields.map((field, index) => (
          <div key={field.key}>
            {index > 0 && <Separator className="mb-6" />}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={cn("p-2 rounded-lg", field.bgColor)}>
                    <field.icon className={cn("h-5 w-5", field.color)} />
                  </div>
                  <div>
                    <Label className="text-base font-medium">{field.label}</Label>
                    <p className="text-xs text-muted-foreground">{field.description}</p>
                  </div>
                </div>
                {getVisibilityBadge(visibility[field.key])}
              </div>

              <div className="grid gap-4 sm:grid-cols-[1fr,180px]">
                <Input
                  id={field.key}
                  placeholder={field.placeholder}
                  value={contacts[field.key]}
                  onChange={(e) => onContactChange(field.key, e.target.value)}
                  className="h-11"
                />
                <Select
                  value={visibility[field.key]}
                  onValueChange={(value) => onVisibilityChange(field.key, value as ContactVisibility)}
                >
                  <SelectTrigger className="h-11">
                    <SelectValue placeholder="Видимость" />
                  </SelectTrigger>
                  <SelectContent>
                    {visibilityOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        <div className="flex items-center gap-2">
                          {option.icon}
                          <span>{option.label}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        ))}

        <div className="flex justify-end pt-4 border-t">
          <Button onClick={onSave} disabled={isSaving} size="lg" className="min-w-[140px]">
            {isSaving ? (
              <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Сохранение...</>
            ) : (
              <><Save className="mr-2 h-4 w-4" />Сохранить</>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
