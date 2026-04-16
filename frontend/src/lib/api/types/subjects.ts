export type FinalControlType = 'exam' | 'credit' | 'differentiated_credit';

export interface GroupSubjectOffering {
  id: string;
  group_id: string;
  group_name: string;
  subject_id: string;
  subject_name: string;
  semester: string;
  final_control_type: FinalControlType | null;
}

export interface AutomaticQueueStudent {
  student_id: string;
  student_name: string;
  completed_count: number;
  automatic_remaining: number;
  completion_at: string | null;
  queue_position: number | null;
  is_winner: boolean;
  is_declined: boolean;
  declined_reason: string | null;
}

export interface AutomaticQueueResponse {
  offering_id: string;
  final_control_type: FinalControlType | null;
  automatic_enabled: boolean;
  automatic_places: number | null;
  total_labs: number;
  students: AutomaticQueueStudent[];
}
