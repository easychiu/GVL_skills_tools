"""GVL 裝備表 Tkinter 圖形化桌面應用"""
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Dict, List, Optional

# 允許從 repo 根目錄或 gvl_app/ 直接執行
_THIS_DIR = Path(__file__).parent
sys.path.insert(0, str(_THIS_DIR))

from data_handler import GVLDataHandler  # noqa: E402

# ─── 技能分類關鍵字 ───────────────────────────────────────────────────────
CANNON_KEYWORDS   = {'砲術', '水平', '彈道', '貫穿', '速射'}
BOARDING_KEYWORDS = {'突擊', '戰術', '射擊'}

# ─── 配色 ────────────────────────────────────────────────────────────────
COLORS = {
    'cannon':   {'bg': '#d0e8ff', 'alt': '#b8d4f5', 'bar': '#1d6bcc'},
    'boarding': {'bg': '#d4edda', 'alt': '#c0e0c8', 'bar': '#1e8a56'},
    'neutral':  {'bg': '#f0f0f0', 'alt': '#e4e4e4', 'bar': '#6b3db8'},
}

PRIMARY    = '#3a5caa'
HEADER_BG  = '#3a5caa'
HEADER_FG  = 'white'
APP_BG     = '#f5f7fa'

FONT_MAIN  = ('Microsoft YaHei', 10)
FONT_BOLD  = ('Microsoft YaHei', 10, 'bold')
FONT_TITLE = ('Microsoft YaHei', 14, 'bold')
FONT_HUGE  = ('Microsoft YaHei', 22, 'bold')


def classify_skill(skill_name: str) -> str:
    """判斷技能類型：cannon / boarding / neutral"""
    for k in CANNON_KEYWORDS:
        if k in skill_name:
            return 'cannon'
    for k in BOARDING_KEYWORDS:
        if k in skill_name:
            return 'boarding'
    return 'neutral'


# ─── ScrollableFrame ──────────────────────────────────────────────────────
class ScrollableFrame(tk.Frame):
    """帶垂直捲軸的容器框架"""

    def __init__(self, parent, bg: str = 'white', **kw):
        super().__init__(parent, bg=bg, **kw)
        self._canvas = tk.Canvas(self, bg=bg, borderwidth=0, highlightthickness=0)
        self._sb = ttk.Scrollbar(self, orient='vertical', command=self._canvas.yview)
        self.inner = tk.Frame(self._canvas, bg=bg)
        self._win_id = self._canvas.create_window((0, 0), window=self.inner, anchor='nw')

        self.inner.bind('<Configure>', self._on_inner_configure)
        self._canvas.bind('<Configure>', self._on_canvas_configure)
        self._canvas.configure(yscrollcommand=self._sb.set)

        self._canvas.pack(side='left', fill='both', expand=True)
        self._sb.pack(side='right', fill='y')

        self._canvas.bind('<Enter>', self._bind_wheel)
        self._canvas.bind('<Leave>', self._unbind_wheel)

    def _on_inner_configure(self, _e):
        self._canvas.configure(scrollregion=self._canvas.bbox('all'))

    def _on_canvas_configure(self, e):
        self._canvas.itemconfig(self._win_id, width=e.width)

    def _bind_wheel(self, _e):
        self._canvas.bind_all('<MouseWheel>', self._on_wheel)

    def _unbind_wheel(self, _e):
        self._canvas.unbind_all('<MouseWheel>')

    def _on_wheel(self, e):
        self._canvas.yview_scroll(-1 * (e.delta // 120), 'units')


# ─── SkillBarRow ──────────────────────────────────────────────────────────
class SkillBarRow(tk.Frame):
    """一行技能數據 + 右側進度條"""

    BAR_W = 170
    BAR_H = 18

    def __init__(self, parent, skill: str, eq: int, prof: int, sailor: int,
                 bonus: int, cap: int, high: int, max_high: int,
                 cat: str, alt: bool, **kw):
        bg = COLORS[cat]['alt'] if alt else COLORS[cat]['bg']
        super().__init__(parent, bg=bg, **kw)

        def _lbl(text, width, anchor='center'):
            tk.Label(self, text=str(text) if text else '-',
                     bg=bg, font=FONT_MAIN, width=width,
                     anchor=anchor).pack(side='left', padx=2, pady=4)

        _lbl(skill,     13, 'w')
        _lbl(eq or 0,    5)
        _lbl(prof or 0,  5)
        _lbl(sailor or 0, 5)
        _lbl(bonus or 0, 5)
        _lbl(cap or 0,   5)
        _lbl(high or 0,  5)

        # 進度條（Canvas）
        bar = tk.Canvas(self, width=self.BAR_W, height=self.BAR_H,
                        bg=bg, highlightthickness=0)
        bar.pack(side='left', padx=(4, 10), pady=4)
        fill_w = int((high / max_high) * self.BAR_W) if max_high > 0 else 0
        bar.create_rectangle(0, 0, self.BAR_W, self.BAR_H, fill='#d8d8d8', outline='')
        if fill_w > 0:
            bar.create_rectangle(0, 0, fill_w, self.BAR_H,
                                 fill=COLORS[cat]['bar'], outline='')
        # 數字標籤放在條內右側或條外
        tx = min(fill_w + 4, self.BAR_W - 28)
        bar.create_text(tx, self.BAR_H // 2, text=str(high),
                        anchor='w', font=FONT_BOLD, fill='#111111')


# ─── SkillResultPanel ─────────────────────────────────────────────────────
class SkillResultPanel(tk.Frame):
    """角色技能計算結果：表頭 + 可滾動技能行"""

    COL_DEFS = [
        ('技能',   13, 'w'),
        ('裝備',    5, 'center'),
        ('職業',    5, 'center'),
        ('航海士',  5, 'center'),
        ('加成',    5, 'center'),
        ('上限',    5, 'center'),
        ('最高值',  5, 'center'),
        ('進度條', 22, 'center'),
    ]

    def __init__(self, parent, **kw):
        super().__init__(parent, bg='white', **kw)
        self._build_header()
        self._scroll = ScrollableFrame(self, bg='white')
        self._scroll.pack(fill='both', expand=True)
        self._legend()

    def _build_header(self):
        hdr = tk.Frame(self, bg=HEADER_BG)
        hdr.pack(fill='x')
        for text, width, anchor in self.COL_DEFS:
            tk.Label(hdr, text=text, bg=HEADER_BG, fg=HEADER_FG,
                     font=FONT_BOLD, width=width, anchor=anchor
                     ).pack(side='left', padx=2, pady=6)

    def _legend(self):
        leg = tk.Frame(self, bg='white')
        leg.pack(fill='x', padx=4, pady=2)
        for cat, label in [('cannon', '■ 砲術系'), ('boarding', '■ 白兵系'), ('neutral', '■ 其他')]:
            tk.Label(leg, text=label, bg=COLORS[cat]['bg'],
                     fg='#2a2a2a', font=FONT_MAIN,
                     padx=8, pady=2, relief='flat').pack(side='left', padx=4)

    def update_results(self, data: dict):
        """刷新技能結果列表"""
        for w in self._scroll.inner.winfo_children():
            w.destroy()

        eq_s     = data.get('equipment_skills', {})
        prof_s   = data.get('profession_bonus', {})
        sailor_s = data.get('sailor_bonus', {})
        bonus_s  = data.get('bonus_skills', {})
        cap_s    = data.get('skill_caps', {})
        high_s   = data.get('highest_skills', {})

        all_skills = sorted(
            {k for k in list(eq_s) + list(prof_s) + list(sailor_s) + list(cap_s) + list(high_s)
             if high_s.get(k, 0) > 0 or cap_s.get(k, 0) > 0},
            key=lambda s: (-high_s.get(s, 0), s)
        )

        if not all_skills:
            tk.Label(self._scroll.inner, text='（尚未選擇裝備）',
                     bg='white', font=FONT_MAIN).pack(pady=20)
            return

        max_high = max((high_s.get(s, 0) for s in all_skills), default=1) or 1

        for i, skill in enumerate(all_skills):
            cat = classify_skill(skill)
            row = SkillBarRow(
                self._scroll.inner,
                skill=skill,
                eq=eq_s.get(skill, 0),
                prof=prof_s.get(skill, 0),
                sailor=sailor_s.get(skill, 0),
                bonus=bonus_s.get(skill, 0),
                cap=cap_s.get(skill, 0),
                high=high_s.get(skill, 0),
                max_high=max_high,
                cat=cat,
                alt=bool(i % 2),
            )
            row.pack(fill='x', pady=1)


# ─── CharacterTab ─────────────────────────────────────────────────────────
class CharacterTab(ttk.Frame):
    """角色配裝計算頁"""

    SLOT_ORDER = ['飾品1', '飾品2', '寶物1', '寶物2', '主武', '副武',
                  '頭盔', '衣服', '手套', '鞋子']
    SLOT_SIDE = {
        '飾品1': 'left', '飾品2': 'left',
        '寶物1': 'left', '寶物2': 'left',
        '主武':  'left', '副武':  'left',
        '頭盔':  'right', '衣服': 'right',
        '手套':  'right', '鞋子': 'right',
    }
    DUPLICATE = {'飾品', '寶物'}

    def __init__(self, parent, handler: GVLDataHandler):
        super().__init__(parent)
        self.handler = handler
        self._slot_vars: Dict[str, tk.StringVar] = {}
        # display_text → real equipment name, per slot
        self._slot_display_to_name: Dict[str, Dict[str, str]] = {}
        # skill hint label below each combobox
        self._slot_skill_labels: Dict[str, tk.Label] = {}
        # slot label → equipment position (for apply-plan logic)
        self._slot_positions: Dict[str, str] = {}
        # auto-build priority skill controls
        self._auto_skill_vars: List[tk.StringVar] = []
        self._auto_skill_cbs: List[ttk.Combobox] = []
        self._all_skills_sorted: List[str] = []
        self._build()
        self._load_options()

    def _build(self):
        # 頂部：職業 + 航海士
        ctrl = ttk.LabelFrame(self, text='角色設定', padding=8)
        ctrl.pack(fill='x', padx=10, pady=(10, 4))

        ttk.Label(ctrl, text='職業：').grid(row=0, column=0, sticky='w')
        self._prof_var = tk.StringVar()
        self._prof_cb = ttk.Combobox(ctrl, textvariable=self._prof_var,
                                     state='readonly', width=14)
        self._prof_cb.grid(row=0, column=1, padx=(4, 20))
        self._prof_cb.bind('<<ComboboxSelected>>', self._on_change)

        self._sailor_var = tk.BooleanVar()
        ttk.Checkbutton(ctrl, text='航海士（選單航海士技能 +1）',
                        variable=self._sailor_var,
                        command=self._on_change).grid(row=0, column=2, padx=4)

        self._sailor_hint = ttk.Label(ctrl, text='', foreground='gray')
        self._sailor_hint.grid(row=0, column=3, padx=(8, 0), sticky='w')

        # 自動配裝控制面板
        auto_lf = ttk.LabelFrame(self, text='⚡ 自動配裝', padding=8)
        auto_lf.pack(fill='x', padx=10, pady=(0, 4))

        for i in range(3):
            ttk.Label(auto_lf, text=f'優先 {i + 1}：').pack(
                side='left', padx=(16 if i > 0 else 0, 2))
            var = tk.StringVar()
            self._auto_skill_vars.append(var)
            cb = ttk.Combobox(auto_lf, textvariable=var, state='readonly', width=16)
            cb.pack(side='left')
            self._auto_skill_cbs.append(cb)
            cb.bind('<<ComboboxSelected>>', self._on_auto_skill_select)

        ttk.Button(auto_lf, text='🔧 自動配裝',
                   command=self._auto_build).pack(side='left', padx=(24, 0))

        # 中央：左欄 + 右欄 + 結果面板
        main = tk.Frame(self, bg=APP_BG)
        main.pack(fill='both', expand=True, padx=10, pady=4)

        # 左側裝備欄
        left_lf = ttk.LabelFrame(main, text='左側裝備', padding=8)
        left_lf.pack(side='left', fill='y', padx=(0, 4))
        self._left_frame = left_lf

        # 右側裝備欄
        right_lf = ttk.LabelFrame(main, text='右側裝備', padding=8)
        right_lf.pack(side='left', fill='y', padx=(0, 8))
        self._right_frame = right_lf

        # 技能結果
        result_lf = ttk.LabelFrame(main, text='技能分解總覽', padding=4)
        result_lf.pack(side='left', fill='both', expand=True)
        self._result_panel = SkillResultPanel(result_lf)
        self._result_panel.pack(fill='both', expand=True)

    def _load_options(self):
        # 職業
        profs = list(self.handler.get_professions().keys())
        self._prof_cb['values'] = profs
        if profs:
            self._prof_var.set(profs[0])

        # 航海士技能提示
        sailor_skills = sorted(self.handler.sailor_skills)
        if sailor_skills:
            self._sailor_hint.config(text='可加成：' + '、'.join(sailor_skills))

        # 按位置建立裝備物件列表（含技能）
        eq_by_pos: Dict[str, List[dict]] = {}
        for pos in sorted(self.handler.positions):
            eq_by_pos[pos] = sorted(
                self.handler.get_equipment_by_position(pos),
                key=lambda e: e['name']
            )

        for slot in self._build_slot_plan(eq_by_pos):
            var = tk.StringVar()
            self._slot_vars[slot['label']] = var
            self._slot_positions[slot['label']] = slot['position']
            parent = self._left_frame if slot['side'] == 'left' else self._right_frame

            lf = ttk.LabelFrame(parent, text=slot['label'], padding=4)
            lf.pack(fill='x', pady=3)

            # 建立顯示文字 → 真實名稱的對應表
            display_map: Dict[str, str] = {}
            choices = ['（不裝備）']
            for eq in slot['equipment']:
                skills = eq.get('skills', {})
                if skills:
                    skill_summary = ' '.join(
                        f"{k}+{v}"
                        for k, v in sorted(skills.items(), key=lambda x: -x[1])
                    )
                    display = f"{eq['name']}  [{skill_summary}]"
                else:
                    display = eq['name']
                choices.append(display)
                display_map[display] = eq['name']

            self._slot_display_to_name[slot['label']] = display_map

            cb = ttk.Combobox(lf, textvariable=var, values=choices,
                              state='readonly', width=36)
            cb.current(0)
            cb.pack(fill='x')

            # 技能詳情提示標籤
            skill_lbl = tk.Label(lf, text='', fg='#555555',
                                 bg='#f8f8f8', font=('Microsoft YaHei', 9),
                                 anchor='w', justify='left', wraplength=260)
            skill_lbl.pack(fill='x', padx=2)
            self._slot_skill_labels[slot['label']] = skill_lbl

            cb.bind('<<ComboboxSelected>>',
                    lambda e, lbl=slot['label'], sv=var, sl=skill_lbl, dm=display_map:
                    self._on_slot_change(lbl, sv, sl, dm))

        # 初始化自動配裝技能下拉選單
        self._all_skills_sorted = sorted(self.handler.skills)
        all_skills_dropdown = ['（不選）'] + self._all_skills_sorted
        for acb in self._auto_skill_cbs:
            acb['values'] = all_skills_dropdown
            acb.current(0)

        self._on_change()

    @staticmethod
    def _skills_detail_text(eq_name: str, display_map: Dict[str, str],
                            handler: 'GVLDataHandler') -> str:
        """根據顯示文字取得技能詳細說明（用於提示標籤）"""
        real_name = display_map.get(eq_name)
        if not real_name:
            return ''
        eq = handler.get_equipment_by_name(real_name)
        if not eq or not eq.get('skills'):
            return '無技能加成'
        parts = ', '.join(
            f"{k} +{v}"
            for k, v in sorted(eq['skills'].items(), key=lambda x: -x[1])
        )
        return f"技能：{parts}"

    def _on_slot_change(self, slot_label: str, sv: tk.StringVar,
                        skill_lbl: tk.Label, display_map: Dict[str, str],
                        _event=None):
        """單一槽位選擇改變：更新技能提示標籤，再重算總技能"""
        display = sv.get()
        if display and display != '（不裝備）':
            text = self._skills_detail_text(display, display_map, self.handler)
            skill_lbl.config(text=text)
        else:
            skill_lbl.config(text='')
        self._on_change()

    def _build_slot_plan(self, eq_by_pos: Dict[str, List[dict]]) -> List[dict]:
        slots = []
        for pos, equipment in eq_by_pos.items():
            count = 2 if pos in self.DUPLICATE else 1
            for i in range(1, count + 1):
                label = f'{pos}{i}' if count > 1 else pos
                side = self.SLOT_SIDE.get(label) or self.SLOT_SIDE.get(pos, 'right')
                slots.append({'position': pos, 'label': label,
                              'equipment': equipment, 'side': side})
        order_map = {s: i for i, s in enumerate(self.SLOT_ORDER)}
        slots.sort(key=lambda s: order_map.get(s['label'], 999))
        return slots

    def _on_change(self, _event=None):
        profession = self._prof_var.get()
        is_sailor = self._sailor_var.get()
        eq_names = []
        for slot_label, var in self._slot_vars.items():
            display = var.get()
            if display and display != '（不裝備）':
                # 從顯示文字還原真實裝備名稱
                real_name = self._slot_display_to_name.get(slot_label, {}).get(display, display)
                eq_names.append(real_name)
        if not profession:
            return
        try:
            result = self.handler.calculate_character_skills(
                profession, eq_names, is_sailor=is_sailor
            )
            self._result_panel.update_results(result)
        except ValueError:
            pass

    def _on_auto_skill_select(self, _event=None):
        """更新自動配裝技能下拉選單，防止重複選擇"""
        all_skills = self._all_skills_sorted
        for i, (acb, var) in enumerate(zip(self._auto_skill_cbs, self._auto_skill_vars)):
            current = var.get()
            others_selected = {
                v.get() for j, v in enumerate(self._auto_skill_vars)
                if j != i and v.get() and v.get() != '（不選）'
            }
            available = ['（不選）'] + [s for s in all_skills if s not in others_selected]
            acb['values'] = available
            if current and current not in available:
                var.set('（不選）')

    def _auto_build(self):
        """執行自動配裝並顯示結果對話視窗"""
        profession = self._prof_var.get()
        if not profession:
            messagebox.showwarning('警告', '請先選擇職業')
            return

        priority_skills = [
            v.get() for v in self._auto_skill_vars
            if v.get() and v.get() != '（不選）'
        ]
        if not priority_skills:
            messagebox.showwarning('警告', '請至少選擇一個優先技能')
            return

        is_sailor = self._sailor_var.get()
        try:
            plans = self.handler.suggest_builds(
                profession, priority_skills, is_sailor=is_sailor, top_n=5
            )
        except Exception as exc:
            messagebox.showerror('錯誤', str(exc))
            return

        if not plans:
            messagebox.showinfo('自動配裝', '找不到符合條件的配裝方案')
            return

        AutoBuildDialog(self, plans, priority_skills, self._apply_plan)

    def _apply_plan(self, equipment_names: List[str]):
        """將自動配裝方案套用至各槽位"""
        # 建立位置 → 裝備名稱清單的映射
        pos_to_names: Dict[str, List[str]] = {}
        for name in equipment_names:
            eq = self.handler.get_equipment_by_name(name)
            if eq:
                pos_to_names.setdefault(eq['position'], []).append(name)

        # 預先建立各槽位的反向對應表（顯示文字 ← 真實名稱）
        slot_inv_maps: Dict[str, Dict[str, str]] = {
            slot_label: {v: k for k, v in dm.items()}
            for slot_label, dm in self._slot_display_to_name.items()
        }

        # 記錄每個位置已分配的索引
        pos_assigned: Dict[str, int] = {}

        for slot_label, var in self._slot_vars.items():
            pos = self._slot_positions.get(slot_label, '')
            names_for_pos = pos_to_names.get(pos, [])
            idx = pos_assigned.get(pos, 0)

            if idx < len(names_for_pos):
                real_name = names_for_pos[idx]
                pos_assigned[pos] = idx + 1

                # 找出對應的顯示文字
                display = slot_inv_maps.get(slot_label, {}).get(real_name, '（不裝備）')
                var.set(display)

                # 更新技能提示標籤
                skill_lbl = self._slot_skill_labels.get(slot_label)
                if skill_lbl:
                    display_map = self._slot_display_to_name.get(slot_label, {})
                    text = self._skills_detail_text(display, display_map, self.handler)
                    skill_lbl.config(text=text)
            else:
                var.set('（不裝備）')
                skill_lbl = self._slot_skill_labels.get(slot_label)
                if skill_lbl:
                    skill_lbl.config(text='')

        self._on_change()


# ─── AutoBuildDialog ──────────────────────────────────────────────────────
class AutoBuildDialog(tk.Toplevel):
    """自動配裝結果對話視窗：顯示 Top-N 套方案，可一鍵套用至角色配裝頁"""

    def __init__(self, parent, plans: List[Dict], priority_skills: List[str],
                 apply_callback):
        super().__init__(parent)
        self.plans = plans
        self.apply_callback = apply_callback
        self.title('⚡ 自動配裝結果')
        self.geometry('1020x480')
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self._build(priority_skills)

    def _build(self, priority_skills: List[str]):
        # 頁首
        hdr = tk.Frame(self, bg=HEADER_BG)
        hdr.pack(fill='x')
        p_text = ' ＞ '.join(priority_skills) if priority_skills else '（無優先技能）'
        tk.Label(hdr,
                 text=f'優先技能：{p_text}　　共 {len(self.plans)} 套方案',
                 bg=HEADER_BG, fg=HEADER_FG, font=FONT_BOLD,
                 pady=8).pack()

        # 方案表格
        lf = ttk.LabelFrame(self, text='配裝方案（雙擊或選中後點「套用」）', padding=8)
        lf.pack(fill='both', expand=True, padx=10, pady=8)

        p_cols = list(priority_skills)
        cols = ['方案'] + p_cols + ['裝備清單']
        self._tree = ttk.Treeview(lf, columns=cols, show='headings', height=10)

        self._tree.heading('方案', text='方案')
        self._tree.column('方案', width=60, minwidth=50, anchor='center')

        for ps in p_cols:
            self._tree.heading(ps, text=ps)
            self._tree.column(ps, width=100, minwidth=70, anchor='center')

        self._tree.heading('裝備清單', text='裝備清單')
        self._tree.column('裝備清單', width=680, minwidth=200)

        sb_y = ttk.Scrollbar(lf, command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb_y.set)
        self._tree.pack(side='left', fill='both', expand=True)
        sb_y.pack(side='right', fill='y')

        for i, plan in enumerate(self.plans):
            pv = plan['priority_values']
            p_vals = [str(pv.get(ps, 0)) for ps in p_cols]
            eq_list = '、'.join(plan['equipment_names'])
            self._tree.insert('', 'end', iid=str(i),
                              values=[f'方案 {i + 1}'] + p_vals + [eq_list])

        # 預設選中第一筆
        if self.plans:
            self._tree.selection_set('0')
            self._tree.focus('0')

        self._tree.bind('<Double-1>', lambda _e: self._apply_selected())

        # 底部按鈕列
        btn_row = tk.Frame(self)
        btn_row.pack(fill='x', padx=10, pady=(0, 10))

        ttk.Button(btn_row, text='✔ 套用選中方案',
                   command=self._apply_selected).pack(side='left', padx=4)
        ttk.Button(btn_row, text='✖ 關閉',
                   command=self.destroy).pack(side='left', padx=4)
        ttk.Label(btn_row, text='提示：可雙擊方案快速套用',
                  foreground='gray').pack(side='left', padx=16)

    def _apply_selected(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning('警告', '請先選擇一個方案', parent=self)
            return
        idx = int(sel[0])
        self.apply_callback(self.plans[idx]['equipment_names'])
        self.destroy()


# ─── SearchTab ────────────────────────────────────────────────────────────
class SearchTab(ttk.Frame):
    """搜索頁"""

    def __init__(self, parent, handler: GVLDataHandler):
        super().__init__(parent)
        self.handler = handler
        self._build()

    def _build(self):
        ctrl = ttk.LabelFrame(self, text='搜索條件', padding=10)
        ctrl.pack(fill='x', padx=10, pady=10)

        # 按名稱
        row1 = ttk.Frame(ctrl)
        row1.pack(fill='x', pady=4)
        ttk.Label(row1, text='名稱：').pack(side='left')
        self._name_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self._name_var, width=24).pack(side='left', padx=4)
        ttk.Button(row1, text='搜索名稱', command=self._search_name).pack(side='left')

        # 按技能
        row2 = ttk.Frame(ctrl)
        row2.pack(fill='x', pady=4)
        ttk.Label(row2, text='技能：').pack(side='left')
        self._skill_var = tk.StringVar()
        ttk.Combobox(row2, textvariable=self._skill_var,
                     values=sorted(self.handler.skills),
                     state='readonly', width=18).pack(side='left', padx=4)
        ttk.Label(row2, text='最小等級：').pack(side='left', padx=(8, 0))
        self._minlv_var = tk.IntVar(value=1)
        ttk.Spinbox(row2, textvariable=self._minlv_var, from_=1, to=99,
                    width=5).pack(side='left', padx=4)
        ttk.Button(row2, text='搜索技能', command=self._search_skill).pack(side='left')

        # 按位置
        row3 = ttk.Frame(ctrl)
        row3.pack(fill='x', pady=4)
        ttk.Label(row3, text='位置：').pack(side='left')
        self._pos_var = tk.StringVar()
        ttk.Combobox(row3, textvariable=self._pos_var,
                     values=sorted(self.handler.positions),
                     state='readonly', width=18).pack(side='left', padx=4)
        ttk.Button(row3, text='搜索位置', command=self._search_position).pack(side='left')

        # 結果表格
        result_lf = ttk.LabelFrame(self, text='搜索結果', padding=8)
        result_lf.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        cols = ('位置', '裝備名稱', '技能加成')
        self._tree = ttk.Treeview(result_lf, columns=cols, show='headings', height=20)
        self._tree.heading('位置',     text='位置')
        self._tree.heading('裝備名稱', text='裝備名稱')
        self._tree.heading('技能加成', text='技能加成')
        self._tree.column('位置',     width=80,  minwidth=60)
        self._tree.column('裝備名稱', width=180, minwidth=120)
        self._tree.column('技能加成', width=500, minwidth=200)

        sb = ttk.Scrollbar(result_lf, command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')

    def _display(self, results: List[dict]):
        self._tree.delete(*self._tree.get_children())
        for eq in results:
            skills_str = ', '.join(f"{k}(+{v})" for k, v in eq['skills'].items()) or '無'
            self._tree.insert('', 'end', values=(eq['position'], eq['name'], skills_str))

    def _search_name(self):
        kw = self._name_var.get().strip()
        if kw:
            self._display(self.handler.search_equipment(kw))

    def _search_skill(self):
        skill = self._skill_var.get()
        if skill:
            self._display(self.handler.get_equipment_by_skill(skill, self._minlv_var.get()))

    def _search_position(self):
        pos = self._pos_var.get()
        if pos:
            self._display(self.handler.get_equipment_by_position(pos))


# ─── EquipmentTab ─────────────────────────────────────────────────────────
class EquipmentTab(ttk.Frame):
    """所有裝備列表頁（分頁）"""

    PER_PAGE = 30

    def __init__(self, parent, handler: GVLDataHandler):
        super().__init__(parent)
        self.handler = handler
        self._page = 0
        self._pages = 1
        self._build()
        self._load()

    def _build(self):
        info_bar = ttk.Frame(self)
        info_bar.pack(fill='x', padx=10, pady=8)
        self._info_lbl = ttk.Label(info_bar, text='', font=FONT_BOLD)
        self._info_lbl.pack(side='left')

        lf = ttk.LabelFrame(self, text='所有裝備', padding=8)
        lf.pack(fill='both', expand=True, padx=10)

        cols = ('位置', '裝備名稱', '技能加成')
        self._tree = ttk.Treeview(lf, columns=cols, show='headings', height=25)
        for col in cols:
            self._tree.heading(col, text=col)
        self._tree.column('位置',     width=80)
        self._tree.column('裝備名稱', width=180)
        self._tree.column('技能加成', width=520)

        sb = ttk.Scrollbar(lf, command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')

        pg = ttk.Frame(self)
        pg.pack(fill='x', padx=10, pady=8)
        ttk.Button(pg, text='‹ 上一頁', command=self._prev).pack(side='left')
        self._pg_lbl = ttk.Label(pg, text='', font=FONT_BOLD)
        self._pg_lbl.pack(side='left', padx=14)
        ttk.Button(pg, text='下一頁 ›', command=self._next).pack(side='left')

    def _load(self):
        all_eq = self.handler.all_equipment
        total  = len(all_eq)
        self._pages = max(1, (total + self.PER_PAGE - 1) // self.PER_PAGE)
        start  = self._page * self.PER_PAGE
        end    = start + self.PER_PAGE

        self._tree.delete(*self._tree.get_children())
        for eq in all_eq[start:end]:
            skills_str = ', '.join(f"{k}(+{v})" for k, v in eq['skills'].items()) or '無'
            self._tree.insert('', 'end', values=(eq['position'], eq['name'], skills_str))

        self._info_lbl.config(text=f'共 {total} 件裝備')
        self._pg_lbl.config(text=f'第 {self._page + 1} / {self._pages} 頁')

    def _prev(self):
        if self._page > 0:
            self._page -= 1
            self._load()

    def _next(self):
        if self._page < self._pages - 1:
            self._page += 1
            self._load()


# ─── StatsTab ─────────────────────────────────────────────────────────────
class StatsTab(ttk.Frame):
    """數據統計頁"""

    def __init__(self, parent, handler: GVLDataHandler):
        super().__init__(parent)
        self.handler = handler
        self._build()

    def _build(self):
        stats = self.handler.get_stats_summary()

        # 摘要卡片
        card_frame = tk.Frame(self, bg=APP_BG)
        card_frame.pack(fill='x', padx=10, pady=12)

        for label, val in [
            ('總裝備數',  stats['total_equipment']),
            ('位置類型',  len(stats['positions'])),
            ('技能種類',  len(stats['skills'])),
        ]:
            card = tk.Frame(card_frame, bg='white',
                            relief='groove', bd=1)
            card.pack(side='left', padx=8, pady=4, ipadx=18, ipady=10)
            tk.Label(card, text=str(val), font=FONT_HUGE,
                     fg=PRIMARY, bg='white').pack()
            tk.Label(card, text=label, font=FONT_MAIN,
                     fg='#555', bg='white').pack()

        # 各位置裝備數
        lf = ttk.LabelFrame(self, text='各位置裝備數', padding=8)
        lf.pack(fill='both', expand=True, padx=10, pady=4)

        cols = ('位置', '裝備數量')
        tree = ttk.Treeview(lf, columns=cols, show='headings', height=15)
        tree.heading('位置',   text='位置')
        tree.heading('裝備數量', text='裝備數量')
        tree.column('位置',   width=180)
        tree.column('裝備數量', width=100)

        for pos, count in sorted(stats['equipment_by_position'].items()):
            tree.insert('', 'end', values=(pos, f'{count} 件'))

        sb = ttk.Scrollbar(lf, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')


# ─── GVLApp 主視窗 ─────────────────────────────────────────────────────────
class GVLApp(tk.Tk):
    """GVL 裝備表桌面應用主視窗"""

    def __init__(self, excel_path: str):
        super().__init__()
        self.title('⚔️ GVL 裝備表系統')
        self.geometry('1280x780')
        self.minsize(960, 620)
        self.configure(bg=APP_BG)

        # ttk 主題
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure('TNotebook.Tab', font=FONT_BOLD, padding=[12, 6])
        style.configure('TLabelframe.Label', font=FONT_BOLD)

        # 讀取資料
        try:
            self.handler = GVLDataHandler(excel_path)
        except Exception as exc:
            messagebox.showerror('載入失敗', f'無法讀取裝備表：{exc}')
            self.destroy()
            return

        # 頁首
        hdr = tk.Frame(self, bg=PRIMARY)
        hdr.pack(fill='x')
        tk.Label(hdr, text='⚔️  GVL 裝備表系統',
                 bg=PRIMARY, fg='white', font=FONT_TITLE,
                 pady=10).pack()
        tk.Label(hdr, text='大航海時代遊戲裝備配置工具',
                 bg=PRIMARY, fg='#c0d0ff', font=FONT_MAIN,
                 pady=4).pack()

        # 分頁標籤
        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True)

        nb.add(SearchTab(nb, self.handler),    text='  🔍 搜索  ')
        nb.add(EquipmentTab(nb, self.handler), text='  🗡️ 裝備  ')
        nb.add(CharacterTab(nb, self.handler), text='  👤 角色配裝  ')
        nb.add(StatsTab(nb, self.handler),     text='  📊 統計  ')


# ─── 入口 ────────────────────────────────────────────────────────────────
def run_gui(excel_path: Optional[str] = None):
    """啟動 tkinter GUI 桌面應用"""
    if excel_path is None:
        excel_path = str(Path(__file__).parent.parent / 'GVL裝備表.xlsx')
    app = GVLApp(excel_path)
    app.mainloop()


if __name__ == '__main__':
    run_gui()
