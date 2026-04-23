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

        # 按位置建立裝備下拉選單
        eq_by_pos: Dict[str, List[str]] = {}
        for pos in sorted(self.handler.positions):
            eq_by_pos[pos] = sorted(
                [eq['name'] for eq in self.handler.get_equipment_by_position(pos)]
            )

        for slot in self._build_slot_plan(eq_by_pos):
            var = tk.StringVar()
            self._slot_vars[slot['label']] = var
            parent = self._left_frame if slot['side'] == 'left' else self._right_frame

            lf = ttk.LabelFrame(parent, text=slot['label'], padding=4)
            lf.pack(fill='x', pady=3)

            choices = ['（不裝備）'] + slot['names']
            cb = ttk.Combobox(lf, textvariable=var, values=choices,
                              state='readonly', width=24)
            cb.current(0)
            cb.pack(fill='x')
            cb.bind('<<ComboboxSelected>>', self._on_change)

        self._on_change()

    def _build_slot_plan(self, eq_by_pos: Dict[str, List[str]]) -> List[dict]:
        slots = []
        for pos, names in eq_by_pos.items():
            count = 2 if pos in self.DUPLICATE else 1
            for i in range(1, count + 1):
                label = f'{pos}{i}' if count > 1 else pos
                side = self.SLOT_SIDE.get(label) or self.SLOT_SIDE.get(pos, 'right')
                slots.append({'position': pos, 'label': label,
                              'names': names, 'side': side})
        order_map = {s: i for i, s in enumerate(self.SLOT_ORDER)}
        slots.sort(key=lambda s: order_map.get(s['label'], 999))
        return slots

    def _on_change(self, _event=None):
        profession = self._prof_var.get()
        is_sailor = self._sailor_var.get()
        eq_names = [
            var.get() for var in self._slot_vars.values()
            if var.get() and var.get() != '（不裝備）'
        ]
        if not profession:
            return
        try:
            result = self.handler.calculate_character_skills(
                profession, eq_names, is_sailor=is_sailor
            )
            self._result_panel.update_results(result)
        except ValueError:
            pass


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
