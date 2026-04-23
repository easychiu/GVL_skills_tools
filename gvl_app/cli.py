"""GVL 裝備表命令行工具"""
import argparse
import sys
from pathlib import Path
from tabulate import tabulate
from data_handler import GVLDataHandler


class GVLCLIApp:
    """GVL裝備表命令行應用"""

    def __init__(self, excel_file: str):
        """初始化CLI應用
        
        Args:
            excel_file: Excel文件路徑
        """
        self.handler = GVLDataHandler(excel_file)

    def cmd_search(self, args):
        """搜索命令"""
        if args.name:
            results = self.handler.search_equipment(args.name)
            if results:
                print(f"\n搜索 '{args.name}' 的結果 ({len(results)} 件):")
                self._print_equipment_table(results)
            else:
                print(f"未找到包含 '{args.name}' 的裝備")
        
        if args.skill:
            results = self.handler.get_equipment_by_skill(args.skill, args.min_level)
            if results:
                print(f"\n技能 '{args.skill}' (最小等級 {args.min_level}) 的裝備 ({len(results)} 件):")
                self._print_equipment_table(results)
            else:
                print(f"未找到擁有技能 '{args.skill}' 的裝備")
        
        if args.position:
            results = self.handler.get_equipment_by_position(args.position)
            if results:
                print(f"\n位置 '{args.position}' 的裝備 ({len(results)} 件):")
                self._print_equipment_table(results)
            else:
                print(f"未找到位置 '{args.position}' 的裝備")

    def cmd_list(self, args):
        """列表命令"""
        if args.positions:
            print("\n所有位置:")
            for i, pos in enumerate(sorted(self.handler.positions), 1):
                count = len(self.handler.get_equipment_by_position(pos))
                print(f"  {i}. {pos} ({count} 件)")
        
        if args.skills:
            print("\n所有技能:")
            for i, skill in enumerate(sorted(self.handler.skills), 1):
                count = len(self.handler.get_equipment_by_skill(skill))
                print(f"  {i}. {skill} ({count} 件)")
        
        if args.equipment:
            print(f"\n所有裝備 (共 {len(self.handler.all_equipment)} 件):")
            self._print_equipment_table(self.handler.all_equipment[:20])
            if len(self.handler.all_equipment) > 20:
                print(f"\n... 還有 {len(self.handler.all_equipment) - 20} 件 ...")

    def cmd_config(self, args):
        """配置命令"""
        config = self.handler.get_config_by_name(args.name)
        if config:
            print(f"\n配置: {args.name}\n")
            for position, equipment_list in config.items():
                if equipment_list:
                    print(f"{position}:")
                    for eq in equipment_list:
                        if eq:
                            skills_str = ', '.join(
                                f"{skill}(+{level})" for skill, level in eq['skills'].items()
                            )
                            print(f"  - {eq['name']}: {skills_str if skills_str else '無技能加成'}")
                    print()
        else:
            print(f"配置 '{args.name}' 未找到")

    def cmd_stats(self, args):
        """統計命令"""
        stats = self.handler.get_stats_summary()
        print("\n" + "="*50)
        print("數據統計摘要")
        print("="*50)
        print(f"總裝備數: {stats['total_equipment']}")
        print(f"總位置數: {len(stats['positions'])}")
        print(f"總技能數: {len(stats['skills'])}")
        print("\n各位置的裝備數:")
        for pos in sorted(stats['positions']):
            count = stats['equipment_by_position'][pos]
            print(f"  {pos}: {count}")
        print("="*50 + "\n")

    def cmd_export(self, args):
        """導出命令"""
        self.handler.export_to_json(args.output)

    def _print_equipment_table(self, equipment_list):
        """以表格形式打印裝備"""
        if not equipment_list:
            print("沒有裝備")
            return
        
        table_data = []
        for eq in equipment_list:
            skills_str = ', '.join(
                f"{skill}(+{level})" for skill, level in eq['skills'].items()
            ) if eq['skills'] else "無"
            
            table_data.append([
                eq['position'],
                eq['name'],
                skills_str
            ])
        
        headers = ['位置', '裝備名稱', '技能加成']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
        print()


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='GVL 裝備表 - 命令行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 搜索裝備
  %(prog)s search --name "戒指"
  
  # 查找特定技能的裝備
  %(prog)s search --skill "炮術" --min-level 2
  
  # 查看特定位置的裝備
  %(prog)s search --position "頭盔"
  
  # 列出所有技能
  %(prog)s list --skills
  
  # 查看預設配置
  %(prog)s config --name "選單"
  
  # 查看數據統計
  %(prog)s stats
  
  # 導出數據為JSON
  %(prog)s export --output gvl_data.json
        """
    )
    
    # 查找Excel文件
    excel_file = Path(__file__).parent.parent / 'GVL裝備表.xlsx'
    if not excel_file.exists():
        print(f"錯誤: Excel文件未找到: {excel_file}")
        sys.exit(1)
    
    # 初始化CLI應用
    app = GVLCLIApp(str(excel_file))
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # search 子命令
    search_parser = subparsers.add_parser('search', help='搜索裝備')
    search_parser.add_argument('--name', '-n', help='按名稱搜索')
    search_parser.add_argument('--skill', '-s', help='按技能搜索')
    search_parser.add_argument('--min-level', type=int, default=1, help='最小技能等級')
    search_parser.add_argument('--position', '-p', help='按位置搜索')
    
    # list 子命令
    list_parser = subparsers.add_parser('list', help='列表查看')
    list_parser.add_argument('--positions', '-p', action='store_true', help='顯示所有位置')
    list_parser.add_argument('--skills', '-s', action='store_true', help='顯示所有技能')
    list_parser.add_argument('--equipment', '-e', action='store_true', help='顯示所有裝備')
    
    # config 子命令
    config_parser = subparsers.add_parser('config', help='查看預設配置')
    config_parser.add_argument('--name', '-n', choices=['選單', '炮船範例'], required=True, help='配置名稱')
    
    # stats 子命令
    stats_parser = subparsers.add_parser('stats', help='查看統計信息')
    
    # export 子命令
    export_parser = subparsers.add_parser('export', help='導出數據')
    export_parser.add_argument('--output', '-o', default='gvl_data.json', help='輸出文件名')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 執行相應的命令
    if args.command == 'search':
        if not any([args.name, args.skill, args.position]):
            search_parser.print_help()
        else:
            app.cmd_search(args)
    elif args.command == 'list':
        if not any([args.positions, args.skills, args.equipment]):
            list_parser.print_help()
        else:
            app.cmd_list(args)
    elif args.command == 'config':
        app.cmd_config(args)
    elif args.command == 'stats':
        app.cmd_stats(args)
    elif args.command == 'export':
        app.cmd_export(args)


if __name__ == '__main__':
    main()
