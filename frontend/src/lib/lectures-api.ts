import api from './api';
import type { SerializedEditorState } from 'lexical';

// --- Lecture Types ---

export interface SubjectBrief {
  id: string;
  name: string;
  code: string | null;
}

export interface LectureCreate {
  title: string;
  content: SerializedEditorState;
  subject_id?: string | null;
}

export interface LectureUpdate {
  title?: string;
  content?: SerializedEditorState;
  subject_id?: string | null;
}

export interface LectureResponse {
  id: string;
  title: string;
  content: SerializedEditorState;
  is_published: boolean;
  public_code: string | null;
  subject_id: string | null;
  subject: SubjectBrief | null;
  created_at: string;
  updated_at: string;
  images: LectureImageResponse[];
}

export interface LectureListResponse {
  id: string;
  title: string;
  is_published: boolean;
  public_code: string | null;
  subject_id: string | null;
  subject: SubjectBrief | null;
  created_at: string;
  updated_at: string;
}

export interface LectureImageResponse {
  id: string;
  lecture_id: string;
  filename: string;
  storage_path: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
}

export interface PublicLinkResponse {
  public_code: string;
  url: string;
}

// --- Lectures API ---

export const LecturesAPI = {
  // List all lectures
  list: async (subjectId?: string) => {
    const params = subjectId ? { subject_id: subjectId } : {};
    const { data } = await api.get<LectureListResponse[]>('/admin/lectures/', { params });
    return data;
  },

  // Get single lecture
  get: async (id: string) => {
    const { data } = await api.get<LectureResponse>(`/admin/lectures/${id}`);
    return data;
  },

  // Create new lecture
  create: async (payload: LectureCreate) => {
    const { data } = await api.post<LectureResponse>('/admin/lectures/', payload);
    return data;
  },

  // Update lecture
  update: async (id: string, payload: LectureUpdate) => {
    const { data } = await api.put<LectureResponse>(`/admin/lectures/${id}`, payload);
    return data;
  },

  // Delete lecture
  delete: async (id: string) => {
    await api.delete(`/admin/lectures/${id}`);
  },

  // Publish lecture (generate public link)
  publish: async (id: string) => {
    const { data } = await api.post<PublicLinkResponse>(`/admin/lectures/${id}/publish`);
    return data;
  },

  // Unpublish lecture
  unpublish: async (id: string) => {
    await api.post(`/admin/lectures/${id}/unpublish`);
  },

  // Upload image
  uploadImage: async (lectureId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post<LectureImageResponse>(
      `/admin/lectures/${lectureId}/images`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return data;
  },

  // Delete image
  deleteImage: async (lectureId: string, imageId: string) => {
    await api.delete(`/admin/lectures/${lectureId}/images/${imageId}`);
  },

  // Export lecture to PDF
  exportPdf: async (lectureId: string): Promise<Blob> => {
    const response = await api.get(`/admin/lectures/${lectureId}/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

// --- Public Lectures API (no auth required) ---

export const PublicLecturesAPI = {
  // Get lecture by public code
  getByCode: async (code: string) => {
    const { data } = await api.get<LectureResponse>(`/lectures/view/${code}`);
    return data;
  },
};

export default LecturesAPI;
