# 📋 HWID 9527 — 输入文件格式要求

> **版本：** v1.0  
> **适用工具：** HWID 9527  
> **用途：** 规范每个项目提交给 HWID 9527 工具的四份输入文件的命名和内部格式要求，以确保工具能正确识别和解析。

---

## ⚠️ 重要说明

工具严格按照以下规范进行解析。**任何偏差都可能导致解析失败或漏检**，请务必提前确认文件格式。

---

## 1. EC Level 文件（KPL）

### 1.1 文件命名

- 格式：`{项目名}_{其他描述}_EC Level*.xlsx`
- 示例：`MCB50_S3A0_EC Level 20260121.xlsx`
- 要求：文件名中必须可识别项目名（工具取文件名 stem 用于生成报告名称）

### 1.2 文件格式

工具现已支持两种常见的模板布局（自动自适应）：

- **Layout A（标准/合并单元格布局，如 Pujjoquince）**：
  - `Key Parts` 位于首列（Col 0），采用合并单元格方式。
  - 数据行起始于 Header 下方（数据行首列有 Category，同类别后续行首列为空）。
- **Layout B（分层行布局，如 Pujjolo）**：
  - `Key Parts` 列位于 Col 1，独立的一行作为分类标题（只有类别名，没有 LCFC PN）。
  - 分类下的具体物料行包含具体的料号（LCFC PN），该行 Col 1 为组件型号描述。

| 要求项 | 说明 |
|--------|------|
| **文件格式** | `.xlsx`（不支持 `.xls`） |
| **Sheet 名称** | 必须包含 `KPL` 或 `EC Level`（不区分大小写），工具自动识别 |
| **标题行** | 必须包含列名 `Key Parts` 和 `LCFC PN`，工具以此自动定位 Header Row |
| **数据识别** | 只要 `LCFC PN` 列包含有效料号即识别为物料数据行 |

### 1.3 必须包含的列

| 列名（不区分大小写） | 说明 | 是否必须 |
|-------------------|------|----------|
| `Key Parts` | 组件类别（Category） | ✅ 必须 |
| `Supplier` / `Vendor` | 供应商名称 | ✅ 必须 |
| `Description` | 组件描述 | ✅ 必须 |
| `LCFC PN` | LCFC 料号，作为与 AVL List 的关联主键 | ✅ 必须（缺失行自动跳过） |
| `LBG PN` / `Lenovo PN` | 联想料号 | 可选 |

### 1.4 Category 识别与映射规范

工具通过 `Key Parts` 列的类别名自动映射到 HWID Component Type：

| EC Level Category | 对应 HWID Type | 处理方式 |
|-------------------|---------------|----------|
| `CPU` | `cpu` | 检查 HWID |
| `Memory` / `RAM` / `DRAM` | `dram` | 检查 HWID |
| `Storage` / `UFS` / `SSD` / `eMMC` | `storage` | 检查 HWID |
| `WLAN` / `WiFi` / `Communication Card` | `wireless` | 检查 HWID |
| `WWAN` / `LTE` / `Cellular` | `cellular` | 检查 HWID |
| `Panel` / `Display` | `display_panel` | 检查 HWID |
| `Camera` / `IR Camera` | `camera` | 检查 HWID |
| `Battery` | `battery` | 检查 HWID |
| `Touchpad PCBA` / `Touchpad` / `Clickpad` | `touchpad` | 检查 HWID |
| `Finger Print` / `Fingerprint` | `fingerprint` | 检查 HWID |
| `KYB_NB` / `Keyboard` / `KB` | `None` | **自动跳过（HWID 无此项）** |
| `Thermal` / `Thermal Module` / `Fan` | `None` | **自动跳过** |
| `Adapter` / `Powercord` / `Power Cord` | `None` | **自动跳过** |
| `Antenna` / `WLAN Antenna` | `None` | **自动跳过** |
| `Speaker` | `None` | **自动跳过** |
| `Stylus` / `Stylus/PEN` / `Pen` | `None` | **自动跳过** |

> [!NOTE]
> 如 Category 名与上表不符，请告知 SWDE-SIE 团队更新映射表（`core/mappings.py`）。

---

## 2. AVL List 文件

### 2.1 文件命名

- 格式：`{项目名} AVL List*.xlsx`
- 示例：`Pujjoquince AVL List.xlsx`
- 要求：文件名中必须可识别项目名（工具取文件名 stem 用于生成报告名称）

### 2.2 文件格式

工具支持自动寻找表头行（自动扫描第一行包含 `LCFC PN` 的行作为 Header）：

| 要求项 | 说明 |
|--------|------|
| **文件格式** | `.xlsx`（不支持 `.xls`） |
| **Sheet 名称** | 必须包含 `AVL List` 或 `AVL`（不区分大小写） |
| **标题行** | 自动查找包含 `LCFC PN` 的行作为表头（支持位于 Row 0 或 Row 1） |
| **数据行** | 表头行之后的行，只要包含有效料号即被解析 |

### 2.3 必须包含的列（Header Row）

| 列名（关键词匹配，不区分大小写） | 说明 | 是否必须 |
|----------------------------------|------|----------|
| `Category` 或第 0 列 | 组件类别（自动查找含 Category 的列，未找到则取第 0 列） | ✅ 必须 |
| 含 `Vendor` | 供应商名称 | ✅ 必须 |
| 含 `MPN` | 制造商料号（用于 HWID DB 模糊匹配兜底） | ✅ 必须 |
| 含 `LCFC PN` | LCFC 料号，关联键 | ✅ 必须 |
| 含 `LNV PN` | Lenovo 料号 | 可选 |
| 含 `AVL Status` | AVL 审核状态，必须填写标准值 | ✅ 必须 |
| 含 `Google AVL Link` | Google AVL URL | ✅ 必须（QUALIFIED 条目必须填写） |

---

## 3. OD 文件（出货国别）

### 3.1 文件命名

- 格式：`*OD*.xlsx`
- 示例：`Lenovo Chrome 15ITN10 OD v4.4.0.xlsx` / `OD_500eGen5_v4.02.xlsx`

### 3.2 文件格式与支持布局

工具支持自动识别以下两种出货国家表布局（且自动适应前置是否存在空白列）：

- **Layout A（独立 Geo 与 Regions/Country 表头，如 Pujjoquince）**：
  - 表头行同时包含 `Geo` 与 `Regions`（或 `Country`）。
  - 工具自动定位这两列的实际位置（Geo 列向下填充，Regions 列为出货国家名）。
- **Layout B（矩阵/列表标记式，如 Pujjolo）**：
  - 表头无 `Geo` 列（为硬件射频配置列），国别列下混合了 Geo 分区标签与国家名称。
  - 工具自动探测国别数据列与后续的标记列。标记列有内容（如 `Yes`, `Yes, optional` 等）判定为出货国家；标记列为空判定为所属 Geo 分区标题。

| 要求项 | 说明 |
|--------|------|
| **文件格式** | `.xlsx` |
| **Sheet 名称** | 包含 `Country List` 或 `Country`（不区分大小写） |

### 3.3 国别名称规范

国别名称必须与 `Region code list_v2.5a.xls` 中的 Country 列一致（不区分大小写）。常见标准名称：

| 正确写法 | 对应 HWID Code(s) |
|---------|-------------------|
| Canada | ca.fr, ca.ansi, ca.hybrid |
| USA | us |
| UK | gb |
| Germany | de |
| France | fr |
| Japan | jp, jp.us |
| South Korea | kr |
| Türkiye / Turkiye | tr |
| Hong Kong / Hongkong | hk |
| ... | ... |

> [!WARNING]
> 如填写非标准名称（如 "United States" 而非 "USA"），会出现 `UNKNOWN_MAPPING`。请以 `Region code list_v2.5a.xls` 为准。

---

## 4. HWID Database 文件

### 4.1 文件命名

- 格式：`{项目名}.yaml` 或 `hwid_database.yaml`
- 示例：`pujjoquince.yaml`

### 4.2 文件格式

标准 Google HWID Database YAML 格式，工具读取以下字段：

```yaml
# Region 检查用
encoded_fields:
  region_field:
    - ca.fr
    - ca.ansi
    - ca.hybrid
    - us
    - ...

# Device 检查用
components:
  dram:
    dram_5199_15673:
      status: supported    # 或 unsupported
      values:
        part: "..."
  cpu:
    cpu_12345:
      status: supported
  ...
```

> [!IMPORTANT]
> - `region_field` 必须列出所有出货国别对应的 HWID region code
> - `components` 下每个 component 必须有 `status` 字段（`supported` 或 `unsupported`）

---

## 5. 项目名称命名约定

工具生成的报告名称（右上角 Project Name）格式为：

```
{EC Level 文件名第一段（第一个 _ 前）}_{HWID Database 文件名（不含扩展名）}
```

例如：  
EC Level: `MCB50_S3A0_EC Level 20260121.xlsx` → 取 `MCB50`  
HWID DB: `pujjoquince.yaml` → 取 `pujjoquince`  
→ **Project Name：`MCB50_pujjoquince`**

> [!NOTE]
> EC Level 文件名第一段即第一个 `_` 前的字符串，通常为项目代号。
> 请确保 EC Level 文件名以项目代号开头，例如 `MCB50_...`。

---

## 6. 常见问题

| 症状 | 可能原因 | 解决方法 |
|------|---------|---------|
| 解析失败 "Cannot find KPL sheet" | EC Level 中没有含 KPL 或 EC Level 的 sheet | 重命名 sheet |
| 解析失败 "Cannot find header row" | 标题行缺少 `Key Parts` 或 `LCFC PN` | 检查列名拼写 |
| 大量 `UNKNOWN_MAPPING` | OD 国别名不在映射表中 | 对照 Region code list_v2.5a.xls 修正 |
| 大量 `NOT_IN_AVL` | EC Level 和 AVL List 的 LCFC PN 对不上 | 检查两个文件的 LCFC PN 列是否一致 |
| 大量 `AVL_NOT_QUALIFIED` | AVL Status 列值不是 `QUALIFIED` | 确认 AVL 审核状态是否已更新 |
| `NO_AVL_ID` | QUALIFIED 条目未填 Google AVL URL | 补填 URL |
