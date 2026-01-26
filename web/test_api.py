# Web 后端测试脚本

import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("测试 Gitea Mirror Backup Web API")
print("=" * 60)

# 1. 健康检查
print("\n1. 健康检查...")
try:
    r = requests.get(f"{BASE_URL}/health")
    print(f"   状态码: {r.status_code}")
    print(f"   响应: {r.json()}")
except Exception as e:
    print(f"   错误: {e}")

# 2. 根路径
print("\n2. 根路径...")
try:
    r = requests.get(f"{BASE_URL}/")
    print(f"   状态码: {r.status_code}")
    print(f"   响应: {r.json()}")
except Exception as e:
    print(f"   错误: {e}")

# 3. 登录
print("\n3. 用户登录...")
try:
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    print(f"   状态码: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        token = data.get("access_token")
        print(f"   Token: {token[:50]}...")
        
        # 4. 获取当前用户信息
        print("\n4. 获取当前用户信息...")
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        print(f"   状态码: {r.status_code}")
        print(f"   用户信息: {json.dumps(r.json(), indent=2, ensure_ascii=False)}")
        
        # 5. 获取仪表板统计
        print("\n5. 获取仪表板统计...")
        r = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        print(f"   状态码: {r.status_code}")
        print(f"   统计数据: {json.dumps(r.json(), indent=2, ensure_ascii=False)}")
        
        # 6. 获取仓库列表
        print("\n6. 获取仓库列表...")
        r = requests.get(f"{BASE_URL}/api/repositories", headers=headers)
        print(f"   状态码: {r.status_code}")
        print(f"   仓库数量: {len(r.json())}")
        
        # 7. 获取快照列表
        print("\n7. 获取快照列表...")
        r = requests.get(f"{BASE_URL}/api/snapshots", headers=headers)
        print(f"   状态码: {r.status_code}")
        print(f"   快照数量: {len(r.json())}")
        
        # 8. 获取报告列表
        print("\n8. 获取报告列表...")
        r = requests.get(f"{BASE_URL}/api/reports", headers=headers)
        print(f"   状态码: {r.status_code}")
        print(f"   报告数量: {len(r.json())}")
        
    else:
        print(f"   登录失败: {r.json()}")
except Exception as e:
    print(f"   错误: {e}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
print("\nAPI 文档: http://localhost:8000/docs")

