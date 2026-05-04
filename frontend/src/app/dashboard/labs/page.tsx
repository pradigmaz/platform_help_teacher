'use client';

import { LabsEmptyState } from './components/LabsEmptyState';
import { LabsFilters } from './components/LabsFilters';
import { LabsGrid } from './components/LabsGrid';
import { LabsProgressCard } from './components/LabsProgressCard';
import { LabsSkeleton } from './components/LabsSkeleton';
import { LabsSubjectSelector } from './components/LabsSubjectSelector';
import { useStudentLabsPage } from './useStudentLabsPage';

export default function LabsPage() {
  const page = useStudentLabsPage();

  if (page.loading) return <LabsSkeleton />;

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-foreground">Лабораторные работы</h1>
        <p className="text-muted-foreground">Выберите предмет и сдавайте работы преподавателю в правильном контексте</p>
      </div>

      <LabsSubjectSelector
        subjects={page.subjects}
        selectedSubject={page.selectedSubject}
        selectedSubjectId={page.selectedSubjectId}
        onSelectSubject={page.selectSubject}
      />

      {!page.mustChooseSubject && (
        <>
          <LabsProgressCard acceptedCount={page.counts.accepted} totalCount={page.labs.length} progress={page.progress} />
          <LabsFilters counts={page.counts} filter={page.filter} onFilterChange={page.setFilter} />
        </>
      )}

      {page.filteredLabs.length > 0 && !page.mustChooseSubject ? (
        <LabsGrid
          labs={page.filteredLabs}
          hoveredIndex={page.hoveredIndex}
          actionLoading={page.actionLoading}
          onHover={page.setHoveredIndex}
          onMarkReady={page.handleMarkReady}
          onCancelReady={page.handleCancelReady}
        />
      ) : (
        <LabsEmptyState
          filter={page.filter}
          mustChooseSubject={page.mustChooseSubject}
          subjectScopeError={page.subjectScopeError}
        />
      )}
    </div>
  );
}
