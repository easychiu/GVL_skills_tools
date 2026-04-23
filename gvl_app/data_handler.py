"""GVL 裝備表數據處理模塊"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
import json


class GVLDataHandler:
    """GVL裝備表數據處理類"""

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
        self.load_data()
        self.professions = self._get_profession_data()

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
            
            # 提取所有位置
            self.positions = set(self.data['source']['位置'].dropna().unique())
            
            # 建立所有裝備的完整清單
            self._build_equipment_list()
            
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
        df = df[df['裝備名稱'] != '裝備名稱']
        
        for _, row in df.iterrows():
            try:
                position = row['位置']
                name = row['裝備名稱']
                
                # 跳過無效數據
                if pd.isna(position) or pd.isna(name):
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

    def _get_profession_data(self) -> Dict[str, Dict[str, int]]:
        """獲取預設職業與技能加成映射"""
        return {
            '通用': {},
            '冒險家': {
                '航海技術': 2,
                '地理學': 1,
                '搜索': 1
            },
            '砲術家': {
                '炮術': 2,
                '彈道學': 1,
                '水平射擊': 1
            },
            '劍士': {
                '劍術': 2,
                '突擊': 1,
                '防禦': 1
            },
            '商人': {
                '會計': 2,
                '社交': 1,
                '運用': 1
            }
        }

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
        self, profession: str, equipment_names: List[str]
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

        total_skills = equipment_skills.copy()
        for skill, level in profession_bonus.items():
            total_skills[skill] = total_skills.get(skill, 0) + level

        total_skills = dict(
            sorted(total_skills.items(), key=lambda item: (-item[1], item[0]))
        )

        return {
            'profession': profession,
            'selected_equipment': selected_equipment,
            'invalid_equipment': invalid_equipment,
            'equipment_skills': equipment_skills,
            'profession_bonus': profession_bonus,
            'total_skills': total_skills
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
