#!/bin/bash
# GVL 裝備表系統 - 快速啟動腳本

echo "🎮 GVL 裝備表系統 - 安裝和啟動"
echo "================================"
echo ""

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 錯誤: 未安裝 Python 3"
    exit 1
fi
echo "✓ Python 3 已找到: $(python3 --version)"

# 檢查 Excel 文件
if [ ! -f "GVL裝備表.xlsx" ]; then
    echo "❌ 錯誤: 未找到 GVL裝備表.xlsx"
    exit 1
fi
echo "✓ Excel 文件已找到"

# 安裝依賴
echo ""
echo "📦 安裝 Python 依賴..."
pip install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ 依賴安裝完成"
else
    echo "❌ 依賴安裝失敗"
    exit 1
fi

# 詢問用戶
echo ""
echo "選擇運行模式:"
echo "  1) Web 應用 (推薦) - 瀏覽器訪問"
echo "  2) CLI 工具 - 命令行工具"
echo "  3) 執行測試 - 驗證功能"
echo ""
read -p "請選擇 [1/2/3]: " choice

case $choice in
    1)
        echo ""
        echo "🚀 啟動 Web 應用..."
        echo "📍 訪問: http://127.0.0.1:5000"
        echo "⌨️  按 Ctrl+C 停止"
        echo ""
        python main.py web
        ;;
    2)
        echo ""
        echo "💻 CLI 工具 - 命令示例:"
        echo ""
        echo "  # 搜索裝備"
        echo "  python main.py cli search --name '戒指'"
        echo ""
        echo "  # 查找技能"
        echo "  python main.py cli search --skill '炮術' --min-level 2"
        echo ""
        echo "  # 查看配置"
        echo "  python main.py cli config --name '選單'"
        echo ""
        echo "  # 查看幫助"
        echo "  python main.py cli --help"
        echo ""
        read -p "輸入命令 (例如: search --name 戒指): " cmd
        python main.py cli $cmd
        ;;
    3)
        echo ""
        echo "🧪 運行測試..."
        python test_api.py
        ;;
    *)
        echo "❌ 無效選擇"
        exit 1
        ;;
esac
