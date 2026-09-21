# modelOne 部署基线

完整交付资料入口：[modelOne 文档](modelone/README.md)。当前为开发基线，真实安装、升级及离线验收仍待企业环境。

唯一默认品牌源为 `config/modelone.json`。Python 后端直接读取；三个前端在构建前通过 `scripts/generate_brand.py` 生成默认值，浏览器可从 `/myapp/brand.js` 读取部署环境覆盖。`scripts/render_deployment.py` 使用同一配置生成 Compose 和 Kubernetes 清单。

| 配置环境变量 | 用途 |
| --- | --- |
| `MODELONE_CONFIG` | JSON 配置文件路径 |
| `MODELONE_IMAGE_REGISTRY` | 企业镜像仓库，不带 `/modelone` |
| `MODELONE_ASSET_BASE_URL` | 企业资源根地址 |
| `MODELONE_MNIST_BASE_URL` | MNIST 示例资源根地址；任务会在其下读取 `datasets/mnist/` |
| `MODELONE_COPYRIGHT_HOLDER` / `MODELONE_COPYRIGHT_YEAR` | 企业版权 |
| `MODELONE_HELP_URL` / `MODELONE_SUPPORT_URL` | 帮助与技术支持 |
| `MODELONE_TERMS_URL` / `MODELONE_PRIVACY_URL` | 用户协议与隐私 |
| `MODELONE_LOGO_URL` / `MODELONE_LOGO_REVERSE_URL` / `MODELONE_FAVICON_URL` | 正式品牌图形 |
| `MODELONE_PRIMARY_COLOR` | CSS 十六进制主色：`#RGB`、`#RGBA`、`#RRGGBB` 或 `#RRGGBBAA` |
| `MODELONE_SECONDARY_COLOR` | CSS 十六进制辅助色，用于焦点、链接和编排器辅助强调 |
| `MODELONE_LOGIN_BACKGROUND_COLOR` / `MODELONE_LOGIN_SURFACE_COLOR` | 登录页及错误页的背景色和面板色 |
| `MODELONE_FONT_FAMILY` | 字体回退列表；只允许字体名、逗号、空格和常用名称字符 |

发布前运行 `python3 scripts/test_modelone.py` 和 `python3 scripts/brand_scan.py --built`；渲染交付目录后，再用 `scripts/brand_scan.py --artifact` 检查 Compose、Kubernetes 和品牌清单。数据库迁移、资源同步、许可证和验收边界分别见交付手册。默认 `modelone/` 镜像和本地资源路径是待配置引用，不表示已经有可用镜像或已完成离线资源准备。
