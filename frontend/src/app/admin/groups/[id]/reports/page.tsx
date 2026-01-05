'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Plus, Eye, EyeOff, Link2, BarChart3, RefreshCw, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { toast } from '@/components/ui/sonner';
import { Skeleton } from '@/components/ui/skeleton';
import { GroupsAPI, ReportsAPI, Report, GroupDetailResponse } from '@/lib/api';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { CreateReportDialog } from './components/CreateReportDialog';
import { ReportLinkCopy } from './components/ReportLinkCopy';

export default function GroupReportsPage() {
  const params = useParams();
  const router = useRouter();
  const groupId = params.id as string;

  const [group, setGroup] = useState<GroupDetailResponse | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [reportToDelete, setReportToDelete] = useState<Report | null>(null);
  const [regeneratingId, setRegeneratingId] = useState<string | null>(null);

  useEffect(() => { loadData(); }, [groupId]);

  const loadData = async () => {
    try {
      const [groupData, reportsData] = await Promise.all([GroupsAPI.get(groupId), ReportsAPI.list()]);
      setGroup(groupData);
      setReports(reportsData.reports.filter(r => r.group_id === groupId));
    } catch (e) {
      toast.error('Ошибка загрузки данных');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteReport = async () => {
    if (!reportToDelete) return;
    try {
      await ReportsAPI.delete(reportToDelete.id);
      toast.success('Отчёт деактивирован');
      await loadData();
    } catch { toast.error('Ошибка при удалении'); }
    finally { setReportToDelete(null); }
  };

  const handleRegenerateCode = async (reportId: string) => {
    setRegeneratingId(reportId);
    try {
      await ReportsAPI.regenerate(reportId);
      toast.success('Код обновлён');
      await loadData();
    } catch { toast.error('Ошибка'); }
    finally { setRegeneratingId(null); }
  };

  const getReportTypeBadge = (type: string): React.ReactNode => {
    switch (type) {
      case 'full':
        return <Badge>Полный</Badge>;
      case 'attestation_only':
        return <Badge variant="secondary">Аттестация</Badge>;
      case 'attendance_only':
        return <Badge variant="outline">Посещаемость</Badge>;
      default:
        return <Badge variant="outline">{type}</Badge>;
    }
  };

  const getStatusBadge = (report: Report) => {
    if (!report.is_active) return <Badge variant="destructive">Неактивен</Badge>;
    if (report.expires_at && new Date(report.expires_at) < new Date()) return <Badge variant="destructive">Истёк</Badge>;
    return <Badge className="bg-green-500 hover:bg-green-600">Активен</Badge>;
  };

  const formatDate = (d?: string) => d ? new Date(d).toLocaleDateString('ru-RU') : '—';

  if (isLoading) return <div className="max-w-6xl mx-auto p-8"><Skeleton className="h-64 w-full rounded-xl" /></div>;
  if (!group) return <div className="p-8 text-center"><p className="text-muted-foreground">Группа не найдена</p></div>;

  return (
    <div className="max-w-6xl mx-auto p-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push(`/admin/groups/${groupId}`)}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Публичные отчёты</h1>
            <p className="text-muted-foreground">Группа: <span className="font-medium">{group.name}</span></p>
          </div>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)} className="gap-2"><Plus className="w-4 h-4" />Создать отчёт</Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Link2 className="w-5 h-5" />Список отчётов</CardTitle>
          <CardDescription>Управление публичными ссылками на отчёты группы</CardDescription>
        </CardHeader>
        <CardContent>
          {reports.length === 0 ? (
            <div className="text-center py-12 border rounded-lg">
              <BarChart3 className="w-12 h-12 mx-auto text-muted-foreground/30 mb-4" />
              <p className="text-muted-foreground">Отчёты ещё не созданы</p>
              <Button className="mt-4" onClick={() => setCreateDialogOpen(true)}><Plus className="w-4 h-4 mr-2" />Создать первый отчёт</Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Тип</TableHead>
                  <TableHead>Статус</TableHead>
                  <TableHead>Ссылка</TableHead>
                  <TableHead>Срок</TableHead>
                  <TableHead>PIN</TableHead>
                  <TableHead className="text-center">Просмотры</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reports.map((report) => (
                  <TableRow key={report.id}>
                    <TableCell>{getReportTypeBadge(report.report_type)}</TableCell>
                    <TableCell>{getStatusBadge(report)}</TableCell>
                    <TableCell><ReportLinkCopy code={report.code} /></TableCell>
                    <TableCell>{report.expires_at ? formatDate(report.expires_at) : 'Бессрочно'}</TableCell>
                    <TableCell>{report.has_pin ? <Badge variant="outline" className="gap-1"><Eye className="w-3 h-3" />Да</Badge> : <Badge variant="secondary" className="gap-1"><EyeOff className="w-3 h-3" />Нет</Badge>}</TableCell>
                    <TableCell className="text-center font-mono">{report.views_count}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button size="sm" variant="ghost" onClick={() => handleRegenerateCode(report.id)} disabled={regeneratingId === report.id}><RefreshCw className={`w-4 h-4 ${regeneratingId === report.id ? 'animate-spin' : ''}`} /></Button>
                        <Button size="sm" variant="ghost" className="text-destructive" onClick={() => setReportToDelete(report)}><Trash2 className="w-4 h-4" /></Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <CreateReportDialog open={createDialogOpen} onOpenChange={setCreateDialogOpen} groupId={groupId} onSuccess={() => { setCreateDialogOpen(false); loadData(); }} />

      <AlertDialog open={!!reportToDelete} onOpenChange={(open) => !open && setReportToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Деактивировать отчёт?</AlertDialogTitle>
            <AlertDialogDescription>Ссылка перестанет работать. Это действие можно отменить.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteReport} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">Деактивировать</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
