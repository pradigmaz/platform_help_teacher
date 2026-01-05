'use client';

/**
 * Страница рендера лекции для PDF экспорта.
 * Используется Playwright для генерации PDF.
 * Requirements: 6.4, 6.6
 */

import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import { LectureViewer } from '@/components/lectures/LectureViewer';
import { LecturesAPI, type LectureResponse } from '@/lib/lectures-api';

export default function LectureRenderPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const lectureId = params.id as string;
  const isPdfMode = searchParams.get('mode') === 'pdf';
  
  const [lecture, setLecture] = useState<LectureResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!lectureId) return;

    const fetchLecture = async () => {
      try {
        const data = await LecturesAPI.get(lectureId);
        setLecture(data);
      } catch (err) {
        console.error('Failed to fetch lecture:', err);
        setError('Не удалось загрузить лекцию');
      } finally {
        setLoading(false);
      }
    };

    fetchLecture();
  }, [lectureId]);

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Загрузка...</p>
      </div>
    );
  }

  // Error state
  if (error || !lecture) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-red-500">{error || 'Лекция не найдена'}</p>
      </div>
    );
  }

  // PDF render mode - optimized for print
  return (
    <div 
      className={`lecture-content bg-white text-black ${isPdfMode ? 'pdf-mode' : ''}`}
      style={{
        padding: isPdfMode ? '0' : '2rem',
        maxWidth: isPdfMode ? 'none' : '900px',
        margin: '0 auto',
      }}
    >
      {/* PDF-specific styles */}
      {isPdfMode && (
        <style jsx global>{`
          @media print {
            body {
              -webkit-print-color-adjust: exact !important;
              print-color-adjust: exact !important;
            }
          }
          
          .pdf-mode {
            font-size: 14px;
            line-height: 1.6;
          }
          
          .pdf-mode h1 {
            font-size: 24px;
            margin-bottom: 1.5rem;
            page-break-after: avoid;
          }
          
          .pdf-mode h2, .pdf-mode h3 {
            page-break-after: avoid;
          }
          
          .pdf-mode pre, .pdf-mode code {
            page-break-inside: avoid;
          }
          
          .pdf-mode img {
            max-width: 100%;
            page-break-inside: avoid;
          }
          
          .pdf-mode .visualization-container {
            page-break-inside: avoid;
          }
          
          /* Mark as ready for Playwright */
          .visualization-ready {
            opacity: 1;
          }
        `}</style>
      )}

      {/* Title */}
      <h1 
        className="text-2xl font-bold mb-6"
        style={{ 
          borderBottom: isPdfMode ? '2px solid #333' : 'none',
          paddingBottom: isPdfMode ? '0.5rem' : '0',
        }}
      >
        {lecture.title}
      </h1>

      {/* Lecture content */}
      <div className="visualization-ready">
        <LectureViewer
          content={lecture.content}
          className="prose prose-neutral max-w-none"
        />
      </div>

      {/* Footer for PDF */}
      {isPdfMode && (
        <footer 
          className="mt-8 pt-4 text-sm text-gray-500"
          style={{ borderTop: '1px solid #ddd' }}
        >
          <p>Сгенерировано: {new Date().toLocaleDateString('ru-RU')}</p>
        </footer>
      )}
    </div>
  );
}
