/**
 * Типы для device fingerprint.
 */

export type OrientationType = 'portrait-primary' | 'portrait-secondary' | 'landscape-primary' | 'landscape-secondary' | string;

export interface ScreenInfo {
  width: number;
  height: number;
  availWidth: number;
  availHeight: number;
  colorDepth: number;
  pixelDepth: number;
  pixelRatio: number;
  orientation?: OrientationType;
  orientationAngle?: number;
}

export interface WebGLInfo {
  vendor: string;
  renderer: string;
  version?: string;
  shadingLanguageVersion?: string;
  maxTextureSize?: number;
  maxViewportDims?: number[];
  maxRenderbufferSize?: number;
  maxVertexAttribs?: number;
  maxVertexUniformVectors?: number;
  maxFragmentUniformVectors?: number;
  maxVaryingVectors?: number;
  aliasedLineWidthRange?: number[];
  aliasedPointSizeRange?: number[];
  extensions?: string[];
}

export interface AudioContextInfo {
  sampleRate?: number;
  maxChannelCount?: number;
  state?: string;
}

export interface ConnectionInfo {
  type?: string;
  effectiveType?: string;
  downlink?: number;
  downlinkMax?: number;
  rtt?: number;
  saveData?: boolean;
}

export interface MediaDevicesInfo {
  cameras: number;
  microphones: number;
  speakers: number;
  deviceIds: string[];
}

export interface StorageInfo {
  quota?: number;
  usage?: number;
  persistent?: boolean;
}

export interface BatteryInfo {
  charging?: boolean;
  level?: number;
  chargingTime?: number;
  dischargingTime?: number;
}

export interface PermissionsInfo {
  notifications?: string;
  geolocation?: string;
  camera?: string;
  microphone?: string;
}

export interface DeviceFingerprint {
  // Screen
  screen: ScreenInfo;
  
  // GPU
  webgl?: WebGLInfo;
  webgl2Available: boolean;
  
  // Canvas
  canvas?: string;
  canvasGeometry?: string;
  
  // Audio
  audio?: string;
  audioContext?: AudioContextInfo;
  
  // System
  platform: string;
  oscpu?: string;
  hardwareConcurrency: number;
  deviceMemory?: number;
  
  // Browser
  userAgent: string;
  vendor: string;
  vendorSub: string;
  product: string;
  productSub: string;
  buildID?: string;
  appName: string;
  appVersion: string;
  appCodeName: string;
  
  // Locale
  language: string;
  languages: string[];
  timezone: string;
  timezoneOffset: number;
  
  // Network
  connection?: ConnectionInfo;
  onLine: boolean;
  
  // Input
  touchSupport: boolean;
  maxTouchPoints: number;
  pointerEnabled?: boolean;
  
  // Media
  mediaDevices?: MediaDevicesInfo;
  
  // Storage
  storage?: StorageInfo;
  cookieEnabled: boolean;
  localStorageAvailable: boolean;
  sessionStorageAvailable: boolean;
  indexedDBAvailable: boolean;
  
  // Permissions
  permissions?: PermissionsInfo;
  
  // Fonts
  fonts?: string[];
  
  // Plugins
  plugins: string[];
  mimeTypes: string[];
  
  // Flags
  pdfViewerEnabled: boolean;
  webdriver: boolean;
  doNotTrack: string | null;
  globalPrivacyControl?: boolean;
  
  // Battery
  battery?: BatteryInfo;
  
  // Media features
  colorGamut?: string;
  contrast?: string;
  reducedMotion?: boolean;
  reducedTransparency?: boolean;
  forcedColors?: boolean;
  hdr?: boolean;
  invertedColors?: boolean;
  
  // Math
  math?: string;
  
  // Timing
  performanceTiming?: {
    navigationStart?: number;
    loadEventEnd?: number;
  };
  dateFormat?: string;
}
