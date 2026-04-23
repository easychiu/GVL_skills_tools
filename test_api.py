#!/usr/bin/env python3
"""快速測試 Flask API"""
import sys
sys.path.insert(0, 'gvl_app')

from app import app
import json

# 創建測試客戶端
client = app.test_client()

# 測試統計 API
print("測試 /api/stats:")
response = client.get('/api/stats')
print(f"狀態碼: {response.status_code}")
data = response.get_json()
print(f"總裝備數: {data['total_equipment']}")
print(f"位置數: {len(data['positions'])}")
print()

# 測試技能 API
print("測試 /api/skills:")
response = client.get('/api/skills')
print(f"狀態碼: {response.status_code}")
data = response.get_json()
print(f"技能數: {data['count']}")
print(f"技能列表: {data['skills'][:5]}...")
print()

# 測試裝備 API
print("測試 /api/equipment?page=1&per_page=5:")
response = client.get('/api/equipment?page=1&per_page=5')
print(f"狀態碼: {response.status_code}")
data = response.get_json()
print(f"返回裝備數: {len(data['equipment'])}")
print(f"第一件裝備: {data['equipment'][0]['name']} ({data['equipment'][0]['position']})")
print()

# 測試搜索 API
print("測試 /api/search?q=戒指&type=name:")
response = client.get('/api/search?q=戒指&type=name')
print(f"狀態碼: {response.status_code}")
data = response.get_json()
print(f"搜索結果數: {data['count']}")
if data['results']:
    print(f"第一個結果: {data['results'][0]['name']}")
print()

print("✅ 所有 API 測試完成！")
