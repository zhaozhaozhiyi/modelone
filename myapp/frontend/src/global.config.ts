import { TThemeType } from "./theme"
import { brand } from './brand'

// UI 规范 3.0：控制台导轨与登录页使用浅色横版主标；反白标仅保留给深色检视窗/营销物料
const appLogo = brand.logoUrl ? { default: brand.logoUrl } : { default: require('./images/modelone-logo.svg') }
const loadingLogo = brand.faviconUrl ? { default: brand.faviconUrl } : require('./images/modelone-mark.svg')

interface IGlobalConfig {
    appLogo: any,
    loadingLogo: any,
    theme: TThemeType,
    brand: typeof brand,
}

const globalConfig: IGlobalConfig = {
    appLogo,
    loadingLogo,
    theme: 'modelone',
    brand,
}

export default globalConfig
