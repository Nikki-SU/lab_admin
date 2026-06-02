#!/usr/bin/env python3
"""
LabVault 测试脚本 - 模拟 Leaf Agent 上传文件
用于单电脑调试场景
"""

import requests
import os
import tempfile
import time
from datetime import datetime

# 配置
HUB_URL = "http://localhost:8000/api"
USERNAME = "admin"
PASSWORD = "admin123"

def get_token():
    """获取登录 token"""
    print(f"[1/4] 正在获取 token (用户: {USERNAME})...")
    try:
        response = requests.post(
            f"{HUB_URL}/token",
            data={"username": USERNAME, "password": PASSWORD}
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        print("    ✅ Token 获取成功")
        return token
    except Exception as e:
        print(f"    ❌ 获取 token 失败: {e}")
        print("    请确认 Hub Server 正在运行，并且默认账号密码正确")
        return None

def create_test_files():
    """创建测试文件"""
    print("\n[2/4] 正在创建测试文件...")
    test_files = []
    
    # 测试文件 1
    f1 = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    f1.write("测试数据文件 1\n")
    f1.write(f"创建时间: {datetime.now().isoformat()}\n")
    f1.write("这是用于 LabVault 测试的文件")
    f1.close()
    test_files.append(("test-file-1.txt", f1.name))
    
    # 测试文件 2
    f2 = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    f2.write("Sample,Wave_1,Wave_2,Wave_3\n")
    f2.write("1,0.5,0.6,0.7\n")
    f2.write("2,0.4,0.5,0.6\n")
    f2.write("3,0.3,0.4,0.5\n")
    f2.close()
    test_files.append(("test-file-2.csv", f2.name))
    
    print(f"    ✅ 创建了 {len(test_files)} 个测试文件")
    return test_files

def upload_files(token, test_files):
    """上传测试文件"""
    print("\n[3/4] 正在上传测试文件...")
    headers = {"Authorization": f"Bearer {token}"}
    uploaded = []
    
    for filename, filepath in test_files:
        print(f"    正在上传: {filename}")
        try:
            with open(filepath, "rb") as f:
                files = {"file": (filename, f)}
                data = {
                    "zone": "DATA",
                    "path": f"/Test-Device/{filename}",
                    "source_device": "Test-Device",
                    "is_edit": "false"
                }
                
                response = requests.post(
                    f"{HUB_URL}/files/upload",
                    headers=headers,
                    files=files,
                    data=data
                )
            
            if response.status_code == 200:
                print(f"      ✅ {filename} 上传成功")
                uploaded.append(filename)
            else:
                print(f"      ❌ {filename} 上传失败: {response.status_code}")
                print(f"         {response.text}")
        except Exception as e:
            print(f"      ❌ {filename} 上传异常: {e}")
    
    return uploaded

def verify_uploads(token):
    """验证上传结果"""
    print("\n[4/4] 正在验证上传结果...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{HUB_URL}/files",
            headers=headers,
            params={"zone": "DATA"}
        )
        response.raise_for_status()
        files = response.json()
        
        print(f"    ✅ 当前共有 {len(files)} 个文件在 DATA 区")
        print("\n    文件列表:")
        for i, f in enumerate(files[-5:], 1):  # 显示最近 5 个
            edited_marker = " ⚠️已编辑" if f.get('edited') else ""
            print(f"      {i}. {f['name']} ({f['size']} 字节){edited_marker}")
        
        return files
    except Exception as e:
        print(f"    ❌ 获取文件列表失败: {e}")
        return []

def cleanup_test_files(test_files):
    """清理临时文件"""
    print("\n正在清理临时文件...")
    for _, filepath in test_files:
        try:
            os.unlink(filepath)
        except:
            pass
    print("    ✅ 清理完成")

def main():
    print("=" * 60)
    print("  LabVault 单电脑调试 - 测试脚本")
    print("=" * 60)
    print()
    
    # 步骤 1: 获取 token
    token = get_token()
    if not token:
        return
    
    # 步骤 2: 创建测试文件
    test_files = create_test_files()
    
    try:
        # 步骤 3: 上传文件
        uploaded = upload_files(token, test_files)
        
        # 步骤 4: 验证结果
        verify_uploads(token)
        
        print("\n" + "=" * 60)
        print("  测试完成!")
        print("=" * 60)
        print()
        print("接下来你可以:")
        print("  1. 打开浏览器访问 http://localhost:3000")
        print("  2. 使用 admin/admin123 登录")
        print("  3. 在个人数据区查看刚才上传的文件")
        print("  4. 测试下载、删除等功能")
        print()
        
    finally:
        # 清理
        cleanup_test_files(test_files)

if __name__ == "__main__":
    main()
