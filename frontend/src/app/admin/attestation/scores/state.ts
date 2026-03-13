'use no memo';

import type {
  AttestationResult,
  AttestationSubjectOption,
  AttestationType,
  GroupAttestationResult,
  GroupResponse,
} from '@/lib/api';

export type ViewMode = 'by-group' | 'all-students';
export type SortKey = 'name' | 'group' | 'total' | 'labs' | 'attendance' | 'activity';
export type SortOrder = 'asc' | 'desc';

export interface State {
  viewMode: ViewMode;
  attestationType: AttestationType;
  selectedGroupId: string;
  selectedSubjectId: string;
  searchQuery: string;
  sortKey: SortKey;
  sortOrder: SortOrder;
  groups: GroupResponse[];
  availableSubjects: AttestationSubjectOption[];
  data: GroupAttestationResult | null;
  loading: boolean;
  groupsLoading: boolean;
  selectedStudent: AttestationResult | null;
  detailSheetOpen: boolean;
}

export type Action =
  | { type: 'SET_VIEW_MODE'; payload: ViewMode }
  | { type: 'SET_ATTESTATION_TYPE'; payload: AttestationType }
  | { type: 'SET_GROUP_ID'; payload: string }
  | { type: 'SET_SUBJECT_ID'; payload: string }
  | { type: 'SET_SEARCH'; payload: string }
  | { type: 'TOGGLE_SORT'; payload: SortKey }
  | { type: 'SET_GROUPS'; payload: GroupResponse[] }
  | { type: 'SET_AVAILABLE_SUBJECTS'; payload: AttestationSubjectOption[] }
  | { type: 'SET_DATA'; payload: GroupAttestationResult | null }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_GROUPS_LOADING'; payload: boolean }
  | { type: 'OPEN_DETAIL'; payload: AttestationResult }
  | { type: 'CLOSE_DETAIL' };

export const initialState: State = {
  viewMode: 'by-group',
  attestationType: 'first',
  selectedGroupId: '',
  selectedSubjectId: '',
  searchQuery: '',
  sortKey: 'name',
  sortOrder: 'asc',
  groups: [],
  availableSubjects: [],
  data: null,
  loading: false,
  groupsLoading: true,
  selectedStudent: null,
  detailSheetOpen: false,
};

export function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'SET_VIEW_MODE':
      return { ...state, viewMode: action.payload, searchQuery: '', selectedSubjectId: '', data: null };
    case 'SET_ATTESTATION_TYPE':
      return { ...state, attestationType: action.payload, selectedSubjectId: '', data: null };
    case 'SET_GROUP_ID':
      return { ...state, selectedGroupId: action.payload, selectedSubjectId: '', data: null };
    case 'SET_SUBJECT_ID':
      return { ...state, selectedSubjectId: action.payload, data: null };
    case 'SET_SEARCH':
      return { ...state, searchQuery: action.payload };
    case 'TOGGLE_SORT':
      return state.sortKey === action.payload
        ? { ...state, sortOrder: state.sortOrder === 'asc' ? 'desc' : 'asc' }
        : { ...state, sortKey: action.payload, sortOrder: 'asc' };
    case 'SET_GROUPS':
      return {
        ...state,
        groups: action.payload,
        selectedGroupId: action.payload[0]?.id || '',
        groupsLoading: false,
      };
    case 'SET_AVAILABLE_SUBJECTS':
      return { ...state, availableSubjects: action.payload };
    case 'SET_DATA':
      return { ...state, data: action.payload, loading: false };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_GROUPS_LOADING':
      return { ...state, groupsLoading: action.payload };
    case 'OPEN_DETAIL':
      return { ...state, selectedStudent: action.payload, detailSheetOpen: true };
    case 'CLOSE_DETAIL':
      return { ...state, detailSheetOpen: false };
    default:
      return state;
  }
}
