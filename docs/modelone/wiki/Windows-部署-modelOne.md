> **状态：上游继承，modelOne 待核验。** 本页内容来自 CubeStudio Wiki 上游版本，尚未逐项对照 modelOne 当前代码和部署配置。文中的旧项目名称、仓库路径、镜像、域名、示例数据、截图及外部资源均须在使用前核验；可用的当前说明请先查阅 [modelOne 交付文档](../README.md) 和[迁移记录](MIGRATION.md)。


# Windows 部署 modelOne

## 环境要求

控制端机器：CPU >= 16核，内存 >= 32G，至少 1 台。
生产配置建议：32核64G × 2 台。

---

## 一、启用 Windows 功能（WSL）

1. 按下 `Win + R`，输入 `optionalfeatures` 回车，打开「Windows 功能」窗口；

   ![在这里插入图片描述](https://cube-studio.oss-cn-hangzhou.aliyuncs.com/docs/csdn_image/d550a067d1ea4d028a29abd3f68ee978.png)


2. 勾选所需功能后，点击窗口底部「确定」，系统会开始安装所选功能，等待安装完成（约 1~3 分钟，视电脑配置而定）；

3. 安装完成后，会提示「需要重启电脑才能生效」，点击「立即重启」（**务必重启，否则后续步骤会失败**）。

---

## 二、确认虚拟化已启用

1. 按下 `Ctrl + Shift + Esc` 打开任务管理器；
2. 切换到「性能」选项卡；
3. 查看右下角「虚拟化」是否为「**已启用**」。

   ![在这里插入图片描述](https://cube-studio.oss-cn-hangzhou.aliyuncs.com/docs/csdn_image/bf977816308745a1a757b42ee4e312a8.png)


4. 如果没有启用，开机前按 `F1` / `F12` / `Del` 进入 BIOS/UEFI 设置，在 **Advanced → Intel RC Setup** 中找到：
   - **Intel Virtualization Technology (VT-x)**，或
   - **AMD-V** 选项，

   将其改为 **Enable**。

---

## 三、安装 WSL2 及 Ubuntu

### 3.1 更新 WSL

以管理员身份运行 cmd（`Win + R` → 输入 `cmd` → 右键以管理员身份运行），执行：

```bash
wsl --update
```

> 如果出现错误 `0x80070005`，请使用：
> ```bash
> wsl --update --web-download
> ```

### 3.2 安装 Ubuntu 发行版

```bash
# 查看可用的发行版版本
wsl --list --online

# 设置默认使用 WSL2（而非 WSL1）
wsl --set-default-version 2

# 安装 Ubuntu 发行版
wsl --install -d Ubuntu
```

> 如果出现错误 `0x80072ee2`，请检查网络连通性：
> ```bash
> curl -I https://aka.ms/wslubuntu2204
> ```

### 3.3 验证安装

```bash
# 查看安装是否成功
wsl -l -v

# 进入虚拟机
wsl -d Ubuntu
```

---

## 四、配置 WSL2

### 4.1 修改根目录挂载传播模式

进入 WSL 后，查看 `/` 分区的传播模式：

```bash
findmnt -o PROPAGATION,SOURCE,TARGET /
```

输出示例：

```
PROPAGATION  SOURCE    TARGET
private      /dev/sdd  /
```

如果显示为 `private`，需要改为 `shared`：

```bash
sudo mount --make-shared /
```

### 4.2 限制 WSL2 内存与 CPU 占用

WSL2 默认会占用较多内存，可通过配置文件进行限制。在 Windows 用户目录（如 `C:\Users\你的用户名\`）下创建或编辑文件 `.wslconfig`：

```ini
[wsl2]

# 限制内存使用，避免 WSL 吃光所有内存
memory=4GB

# 限制 CPU 核心数（建议设为物理核心数的一半）
processors=2

# 启用 localhost 转发（方便在 Windows 浏览器访问 WSL 服务）
localhostForwarding=true
```

---

## 五、WSL2 迁移至其他目录（可选）

WSL2 默认安装在 C 盘，如需迁移至其他目录，按以下步骤操作：

**1. 停止正在运行的 WSL：**

```bash
wsl --shutdown
```

**2. 导出目标 Linux 发行版：**

```bash
wsl --export Ubuntu D:/export.tar
```

**3. 卸载原有的 Linux 发行版：**

```bash
wsl --unregister Ubuntu
```

**4. 将导出文件导入到目标目录：**

```bash
wsl --import Ubuntu D:\export\ D:\export.tar --version 2
```
