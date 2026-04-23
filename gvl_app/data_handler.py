"""GVL 裝備表數據處理模塊"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import json


class GVLDataHandler:
    """GVL裝備表數據處理類"""
    HEADER_EQUIPMENT_NAME = '裝備名稱'

    def __init__(self, excel_file: str):
        """初始化數據處理器
        
        Args:
            excel_file: Excel文件路徑
        """
        self.excel_file = excel_file
        self.data = {}
        self.all_equipment = []
        self.positions = set()
        self.skills = set()
        self.professions = {}
        self.skill_caps = {}
        self.sailor_skills = set()
        # 系統列標記：重複標題（位置=位置）與非裝備資料（職業、角色上限）皆需排除
        self.system_positions = {'位置', '職業', '角色上限'}
        self.load_data()

    def load_data(self):
        """從Excel文件加載數據"""
        try:
            # 讀取三個sheet
            self.data['menu'] = pd.read_excel(self.excel_file, sheet_name='選單')
            self.data['cannon_example'] = pd.read_excel(
                self.excel_file, sheet_name='炮船範例'
            )
            self.data['source'] = pd.read_excel(
                self.excel_file, sheet_name='資料源(請謹慎編輯)'
            )
            
            # 提取技能列表（除了位置和裝備名稱）
            cols = self.data['source'].columns.tolist()
            self.skills = set(cols[2:])  # 跳過前兩列
            
            # 提取所有可裝備位置（排除系統行）
            self.positions = set(
                pos for pos in self.data['source']['位置'].dropna().unique()
                if pos not in self.system_positions
            )
            
            # 建立所有裝備的完整清單
            self._build_equipment_list()
            self.professions = self._load_professions_from_source()
            self.skill_caps = self._load_skill_caps_from_source()
            self.sailor_skills = self._load_sailor_skills_from_menu()
            
            print(f"✓ 成功加載數據")
            print(f"  - 位置類型: {len(self.positions)}")
            print(f"  - 技能數量: {len(self.skills)}")
            print(f"  - 裝備總數: {len(self.all_equipment)}")
            
        except Exception as e:
            print(f"✗ 加載數據失敗: {e}")
            raise

    def _build_equipment_list(self):
        """構建所有裝備的列表"""
        self.all_equipment = []
        df = self.data['source'].copy()
        
        # 移除空行和標題行
        df = df.dropna(subset=['裝備名稱'])
        # 移除包含技能名稱作為值的行（通常是複製的標題）
        df = df[df['裝備名稱'] != self.HEADER_EQUIPMENT_NAME]
        
        for _, row in df.iterrows():
            try:
                position = row['位置']
                name = row['裝備名稱']
                
                # 跳過無效數據
                if pd.isna(position) or pd.isna(name):
                    continue
                if position in self.system_positions:
                    continue
                
                equipment = {
                    'position': position,
                    'name': name,
                    'skills': {}
                }
                
                # 提取技能信息
                for skill in self.skills:
                    if skill in row:
                        val = row[skill]
                        if pd.notna(val):
                            try:
                                level = int(val)
                                equipment['skills'][skill] = level
                            except (ValueError, TypeError):
                                # 無法轉換為整數，跳過此技能
                                pass
                
                self.all_equipment.append(equipment)
            except Exception as e:
                # 跳過有問題的行
                continue

    def _extract_skill_values(self, row: pd.Series) -> Dict[str, int]:
        """從資料列提取技能值"""
        skill_values = {}
        for skill in self.skills:
            if skill not in row:
                continue
            value = row[skill]
            if pd.isna(value):
                continue
            try:
                level = int(value)
            except (ValueError, TypeError):
                continue
            if level > 0:
                skill_values[skill] = level
        return skill_values

    def _load_professions_from_source(self) -> Dict[str, Dict[str, int]]:
        """從資料源位置=職業載入職業技能加成"""
        df = self.data['source']
        profession_rows = df[df['位置'] == '職業'].dropna(subset=['裝備名稱'])
        profession_rows = profession_rows[
            profession_rows['裝備名稱'] != self.HEADER_EQUIPMENT_NAME
        ]

        professions = {'通用': {}}
        for _, row in profession_rows.iterrows():
            name = row['裝備名稱']
            if pd.isna(name):
                continue
            name = str(name).strip()
            if not name:
                continue
            professions[name] = self._extract_skill_values(row)
        return professions

    def _sort_skill_map(self, skill_map: Dict[str, int]) -> Dict[str, int]:
        """排序技能映射：先按數值由大到小，同分時按技能名稱升序"""
        return dict(sorted(skill_map.items(), key=lambda item: (-item[1], item[0])))

    def _load_skill_caps_from_source(self) -> Dict[str, Dict[str, int]]:
        """從資料源位置=角色上限載入技能上限"""
        df = self.data['source']
        cap_rows = df[df['位置'] == '角色上限'].dropna(how='all')
        if cap_rows.empty:
            return {}

        default_caps = {}
        caps_by_name = {}
        for _, row in cap_rows.iterrows():
            caps = self._extract_skill_values(row)
            if not caps:
                continue
            if not default_caps:
                default_caps = caps
            name = row.get('裝備名稱')
            if pd.notna(name) and str(name).strip():
                caps_by_name[str(name).strip()] = caps

        if not default_caps:
            return {}

        result = {'通用': default_caps}
        for profession in self.professions.keys():
            result[profession] = caps_by_name.get(profession, default_caps)
        return result

    def _load_sailor_skills_from_menu(self) -> Set[str]:
        """從選單位置=航海士載入可觸發+1的技能集合"""
        menu = self.data['menu']
        sailor_rows = menu[menu['位置'] == '航海士']
        skills = set()
        for _, row in sailor_rows.iterrows():
            for skill in self.skills:
                if skill not in row:
                    continue
                if pd.notna(row[skill]):
                    skills.add(skill)
        return skills

    def get_equipment_by_position(self, position: str) -> List[Dict]:
        """根據位置獲取所有裝備
        
        Args:
            position: 裝備位置
            
        Returns:
            裝備列表
        """
        return [eq for eq in self.all_equipment if eq['position'] == position]

    def get_equipment_by_name(self, name: str) -> Optional[Dict]:
        """根據名稱查詢裝備
        
        Args:
            name: 裝備名稱
            
        Returns:
            裝備字典或None
        """
        for eq in self.all_equipment:
            if eq['name'] == name:
                return eq
        return None

    def search_equipment(self, keyword: str) -> List[Dict]:
        """模糊搜索裝備
        
        Args:
            keyword: 搜索關鍵字
            
        Returns:
            匹配的裝備列表
        """
        keyword = keyword.lower()
        results = []
        for eq in self.all_equipment:
            if keyword in eq['name'].lower():
                results.append(eq)
        return results

    def get_equipment_by_skill(self, skill: str, min_level: int = 1) -> List[Dict]:
        """根據技能查找裝備
        
        Args:
            skill: 技能名稱
            min_level: 最小技能等級
            
        Returns:
            滿足條件的裝備列表
        """
        results = []
        for eq in self.all_equipment:
            if skill in eq['skills'] and eq['skills'][skill] >= min_level:
                results.append(eq)
        return results

    def get_professions(self) -> Dict[str, Dict[str, int]]:
        """獲取所有職業與技能加成"""
        return self.professions

    def calculate_character_skills(
        self, profession: str, equipment_names: List[str], is_sailor: bool = False
    ) -> Dict[str, Any]:
        """計算角色總技能（裝備 + 職業）

        Args:
            profession: 職業名稱
            equipment_names: 裝備名稱列表

        Returns:
            包含職業、已選裝備、裝備技能、職業加成與總技能的字典

        Raises:
            ValueError: 職業名稱不存在時拋出
        """
        if profession not in self.professions:
            raise ValueError(f'不支持的職業: {profession}')

        profession_bonus = self.professions[profession]
        skill_caps = self.skill_caps.get(profession, self.skill_caps.get('通用', {}))
        equipment_skills = {}
        selected_equipment = []
        invalid_equipment = []

        for name in equipment_names:
            eq = self.get_equipment_by_name(name)
            if not eq:
                invalid_equipment.append(name)
                continue
            selected_equipment.append({
                'position': eq['position'],
                'name': eq['name']
            })
            for skill, level in eq['skills'].items():
                equipment_skills[skill] = equipment_skills.get(skill, 0) + level

        sailor_bonus = {}
        if is_sailor:
            for skill in self.sailor_skills:
                sailor_bonus[skill] = 1

        bonus_skills = {}
        all_bonus_keys = set(equipment_skills) | set(profession_bonus) | set(sailor_bonus)
        for skill in all_bonus_keys:
            bonus_skills[skill] = (
                equipment_skills.get(skill, 0)
                + profession_bonus.get(skill, 0)
                + sailor_bonus.get(skill, 0)
            )

        highest_skills = {}
        all_skill_keys = set(skill_caps) | set(bonus_skills)
        for skill in all_skill_keys:
            highest_skills[skill] = skill_caps.get(skill, 0) + bonus_skills.get(skill, 0)

        equipment_skills = self._sort_skill_map(equipment_skills)
        profession_bonus = self._sort_skill_map(profession_bonus)
        sailor_bonus = self._sort_skill_map(sailor_bonus)
        skill_caps = self._sort_skill_map(skill_caps)
        bonus_skills = self._sort_skill_map(bonus_skills)
        highest_skills = self._sort_skill_map(highest_skills)

        return {
            'profession': profession,
            'is_sailor': is_sailor,
            'selected_equipment': selected_equipment,
            'invalid_equipment': invalid_equipment,
            'equipment_skills': equipment_skills,
            'profession_bonus': profession_bonus,
            'sailor_bonus': sailor_bonus,
            'skill_caps': skill_caps,
            'bonus_skills': bonus_skills,
            'highest_skills': highest_skills
        }

    def get_config_by_name(self, config_name: str) -> Optional[Dict]:
        """根據配置名稱獲取完整配置
        
        Args:
            config_name: 配置名稱（'選單'或'炮船範例'）
            
        Returns:
            配置字典或None
        """
        if config_name == '選單':
            df = self.data['menu']
        elif config_name == '炮船範例':
            df = self.data['cannon_example']
        else:
            return None
        
        config = {}
        for position in self.positions:
            equipment_list = df[df['位置'] == position]['裝備名稱'].dropna().unique()
            config[position] = [
                self.get_equipment_by_name(name)
                for name in equipment_list
            ]
        
        return config

    def export_to_json(self, output_file: str = 'gvl_data.json'):
        """將數據導出為JSON格式
        
        Args:
            output_file: 輸出文件名
        """
        data = {
            'positions': sorted(list(self.positions)),
            'skills': sorted(list(self.skills)),
            'equipment': self.all_equipment,
            'configs': {
                '選單': self.get_config_by_name('選單'),
                '炮船範例': self.get_config_by_name('炮船範例')
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 數據已導出到 {output_file}")

    def get_stats_summary(self) -> Dict[str, Any]:
        """獲取數據統計摘要
        
        Returns:
            統計信息字典
        """
        return {
            'total_equipment': len(self.all_equipment),
            'positions': sorted(list(self.positions)),
            'skills': sorted(list(self.skills)),
            'equipment_by_position': {
                pos: len(self.get_equipment_by_position(pos))
                for pos in self.positions
            }
        }

    def suggest_builds(
        self,
        profession: str,
        priority_skills: List[str],
        is_sailor: bool = False,
        top_n: int = 5,
        candidates_per_slot: int = 3,
        skill_cap: int = 25,
        exclude_quality: bool = False,
    ) -> List[Dict[str, Any]]:
        """根據優先技能搜尋最佳 Top-N 配裝方案。

        算法：每個槽位保留 candidates_per_slot 件高分候選，枚舉所有組合後
        依 (優先技能1總值, 優先技能2總值, 優先技能3總值, 全技能加成總和) 排序，
        去重後回傳前 top_n 套。

        Args:
            profession: 職業名稱
            priority_skills: 優先技能清單（最多 3 個，可含空字串）
            is_sailor: 是否套用航海士 +1
            top_n: 回傳方案數量
            candidates_per_slot: 每個槽位保留的候選裝備數（影響計算速度與品質）
            skill_cap: 單一技能加成上限（超過此值的方案將被過濾，預設 25）
            exclude_quality: 若為 True，排除名稱含「(質變)」的裝備

        Returns:
            方案列表，每筆包含：
              - equipment_names: 裝備名稱清單
              - score_key: 排序用分數 tuple (p1, p2, p3, total_bonus)
              - priority_values: {技能名: 合計值} 字典
              - skill_result: 完整技能計算結果（同 calculate_character_skills 輸出）

        Raises:
            ValueError: 職業名稱不存在時拋出
        """
        from itertools import product as iterproduct

        if profession not in self.professions:
            raise ValueError(f'不支持的職業: {profession}')

        # 只保留有效技能
        p_skills = [s for s in priority_skills if s and s in self.skills]

        # 槽位配置常數（與 CharacterTab 保持一致）
        _DUPLICATE = {'飾品', '寶物'}
        _SLOT_ORDER = ['飾品1', '飾品2', '寶物1', '寶物2', '主武', '副武',
                       '頭盔', '衣服', '手套', '鞋子']

        # 建立各位置裝備清單
        eq_by_pos: Dict[str, List[dict]] = {}
        for pos in sorted(self.positions):
            eq_list = self.get_equipment_by_position(pos)
            if exclude_quality:
                eq_list = [e for e in eq_list if '(質變)' not in e['name']]
            eq_by_pos[pos] = sorted(eq_list, key=lambda e: e['name'])

        # 展開雙槽位（飾品/寶物各兩個）
        slots: List[Dict[str, Any]] = []
        for pos, equipment in eq_by_pos.items():
            count = 2 if pos in _DUPLICATE else 1
            for i in range(1, count + 1):
                label = f'{pos}{i}' if count > 1 else pos
                slots.append({'label': label, 'position': pos, 'equipment': equipment})

        order_map = {s: idx for idx, s in enumerate(_SLOT_ORDER)}
        slots.sort(key=lambda s: order_map.get(s['label'], 999))

        def _score(eq: dict) -> tuple:
            """裝備優先技能評分 tuple：(p1, p2, p3, total_bonus)"""
            sk = eq.get('skills', {})
            pvals = tuple(sk.get(s, 0) for s in p_skills)
            return pvals + (sum(sk.values()),)

        # 每槽保留 Top-K 候選；槽位無裝備時以 None 占位
        slot_candidates: List[List[Optional[dict]]] = []
        for slot in slots:
            eq_list = slot['equipment']
            if not eq_list:
                slot_candidates.append([None])
                continue
            scored = sorted(eq_list, key=_score, reverse=True)
            slot_candidates.append(scored[:candidates_per_slot])

        # 預先計算每件裝備的技能合計（避免在組合枚舉中重複 sum）
        eq_total_cache: Dict[int, int] = {}
        for cands in slot_candidates:
            for eq in cands:
                if eq is not None:
                    eid = id(eq)
                    if eid not in eq_total_cache:
                        eq_total_cache[eid] = sum(eq.get('skills', {}).values())

        # 枚舉所有組合並計算分數
        scored_combos: List[tuple] = []
        for combo in iterproduct(*slot_candidates):
            pvals = [0] * len(p_skills)
            total_bonus = 0
            eq_names: List[str] = []
            for eq in combo:
                if eq is None:
                    continue
                sk = eq.get('skills', {})
                for i, ps in enumerate(p_skills):
                    pvals[i] += sk.get(ps, 0)
                total_bonus += eq_total_cache[id(eq)]
                eq_names.append(eq['name'])
            # 名稱含「(唯一)」的裝備不可重複裝備
            unique_names = [n for n in eq_names if '(唯一)' in n]
            if len(unique_names) != len(set(unique_names)):
                continue
            score_key = tuple(pvals) + (total_bonus,)
            scored_combos.append((score_key, eq_names))

        # 降序排列，去重（排列不同但裝備集合相同視為同一套），取前 top_n
        scored_combos.sort(key=lambda x: x[0], reverse=True)

        seen: set = set()
        results: List[Dict[str, Any]] = []
        for score_key, eq_names in scored_combos:
            sig = tuple(sorted(eq_names))
            if sig in seen:
                continue
            seen.add(sig)
            try:
                skill_result = self.calculate_character_skills(
                    profession, eq_names, is_sailor=is_sailor
                )
            except ValueError:
                continue
            # 過濾：任一技能加成超過上限的方案
            if skill_cap > 0 and any(
                v > skill_cap for v in skill_result.get('bonus_skills', {}).values()
            ):
                continue
            priority_values = {p_skills[i]: score_key[i] for i in range(len(p_skills))}
            results.append({
                'equipment_names': eq_names,
                'score_key': score_key,
                'priority_values': priority_values,
                'skill_result': skill_result,
            })
            if len(results) >= top_n:
                break

        return results
