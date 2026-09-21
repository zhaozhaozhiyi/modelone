export interface BrandConfig {
  name: string;
  internalName: string;
  title: string;
  description: string;
  assetBaseUrl: string;
  logoUrl?: string;
  logoReverseUrl?: string;
  faviconUrl?: string;
  copyright?: string;
  helpUrl?: string;
  supportUrl?: string;
  termsUrl?: string;
  privacyUrl?: string;
  primaryColor?: string;
  secondaryColor?: string;
  loginBackgroundColor?: string;
  loginSurfaceColor?: string;
  fontFamily?: string;
}

const env = (key: string, fallback: string): string => {
  const value = (process.env as Record<string, string | undefined>)[key];
  return value === undefined ? fallback : value;
};

export const brand: BrandConfig = {
  name: env('REACT_APP_BRAND_NAME', 'modelOne'),
  internalName: env('REACT_APP_BRAND_INTERNAL_NAME', 'modelone'),
  title: env('REACT_APP_BRAND_TITLE', 'modelOne｜企业级 AI 开发与模型生产平台'),
  description: env('REACT_APP_BRAND_DESCRIPTION', '企业级 AI 开发与模型生产平台'),
  assetBaseUrl: env('REACT_APP_ASSET_BASE_URL', ''),
  ...((window as Window & { MODELONE_BRAND?: Partial<BrandConfig> }).MODELONE_BRAND || {}),
};

export const brandAsset = (path: string): string => {
  const base = brand.assetBaseUrl.replace(/\/$/, '');
  return base ? `${base}/${path.replace(/^\//, '')}` : `/static/assets/modelone/${path.replace(/^\//, '')}`;
};
