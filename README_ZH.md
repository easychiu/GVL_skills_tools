# GVL 裝備表系統

一個功能完整的 Python 應用，提供本地命令行工具和網頁介面，用於管理和查詢遊戲裝備配置。

## 功能特性

### 📊 核心功能
- **數據管理**: 讀取和解析 Excel 裝備表
- **多種搜索方式**: 按名稱、技能、位置查詢
- **預設配置**: 查看「選單」和「炮船範例」等預設配置
- **數據統計**: 完整的數據統計和分析
- **數據導出**: 支持導出為 JSON 格式

### 💻 命令行工具 (CLI)
```bash
python main.py cli search --name "戒指"
python main.py cli search --skill "炮術" --min-level 2
python main.py cli search --position "頭盔"
python main.py cli list --skills
python main.py cli list --positions
python main.py cli config --name "選單"
python main.py cli stats
python main.py cli export --output gvl_data.json
```

### 🌐 網頁應用
- 現代化的響應式 UI
- 多頁籤導航設計
- 實時搜索功能
- 裝備詳情展示
- 配置管理
- 數據統計面板

## 安裝指南

### 環境要求
- Python 3.8+
- pip (Python 包管理器)

### 安裝步驟

1. **克隆或進入項目目錄**
```bash
cd /workspaces/GVL_skills_tools
```

2. **安裝依賴**
```bash
pip install -r requirements.txt
```

3. **驗證 Excel 文件存在**
確保 `GVL裝備表.xlsx` 文件在項目根目錄

## 使用方法

### 方式 1: 啟動網頁應用

```bash
# 基本模式（本地訪問）
python main.py web

# 調試模式（自動重新加載）
python main.py web --debug

# 自定義端口
python main.py web --port 8080

# 完整參數
python main.py web --host 0.0.0.0 --port 8080 --debug
```

啟動後，訪問 http://127.0.0.1:5000

### 方式 2: 使用命令行工具

#### 搜索功能
```bash
# 按名稱搜索
python main.py cli search --name "戒指"

# 按技能搜索
python main.py cli search --skill "炮術" --min-level 2

# 按位置搜索
python main.py cli search --position "頭盔"
```

#### 列表功能
```bash
# 列出所有位置
python main.py cli list --positions

# 列出所有技能
python main.py cli list --skills

# 列出所有裝備
python main.py cli list --equipment
```

#### 配置功能
```bash
# 查看選單配置
python main.py cli config --name "選單"

# 查看炮船範例配置
python main.py cli config --name "炮船範例"
```

#### 統計和導出
```bash
# 查看統計信息
python main.py cli stats

# 導出為 JSON
python main.py cli export --output gvl_data.json
```

## 項目結構

```
GVL_skills_tools/
├── main.py                    # 主入口文件
├── requirements.txt           # 依賴列表
├── GVL裝備表.xlsx             # 源數據文件
├── README.md                  # 本文件
└── gvl_app/                   # 應用主目錄
    ├── data_handler.py        # 數據處理核心模塊
    ├── app.py                 # Flask Web 應用
    ├── cli.py                 # 命令行工具
    ├── templates/             # HTML 模板
    │   └── index.html         # 主頁模板
    └── static/                # 靜態文件
        ├── style.css          # 樣式文件
        └── script.js          # 前端腳本
```

## API 文檔

### RESTful API Endpoints

#### 搜索 API
- `GET /api/search?q=<query>&type=<type>&min_level=<level>`
  - type: `name` (按名稱), `skill` (按技能), `position` (按位置)

#### 裝備 API
- `GET /api/equipment?page=<page>&per_page=<per_page>` - 獲取裝備列表
- `GET /api/equipment/<name>` - 獲取裝備詳情

#### 配置 API
- `GET /api/config/<name>` - 獲取預設配置

#### 統計 API
- `GET /api/positions` - 獲取所有位置
- `GET /api/skills` - 獲取所有技能
- `GET /api/stats` - 獲取統計信息

## 技術棧

### 後端
- **Flask**: Web 框架
- **Pandas**: 數據處理
- **OpenPyXL**: Excel 文件解析

### 前端
- **HTML5**: 結構
- **CSS3**: 樣式（響應式設計）
- **JavaScript**: 交互和 API 調用

## 使用示例

### 示例 1: 查找所有包含"戒指"的裝備
```bash
python main.py cli search --name "戒指"
```

### 示例 2: 查找炮術技能等級 ≥ 2 的所有裝備
```bash
python main.py cli search --skill "炮術" --min-level 2
```

### 示例 3: 通過網頁應用查看所有選單配置
```bash
python main.py web
# 訪問 http://127.0.0.1:5000 → 點擊"配置"標籤 → 查看"選單"
```

### 示例 4: 導出所有數據為 JSON
```bash
python main.py cli export --output data.json
```

## 故障排除

### 問題 1: 找不到 Excel 文件
**解決**: 確保 `GVL裝備表.xlsx` 在項目根目錄，且文件名完全匹配

### 問題 2: 模塊未找到
**解決**: 重新安裝依賴
```bash
pip install -r requirements.txt
```

### 問題 3: 端口已被佔用
**解決**: 使用不同的端口
```bash
python main.py web --port 8080
```

### 問題 4: 編碼問題
**解決**: 確保系統支持 UTF-8 編碼

## 開發說明

### 擴展功能

#### 添加新的搜索類型
編輯 `gvl_app/data_handler.py` 中的 `GVLDataHandler` 類，添加新的搜索方法。

#### 自定義 UI
編輯 `gvl_app/static/style.css` 和 `gvl_app/templates/index.html`

#### 添加新的 API 端點
編輯 `gvl_app/app.py`，使用 Flask 的 `@app.route()` 裝飾器

## 許可証

MIT License

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 更新日誌

### v1.0.0 (2024)
- ✅ 完整的數據讀取和處理功能
- ✅ 命令行工具完整實現
- ✅ Web 應用完整實現
- ✅ 響應式網頁設計
- ✅ 多種搜索方式
- ✅ 數據導出功能

---

**最後更新**: 2024年4月

有問題或建議？歡迎反饋！
