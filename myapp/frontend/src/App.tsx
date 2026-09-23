import React, { useEffect, useState } from 'react';
import {
  BrowserRouter as Routers,
  useRoutes,
  useNavigate,
  useLocation,
  RouteObject
} from "react-router-dom";

import { Dropdown, Menu, Spin, Tag } from 'antd';
import { IRouterConfigPlusItem } from './api/interface/baseInterface';
import { formatRoute, getDefaultOpenKeys, routerConfigPlus } from './routerConfig';
import SubMenu from 'antd/lib/menu/SubMenu';
import { clearWaterNow, drawWater, drawWaterNow, getParam, obj2UrlParam, parseParam2Obj } from './util'
import { getAppHeaderConfig, getAppMenu, getCustomDialog, userLogout } from './api/kubeflowApi';
import { IAppHeaderItem, IAppMenuItem, ICustomDialog } from './api/interface/kubeflowInterface';
import { LeftOutlined, MenuOutlined, RightOutlined } from '@ant-design/icons';
import { User } from 'lucide-react';
import { MenuGlyph, renderMenuIcon } from './menuIcon';
import Cookies from 'js-cookie'
import { handleTips } from './api';
import globalConfig from './global.config'
import AiChatBot from './components/AiChatBot/AiChatBot'
import { ProjectSwitcher } from './projectSwitcher'
import { PageExtraContext } from './pageExtra'
const userName = Cookies.get('myapp_username')

// 左侧一级菜单常驻项。安全设置、链接等仍留在所属模块的内栏，不在导轨再做「更多」分组。
const RESIDENT_NAV_NAMES = ['group', 'data', 'dev', 'train', 'service'];

const RouterConfig = (config: RouteObject[]) => {
  let element = useRoutes(config);
  return element;
}

const getRouterMap = (routerList: IRouterConfigPlusItem[]): Record<string, IRouterConfigPlusItem> => {
  const res: Record<string, IRouterConfigPlusItem> = {}
  const queue = [...routerList]
  while (queue.length) {
    const item = queue.shift()
    if (item) {
      res[item?.path || ''] = item
      if (item?.children && item.children.length) {
        queue.push(...item.children)
      }
    }
  }
  return res
}

const getValidAppList = (config: IRouterConfigPlusItem[]) => config.filter(item => !!item.name && !item.hidden)

interface IProps { }

const AppWrapper = (props: IProps) => {
  const [openKeys, setOpenKeys] = useState<string[]>([])
  const [currentNavList, setCurrentNavList] = useState<IRouterConfigPlusItem[]>([])
  const [sourceAppList, setSourceAppList] = useState<IRouterConfigPlusItem[]>([])
  const [sourceAppMap, setSourceAppMap] = useState<Record<string, IRouterConfigPlusItem>>({})
  const [CurrentRouteComponent, setCurrentRouteComponent] = useState<any>()
  const [isMenuCollapsed, setIsMenuCollapsed] = useState(false)
  const [isShowSlideMenu, setIsShowSlideMenu] = useState(true)
  const [customDialogInfo, setCustomDialogInfo] = useState<ICustomDialog>()
  const [headerConfig, setHeaderConfig] = useState<IAppHeaderItem[]>([])
  const [navSelected, setNavSelected] = useState<string[]>([])
  const [railCollapsed, setRailCollapsed] = useState(false)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const isShowNav = getParam('isShowNav')

  const navigate = useNavigate();
  const location = useLocation()

  useEffect(() => {
    getAppMenu().then(res => {
      const remoteRoute = res.data

      const dynamicRoute = formatRoute([...remoteRoute])
      const tarRoute = [...dynamicRoute, ...routerConfigPlus]
      const tarRouteMap = getRouterMap(tarRoute)

      setSourceAppList(tarRoute)
      setSourceAppMap(tarRouteMap)

      const defaultOpenKeys = getDefaultOpenKeys(tarRoute)
      setOpenKeys(defaultOpenKeys)

      setCurrentRouteComponent(() => () => RouterConfig(tarRoute as RouteObject[]))
    }).catch(err => { })

    getAppHeaderConfig().then(res => {
      const config = res.data
      setHeaderConfig(config)
    }).catch(err => { })
  }, [])

  useEffect(() => {
    if (sourceAppList.length && Object.keys(sourceAppMap).length) {
      const { pathname } = location
      if (pathname === '/') {
        clearWaterNow()
      } else {
        drawWaterNow()
      }
      handleCurrentRoute(sourceAppMap, getValidAppList(sourceAppList))
    }
  }, [location, sourceAppList, sourceAppMap])

  // UI 规范 3.0 响应式：768-1099px 主导航折叠为 64px
  useEffect(() => {
    const query = window.matchMedia('(max-width: 1099px)');
    const apply = () => setRailCollapsed(query.matches);
    apply();
    if (query.addEventListener) query.addEventListener('change', apply);
    return () => { if (query.removeEventListener) query.removeEventListener('change', apply); };
  }, []);

  useEffect(() => {
    const controller = new AbortController()
    const url = encodeURIComponent(location.pathname)
    setCustomDialogInfo(undefined)
    getCustomDialog(url, controller.signal).then(res => {
      if (res.status !== 502 && res.data?.content && res.data.hit) {
          setCustomDialogInfo(res.data)
      } else {
          setCustomDialogInfo(undefined)
      }
    }).catch(err => {
      console.error(err);
    })
    return () => {
      controller.abort()
    }
  }, [location])

  const handleCurrentRoute = (appMap: Record<string, IRouterConfigPlusItem>, appList: IRouterConfigPlusItem[]) => {
    const { pathname } = location
    const [_, stLevel, edLevel] = pathname.split('/')
    const stLevelApp = appMap[`/${stLevel}`]
    let currentNavKey = ""
    if (stLevelApp && stLevelApp.isSingleModule) {
      currentNavKey = `/${stLevel}/${edLevel}`
    } else {
      currentNavKey = `/${stLevel}`
    }

    let topNavAppList = appList
    if (stLevelApp && stLevelApp.isSingleModule) {
      topNavAppList = stLevelApp.children || []
    }

    setCurrentNavList(topNavAppList)
    setNavSelected([pathname === '/' ? '/' : currentNavKey])
    setIsShowSlideMenu(pathname !== '/' && !!stLevelApp && !stLevelApp.isCollapsed)
  }

  const handleClickNav = (app: IRouterConfigPlusItem, subPath?: string) => {

    if (app.path === '/') {
      navigate(app.path || '/')
    } else if (app.menu_type === 'iframe' && app.path) {
      navigate(app.path)
    } else if (app.menu_type === 'out_link' && app.url) {
      window.open(app.url, 'blank')
    } else if (app.menu_type === 'in_link' && app.path) {
      window.open(app.url, 'blank')
    } else {

      const currentApp = sourceAppMap[subPath || '']

      let currentItem = subPath ? currentApp : app

      while (currentItem && currentItem.children?.length) {
        currentItem = currentItem.children[0]
      }

      if (currentItem) {
        let appMenuPath = currentItem.path || ''
        navigate(appMenuPath)
      }
    }
  }

  const navApps = getValidAppList(sourceAppList);
  const residentApps = RESIDENT_NAV_NAMES
    .map(name => navApps.find(item => item.name === name))
    .filter(Boolean) as IRouterConfigPlusItem[];

  const renderRailItems = (apps: IRouterConfigPlusItem[]) => apps.map(app => (
    <Menu.Item key={app.path} disabled={!!app.disable} title={false} onClick={() => {
      setMobileNavOpen(false);
      handleClickNav(app);
    }}>
      <span className="icon-wrapper">
        {renderMenuIcon(app.icon)}
        <span>{app.title}</span>
      </span>
    </Menu.Item>
  ));

  const userMenu = (
    <Menu>
      {globalConfig.brand.termsUrl && <Menu.Item><a href={globalConfig.brand.termsUrl} target="_blank" rel="noreferrer">用户协议</a></Menu.Item>}
      {globalConfig.brand.privacyUrl && <Menu.Item><a href={globalConfig.brand.privacyUrl} target="_blank" rel="noreferrer">隐私政策</a></Menu.Item>}
      {globalConfig.brand.copyright && <Menu.Item disabled>{globalConfig.brand.copyright}</Menu.Item>}
      <Menu.Item onClick={() => {
        navigate('/user')
      }}>{"用户中心"}</Menu.Item>
      <Menu.Item onClick={() => {
        Cookies.remove('myapp_username');
        handleTips.userlogout()
      }}>{"退出登录"}</Menu.Item>
    </Menu>
  );

  const renderMenu = () => {
    const { pathname } = location
    const currentNavMap = sourceAppMap
    const [currentSelected] = navSelected

    if (currentNavMap && currentSelected && currentNavMap[currentSelected]?.children?.length) {

      const currentAppMenu = currentNavMap[currentSelected].children || []
      if (currentAppMenu && currentAppMenu.length) {

        const menuContent = currentAppMenu.map(menu => {
          if (menu.isMenu) {
            return <SubMenu key={menu.path} title={<span className="icon-wrapper">{renderMenuIcon(menu.icon)}<span>{menu.title}</span></span>}>
              {
                menu.children?.map(sub => {
                  if (sub.isMenu) {
                    return <Menu.ItemGroup key={sub.path} title={<span className="icon-wrapper">{renderMenuIcon(sub.icon)}<span>{sub.title}</span></span>}>
                      {
                        sub.children?.map(thr => {
                          return <Menu.Item disabled={!!thr.disable} hidden={!!thr.hidden} key={thr.path} onClick={() => {
                            if (!menu.isCollapsed) {
                              setIsMenuCollapsed(false)
                            }
                            if (thr.menu_type === 'out_link' || thr.menu_type === 'in_link') {
                              window.open(thr.url, 'blank')
                            } else {
                              navigate(thr.path || '')
                            }
                          }}>
                            <div className="icon-wrapper">
                              {renderMenuIcon(thr.icon)}
                              {thr.title}
                            </div>
                          </Menu.Item>
                        })
                      }
                    </Menu.ItemGroup>
                  }
                  return <Menu.Item disabled={!!sub.disable} hidden={!!sub.hidden} key={sub.path} onClick={() => {
                    if (!menu.isCollapsed) {
                      setIsMenuCollapsed(false)
                    }
                    if (sub.menu_type === 'out_link' || sub.menu_type === 'in_link') {
                      window.open(sub.url, 'blank')
                    } else {
                      navigate(sub.path || '')
                    }
                  }}>
                    <div className="icon-wrapper">
                      {renderMenuIcon(sub.icon)}
                      {sub.title}
                    </div>
                  </Menu.Item>
                })
              }
            </SubMenu>
          }
          return <Menu.Item disabled={!!menu.disable} hidden={!!menu.hidden} key={menu.path} onClick={() => {
            if (!menu.isCollapsed) {
              setIsMenuCollapsed(false)
            }
            if (menu.menu_type === 'out_link' || menu.menu_type === 'in_link') {
              window.open(menu.url, 'blank')
            } else {
              navigate(menu.path || '')
            }
          }}>
            <div className="icon-wrapper">
              {renderMenuIcon(menu.icon)}
              {menu.title}
            </div>
          </Menu.Item>
        })

        return <div className="side-menu">
          <div className="h100 ov-h d-f fd-c" style={{ width: isMenuCollapsed ? 0 : 'auto' }}>
            <Menu
              selectedKeys={[pathname]}
              openKeys={openKeys}
              mode="inline"
              onOpenChange={(openKeys) => {
                setOpenKeys(openKeys)
              }}
              onSelect={(info) => {
                const key = info.key
              }}
            >
              {menuContent}
            </Menu>
            <div className="p16 ta-r bor-t" style={{ borderColor: '#e5e6eb' }}>
              <div className="d-il bor-l pl16" style={isMenuCollapsed ? { position: 'absolute', bottom: 16, left: 0, borderColor: '#e5e6eb' } : { borderColor: '#e5e6eb' }}>
                {
                  isMenuCollapsed ? <RightOutlined className="cp" onClick={() => {
                    setIsMenuCollapsed(!isMenuCollapsed)
                  }} /> : <LeftOutlined className="cp" onClick={() => {
                    setIsMenuCollapsed(!isMenuCollapsed)
                  }} />
                }
              </div>
            </div>
          </div>
        </div>
      }
    }

    return null
  }

  return (
    <PageExtraContext.Provider value={customDialogInfo}>
    <div className="content-container fade-in mo-shell">
      {/* 左侧主导航：浅色导轨（UI 规范 3.0），顶部 Logo/折叠、中部一级菜单、底部空间与用户 */}
      {
        isShowNav === 'false' ? null : <aside className={`mo-side-nav${railCollapsed ? ' is-collapsed' : ''}${mobileNavOpen ? ' is-open' : ''}`}>
          <div className="mo-side-nav-top">
            <img className="cp mo-side-logo" src={railCollapsed ? globalConfig.loadingLogo.default : (globalConfig.brand.logoUrl || globalConfig.appLogo.default)} alt={globalConfig.brand.name} onClick={() => {
              setMobileNavOpen(false);
              navigate('/', { replace: true });
            }} />
            <button type="button" className="mo-side-nav-collapse" aria-label={railCollapsed ? '展开导航' : '折叠导航'} title={railCollapsed ? '展开导航' : '折叠导航'} onClick={() => setRailCollapsed(!railCollapsed)}>
              <svg className="mo-side-nav-collapse-icon" width="18" height="18" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <rect x="1.75" y="2.25" width="12.5" height="11.5" rx="2" stroke="currentColor" strokeWidth="1.6" />
                <path d="M6 2.25v11.5" stroke="currentColor" strokeWidth="1.6" />
              </svg>
            </button>
          </div>
          <Menu mode="inline" className="mo-side-menu" inlineCollapsed={railCollapsed} selectedKeys={navSelected}>
            <Menu.Item key="/" title={false} onClick={() => {
              setMobileNavOpen(false);
              navigate('/', { replace: true });
            }}>
              <span className="icon-wrapper"><MenuGlyph name="home" />{"主页"}</span>
            </Menu.Item>
            {renderRailItems(residentApps)}
          </Menu>
          {!!globalConfig.brand.helpUrl && (
            <a className="mo-side-doc" href={globalConfig.brand.helpUrl} target="_blank" rel="noreferrer" aria-label="文档" title={railCollapsed ? '文档' : undefined}>
              <MenuGlyph name="file-text" />
              {!railCollapsed && <span>文档</span>}
            </a>
          )}
          <div className="mo-side-nav-bottom">
            <ProjectSwitcher />
            <Dropdown overlay={userMenu}>
              <div className="mo-side-user cp">
                <span className="mo-side-avatar" aria-hidden="true">
                  <User size={16} strokeWidth={2} absoluteStrokeWidth />
                </span>
                {!railCollapsed && <span className="mo-side-user-name">{userName || '用户'}</span>}
              </div>
            </Dropdown>
          </div>
        </aside>
      }
      <button type="button" className="mo-mobile-toggle" aria-label="打开导航" onClick={() => setMobileNavOpen(true)}>
        <MenuOutlined />
      </button>

      <div className="main-content-container mo-main">
        {isShowSlideMenu ? renderMenu() : null}

        <div className="ov-a w100 p-r mo-content" id="componentContainer">
          {
            CurrentRouteComponent && <CurrentRouteComponent />
          }
        </div>

      </div >
      {/* AI 机器人悬浮按钮与聊天面板，固定在页面右下角，全局可用 */}
      <AiChatBot />
    </div>
    </PageExtraContext.Provider>
  );
};

export default AppWrapper;
