# modelOne

企业级 AI 开发与模型生产平台，提供数据管理、在线开发、Pipeline 编排、训练、模型、推理服务和智能应用。

当前版本为 `0.1.0-dev` 品牌改造基线。企业仓库、资源迁移和真实安装/升级验收尚待完成。

- [交付资料与验收边界](docs/modelone/README.md)
- [安装部署](docs/modelone/installation.md)
- [升级迁移](docs/modelone/upgrade.md)
- [版本说明](docs/modelone/release-notes.md)
- [统一品牌配置](config/modelone.json)

本地检查：

```sh
python3 scripts/test_modelone.py
python3 scripts/brand_scan.py
```

生产发布须先构建三个前端，再运行 `python3 scripts/brand_scan.py --built`。CI 已包含此检查。缺少企业镜像和资源时，不能仅凭页面构建成功认定平台可部署。

原项目和第三方许可证随源码及交付包保留：[LICENSE](LICENSE)、[版权说明](docs/modelone/licenses.md)、[内部上游资料](docs/upstream/README.md)。这些资料不作为产品页面展示内容。
