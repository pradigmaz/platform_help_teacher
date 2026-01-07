'use client';

import { motion } from 'motion/react';
import { LectureViewer } from '@/components/lectures/LectureViewer';
import { LecturePublicHeader } from './LecturePublicHeader';
import { LecturePublicTOC } from './LecturePublicTOC';
import type { LectureResponse } from '@/lib/lectures-api';
import type { ReaderSettings, TOCItem } from './types';

interface LectureContentProps {
  lecture: LectureResponse;
  settings: ReaderSettings;
  onUpdateSettings: (settings: Partial<ReaderSettings>) => void;
  progress: number;
  tocItems: TOCItem[];
  activeHeadingId: string;
  onHeadingClick: (id: string) => void;
  fontClass: string;
}

/**
 * Main lecture content layout with header, TOC sidebar, and content
 */
export function LectureContent({
  lecture,
  settings,
  onUpdateSettings,
  progress,
  tocItems,
  activeHeadingId,
  onHeadingClick,
  fontClass,
}: LectureContentProps) {
  return (
    <div className="min-h-screen bg-background text-foreground transition-colors duration-300">
      <LecturePublicHeader
        title={lecture.title}
        progress={progress}
        settings={settings}
        onUpdateSettings={onUpdateSettings}
      />

      <div className="pt-20 pb-16 px-4 max-w-7xl mx-auto flex">
        {/* TOC Sidebar - Desktop */}
        <aside className="hidden lg:block w-64 flex-shrink-0 mr-8">
          <div className="sticky top-20">
            <LecturePublicTOC
              items={tocItems}
              activeId={activeHeadingId}
              onItemClick={onHeadingClick}
            />
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 min-w-0 max-w-4xl">
          <motion.article
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className={fontClass}
            style={{ fontSize: `${settings.fontSize}px` }}
          >
            <header className="mb-10 pb-8 border-b border-border">
              <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
                {lecture.title}
              </h1>
            </header>

            <div className="lecture-content" style={{ lineHeight: '1.7' }}>
              <LectureViewer
                content={lecture.content}
                className="max-w-none"
              />
            </div>
          </motion.article>
        </main>
      </div>
    </div>
  );
}
