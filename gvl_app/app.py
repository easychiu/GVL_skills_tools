"""GVL 裝備表 Flask Web 應用"""
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from pathlib import Path
from data_handler import GVLDataHandler

# 初始化Flask應用
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# 初始化數據處理器
excel_path = Path(__file__).parent.parent / 'GVL裝備表.xlsx'
handler = GVLDataHandler(str(excel_path))

# 獲取統計信息
stats = handler.get_stats_summary()


@app.route('/')
def index():
    """首頁"""
    return render_template('index.html', stats=stats)


@app.route('/api/equipment')
def api_equipment():
    """獲取所有裝備API"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    start = (page - 1) * per_page
    end = start + per_page
    
    equipment = handler.all_equipment[start:end]
    total = len(handler.all_equipment)
    
    return jsonify({
        'equipment': equipment,
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': (total + per_page - 1) // per_page
    })


@app.route('/api/search')
def api_search():
    """搜索API"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'name')  # 'name', 'skill', 'position'
    
    if not query:
        return jsonify({'error': '搜索關鍵字不能為空'}), 400
    
    if search_type == 'name':
        results = handler.search_equipment(query)
    elif search_type == 'skill':
        min_level = request.args.get('min_level', 1, type=int)
        results = handler.get_equipment_by_skill(query, min_level)
    elif search_type == 'position':
        results = handler.get_equipment_by_position(query)
    else:
        return jsonify({'error': '不支持的搜索類型'}), 400
    
    return jsonify({
        'query': query,
        'type': search_type,
        'count': len(results),
        'results': results
    })


@app.route('/api/equipment/<name>')
def api_equipment_detail(name):
    """獲取裝備詳情API"""
    equipment = handler.get_equipment_by_name(name)
    if not equipment:
        return jsonify({'error': '裝備未找到'}), 404
    return jsonify(equipment)


@app.route('/api/positions')
def api_positions():
    """獲取所有位置API"""
    return jsonify({
        'positions': sorted(list(handler.positions)),
        'count': len(handler.positions)
    })


@app.route('/api/skills')
def api_skills():
    """獲取所有技能API"""
    return jsonify({
        'skills': sorted(list(handler.skills)),
        'count': len(handler.skills)
    })


@app.route('/api/professions')
def api_professions():
    """獲取職業與技能加成API"""
    professions = handler.get_professions()
    return jsonify({
        'professions': professions,
        'count': len(professions)
    })


@app.route('/api/character/options')
def api_character_options():
    """獲取角色配裝選項API，包含位置、裝備列表與職業資訊"""
    equipment_by_position = {}
    for position in sorted(handler.positions):
        position_equipment = handler.get_equipment_by_position(position)
        equipment_by_position[position] = sorted(
            [eq['name'] for eq in position_equipment]
        )

    return jsonify({
        'positions': sorted(list(handler.positions)),
        'equipment_by_position': equipment_by_position,
        'professions': handler.get_professions()
    })


@app.route('/api/character/calculate', methods=['POST'])
def api_character_calculate():
    """計算角色技能API

    Request JSON:
        profession: 職業名稱
        equipment_names: 裝備名稱陣列

    Response JSON:
        職業、已選裝備、裝備技能、職業加成、總技能
    """
    payload = request.get_json(silent=True) or {}
    profession = payload.get('profession', '通用')
    equipment_names = payload.get('equipment_names', [])

    if not isinstance(equipment_names, list):
        return jsonify({'error': 'equipment_names 必須為陣列'}), 400

    try:
        result = handler.calculate_character_skills(profession, equipment_names)
    except ValueError:
        return jsonify({'error': '不支持的職業'}), 400

    return jsonify(result)


@app.route('/api/config/<config_name>')
def api_config(config_name):
    """獲取預設配置API"""
    config = handler.get_config_by_name(config_name)
    if not config:
        return jsonify({'error': '配置未找到'}), 404
    return jsonify({'name': config_name, 'config': config})


@app.route('/api/stats')
def api_stats():
    """獲取統計信息API"""
    return jsonify(stats)


@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供靜態文件"""
    return send_from_directory('static', filename)


@app.errorhandler(404)
def not_found(error):
    """404錯誤處理"""
    return jsonify({'error': '頁面未找到'}), 404


@app.errorhandler(500)
def server_error(error):
    """500錯誤處理"""
    return jsonify({'error': '伺服器內部錯誤'}), 500


if __name__ == '__main__':
    print("\n" + "="*50)
    print("GVL 裝備表 Web 應用已啟動")
    print("="*50)
    print(f"本地位址: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服務器")
    print("="*50 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)
