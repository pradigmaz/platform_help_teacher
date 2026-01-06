export interface StudentImport {
  full_name: string;
  username?: string;
  email?: string;
}

export interface StudentInGroup {
  id: string;
  full_name: string;
  username?: string;
  invite_code?: string;
  subgroup?: number | null;
  is_active: boolean;
}

export interface GroupCreate {
  name: string;
  code: string;
  students: StudentImport[];
}

export interface GroupResponse {
  id: string;
  name: string;
  code: string;
  invite_code?: string;
  students_count: number;
  has_subgroups: boolean;
}

export interface GroupDetailResponse {
  id: string;
  name: string;
  code: string;
  invite_code?: string;
  created_at: string;
  students: StudentInGroup[];
  has_subgroups: boolean;
}
