'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { BookOpenCheck, FolderGit2, GraduationCap, Link2, SplitSquareVertical } from 'lucide-react';
import { toast } from 'sonner';
import { BlurFade } from '@/components/ui/blur-fade';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ExamBanksAPI, type AdminExamOfferingRef, type AdminExamSubjectGroup } from '@/lib/api';
import { ExamBankAssignmentDialog } from './components/ExamBankAssignmentDialog';
import { ExamBankSplitDialog } from './components/ExamBankSplitDialog';
import { ExamOfferingContextSheet } from './components/ExamOfferingContextSheet';
import { ExamQuestionBankEditorSheet } from './components/ExamQuestionBankEditorSheet';

interface AssignmentState {
  bankId: string;
  offerings: AdminExamOfferingRef[];
}

interface SplitState {
  bankId: string;
  offerings: AdminExamOfferingRef[];
}

export default function AdminExamsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const offeringContextId = searchParams.get('offering');

  const [groups, setGroups] = useState<AdminExamSubjectGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [editorBankId, setEditorBankId] = useState<string | null>(null);
  const [assignmentState, setAssignmentState] = useState<AssignmentState | null>(null);
  const [splitState, setSplitState] = useState<SplitState | null>(null);
  const [creatingGroupKey, setCreatingGroupKey] = useState<string | null>(null);

  async function loadGroups() {
    setLoading(true);
    try {
      setGroups(await ExamBanksAPI.listGroups());
    } catch {
      toast.error('Не удалось загрузить экзаменационные банки');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadGroups();
  }, []);

  const totalBanks = useMemo(() => groups.reduce((total, group) => total + group.banks.length, 0), [groups]);
  const totalAttachedGroups = useMemo(
    () => groups.reduce((total, group) => total + group.banks.reduce((sum, bank) => sum + bank.offerings.length, 0), 0),
    [groups],
  );
  const totalUnassignedGroups = useMemo(
    () => groups.reduce((total, group) => total + group.unassigned_offerings.length, 0),
    [groups],
  );

  async function handleCreateBank(offeringIds: string[], groupKey: string) {
    setCreatingGroupKey(groupKey);
    try {
      const response = await ExamBanksAPI.createBank(offeringIds);
      toast.success('Создан новый общий банк');
      await loadGroups();
      setEditorBankId(response.bank_id);
    } catch {
      toast.error('Не удалось создать банк вопросов');
    } finally {
      setCreatingGroupKey(null);
    }
  }

  function closeOfferingContext() {
    router.replace('/admin/exams');
  }

  return (
    <div className="space-y-6">
      <BlurFade delay={0.1}>
        <div>
          <h1 className="flex items-center gap-3 text-3xl font-bold tracking-tight">
            <BookOpenCheck className="h-8 w-8 text-primary" />
            Экзамены
          </h1>
          <p className="mt-1 text-muted-foreground">
            Здесь управляются общие банки вопросов. Один банк можно привязать к нескольким группам одного предмета и семестра.
          </p>
        </div>
      </BlurFade>

      <BlurFade delay={0.15}>
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="border-border/60 bg-background/80 shadow-none">
            <CardHeader className="pb-3">
              <CardDescription>Банков вопросов</CardDescription>
              <CardTitle className="text-3xl">{totalBanks}</CardTitle>
            </CardHeader>
          </Card>
          <Card className="border-border/60 bg-background/80 shadow-none">
            <CardHeader className="pb-3">
              <CardDescription>Привязанных групп</CardDescription>
              <CardTitle className="text-3xl">{totalAttachedGroups}</CardTitle>
            </CardHeader>
          </Card>
          <Card className="border-border/60 bg-background/80 shadow-none">
            <CardHeader className="pb-3">
              <CardDescription>Групп без банка</CardDescription>
              <CardTitle className="text-3xl">{totalUnassignedGroups}</CardTitle>
            </CardHeader>
          </Card>
        </div>
      </BlurFade>

      <BlurFade delay={0.2}>
        {loading ? (
          <div className="rounded-xl border border-border/60 bg-background/80 p-10 text-center text-sm text-muted-foreground">
            Загружаю экзамены…
          </div>
        ) : !groups.length ? (
          <Card className="border-dashed border-border/60 bg-background/80 shadow-none">
            <CardHeader>
              <CardTitle>Экзаменов пока нет</CardTitle>
              <CardDescription>
                Как только хотя бы у одной связки появится форма контроля «Экзамен», здесь появится управление общими банками вопросов.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <div className="space-y-4">
            {groups.map((group) => {
              const groupKey = `${group.subject_id}:${group.semester}`;
              return (
                <Card key={groupKey} className="border-border/60 bg-background/80 shadow-none">
                  <CardHeader className="gap-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge className="bg-emerald-600 text-white hover:bg-emerald-600">Экзамен</Badge>
                      <Badge variant="outline">{group.semester}</Badge>
                      <Badge variant="outline">Банков: {group.banks.length}</Badge>
                    </div>
                    <div className="space-y-1">
                      <CardTitle className="text-xl">{group.subject_name}</CardTitle>
                      <CardDescription>
                        Сначала создаётся общий банк, затем при необходимости он делится на отдельные группы.
                      </CardDescription>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {group.banks.map((bank) => (
                      <div key={bank.bank_id} className="rounded-2xl border border-border/50 bg-muted/20 p-4">
                        <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
                          <div className="space-y-2">
                            <div className="flex flex-wrap gap-2">
                              <Badge variant="outline">Вопросов: {bank.questions_count}</Badge>
                              <Badge variant="outline">Групп: {bank.offerings.length}</Badge>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {bank.offerings.map((offering) => (
                                <Badge key={offering.offering_id} variant="secondary">
                                  {offering.group_name}
                                </Badge>
                              ))}
                            </div>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            <Button type="button" variant="outline" onClick={() => setEditorBankId(bank.bank_id)}>
                              <FolderGit2 className="mr-2 h-4 w-4" />
                              Редактировать банк
                            </Button>
                            {group.unassigned_offerings.length ? (
                              <Button
                                type="button"
                                variant="outline"
                                onClick={() => setAssignmentState({ bankId: bank.bank_id, offerings: group.unassigned_offerings })}
                              >
                                <Link2 className="mr-2 h-4 w-4" />
                                Добавить группы
                              </Button>
                            ) : null}
                            {bank.offerings.length > 1 ? (
                              <Button
                                type="button"
                                variant="outline"
                                onClick={() => setSplitState({ bankId: bank.bank_id, offerings: bank.offerings })}
                              >
                                <SplitSquareVertical className="mr-2 h-4 w-4" />
                                Разделить
                              </Button>
                            ) : null}
                          </div>
                        </div>
                      </div>
                    ))}

                    {group.unassigned_offerings.length ? (
                      <div className="rounded-2xl border border-dashed border-border/60 p-4">
                        <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
                          <div className="space-y-2">
                            <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                              <GraduationCap className="h-4 w-4" />
                              Группы без банка
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {group.unassigned_offerings.map((offering) => (
                                <Badge key={offering.offering_id} variant="outline">
                                  {offering.group_name}
                                </Badge>
                              ))}
                            </div>
                          </div>
                          <Button
                            type="button"
                            onClick={() => handleCreateBank(group.unassigned_offerings.map((offering) => offering.offering_id), groupKey)}
                            disabled={creatingGroupKey === groupKey}
                          >
                            Создать общий банк
                          </Button>
                        </div>
                      </div>
                    ) : null}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </BlurFade>

      <ExamQuestionBankEditorSheet
        open={Boolean(editorBankId)}
        bankId={editorBankId}
        onOpenChange={(open) => !open && setEditorBankId(null)}
        onSaved={() => {
          void loadGroups();
        }}
      />

      <ExamBankAssignmentDialog
        open={Boolean(assignmentState)}
        bankId={assignmentState?.bankId ?? null}
        offerings={assignmentState?.offerings ?? []}
        onOpenChange={(open) => !open && setAssignmentState(null)}
        onAssigned={() => {
          void loadGroups();
        }}
      />

      <ExamBankSplitDialog
        open={Boolean(splitState)}
        bankId={splitState?.bankId ?? null}
        offerings={splitState?.offerings ?? []}
        onOpenChange={(open) => !open && setSplitState(null)}
        onSplit={(nextBankId) => {
          void loadGroups();
          setEditorBankId(nextBankId);
        }}
      />

      <ExamOfferingContextSheet
        open={Boolean(offeringContextId)}
        offeringId={offeringContextId}
        onOpenChange={(open) => !open && closeOfferingContext()}
        onChanged={() => {
          void loadGroups();
        }}
        onBankOpened={(bankId) => {
          setEditorBankId(bankId);
          closeOfferingContext();
        }}
      />
    </div>
  );
}
