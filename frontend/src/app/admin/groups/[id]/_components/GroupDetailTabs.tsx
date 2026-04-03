'use client';

import { AnimatePresence, motion } from 'motion/react';
import { BarChart3, Key, Users, Users2 } from 'lucide-react';
import { Command, CommandInput } from '@/components/ui/command';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { GroupDetailResponse } from '@/lib/api';
import { CodesTab } from './CodesTab';
import { StatsTab } from './StatsTab';
import { StudentsTab } from './StudentsTab';
import { SubgroupsTab } from './SubgroupsTab';

export type GroupDetailTab = 'students' | 'subgroups' | 'codes' | 'stats';

interface GroupDetailTabsProps {
  group: GroupDetailResponse;
  activeTab: GroupDetailTab;
  searchQuery: string;
  isGenerating: boolean;
  isRegeneratingGroupCode: boolean;
  onTabChange: (tab: GroupDetailTab) => void;
  onSearchQueryChange: (value: string) => void;
  onDeleteStudent: (id: string, name: string) => void;
  onDeleteStudentsBulk: (ids: string[]) => void;
  onAssignSubgroup: (subgroup: number | null) => void;
  onClearSubgroups: () => void;
  onGenerateCodes: () => Promise<void>;
  onRegenerateCode: (userId: string) => Promise<void>;
  onRegenerateGroupCode: () => Promise<void>;
}

export function GroupDetailTabs({
  group,
  activeTab,
  searchQuery,
  isGenerating,
  isRegeneratingGroupCode,
  onTabChange,
  onSearchQueryChange,
  onDeleteStudent,
  onDeleteStudentsBulk,
  onAssignSubgroup,
  onClearSubgroups,
  onGenerateCodes,
  onRegenerateCode,
  onRegenerateGroupCode,
}: GroupDetailTabsProps) {
  const showStudentSearch = activeTab === 'students' || activeTab === 'codes';

  return (
    <>
      <Tabs value={activeTab} onValueChange={(value) => onTabChange(value as GroupDetailTab)} className="mb-6">
        <TabsList className={`grid w-fit ${group.has_subgroups ? 'grid-cols-4' : 'grid-cols-3'}`}>
          <TabsTrigger value="students" className="flex items-center gap-2">
            <Users className="w-4 h-4" /> Студенты
          </TabsTrigger>
          {group.has_subgroups && (
            <TabsTrigger value="subgroups" className="flex items-center gap-2">
              <Users2 className="w-4 h-4" /> Подгруппы
            </TabsTrigger>
          )}
          <TabsTrigger value="codes" className="flex items-center gap-2">
            <Key className="w-4 h-4" /> Инвайт-коды
          </TabsTrigger>
          <TabsTrigger value="stats" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" /> Статистика
          </TabsTrigger>
        </TabsList>

        {showStudentSearch && (
          <div className="mt-6 mb-6">
            <Command className="border rounded-lg shadow-sm">
              <CommandInput
                placeholder="Поиск студентов по ФИО..."
                value={searchQuery}
                onValueChange={onSearchQueryChange}
              />
            </Command>
          </div>
        )}
      </Tabs>

      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
        >
          {activeTab === 'students' && (
            <StudentsTab
              students={group.students}
              searchQuery={searchQuery}
              onDeleteStudent={onDeleteStudent}
              onDeleteStudentsBulk={onDeleteStudentsBulk}
            />
          )}
          {activeTab === 'subgroups' && group.has_subgroups && (
            <SubgroupsTab
              students={group.students}
              onAssignSubgroup={onAssignSubgroup}
              onClearSubgroups={onClearSubgroups}
            />
          )}
          {activeTab === 'codes' && (
            <CodesTab
              students={group.students}
              searchQuery={searchQuery}
              groupInviteCode={group.invite_code}
              onGenerateCodes={onGenerateCodes}
              onRegenerateCode={onRegenerateCode}
              onRegenerateGroupCode={onRegenerateGroupCode}
              isGenerating={isGenerating}
              isRegeneratingGroupCode={isRegeneratingGroupCode}
            />
          )}
          {activeTab === 'stats' && <StatsTab />}
        </motion.div>
      </AnimatePresence>
    </>
  );
}
