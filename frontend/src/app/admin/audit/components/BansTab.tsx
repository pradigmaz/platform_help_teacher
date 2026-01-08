"use client";

import { useState, useEffect } from "react";
import { Ban, Clock, Globe, User, Unlock, AlertTriangle, History } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RateLimitAPI, type RateLimitWarning } from "@/lib/api";
import { toast } from "sonner";

const LEVEL_BADGES: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  soft_warning: { label: "Предупреждение", variant: "secondary" },
  recorded: { label: "Записано", variant: "outline" },
  soft_ban: { label: "Мягкий бан", variant: "default" },
  hard_ban: { label: "Жёсткий бан", variant: "destructive" },
};

export function BansTab() {
  const [activeBans, setActiveBans] = useState<RateLimitWarning[]>([]);
  const [history, setHistory] = useState<RateLimitWarning[]>([]);
  const [loading, setLoading] = useState(true);
  const [unbanDialog, setUnbanDialog] = useState<RateLimitWarning | null>(null);
  const [unbanReason, setUnbanReason] = useState("");
  const [unbanning, setUnbanning] = useState(false);
  const [subTab, setSubTab] = useState("active");

  const fetchData = async () => {
    setLoading(true);
    try {
      const [bansData, historyData] = await Promise.all([
        RateLimitAPI.getActiveBans(0, 100),
        RateLimitAPI.getHistory({ limit: 100 }),
      ]);
      setActiveBans(bansData.items);
      setHistory(historyData.items);
    } catch (error) {
      console.error("Failed to fetch bans:", error);
      toast.error("Не удалось загрузить данные о банах");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleUnban = async () => {
    if (!unbanDialog || !unbanReason.trim()) return;
    
    setUnbanning(true);
    try {
      await RateLimitAPI.unban(unbanDialog.id, unbanReason);
      toast.success("Пользователь разбанен");
      setUnbanDialog(null);
      setUnbanReason("");
      fetchData();
    } catch (error) {
      console.error("Failed to unban:", error);
      toast.error("Не удалось разбанить");
    } finally {
      setUnbanning(false);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatBanUntil = (dateStr: string | null) => {
    if (!dateStr) return "—";
    const date = new Date(dateStr);
    const now = new Date();
    const diff = date.getTime() - now.getTime();
    
    if (diff <= 0) return "Истёк";
    
    const minutes = Math.floor(diff / 60000);
    if (minutes < 60) return `${minutes} мин`;
    const hours = Math.floor(minutes / 60);
    return `${hours} ч ${minutes % 60} мин`;
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Tabs value={subTab} onValueChange={setSubTab}>
        <TabsList>
          <TabsTrigger value="active" className="gap-2">
            <Ban className="h-4 w-4" />
            Активные баны ({activeBans.length})
          </TabsTrigger>
          <TabsTrigger value="history" className="gap-2">
            <History className="h-4 w-4" />
            История
          </TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="mt-4">
          {activeBans.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Ban className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Нет активных банов</p>
            </div>
          ) : (
            <BansTable 
              items={activeBans} 
              onUnban={setUnbanDialog}
              formatDate={formatDate}
              formatBanUntil={formatBanUntil}
              showUnban
            />
          )}
        </TabsContent>

        <TabsContent value="history" className="mt-4">
          {history.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <History className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>История пуста</p>
            </div>
          ) : (
            <BansTable 
              items={history} 
              formatDate={formatDate}
              formatBanUntil={formatBanUntil}
              showUnban={false}
            />
          )}
        </TabsContent>
      </Tabs>

      {/* Unban Dialog */}
      <Dialog open={!!unbanDialog} onOpenChange={() => setUnbanDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Разбанить пользователя</DialogTitle>
            <DialogDescription>
              {unbanDialog?.user_name || unbanDialog?.ip_address}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Причина разбана</Label>
              <Input
                value={unbanReason}
                onChange={(e) => setUnbanReason(e.target.value)}
                placeholder="Например: ошибочный бан, проверено"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setUnbanDialog(null)}>
              Отмена
            </Button>
            <Button 
              onClick={handleUnban} 
              disabled={!unbanReason.trim() || unbanning}
            >
              {unbanning ? "Разбан..." : "Разбанить"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function BansTable({ 
  items, 
  onUnban,
  formatDate,
  formatBanUntil,
  showUnban,
}: {
  items: RateLimitWarning[];
  onUnban?: (item: RateLimitWarning) => void;
  formatDate: (d: string | null) => string;
  formatBanUntil: (d: string | null) => string;
  showUnban: boolean;
}) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Пользователь</TableHead>
          <TableHead>IP</TableHead>
          <TableHead>Уровень</TableHead>
          <TableHead>Нарушений</TableHead>
          <TableHead>Бан до</TableHead>
          <TableHead>Создан</TableHead>
          {showUnban && <TableHead className="w-[100px]">Действия</TableHead>}
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((item) => {
          const levelInfo = LEVEL_BADGES[item.warning_level] || { 
            label: item.warning_level, 
            variant: "outline" as const 
          };
          
          return (
            <TableRow key={item.id}>
              <TableCell>
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-muted-foreground" />
                  {item.user_name || "Аноним"}
                </div>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Globe className="h-4 w-4 text-muted-foreground" />
                  <code className="text-xs">{item.ip_address}</code>
                </div>
              </TableCell>
              <TableCell>
                <Badge variant={levelInfo.variant}>{levelInfo.label}</Badge>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-1">
                  <AlertTriangle className="h-4 w-4 text-yellow-500" />
                  {item.violation_count}
                </div>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  {formatBanUntil(item.ban_until)}
                </div>
              </TableCell>
              <TableCell className="text-muted-foreground text-sm">
                {formatDate(item.created_at)}
              </TableCell>
              {showUnban && (
                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onUnban?.(item)}
                  >
                    <Unlock className="h-4 w-4" />
                  </Button>
                </TableCell>
              )}
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
