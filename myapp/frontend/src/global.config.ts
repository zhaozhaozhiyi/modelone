import { TThemeType } from "./theme"
import { brand } from './brand'

const appLogo = brand.logoReverseUrl ? { default: brand.logoReverseUrl } : require('./images/modelone-logo-reverse.svg')
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
