import { brand } from './brand';

interface IThemeConfig {
    [key: string]: string
}

const DEFAULT_PRIMARY = '#17191D';
const DEFAULT_THEME = {
    hover: '#262A31',
    active: '#0E1013',
    soft: '#E9EAEC',
};

interface ParsedColor {
    rgb: [number, number, number];
    alpha: number;
}

const parseHex = (value: string): ParsedColor | null => {
    const match = value.trim().match(/^#([0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})$/i);
    if (!match) return null;
    let hex = match[1];
    if (hex.length === 3 || hex.length === 4) {
        hex = hex.split('').map((channel) => channel + channel).join('');
    }
    const alpha = hex.length === 8 ? parseInt(hex.slice(6, 8), 16) / 255 : 1;
    return {
        rgb: [
            parseInt(hex.slice(0, 2), 16),
            parseInt(hex.slice(2, 4), 16),
            parseInt(hex.slice(4, 6), 16),
        ],
        alpha,
    };
};

const cssColor = ({ rgb, alpha }: ParsedColor): string => {
    const channels = rgb.map((channel) => channel.toString(16).padStart(2, '0')).join('').toUpperCase();
    if (alpha >= 1) return `#${channels}`;
    return `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${Number(alpha.toFixed(3))})`;
};

const mix = (value: ParsedColor, target: [number, number, number], amount: number): string => {
    const rgb = value.rgb.map((channel, index) => Math.round(channel + (target[index] - channel) * amount)) as [number, number, number];
    return cssColor({ rgb, alpha: value.alpha });
};

const parsedPrimary = parseHex(brand.primaryColor || '') || parseHex(DEFAULT_PRIMARY)!;
const primary = cssColor(parsedPrimary);
const primaryHover = primary === DEFAULT_PRIMARY ? DEFAULT_THEME.hover : mix(parsedPrimary, [255, 255, 255], 0.12);
const primaryActive = primary === DEFAULT_PRIMARY ? DEFAULT_THEME.active : mix(parsedPrimary, [0, 0, 0], 0.2);
const primarySoft = primary === DEFAULT_PRIMARY ? DEFAULT_THEME.soft : mix(parsedPrimary, [255, 255, 255], 0.9);
const primaryOutline = parsedPrimary
    ? `rgba(${parsedPrimary.rgb[0]}, ${parsedPrimary.rgb[1]}, ${parsedPrimary.rgb[2]}, 0.18)`
    : 'rgba(23, 25, 29, 0.18)';

const modelone: IThemeConfig = {
    '--ant-primary-color': primary,
    '--ant-primary-color-hover': primaryHover,
    '--ant-primary-color-active': primaryActive,
    '--ant-primary-color-outline': primaryOutline,
    '--ant-primary-1': '#F5F6F7',
    '--ant-primary-2': '#E9EAEC',
    '--ant-primary-3': '#E5E6EB',
    '--ant-primary-4': '#C9CDD4',
    '--ant-primary-5': primary,
    '--ant-primary-6': primaryHover,
    '--ant-primary-7': primaryActive,
    '--ant-primary-color-deprecated-pure': '',
    '--ant-primary-color-deprecated-l-35': primarySoft,
    '--ant-primary-color-deprecated-l-20': primarySoft,
    '--ant-primary-color-deprecated-t-20': primarySoft,
    '--ant-primary-color-deprecated-t-50': '#C9CDD4',
    '--ant-primary-color-deprecated-f-12': `rgba(${parsedPrimary.rgb[0]}, ${parsedPrimary.rgb[1]}, ${parsedPrimary.rgb[2]}, 0.12)`,
    '--ant-primary-color-active-deprecated-f-30': 'rgba(233, 234, 236, 0.3)',
    '--ant-primary-color-active-deprecated-d-02': '#E9EAEC',
    '--ant-success-color': '#16825D',
    '--ant-success-color-hover': '#126D4D',
    '--ant-success-color-active': '#0E593E',
    '--ant-success-color-outline': 'rgba(22, 130, 93, 0.2)',
    '--ant-success-color-deprecated-bg': '#E7F5EF',
    '--ant-success-color-deprecated-border': '#A6D7C3',
    '--ant-error-color': '#C7353C',
    '--ant-error-color-hover': '#AA2B32',
    '--ant-error-color-active': '#8C2329',
    '--ant-error-color-outline': 'rgba(199, 53, 60, 0.2)',
    '--ant-error-color-deprecated-bg': '#FDEBEC',
    '--ant-error-color-deprecated-border': '#F1B5B8',
    '--ant-warning-color': '#A65F00',
    '--ant-warning-color-hover': '#8C5000',
    '--ant-warning-color-active': '#713F00',
    '--ant-warning-color-outline': 'rgba(166, 95, 0, 0.2)',
    '--ant-warning-color-deprecated-bg': '#FFF3DF',
    '--ant-warning-color-deprecated-border': '#EAC58B',
    '--ant-info-color': '#1769AA',
    '--ant-info-color-hover': '#125587',
    '--ant-info-color-active': '#0D4167',
    '--ant-info-color-outline': 'rgba(23, 105, 170, 0.2)',
    '--ant-info-color-deprecated-bg': '#E9F3FA',
    '--ant-info-color-deprecated-border': '#A9CBE3',
    '--ant-link': primary,
    '--mo-bg': '#F5F6F7',
    '--mo-surface': '#FFFFFF',
    '--mo-surface-muted': '#F0F2F4',
    '--mo-surface-hover': '#F8F9FA',
    '--mo-surface-selected': '#E9EAEC',
    '--mo-ink': '#17191D',
    '--mo-ink-hover': '#262A31',
    '--mo-text': '#17191D',
    '--mo-text-secondary': '#50545C',
    '--mo-text-tertiary': '#737985',
    '--mo-border': '#E5E6EB',
    '--mo-border-strong': '#C9CDD4',
    '--mo-brand-primary': primary,
    '--mo-brand-primary-hover': primaryHover,
    '--mo-brand-primary-active': primaryActive,
    '--mo-brand-primary-soft': primarySoft,
    '--mo-brand-secondary': brand.secondaryColor || '#3B82F6',
    '--mo-brand-text': primary,
    '--mo-brand-contrast': '#FFFFFF',
    '--mo-brand-signal': primary,
    '--mo-brand-signal-hover': primaryHover,
    '--mo-brand-signal-active': primaryActive,
    '--mo-brand-signal-soft': primarySoft,
    '--mo-radius-nav-item': '8px',
    '--mo-radius-pill': '999px',
    '--mo-sider': '208px',
    '--mo-sider-collapsed': '64px',
    '--mo-sider-inner': '200px',
    '--mo-nav-item-height': '40px',
    '--mo-shadow-nav': '0 1px 4px rgba(23, 25, 29, 0.08)',
    '--mo-shadow-pop': '0 8px 24px rgba(23, 25, 29, 0.16)',
    '--mo-font-sans': brand.fontFamily || 'Inter, "PingFang SC", "Microsoft YaHei", sans-serif',
    '--mo-success': '#16825D',
    '--mo-info': '#1769AA',
    '--mo-warning': '#A65F00',
    '--mo-danger': '#C7353C',
};

// Keep the historical theme keys available for configuration compatibility.
const themesCollection: Record<TThemeType, IThemeConfig> = {
    modelone,
    star: modelone,
    blue: modelone,
    dark: modelone,
};

export type TThemeType = 'dark' | 'blue' | 'star' | 'modelone'

export const setTheme = (theme: TThemeType) => {
    const nextTheme = themesCollection[theme] || modelone;

    Object.keys(nextTheme).forEach((key) => {
        document.documentElement.style.setProperty(key, nextTheme[key]);
    });
    document.documentElement.dataset.theme = 'modelone';
};
