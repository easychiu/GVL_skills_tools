# 🚀 GVL 裝備表 - 快速開始指南

## 5 分鐘快速上手

### 第 1 步：安裝依賴
```bash
cd /workspaces/GVL_skills_tools
pip install -r requirements.txt
```

### 第 2 步：選擇運行模式

#### 選項 A：使用網頁應用（推薦）
```bash
python main.py web
```
然後在瀏覽器中打開：
- 電腦本機：http://127.0.0.1:5000
- 手機同 Wi-Fi：http://<你的電腦IP>:5000

#### 選項 B：使用命令行工具
```bash
# 查看所有技能
python main.py cli list --skills

# 搜索特定裝備
python main.py cli search --name "戒指"

# 查找某項技能的裝備
python main.py cli search --skill "炮術" --min-level 2

# 查看預設配置
python main.py cli config --name "選單"

# 查看統計信息
python main.py cli stats
```

## 📊 Web 應用功能演示

### 1. 搜索頁籤
- **按名稱搜索**：輸入裝備名稱搜索
- **按技能搜索**：選擇技能和最小等級
- **按位置搜索**：選擇裝備位置

### 2. 裝備頁籤
- 瀏覽所有 68 件裝備
- 使用分頁瀏覽
- 查看每件裝備的技能加成

### 3. 配置頁籤
- 查看「選單」配置
- 查看「炮船範例」配置
- 了解預設裝備組合

### 4. 統計頁籤
- 查看總體數據統計
- 了解各位置的裝備分佈
- 查看技能種類

## 💡 常見使用場景

### 場景 1：構建最優配置
```bash
# 查找炮術技能最高的裝備
python main.py cli search --skill "炮術" --min-level 3
```

### 場景 2：快速查詢裝備
```bash
# 搜索特定名稱的裝備
python main.py cli search --name "護身符"
```

### 場景 3：查看某位置的所有選項
```bash
# 查看頭盔類型的所有裝備
python main.py cli search --position "頭盔"
```

### 場景 4：導出數據進行分析
```bash
# 將所有數據導出為 JSON
python main.py cli export --output my_gvl_data.json
```

## 🔧 CLI 命令完整參考

### 搜索命令
```bash
python main.py cli search [選項]

選項：
  --name, -n <名稱>          按裝備名稱搜索
  --skill, -s <技能名>       按技能搜索
  --min-level <等級>         技能最小等級（預設値: 1）
  --position, -p <位置>      按位置搜索
```

### 列表命令
```bash
python main.py cli list [選項]

選項：
  --positions, -p            顯示所有位置
  --skills, -s               顯示所有技能
  --equipment, -e            顯示所有裝備
```

### 配置命令
```bash
python main.py cli config --name <名稱>

名稱選項：
  選單
  炮船範例
```

### 統計命令
```bash
python main.py cli stats
```

### 導出命令
```bash
python main.py cli export [選項]

選項：
  --output, -o <檔名>        輸出 JSON 文件名（預設値: gvl_data.json）
```

## 🌐 Web 應用高級用法

### 自定義主機和端口
```bash
python main.py web --host 0.0.0.0 --port 8080
```

### 啟用調試模式（開發用）
```bash
python main.py web --debug
```

## 📈 數據統計

當前數據庫包含：
- **總裝備數**：68 件
- **位置類型**：11 種
  - 飾品、寶物、主武、副武、頭盔、衣服、手套、鞋子、職業、位置、角色上限
- **技能種類**：24 種
  - 炮術、水平射擊、速射、貫穿、彈道學、水雷、齊射、修理、掠奪、迴避、應急、手術、划船、劍術、突擊、戰術、射擊、防禦、識破、猛擊、迅捷、接舷、操舵、搜尋

## 🐛 常見問題

**Q: 如何停止 Web 應用？**  
A: 按 Ctrl+C

**Q: 如何改變 Web 應用的監聽端口？**  
A: 使用 `--port <端口號>` 參數

**Q: 能否在其他電腦上訪問 Web 應用？**  
A: 是的，使用 `python main.py web --host 0.0.0.0` 後，其他電腦可以通過 `http://<你的IP>:5000` 訪問

**Q: 如何匯出數據？**  
A: 使用 `python main.py cli export --output <檔名>.json`

## 📝 更新 Excel 數據後

1. 編輯 `GVL裝備表.xlsx` 文件
2. 保存文件
3. 重新啟動應用（應用會自動重新加載數據）

---

**需要更多幫助？**請查看完整文檔：[README_ZH.md](README_ZH.md)
