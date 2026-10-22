# 🖥️ Mac 磁盘空间深度分析与清理记录

**最新更新时间**：2026年10月22日  
**扫描对象**：Macintosh HD (APFS Volume Group)  
**操作系统**：macOS (Apple Silicon arm64)

---

## 📊 一、 清理后磁盘状态

| 指标 | 清理前 | 清理后 | 变化 |
| :--- | :--- | :--- | :--- |
| **已用空间 (Used)** | 176 GiB | **171 GiB** | **📉 释放了 ~5.0 GB** |
| **可用剩余空间 (Avail)** | 246 GiB | **251 GiB** | **📈 增加到 251 GB** |
| **磁盘使用率** | 42% | **41%** | 状态极佳 |

---

## ✅ 二、 已执行的清理项明细

1. **Anaconda 包与索引缓存清理 (`conda clean --all -y`)**
   * 清除了 638 个旧版本压缩包（tarballs，约 1000 MB）；
   * 清除了 79 个无引用依赖包（约 667 MB）；
   * 累计释放：**~1.7 GB**。

2. **微信历史自动更新与安装包残留**
   * 删除了 `~/Library/Caches/com.tencent.xinWeChat/org.sparkle-project.Sparkle/` 下沉淀的所有历史版本升级包（含已安装的 506MB 安装镜像）；
   * 微信缓存从 1.9 GB 降为 0 B；
   * 累计释放：**~1.9 GB**。

3. **Steam 平台及所有相关组件彻底卸载**
   * 卸载应用程序：`/Applications/Steam.app`；
   * 删除核心支持库：`~/Library/Application Support/Steam`（**1.4 GB**）；
   * 清除后台守护项：`~/Library/LaunchAgents/com.valvesoftware.steamclean.plist`；
   * 清除网络与崩溃日志：`com.valvesoftware.steam.helper` 等；
   * 累计释放：**~1.4 GB+**。

---

## 🗂️ 三、 当前主要空间占用现状（更新后）

* **Windows 11 虚拟机**：**47 GB**（`~/Virtual Machines.localized/`）
* **应用程序**：**~31.5 GB**（已剔除 Steam，最大应用为 MATLAB 3.4G、BlueStacks 2.9G、微软 Office ~11.3G）
* **Anaconda 环境**：**~8.2 GB**（精简后）
* **系统核心与系统缓存**：~35-40 GB
