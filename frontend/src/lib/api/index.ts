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
export { JournalAPI } from './journal';
export { ReportsAPI, PublicReportAPI } from './reports';
export { AdminAPI } from './admin';
export { AdminAnnouncementsAPI } from './admin-announcements';
export type {
  AdminAnnouncement,
  AnnouncementDeliveryStats,
  AnnouncementSendStatus,
} from './admin-announcements';
export { TransfersAPI } from './transfers';
export { AuditAPI } from './audit';
export type { AuditLog, AuditLogListResponse, AuditStats, AuditFilters } from './audit';
export { RateLimitAPI } from './rate-limit';
export type { RateLimitWarning, WarningListResponse } from './rate-limit';
export { SecurityAPI } from './security';
export type { SecurityStrikesResponse, SecurityStatsResponse, StrikeDetail, ClearStrikesResponse, UserInfoResponse } from './security';
export { DevicesAPI } from './devices';
export type { Device, DeviceListResponse } from './devices';
export { SubjectsAPI } from './subjects';
export { BackupAPI } from './backup';
export type {
  BackupInfo,
  BackupListResponse,
  BackupCreateResponse,
  UploadBackupResponse,
  BackupSettings,
  BackupSettingsUpdate,
  RestoreResponse,
  VerifyResponse,
  BackupVerificationStatus,
  BackupHealthResponse,
} from './backup';
