'use client';

import type { LectureListResponse, LectureResponse } from '@/lib/lectures-api';

export interface AdminLectureSubject {
  id: string;
  name: string;
  code: string | null;
  is_active: boolean;
}

export interface AdminLecturesListData {
  lectures: LectureListResponse[];
  subjects: AdminLectureSubject[];
}

let lecturesListCache: AdminLecturesListData | null = null;
let lecturesListPromise: Promise<AdminLecturesListData> | null = null;

const lectureDetailCache = new Map<string, LectureResponse>();
const lectureDetailPromises = new Map<string, Promise<LectureResponse>>();

function toLectureListItem(lecture: LectureResponse): LectureListResponse {
  return {
    id: lecture.id,
    title: lecture.title,
    is_published: lecture.is_published,
    public_code: lecture.public_code,
    subject_id: lecture.subject_id,
    subject: lecture.subject,
    created_at: lecture.created_at,
    updated_at: lecture.updated_at,
  };
}

export async function loadAdminLecturesList(
  loader: () => Promise<AdminLecturesListData>,
  force = false,
) {
  if (!force) {
    if (lecturesListCache) {
      return lecturesListCache;
    }

    if (lecturesListPromise) {
      return lecturesListPromise;
    }
  }

  const request = loader()
    .then((data) => {
      lecturesListCache = data;
      lecturesListPromise = null;
      return data;
    })
    .catch((error) => {
      lecturesListPromise = null;
      throw error;
    });

  lecturesListPromise = request;

  return request;
}

export function primeAdminLecturesList(data: AdminLecturesListData) {
  lecturesListCache = data;
}

export function clearAdminLecturesList() {
  lecturesListCache = null;
  lecturesListPromise = null;
}

export function upsertAdminLectureListItem(lecture: LectureResponse) {
  if (!lecturesListCache) {
    return;
  }

  const nextItem = toLectureListItem(lecture);
  const nextLectures = lecturesListCache.lectures.filter((item) => item.id !== lecture.id);
  nextLectures.unshift(nextItem);
  lecturesListCache = { ...lecturesListCache, lectures: nextLectures };
}

export function removeAdminLectureListItem(id: string) {
  if (!lecturesListCache) {
    return;
  }

  lecturesListCache = {
    ...lecturesListCache,
    lectures: lecturesListCache.lectures.filter((lecture) => lecture.id !== id),
  };
}

export async function loadAdminLectureDetail(
  id: string,
  loader: () => Promise<LectureResponse>,
  force = false,
) {
  if (!force) {
    const cached = lectureDetailCache.get(id);
    if (cached) {
      return cached;
    }

    const pending = lectureDetailPromises.get(id);
    if (pending) {
      return pending;
    }
  }

  const request = loader()
    .then((lecture) => {
      lectureDetailCache.set(id, lecture);
      lectureDetailPromises.delete(id);
      upsertAdminLectureListItem(lecture);
      return lecture;
    })
    .catch((error) => {
      lectureDetailPromises.delete(id);
      throw error;
    });

  lectureDetailPromises.set(id, request);

  return request;
}

export function primeAdminLectureDetail(lecture: LectureResponse) {
  lectureDetailCache.set(lecture.id, lecture);
  upsertAdminLectureListItem(lecture);
}

export function peekAdminLectureDetail(id: string) {
  return lectureDetailCache.get(id) ?? null;
}

export function clearAdminLectureDetail(id?: string) {
  if (id) {
    lectureDetailCache.delete(id);
    lectureDetailPromises.delete(id);
    return;
  }

  lectureDetailCache.clear();
  lectureDetailPromises.clear();
}
