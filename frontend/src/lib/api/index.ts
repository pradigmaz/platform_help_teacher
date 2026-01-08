// Client & utilities
export { api, publicApi, ApiError, ensureCsrfToken, resetCsrfToken } from './client';
export { default } from './client';

// Types
export * from './types';

// API modules
export { AuthAPI } from './auth';
export { GroupsAPI } from './groups';
export { LabsAPI } from './labs';
export { LabQueueAPI } from './lab-queue';
export { AttestationAPI } from './attestation';
export { WorksAPI, WorkSubmissionsAPI } from './works';
export { ActivitiesAPI } from './activities';
export { StudentAPI } from './student';
export { ScheduleAPI } from './schedule';
export { ReportsAPI, PublicReportAPI } from './reports';
export { AdminAPI } from './admin';
export { TransfersAPI } from './transfers';
export { AuditAPI } from './audit';
export type { AuditLog, AuditLogListResponse, AuditStats, AuditFilters } from './audit';
export { BackupAPI } from './backup';
export type { 
  BackupInfo, 
  BackupListResponse, 
  BackupCreateResponse, 
  BackupSettings, 
  BackupSettingsUpdate,
  RestoreResponse,
  VerifyResponse,
} from './backup';
