# Obsidian Word Importer

Chrome 浏览器扩展 —— 选中英文单词/词组 → Ctrl+C 自动收录到 Obsidian 词库，支持音标发音、词根词缀分析和按字母排序。

![](icons/icon128.png)

## 功能

- **一键收录**: 在任意网页选中英文单词或词组，Ctrl+C 即自动查询并写入 Obsidian
- **沉浸式翻译优先**: 如果页面上已启用 [沉浸式翻译](https://immersivetranslate.com/)（全页双语模式），直接提取页面上的中文翻译作为释义
- **多 API 兜底**: 沉浸式翻译 → Google 翻译 / 有道词典 → 本地词库（CET-6 + 测绘专业）
- **词根词缀分析**: 自动拆解前缀、词根、后缀，辅助记忆
- **IPA 音标**: 本地词库命中时附带音标发音
- **按字母排序**: 单词自动按字母顺序插入文件
- **文件自动轮转**: 满 100 个单词自动新建 `论文单词1.md`、`论文单词2.md` …
- **桌面通知**: Chrome 桌面通知 3 秒自动消失，收录结果即时可见
- **防抖去重**: 同一单词在设定的时间内不重复查询
- **右键菜单**: 右键选中单词 → 「添加到 Obsidian 词库」

## 安装

```bash
chmod +x install.sh && ./install.sh
```

**一条命令完成所有安装**：Native Host 清单 + 扩展注册 + 权限配置。重启 Chrome 即可使用。

### 配置（可选）

点击浏览器工具栏的扩展图标：

| 设置项 | 说明 | 默认值 |
|--------|------|--------|
| Vault 路径 | Obsidian Vault 的绝对路径 | 自动检测 |
| 目标文件 | 相对于 Vault 的词库文件 | `6英语/论文单词.md` |
| 词典 API | Google 翻译 / 有道词典 / 仅本地 | Google |
| 防抖时间 | 同一单词重复收录的冷却时间 | 60 秒 |
| 桌面通知 | 是否弹出 Chrome 桌面通知 | 开启 |

> **注意**: 如果未配置 Vault 路径，插件会自动扫描系统中常见的 Obsidian Vault 位置。

## 使用

1. 打开任意英文网页（建议开启沉浸式翻译全页双语模式以获得最佳翻译质量）
2. 选中英文单词或词组
3. 按 `Ctrl+C`
4. 桌面通知显示收录结果
5. 打开 Obsidian 查看词库文件

## 文件格式

单词以 Markdown 格式保存，排版清晰：

```markdown
# 论文词汇表

### geodesy /dʒiːˈɒdɪsi/
[n.] 大地测量学
← *geo(地球)+desy(划分)→大地测量*

### ubiquitous /juːˈbɪk.wɪ.təs/
[n.] 无处不在的
← *ubiqu(到处)+itous(形容词后缀)*
```

- `###` 标题：单词 + 发音（较大字体）
- 第二行：`[词性] 释义`（正常字体）
- 第三行：词根词缀分析（斜体小字）
- 单词之间空行分隔

## 本地词库

内置 **CET-6 高频核心词 300+**、**测绘/遥感/GIS/导航专业术语 100+**、**学术写作高频词 100+**，覆盖：

- 测绘工程: geodesy, photogrammetry, lidar, theodolite, cartography…
- 导航定位: GNSS, inertial, gyroscope, magnetometer, ephemeris…
- 遥感: multispectral, backscatter, radiometer, interferometry…
- 学术写作: hypothesis, methodology, empirical, quantitative…

## 技术架构

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│  content.js  │────▶│ background.js │────▶│   host.py     │
│  (网页复制)   │     │  (Service     │     │  (Native Host) │
│              │     │   Worker)     │     │               │
│  · 捕获 Ctrl+C│     │               │     │  · 翻译查询    │
│  · 提取沉浸式  │     │  · 缓存/去重   │     │  · 文件写入    │
│    翻译内容   │     │  · 通知/设置   │     │  · 排序去重    │
└─────────────┘     └──────────────┘     └───────────────┘
       ▲                                       │
       │            Chrome Native              │
       │            Messaging API              ▼
       │                               ┌───────────────┐
       └───────────────────────────────│  Obsidian     │
                                       │  Vault (.md)  │
                                       └───────────────┘
```

## 文件结构

```
obsidian-word-importer/
├── manifest.json           # Chrome MV3 扩展清单
├── background.js           # Service Worker
├── content.js              # 网页内容脚本
├── popup/
│   ├── popup.html          # 配置面板
│   ├── popup.js            # 配置逻辑
│   └── popup.css           # 样式
├── icons/
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
├── native-host/
│   ├── host.py             # Python Native Host
│   ├── host.json           # Native Host 清单模板
│   └── install.sh          # 安装脚本
└── README.md
```

## License

MIT
