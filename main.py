#!/usr/bin/env python3
"""GVL 裝備表系統主入口"""
import sys
import argparse
from pathlib import Path

# 添加gvl_app到路徑
sys.path.insert(0, str(Path(__file__).parent / 'gvl_app'))


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='GVL 裝備表系統 - 本地工具和網頁應用',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 啟動圖形化桌面應用（tkinter GUI）
  python main.py gui

  # 互動式配裝計算器
  python main.py interactive

  # 啟動網頁應用
  python main.py web
  
  # 運行CLI工具
  python main.py cli search --name "戒指"
  python main.py cli list --skills
  python main.py cli config --name "選單"
        """
    )
    
    subparsers = parser.add_subparsers(dest='mode', help='運行模式')

    # gui 子命令
    subparsers.add_parser('gui', help='啟動圖形化桌面應用（tkinter GUI）')

    # interactive 子命令
    subparsers.add_parser('interactive', help='互動式配裝計算器（純 Python 終端版）')
    
    # web 子命令
    web_parser = subparsers.add_parser('web', help='啟動網頁應用')
    web_parser.add_argument('--host', '-H', default='127.0.0.1', help='監聽地址')
    web_parser.add_argument('--port', '-P', type=int, default=5000, help='監聽端口')
    web_parser.add_argument('--debug', '-d', action='store_true', help='調試模式')
    
    # cli 子命令
    cli_parser = subparsers.add_parser('cli', help='運行命令行工具')
    cli_subparsers = cli_parser.add_subparsers(dest='command', required=True)
    
    # cli search
    search_parser = cli_subparsers.add_parser('search', help='搜索裝備')
    search_parser.add_argument('--name', '-n', help='按名稱搜索')
    search_parser.add_argument('--skill', '-s', help='按技能搜索')
    search_parser.add_argument('--min-level', type=int, default=1, help='最小技能等級')
    search_parser.add_argument('--position', '-p', help='按位置搜索')
    
    # cli list
    list_parser = cli_subparsers.add_parser('list', help='列表查看')
    list_parser.add_argument('--positions', '-p', action='store_true', help='顯示所有位置')
    list_parser.add_argument('--skills', '-s', action='store_true', help='顯示所有技能')
    list_parser.add_argument('--equipment', '-e', action='store_true', help='顯示所有裝備')
    
    # cli config
    config_parser = cli_subparsers.add_parser('config', help='查看預設配置')
    config_parser.add_argument('--name', '-n', choices=['選單', '炮船範例'], required=True, help='配置名稱')
    
    # cli stats
    cli_subparsers.add_parser('stats', help='查看統計信息')
    
    # cli export
    export_parser = cli_subparsers.add_parser('export', help='導出數據')
    export_parser.add_argument('--output', '-o', default='gvl_data.json', help='輸出文件名')
    
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        sys.exit(0)

    if args.mode == 'gui':
        from gui import run_gui
        excel_file = Path(__file__).parent / 'GVL裝備表.xlsx'
        if not excel_file.exists():
            print(f"錯誤: Excel文件未找到: {excel_file}")
            sys.exit(1)
        run_gui(str(excel_file))

    elif args.mode == 'interactive':
        from interactive import GVLInteractiveApp
        excel_file = Path(__file__).parent / 'GVL裝備表.xlsx'
        if not excel_file.exists():
            print(f"錯誤: Excel文件未找到: {excel_file}")
            sys.exit(1)
        GVLInteractiveApp(str(excel_file)).run()

    elif args.mode == 'web':
        # 啟動網頁應用
        from app import app
        print("\n" + "="*60)
        print("🚀 GVL 裝備表 Web 應用已啟動")
        print("="*60)
        print(f"📍 本地位址: http://{args.host}:{args.port}")
        print(f"🛠️  模式: {'調試' if args.debug else '生產'}")
        print("✋ 按 Ctrl+C 停止服務器")
        print("="*60 + "\n")
        
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
    
    elif args.mode == 'cli':
        # 運行CLI工具
        from cli import GVLCLIApp
        
        excel_file = Path(__file__).parent / 'GVL裝備表.xlsx'
        if not excel_file.exists():
            print(f"錯誤: Excel文件未找到: {excel_file}")
            sys.exit(1)
        
        cli_app = GVLCLIApp(str(excel_file))
        
        if args.command == 'search':
            if not any([args.name, args.skill, args.position]):
                search_parser.print_help()
            else:
                cli_app.cmd_search(args)
        elif args.command == 'list':
            if not any([args.positions, args.skills, args.equipment]):
                list_parser.print_help()
            else:
                cli_app.cmd_list(args)
        elif args.command == 'config':
            cli_app.cmd_config(args)
        elif args.command == 'stats':
            cli_app.cmd_stats(args)
        elif args.command == 'export':
            cli_app.cmd_export(args)


if __name__ == '__main__':
    main()
