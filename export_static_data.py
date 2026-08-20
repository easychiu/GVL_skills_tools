#!/usr/bin/env python3
"""將 Flask 後端資料匯出為靜態檔，供 GitHub Pages 純前端版使用。

於 repo 根目錄產生：
  - data.json   GVLDataHandler 各項資料的完整 JSON 快照
  - index.html  templates/index.html 去除 Jinja 語法後的靜態版本
"""
import io
import json
import sys
from pathlib import Path

# Windows 主控台輸出中文可能爆 UnicodeEncodeError，先包成 utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path(__file__).parent
APP_DIR = ROOT / 'gvl_app'

# gvl_app 不是 package（app.py 用 from data_handler import ...），需手動加入路徑
sys.path.insert(0, str(APP_DIR))
from data_handler import GVLDataHandler  # noqa: E402

# ---- 1. 匯出 data.json ----
handler = GVLDataHandler(str(ROOT / 'GVL裝備表.xlsx'))

data = {
    'positions': sorted(handler.positions),
    'skills': sorted(handler.skills),
    'equipment': handler.all_equipment,
    'professions': handler.get_professions(),
    'skill_caps': handler.skill_caps,
    'sailor_skills': sorted(handler.sailor_skills),
    'configs': {
        '選單': handler.get_config_by_name('選單'),
        '炮船範例': handler.get_config_by_name('炮船範例'),
    },
    'stats': handler.get_stats_summary(),
}

data_json_path = ROOT / 'data.json'
with open(data_json_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# ---- 2. 匯出 index.html ----
html = (APP_DIR / 'templates' / 'index.html').read_text(encoding='utf-8')

html = html.replace(
    "{{ url_for('serve_static', filename='style.css') }}", 'gvl_app/static/style.css'
)
html = html.replace(
    "{{ url_for('serve_static', filename='script.js') }}", 'gvl_app/static/script.js'
)
html = html.replace(
    '    <script src="gvl_app/static/script.js"></script>',
    '    <script src="pages-api.js"></script>\n'
    '    <script src="gvl_app/static/script.js"></script>'
)

if '{{' in html or '{%' in html:
    raise RuntimeError(
        'index.html 仍含未替換的 Jinja 語法，模板可能已新增內容，請檢查後更新此腳本'
    )

# 上面的注入是純字串比對，模板改了縮排或屬性就會靜默失效，產出一個打真 API 的壞頁面
if 'pages-api.js' not in html:
    raise RuntimeError(
        '未注入 pages-api.js，模板的 script 標籤寫法可能已變動，請檢查後更新此腳本'
    )

html = '<!-- 此檔由 export_static_data.py 自動產生，請勿手動修改 -->\n' + html

index_html_path = ROOT / 'index.html'
index_html_path.write_text(html, encoding='utf-8')

# ---- 摘要 ----
print('✓ 靜態資料匯出完成')
print(f'  裝備筆數: {len(handler.all_equipment)}')
print(f'  職業數: {len(data["professions"])}')
print(f'  data.json 大小: {data_json_path.stat().st_size:,} bytes')
print(f'  data.json -> {data_json_path}')
print(f'  index.html -> {index_html_path}')
