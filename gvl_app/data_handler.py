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
                for skill in sorted(self.skills):
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
        for skill in sorted(self.skills):
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
        # 角色上限區塊只有首列的位置欄有標籤，其後各職業列為空白，需先向下填補
        cap_rows = df[df['位置'].ffill() == '角色上限'].dropna(how='all')
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
            for skill in sorted(self.skills):
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
        for position in sorted(self.positions):
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
                for pos in sorted(self.positions)
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

        算法：先柏拉圖裁剪（丟掉在所有優先技能與全技能總和上都被壓制的裝備），
        再對倖存者做分支定界枚舉（以剩餘槽位的樂觀上界剪枝）。兩道裁剪都不會
        排除最佳解，因此結果等同窮舉——全空間有 3.24e14 組，無法直接枚舉。

        評分看的是「最高值」（角色上限 + 加成），即遊戲內實際能到的等級，
        並以 skill_cap 為天花板截斷——堆過頭不加分，多餘點數會被挪去補其他
        選定技能。回傳時每種「技能輪廓」只留最佳一套，讓方案彼此真的不同。

        Args:
            profession: 職業名稱
            priority_skills: 優先技能清單（最多 5 個，可含空字串）
            is_sailor: 是否套用航海士 +1
            top_n: 回傳方案數量
            candidates_per_slot: 已無作用，僅為相容舊呼叫端保留
            skill_cap: 遊戲內技能上限，也是配裝要頂到的目標值（預設 25）
            exclude_quality: 若為 True，排除名稱含「(質變)」的裝備

        Returns:
            方案列表，每筆包含：
              - equipment_names: 裝備名稱清單
              - score_key: 排序用分數 tuple
                (skills_at_cap, effective_total,
                 p1..pN 生效值, priority_raw_total, total_bonus)
              - priority_values: {技能名: 生效最高值（已截到 skill_cap）} 字典
              - skill_result: 完整技能計算結果（同 calculate_character_skills 輸出）

        Raises:
            ValueError: 職業名稱不存在時拋出
        """
        if profession not in self.professions:
            raise ValueError(f'不支持的職業: {profession}')

        # 只保留有效且不重複技能（最多 5 個，保留輸入順序）
        p_skills: List[str] = []
        for skill in priority_skills:
            if not skill:
                continue
            if skill not in self.skills:
                continue
            if skill in p_skills:
                continue
            p_skills.append(skill)
            if len(p_skills) >= 5:
                break

        # 沒有任何有效優先技能時無從評分，且會讓下方的剪枝完全失效（等同全枚舉）
        if not p_skills:
            return []

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

        # ── 柏拉圖裁剪 ────────────────────────────────────────────────────
        # 每件裝備化為向量（各優先技能值…, 該裝備全技能總和）。若 B 的每個分量
        # 都 >= A，任何用 A 的配裝換成 B 都不會更差，A 可安全丟棄——這一步不會
        # 排除最佳解，卻能把搜尋空間從 10^14 級砍到數千～數百萬。
        def _vec(eq: dict) -> tuple:
            sk = eq.get('skills', {})
            return tuple(sk.get(s, 0) for s in p_skills) + (sum(sk.values()),)

        def _pareto(equipment: List[dict]) -> List[tuple]:
            vecs = [(_vec(e), e) for e in equipment]
            uniq = {v for v, _ in vecs}
            nondom = {
                v for v in uniq
                if not any(o != v and all(a >= b for a, b in zip(o, v)) for o in uniq)
            }
            seen, out = set(), []
            for v, e in vecs:
                if v in nondom and v not in seen:
                    seen.add(v)
                    out.append((v, e))
            return out

        empty = ((0,) * (len(p_skills) + 1), None)
        slot_candidates: List[List[tuple]] = []
        for slot in slots:
            equipment = slot['equipment']
            if not equipment:
                slot_candidates.append([empty])
                continue
            cand = _pareto(equipment)
            # 同位置有兩格時，若前緣全是「(唯一)」裝備就填不滿兩格，
            # 需另外補上非唯一裝備的前緣
            if slot['position'] in _DUPLICATE and all('(唯一)' in v[1]['name'] for v in cand):
                plain = [e for e in equipment if '(唯一)' not in e['name']]
                if plain:
                    have = {v for v, _ in cand}
                    cand = cand + [x for x in _pareto(plain) if x[0] not in have]
            slot_candidates.append(cand)

        # ── 分支定界搜尋 ──────────────────────────────────────────────────
        target = skill_cap if skill_cap > 0 else 25
        k = len(p_skills)
        n = len(slot_candidates)

        # 非裝備部分（角色上限 + 職業加成 + 航海士）先算好，裝備只補差額
        prof_bonus = self.professions[profession]
        cap_map = self.skill_caps.get(profession, self.skill_caps.get('通用', {}))
        sailor_set = self.sailor_skills if is_sailor else set()
        base = [
            cap_map.get(s, 0) + prof_bonus.get(s, 0) + (1 if s in sailor_set else 0)
            for s in p_skills
        ]

        # 從第 i 格起，各技能還能拿到的最大值——用來算樂觀上界
        max_remain = [[0] * k for _ in range(n + 1)]
        for i in range(n - 1, -1, -1):
            for j in range(k):
                max_remain[i][j] = max_remain[i + 1][j] + max(
                    v[j] for v, _ in slot_candidates[i]
                )

        # 同位置的兩格候選清單相同，強制索引遞增即可避免枚舉出重複組合
        same_as_prev = [
            i > 0 and slots[i]['position'] == slots[i - 1]['position']
            for i in range(n)
        ]

        # 容差：一併收下略低於最佳的方案，使用者才有不同取捨可挑
        tolerance = 2
        best_total = -1
        by_profile: Dict[tuple, tuple] = {}

        def _dfs(i: int, acc: List[int], chosen: List[Optional[dict]], start: int):
            nonlocal best_total
            if i == n:
                profile = tuple(min(base[j] + acc[j], target) for j in range(k))
                total = sum(profile)
                if total > best_total:
                    best_total = total
                if total < best_total - tolerance:
                    return
                names = [e['name'] for e in chosen if e is not None]
                # 唯一裝備每套只能一件，質變版與原版視為同一件
                uniq = [x.replace('(質變)', '') for x in names if '(唯一)' in x]
                if len(uniq) != len(set(uniq)):
                    return
                skills_at_cap = sum(1 for v in profile if v >= target)
                score_key = (total, skills_at_cap, *profile, acc[k])
                cur = by_profile.get(profile)
                if cur is None or score_key > cur[0]:
                    by_profile[profile] = (score_key, names)
                return
            # 樂觀上界：剩餘槽位全部拿滿也追不上目前最佳就整支剪掉
            upper = sum(
                min(base[j] + acc[j] + max_remain[i][j], target) for j in range(k)
            )
            if upper < best_total - tolerance:
                return
            begin = start if same_as_prev[i] else 0
            candidates = slot_candidates[i]
            for idx in range(begin, len(candidates)):
                v, eq = candidates[idx]
                _dfs(i + 1, [acc[j] + v[j] for j in range(k + 1)], chosen + [eq], idx)

        _dfs(0, [0] * (k + 1), [], 0)

        # 上面那輪求的是「生效總和最大」，會為了總分犧牲第一順位技能。
        # 但使用者填的優先技能是有先後的，所以另外找一套嚴格照順序的方案：
        # 先把第一順位頂到最高，在此前提下再衝第二順位，依此類推。
        best_lex: Optional[tuple] = None

        def _dfs_lex(i: int, acc: List[int], chosen: List[Optional[dict]], start: int):
            nonlocal best_lex
            if i == n:
                names = [e['name'] for e in chosen if e is not None]
                uniq = [x.replace('(質變)', '') for x in names if '(唯一)' in x]
                if len(uniq) != len(set(uniq)):
                    return
                profile = tuple(min(base[j] + acc[j], target) for j in range(k))
                if best_lex is None or profile > best_lex[0]:
                    best_lex = (profile, names)
                return
            # 各分量都取樂觀上界後仍字典序落後，這支就不可能更好（上界單調）
            upper = tuple(
                min(base[j] + acc[j] + max_remain[i][j], target) for j in range(k)
            )
            if best_lex is not None and upper < best_lex[0]:
                return
            begin = start if same_as_prev[i] else 0
            candidates = slot_candidates[i]
            for idx in range(begin, len(candidates)):
                v, eq = candidates[idx]
                _dfs_lex(i + 1, [acc[j] + v[j] for j in range(k + 1)], chosen + [eq], idx)

        _dfs_lex(0, [0] * (k + 1), [], 0)

        def _make(names: List[str], by_order: bool) -> Dict[str, Any]:
            skill_result = self.calculate_character_skills(
                profession, names, is_sailor=is_sailor
            )
            highest = skill_result.get('highest_skills', {})
            values = {s: min(highest.get(s, 0), target) for s in p_skills}
            return {
                'equipment_names': names,
                'score_key': (sum(values.values()), *values.values()),
                'priority_values': values,
                'by_priority_order': by_order,
                'skill_result': skill_result,
            }

        # 每種「技能輪廓」只留最佳的一套，讓回傳的方案彼此真的不同
        cutoff = best_total - tolerance
        ordered = sorted(
            ((prof_key, x) for prof_key, x in by_profile.items() if sum(prof_key) >= cutoff),
            key=lambda item: item[1][0],
            reverse=True,
        )

        results: List[Dict[str, Any]] = []
        seen_profiles = set()
        # 照優先順序的那套放第一個
        if best_lex is not None:
            results.append(_make(best_lex[1], True))
            seen_profiles.add(best_lex[0])
        for prof_key, (_score_key, names) in ordered:
            if len(results) >= top_n:
                break
            if prof_key in seen_profiles:
                continue
            seen_profiles.add(prof_key)
            results.append(_make(names, False))
        return results
