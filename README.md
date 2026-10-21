# 🔍 HWID 9527

> Chromebook HWID Database 自动检查工具  
> 平台：Ubuntu Desktop / Windows | 框架：PyQt6

---

## 📖 项目简介

在 Chromebook 项目量产前，需要将所有出货国别（Region）和出货 device 的信息写入 `hwid_database`（YAML 格式）。人工维护容易遗漏，本工具通过上传四份文件自动完成比对，并以彩色 UI 高亮所有异常条目。

### 检查内容

| 检查项 | 逻辑 | 异常时联系 |
|--------|------|----------|
| **Region Check** | OD 里每个出货国别，按 `Region code list_v2.5a.xls` 映射表，检查所有对应 HWID code 是否都在 Database 的 `region_field` 中（如 Canada → `ca.fr`/`ca.ansi`/`ca.hybrid` 三个 code 都需存在） | **请联系 SWPM** |
| **Device Check** | EC Level 中的每个 component，逐项检查：① AVL List 里是否存在；② AVL 状态是否为 `QUALIFIED`；③ 是否已加入 HWID Database 且 `status: supported` | **请联系 PM** |

### 结果状态说明

| 状态 | 含义 |
|------|------|
| ✅ OK | 正常 |
| ❌ MISSING | Region code 或 HWID DB 条目缺失 |
| ⚠️ UNSUPPORTED | HWID DB 中存在但 status ≠ supported |
| 🚫 NOT_IN_AVL | EC Level 中有，但 AVL List 里不存在 |
| 📋 AVL_NOT_QUALIFIED | AVL List 里有但状态不是 QUALIFIED |
| 🔍 NO_AVL_ID | AVL 状态 QUALIFIED 但缺 Google AVL URL |
| 🔶 POSSIBLE_MATCH | HWID DB 中未精确匹配，通过 MPN 发现疑似条目 |
| ❓ UNKNOWN_MAPPING | OD 国别名在映射表中找不到 |

### Project Name 格式

界面右上角的 Project Name 由两部分组成：

```
{EC Level 文件名第一段（第一个 _ 前的项目代号）}_{HWID Database 文件名（不含扩展名）}
```

示例：`MCB50_S3A0_EC Level 20260121.xlsx` + `pujjoquince.yaml` → **`MCB50_pujjoquince`**

---

## 📁 项目结构

```
hwid_checker/
│
├── main.py                        # 入口文件，启动 PyQt6 应用
├── requirements.txt               # Python 依赖 (PyQt6, openpyxl, PyYAML)
├── setup.sh                       # Linux 一键安装环境脚本
├── run.sh                         # Linux 一键启动脚本
├── build_linux.sh                 # Linux PyInstaller 一键打包脚本
├── build_windows.bat              # Windows PyInstaller 一键打包脚本
├── hwid_checker.spec              # PyInstaller 打包配置文件
├── README.md                      # 项目说明文档
├── FILE_FORMAT_REQUIREMENTS.md    # 四份输入文件的详细格式规范要求
│
├── core/                          # 业务逻辑层（纯 Python，无 UI 依赖）
│   ├── __init__.py
│   ├── models.py                  # 数据类（ODCountry, DeviceResult, CheckReport 等）
│   ├── mappings.py                # EC 类别→HWID 类型映射 / 跳过类别集合
│   │
│   ├── parsers/                   # 四个独立文件解析器
│   │   ├── __init__.py
│   │   ├── od_parser.py           # 解析 OD xlsx → 出货国别列表（动态自适应列位置）
│   │   ├── hwid_parser.py         # 解析 HWID YAML → region_codes + components
│   │   ├── ec_parser.py           # 解析 EC Level xlsx → KPL 组件列表
│   │   └── avl_parser.py          # 解析 AVL List xlsx → 组件 + AVL 状态 + URL
│   │
│   └── checker/                   # 比对逻辑
│       ├── __init__.py
│       ├── region_checker.py      # OD 国别 vs HWID region_field（内置静态映射表）
│       └── device_checker.py      # EC+AVL 组件 vs HWID components
│
├── ui/                            # UI 层（PyQt6）
│   ├── __init__.py
│   ├── main_window.py             # 主窗口：布局、事件、Excel 导出
│   ├── check_worker.py            # QThread 后台检查线程
│   │
│   └── widgets/                   # 可复用 UI 组件
│       ├── __init__.py
│       ├── file_upload_panel.py   # 四个文件拖拽/浏览上传卡片
│       ├── result_table.py        # 彩色结果表格（按 Region / Device 独立筛选栏）
│       └── summary_bar.py         # 顶部状态统计芯片栏
│
└── resources/
    └── (预留目录，Region code 映射已内建于 region_checker.py)
```

---

## 🔄 数据流

```
┌──────────┐   ┌─────────────┐   ┌──────────┐   ┌──────────┐
│    OD    │   │HWID Database│   │ EC Level │   │ AVL List │
│  .xlsx   │   │   (YAML)    │   │  .xlsx   │   │  .xlsx   │
└────┬─────┘   └──────┬──────┘   └────┬─────┘   └────┬─────┘
     │                │               │               │
     ▼                ▼               ▼               ▼
 od_parser       hwid_parser      ec_parser       avl_parser
     │                │               │               │
     │         ┌──────┴──────┐        └───────┬───────┘
     │         │             │                │
     │    region_codes   components      JOIN by LCFC PN
     │         │             │           (QUALIFIED only)
     ▼         ▼             │                │
 region_checker              └────────────────┘
     │                                │
     │                          device_checker
     │                                │
     └──────────────┬─────────────────┘
                    ▼
               CheckReport
                    │
          ┌─────────┴──────────┐
          ▼                    ▼
    Region Tab           Device Tab
   (RegionResult)      (DeviceResult)
          │                    │
          └─────────┬──────────┘
                    ▼
              Export .xlsx
```

---

## 📊 检查状态说明

### Region Check

| 状态 | 含义 |
|------|------|
| ✅ `OK` | OD 国别在 HWID `region_field` 中找到对应 code |
| ❌ `MISSING` | 映射表中预期的 HWID code 在 HWID DB 中缺失（如 Canada 缺少 ca.fr/ca.ansi/ca.hybrid 等） |
| ❓ `UNKNOWN_MAPPING` | OD 国别名在静态映射表中找不到，需人工对照 `Region code list_v2.5a.xls` 确认或添加 |

### Device Check

| 状态 | 含义 |
|------|------|
| ✅ `OK` | 组件在 HWID DB 中存在且 `status: supported` |
| ❌ `MISSING` | HWID DB 中完全找不到对应条目 |
| ⚠️ `UNSUPPORTED` | HWID DB 中存在但 `status: unsupported` |
| 🚫 `NOT_IN_AVL` | 组件在 EC Level 中有料号，但 AVL List 里完全未收录 |
| 📋 `AVL_NOT_QUALIFIED` | AVL List 中存在但状态不是 QUALIFIED（需联系 PM 审核） |
| 🔍 `NO_AVL_ID` | AVL 状态为 QUALIFIED 但没有 Google AVL URL，无法构造 HWID Key，需人工检查 |
| 🔶 `POSSIBLE_MATCH` | 主 Key 未命中，但通过 MPN/part 找到疑似匹配，需人工确认 |
| ⚙️ `UNKNOWN_CATEGORY` | EC Level 的 category 在映射表中没有定义 |

---

## ⚙️ HWID Key 构造规则

```
CPU 类（无 qual_id）:
  URL:  .../component/6473
  Key:  cpu_6473

其他类（有 qual_id）:
  URL:  .../component/5993/qualification/15870
  Key:  wireless_5993_15870

EC Level → HWID 类型映射:
  CPU           → cpu
  Memory        → dram
  WLAN          → wireless
  Panel         → display_panel
  Battery       → battery
  Touchpad PCBA → touchpad
  UFS           → storage
  Finger Print  → fingerprint
  Camera        → camera
  KYB_NB        → (跳过)
  Adapter       → (跳过)
  Powercord     → (跳过)
```

---

## 🚀 安装与运行

> **适用平台：Ubuntu 22.04 LTS（jammy）及以上**

### 第一步：安装系统依赖（只需做一次）

```bash
sudo apt install -y python3-venv
```

> Ubuntu 22.04 默认不带 `python3-venv`，这一步需要 sudo。其他依赖（PyQt6 等）由 `setup.sh` 自动安装到项目内，**不需要 sudo**。

---

### 第二步：初始化项目（只需做一次）

```bash
cd hwid_checker
bash setup.sh
```

`setup.sh` 会自动完成：
1. 检查 Python 3 版本
2. 在项目目录创建 `.venv/` 虚拟环境
3. 安装 PyQt6 / openpyxl / PyYAML 到 `.venv/` 中（不污染系统）
4. 验证安装结果

---

### 第三步：运行（每次启动）

```bash
bash run.sh
```

`run.sh` 会自动检测 `.venv/` 是否完整，如不完整会自动调用 `setup.sh` 安装依赖并启动。

---

### 完整流程（新机器一次性操作）

```bash
# 1. 克隆或复制项目
git clone <仓库地址>
cd hwid_checker

# 2. 安装系统 venv 支持（需要 sudo，只做一次）
sudo apt install -y python3-venv

# 3. 初始化环境（无需 sudo）
bash setup.sh

# 4. 启动
bash run.sh
```


## 🖥️ 使用步骤

1. **启动程序**：`python3 main.py`
2. **上传文件**：将四个文件拖拽到对应卡片，或点击卡片浏览选择

   | 卡片 | 文件类型 | 示例文件名 |
   |------|----------|-----------|
   | 📋 OD | `.xlsx` | `Lenovo Chrome 15ITN10 OD v4.4.0.xlsx` |
   | 🔑 HWID Database | YAML（无后缀）| `pujjoquince` |
   | ⚡ EC Level | `.xlsx` | `MCB50_S3A0_EC Level 20260121.xlsx` |
   | 📦 AVL List | `.xlsx` | `Pujjoquince AVL List.xlsx` |

3. **点击 ▶ Run Check**：后台线程自动解析并比对（有进度条）
4. **查看结果**：
   - 切换 **Region Check** / **Device Check** Tab
   - 使用过滤按钮：All / Issues Only / OK / Missing 等
5. **导出报告**：点击 **⬇ Export** 保存为 `.xlsx`（含 Region + Device 两个 Sheet）

---

## 🗂️ 输入文件格式要求

### OD（Option Document）
- 格式：`.xlsx`
- 必须包含名为 `Country List` 的 Sheet
- Sheet 结构：`col1=Geo, col2=Regions`（第一行为标题行）

### HWID Database
- 格式：无后缀 YAML 文件
- 必须包含 `encoded_fields.region_field` 和 `components` 两个顶级字段
- 支持 ChromeOS 自定义 YAML Tag（`!region_field` 等）

### EC Level
- 格式：`.xlsx`
- 必须包含名称含 `KPL` 的 Sheet（如 `S3A0 EC Level KPL`）
- Header 行需包含 `Key Parts` 和 `LCFC PN` 两列

### AVL List
- 格式：`.xlsx`
- 必须包含名称含 `AVL list` 的 Sheet
- 必须包含 `AVL Status` 和 `Google AVL Link` 两列

---

## 🔧 扩展维护

### 关于国别匹配

国别名称与 HWID region code 的映射**直接基于标准表 `Region code list_v2.5a.xls` 构建**，内建于 `core/checker/region_checker.py` 的 `_COUNTRY_TO_HWID` 静态映射表中，完全脱离外部依赖：

```
Japan                → ["jp", "jp.us"]
United Kingdom       → ["gb"]
Canada               → ["ca.fr", "ca.ansi", "ca.hybrid"]
Nordics (北欧组)     → ["nordic"]
UAE Group (阿联酋组) → ["ae"]
Qatar / Bahrain      → ["gcc"]
```

> 💡 **维护说明**：如果遇到 OD 中填写的非标准国别名称报 `UNKNOWN_MAPPING`，只需对照 `Region code list_v2.5a.xls`，在 `core/checker/region_checker.py` 的 `_COUNTRY_TO_HWID` 字典中补上一行别名映射即可。

### 新增/跳过 EC Level 类别

编辑 `core/mappings.py`：

```python
# 新增有 HWID 字段的类别
EC_CATEGORY_TO_HWID_TYPE = {
    ...
    "新类别": "hwid_type_string",
}

# 新增需要跳过的类别（无 HWID 字段）
SKIP_CATEGORIES = {
    ...
    "新跳过类别",
}
```

---

## 📦 依赖

| 库 | 最低版本 | 用途 |
|----|----------|------|
| `PyQt6` | 6.4.0 | 桌面 UI 框架 |
| `openpyxl` | 3.1.0 | Excel 读写 |
| `PyYAML` | 6.0 | HWID YAML 解析 |

---

## 📝 FAQ

**Q: 上传 HWID 文件时解析失败？**  
A: 确认文件为纯文本 YAML 格式，包含 `encoded_fields:` 和 `components:` 字段。

**Q: EC Level 解析报错"找不到 KPL Sheet"？**  
A: Sheet 名称需包含 `KPL`（大小写不敏感），如 `S3A0 EC Level KPL`。

**Q: 某个国别显示 UNKNOWN_MAPPING？**  
A: 对照 `Region code list_v2.5a.xls`，然后在 `core/checker/region_checker.py` 的 `_COUNTRY_TO_HWID` 中添加该国别名称映射。

**Q: 想让某个 EC Level category 不出现在结果里？**  
A: 在 `core/mappings.py` 的 `SKIP_CATEGORIES` 集合中添加该类别（小写）。

**Q: Device 检查结果里出现大量 UNKNOWN_CATEGORY？**  
A: 在 `core/mappings.py` 的 `EC_CATEGORY_TO_HWID_TYPE` 中补充映射，或加入 `SKIP_CATEGORIES`。
