# GVL 裝備表系統

一個完整的 Python 應用，提供本地命令行工具和現代化網頁介面，用於管理和查詢遊戲裝備配置。

## 🚀 快速開始

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 啟動應用

**Web 應用（推薦）**
```bash
python main.py web
# 訪問 http://127.0.0.1:5000
```

**或使用 CLI 工具**
```bash
python main.py cli search --name "戒指"
python main.py cli search --skill "炮術" --min-level 2
python main.py cli config --name "選單"
```

## 📖 文檔

- [中文詳細文檔](README_ZH.md) - 完整功能說明
- [快速開始指南](QUICKSTART_ZH.md) - 5分鐘快速上手
- [項目概覽](PROJECT_SUMMARY_ZH.md) - 技術和架構詳情

## ✨ 功能特性

### 🌐 Web 應用
- 搜索、分頁瀏覽
- 配置管理
- 數據統計
- 響應式設計

### 💻 CLI 工具
- 按名稱/技能/位置搜索
- 列表查看
- 配置預覽
- JSON 導出

### 🔧 API
- 7 個 RESTful 端點
- JSON 數據格式
- 完整的搜索功能

## 📊 數據

- **總裝備數**: 68 件
- **位置類型**: 11 種
- **技能種類**: 24 種