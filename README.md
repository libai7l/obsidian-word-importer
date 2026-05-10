# Obsidian Word Importer

选中英文单词/词组 → Ctrl+C → 自动收录到 Obsidian 词库（Google Chrome）。

## 功能

- **一键收录**: 在任意网页选中英文单词或词组，Ctrl+C 即自动查询并写入 Obsidian
- **沉浸式翻译优先**: 如果页面上已启用 [沉浸式翻译](https://immersivetranslate.com/)（全页双语模式），直接提取页面上的中文翻译作为释义
- **多 API 兜底**: 沉浸式翻译 → Google 翻译 / 有道词典
- **按字母排序**: 单词自动按字母顺序插入文件
- **文件自动轮转**: 满 100 个单词自动新建 `论文单词1.md`、`论文单词2.md` …
- **桌面通知**: 3 秒自动消失，收录结果即时可见
- **防抖去重**: 同一单词在设定时间内不重复查询
- **右键菜单**: 右键选中单词 → 「添加到 Obsidian 词库」

---

## 下载安装

安装分为两步：

1. **运行 install 脚本** → 注册 Native Messaging Host（操作系统层面）
2. **加载扩展** → 浏览器开发者模式 → 加载已解压的扩展程序

### Ubuntu / Linux

```bash
git clone https://github.com/libai7l/obsidian-word-importer.git
cd obsidian-word-importer
chmod +x install.sh && ./install.sh
```

以上命令已完成 **第 1 步**（Native Host 注册）。接下来完成 **第 2 步**：

1. 打开浏览器，访问 `chrome://extensions`
2. 开启右上角 **「开发者模式」**
3. 点击 **「加载已解压的扩展程序」**
4. 选择 `obsidian-word-importer` 目录
5. 点击扩展图标 → 配置 Obsidian Vault 路径

### Windows

**前提要求：**
- 已安装 Node.js（[下载地址](https://nodejs.org/)）
- 已安装 Google Chrome 浏览器

```powershell
git clone https://github.com/libai7l/obsidian-word-importer.git
cd obsidian-word-importer
powershell -ExecutionPolicy Bypass -File install.ps1
```

以上命令已完成 **第 1 步**（Native Host 注册 + 自动打开扩展管理页面）。接下来完成 **第 2 步**：

1. 在自动打开的扩展管理页面上，开启右上角 **「开发者模式」**
2. 点击 **「加载已解压的扩展程序」**
3. 选择 `obsidian-word-importer` 目录
4. 点击扩展图标 → 配置 Obsidian Vault 路径

---

## 配置（可选）

点击浏览器工具栏的扩展图标：

| 设置项 | 说明 | 默认值 |
|--------|------|--------|
| Vault 路径 | Obsidian Vault 的绝对路径 | 自动检测 |
| 目标文件 | 相对于 Vault 的词库文件 | `论文单词.md` |
| 词典 API | Google 翻译 / 有道词典 | Google |
| 防抖时间 | 同一单词重复收录的冷却时间（秒） | 60 |
| 桌面通知 | 是否弹出桌面通知 | 开启 |

> **注意**: 如果未配置 Vault 路径，插件会自动扫描系统中已安装的 Obsidian Vault。
>
> **Windows 路径示例**: `C:\Users\用户名\Documents\Obsidian Vault`
>
> **Ubuntu 路径示例**: `/home/用户名/文档/Obsidian Vault`

## 使用

1. 打开任意英文网页（建议开启沉浸式翻译全页双语模式以获得最佳翻译质量）
2. 选中英文单词或词组
3. 按 `Ctrl+C`
4. 桌面通知显示收录结果
5. 打开 Obsidian 查看词库文件

也可右键选中单词 → 「添加到 Obsidian 词库」。

## 文件格式

单词以 Markdown 格式保存于 Obsidian Vault：

```markdown
# 论文词汇表

### abandon
放弃；抛弃

### geodesy
大地测量学

### survey methodology
调查方法
```

- `###` 标题：单词（较大字体）
- 第二行：释义（正常字体）
- 单词之间空行分隔
- 满 100 个单词自动轮转到 `论文单词1.md`、`论文单词2.md` …

## 翻译优先级

```
页面沉浸式翻译（优先）
  ↓ 不可用
用户选择的 API（Google 翻译 / 有道词典）
  ↓ 不可用
另一 API 自动兜底
```

页面翻译提取会智能过滤导航栏、菜单、按钮等 UI 元素，确保不会误用「主题」「设置」等短文本。

## 支持浏览器

| 浏览器 | Ubuntu | Windows | 右键菜单 | 桌面通知 |
|--------|--------|---------|----------|----------|
| Google Chrome | ✓ | ✓ | ✓ | ✓ |

## 技术架构

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│  content.js  │────▶│ background.js │────▶│   host.js      │
│  (网页复制)   │     │  (Service     │     │  (Node.js      │
│              │     │   Worker)     │     │   Native Host) │
│  · 捕获 Ctrl+C│     │               │     │               │
│  · 提取沉浸式  │     │  · IndexedDB  │     │  · 翻译查询    │
│    翻译内容   │     │    缓存       │     │  · 文件写入    │
│  · 过滤UI噪音 │     │  · 通知/设置   │     │  · 排序去重    │
└─────────────┘     └──────────────┘     └───────────────┘
       ▲                                       │
       │         Native Messaging              │
       │         (stdio + JSON)                ▼
       │                               ┌───────────────┐
       └───────────────────────────────│  Obsidian     │
                                       │  Vault (.md)  │
                                       └───────────────┘
```

## 文件结构

```
obsidian-word-importer/
├── install.sh               # Ubuntu/Linux 一键安装脚本
├── install.ps1              # Windows PowerShell 一键安装脚本
├── manifest.json            # MV3 扩展清单 (Chrome)
├── background.js            # Service Worker
├── content.js               # 网页内容脚本
├── .gitignore
├── popup/
│   ├── popup.html           # 配置面板
│   ├── popup.js             # 配置逻辑
│   └── popup.css            # 样式
├── icons/
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
├── native-host/
│   ├── host.js              # Node.js Native Host（翻译/写入/排序）
│   ├── host.json            # Native Host 清单模板
│   └── host.bat             # Windows Native Host 启动器
└── README.md
```

## License

MIT
