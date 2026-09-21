/** Assets follow the same runtime configuration as the main console. */
export const brandAsset = (path: string): string => {
  const config = (window as Window & { MODELONE_BRAND?: { assetBaseUrl?: string } }).MODELONE_BRAND;
  const base = (config?.assetBaseUrl || '/static/assets/modelone').replace(/\/$/, '');
  return `${base}/${path.replace(/^\//, '')}`;
};
