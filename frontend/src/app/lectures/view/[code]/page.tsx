'use client';

import { useParams } from 'next/navigation';
import {
  useLectureReader,
  LectureLoadingState,
  LectureNotFoundState,
  LectureErrorState,
  LectureContent,
} from '@/components/lectures/public';

export default function PublicLecturePage() {
  const params = useParams();
  const code = params.code as string;
  
  const {
    lecture,
    loadingState,
    errorMessage,
    settings,
    updateSettings,
    progress,
    activeHeadingId,
    tocItems,
    scrollToHeading,
    getFontClass,
  } = useLectureReader(code);

  if (loadingState === 'loading') {
    return <LectureLoadingState />;
  }

  if (loadingState === 'not_found') {
    return <LectureNotFoundState />;
  }

  if (loadingState === 'error') {
    return <LectureErrorState message={errorMessage} />;
  }

  if (!lecture) return null;

  return (
    <LectureContent
      lecture={lecture}
      settings={settings}
      onUpdateSettings={updateSettings}
      progress={progress}
      tocItems={tocItems}
      activeHeadingId={activeHeadingId}
      onHeadingClick={scrollToHeading}
      fontClass={getFontClass()}
    />
  );
}
