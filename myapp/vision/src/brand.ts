export interface EditorBrandConfig {
  assetBaseUrl?: string;
  primaryColor?: string;
  secondaryColor?: string;
  fontFamily?: string;
}

const config = (window as Window & { MODELONE_BRAND?: EditorBrandConfig }).MODELONE_BRAND || {};
const DEFAULT_FONT = 'Inter, "PingFang SC", "Microsoft YaHei", sans-serif';
const FALLBACK_PRIMARY: [number, number, number] = [23, 25, 29];

const parseHex = (value: string): [number, number, number] | null => {
  const match = value.trim().match(/^#([0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})$/i);
  if (!match) return null;
  const hex = match[1].length === 3 || match[1].length === 4
    ? match[1].split('').map((channel) => channel + channel).join('')
    : match[1];
  return [parseInt(hex.slice(0, 2), 16), parseInt(hex.slice(2, 4), 16), parseInt(hex.slice(4, 6), 16)];
};

const cssColor = (rgb: [number, number, number]): string => `#${rgb.map((channel) => channel.toString(16).padStart(2, '0')).join('').toUpperCase()}`;
const mix = (rgb: [number, number, number], target: [number, number, number], amount: number): string => cssColor(rgb.map((channel, index) => Math.round(channel + (target[index] - channel) * amount)) as [number, number, number]);
const primaryRgb = parseHex(config.primaryColor || '') || FALLBACK_PRIMARY;
const secondaryRgb = parseHex(config.secondaryColor || '') || [59, 130, 246] as [number, number, number];

export const brandFontFamily = config.fontFamily || DEFAULT_FONT;
export const brandSecondary = cssColor(secondaryRgb);
export const brandPalette = {
  themePrimary: cssColor(primaryRgb),
  themeLighterAlt: mix(primaryRgb, [255, 255, 255], 0.96),
  themeLighter: mix(primaryRgb, [255, 255, 255], 0.8),
  themeLight: mix(primaryRgb, [255, 255, 255], 0.6),
  themeTertiary: mix(primaryRgb, [255, 255, 255], 0.4),
  themeSecondary: mix(primaryRgb, [255, 255, 255], 0.2),
  themeDarkAlt: mix(primaryRgb, [0, 0, 0], 0.1),
  themeDark: mix(primaryRgb, [0, 0, 0], 0.2),
  themeDarker: mix(primaryRgb, [0, 0, 0], 0.35),
};

/** Assets follow the same runtime configuration as the main console. */
export const brandAsset = (path: string): string => {
  const base = (config.assetBaseUrl || '/static/assets/modelone').replace(/\/$/, '');
  return `${base}/${path.replace(/^\//, '')}`;
};
