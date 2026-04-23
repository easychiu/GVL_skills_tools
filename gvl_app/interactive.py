"""GVL 裝備表互動式配裝計算器（純 Python 終端版）"""
import sys
from pathlib import Path
from tabulate import tabulate
from data_handler import GVLDataHandler


class GVLInteractiveApp:
    """在終端機逐步引導用戶選擇職業與各部位裝備，最後計算並顯示技能總覽。"""

    def __init__(self, excel_file: str):
        self.handler = GVLDataHandler(excel_file)

    # ------------------------------------------------------------------
    # 主流程
    # ------------------------------------------------------------------

    def run(self):
        self._banner()
        while True:
            profession = self._pick_profession()
            is_sailor = self._pick_sailor()
            selected_names = self._pick_equipment_per_position()
            self._show_result(profession, selected_names, is_sailor)

            again = self._ask("\n重新計算? (y/n，預設 y): ", default='y')
            if again.lower() == 'n':
                print("\n感謝使用 GVL 配裝計算器！\n")
                break

    # ------------------------------------------------------------------
    # 輸入輔助
    # ------------------------------------------------------------------

    @staticmethod
    def _ask(prompt: str, default: str = '') -> str:
        """讀取一行輸入，若直接按 Enter 則傳回 default。"""
        try:
            raw = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
        return raw if raw else default

    @staticmethod
    def _pick_number(prompt: str, max_val: int) -> int:
        """反覆要求輸入，直到取得 0–max_val 之間的整數。"""
        while True:
            raw = GVLInteractiveApp._ask(prompt)
            if raw.isdigit():
                n = int(raw)
                if 0 <= n <= max_val:
                    return n
            print(f"  請輸入 0–{max_val} 之間的數字")

    # ------------------------------------------------------------------
    # 步驟 1：選擇職業
    # ------------------------------------------------------------------

    def _pick_profession(self) -> str:
        professions = sorted(self.handler.professions.keys())
        print("\n" + "=" * 50)
        print("【步驟 1】選擇職業")
        print("=" * 50)
        for i, name in enumerate(professions, 1):
            bonus = self.handler.professions[name]
            bonus_str = '  '.join(f"{k}+{v}" for k, v in bonus.items()) if bonus else "無額外加成"
            print(f"  {i:2d}. {name}（{bonus_str}）")

        n = self._pick_number(f"\n請輸入數字 (1–{len(professions)}): ", len(professions))
        # 0 視同 1（通用）
        if n == 0:
            n = 1
        chosen = professions[n - 1]
        print(f"  ✓ 已選擇職業：{chosen}")
        return chosen

    # ------------------------------------------------------------------
    # 步驟 2：航海士
    # ------------------------------------------------------------------

    def _pick_sailor(self) -> bool:
        print("\n" + "=" * 50)
        print("【步驟 2】航海士加成")
        print("=" * 50)
        if self.handler.sailor_skills:
            skills_str = '、'.join(sorted(self.handler.sailor_skills))
            print(f"  航海士可對以下技能各 +1：{skills_str}")
        ans = self._ask("  套用航海士 +1 加成? (y/n，預設 n): ", default='n')
        is_sailor = ans.lower() == 'y'
        print(f"  ✓ 航海士加成：{'是' if is_sailor else '否'}")
        return is_sailor

    # ------------------------------------------------------------------
    # 步驟 3：逐位置選裝備
    # ------------------------------------------------------------------

    def _pick_equipment_per_position(self):
        positions = sorted(self.handler.positions)
        selected_names = []

        print("\n" + "=" * 50)
        print("【步驟 3】逐部位選擇裝備（輸入 0 表示跳過該部位）")
        print("=" * 50)

        for pos in positions:
            candidates = sorted(
                self.handler.get_equipment_by_position(pos),
                key=lambda eq: eq['name']
            )
            if not candidates:
                continue

            print(f"\n▶ [{pos}]（共 {len(candidates)} 件）")
            print(f"  {'0':>3}. 跳過")
            for i, eq in enumerate(candidates, 1):
                skill_str = self._fmt_skills(eq['skills'])
                suffix = f"  [{skill_str}]" if skill_str else ""
                print(f"  {i:>3}. {eq['name']}{suffix}")

            n = self._pick_number(f"  請選擇 (0–{len(candidates)}): ", len(candidates))
            if n > 0:
                selected_names.append(candidates[n - 1]['name'])
                print(f"  ✓ {candidates[n - 1]['name']}")

        return selected_names

    # ------------------------------------------------------------------
    # 步驟 4：顯示結果
    # ------------------------------------------------------------------

    def _show_result(self, profession: str, equipment_names: list, is_sailor: bool):
        result = self.handler.calculate_character_skills(
            profession, equipment_names, is_sailor=is_sailor
        )

        print("\n" + "=" * 60)
        print("【計算結果】")
        print("=" * 60)

        # 已選裝備
        print(f"\n職業：{result['profession']}"
              + ("（+ 航海士加成）" if result['is_sailor'] else ""))
        print("\n已選裝備：")
        if result['selected_equipment']:
            for eq in result['selected_equipment']:
                print(f"  {eq['position']:<8} {eq['name']}")
        else:
            print("  （未選擇任何裝備）")

        if result['invalid_equipment']:
            print("\n警告：以下裝備名稱無法識別：",
                  '、'.join(result['invalid_equipment']))

        # 技能分項
        print()
        all_skills = sorted(
            set(result['equipment_skills'])
            | set(result['profession_bonus'])
            | set(result['sailor_bonus'])
            | set(result['skill_caps'])
            | set(result['highest_skills'])
        )

        if not all_skills:
            print("（所選裝備 / 職業無任何技能加成）")
            return

        table = []
        for skill in all_skills:
            eq_val = result['equipment_skills'].get(skill, 0)
            prof_val = result['profession_bonus'].get(skill, 0)
            sailor_val = result['sailor_bonus'].get(skill, 0)
            cap_val = result['skill_caps'].get(skill, 0)
            bonus_val = result['bonus_skills'].get(skill, 0)
            highest_val = result['highest_skills'].get(skill, 0)

            # 只顯示有值的行
            if highest_val == 0 and cap_val == 0:
                continue

            table.append([
                skill,
                eq_val or '-',
                prof_val or '-',
                sailor_val or '-',
                bonus_val or '-',
                cap_val or '-',
                highest_val or '-',
            ])

        headers = ['技能', '裝備', '職業', '航海士', '加成小計', '角色上限', '最高值']
        print(tabulate(table, headers=headers, tablefmt='grid'))

    # ------------------------------------------------------------------
    # 工具
    # ------------------------------------------------------------------

    @staticmethod
    def _fmt_skills(skills: dict) -> str:
        if not skills:
            return ''
        return ' '.join(f"{k}+{v}" for k, v in skills.items())

    @staticmethod
    def _banner():
        print("\n" + "=" * 60)
        print("  GVL 角色配裝計算器（純 Python 終端版）")
        print("=" * 60)
        print("  按 Ctrl+C 可隨時離開")
        print("=" * 60)


def main():
    excel_file = Path(__file__).parent.parent / 'GVL裝備表.xlsx'
    if not excel_file.exists():
        print(f"錯誤：找不到 Excel 檔案：{excel_file}")
        sys.exit(1)
    app = GVLInteractiveApp(str(excel_file))
    app.run()


if __name__ == '__main__':
    main()
