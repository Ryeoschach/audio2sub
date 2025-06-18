#!/usr/bin/env python3
"""
Docker配置测试脚本
测试各种Docker配置是否能够正常启动和运行
"""

import subprocess
import time
import requests
import sys
import json
from pathlib import Path

def run_command(command, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"

def test_docker_build(dockerfile_name, tag_name):
    """测试Docker镜像构建"""
    print(f"🏗️ 测试构建 {dockerfile_name}...")
    
    command = f"docker build -f {dockerfile_name} -t {tag_name} ."
    success, stdout, stderr = run_command(command)
    
    if success:
        print(f"✅ {dockerfile_name} 构建成功")
        return True
    else:
        print(f"❌ {dockerfile_name} 构建失败")
        print(f"错误信息: {stderr}")
        return False

def test_docker_run(tag_name, port="8001"):
    """测试Docker容器运行"""
    print(f"🚀 测试运行容器 {tag_name}...")
    
    # 停止可能存在的容器
    subprocess.run(f"docker stop test-audio2sub-{port}", shell=True, capture_output=True)
    subprocess.run(f"docker rm test-audio2sub-{port}", shell=True, capture_output=True)
    
    # 启动容器
    command = f"docker run -d --name test-audio2sub-{port} -p {port}:8000 {tag_name}"
    success, stdout, stderr = run_command(command)
    
    if not success:
        print(f"❌ 容器启动失败: {stderr}")
        return False
    
    container_id = stdout.strip()
    print(f"📦 容器启动成功: {container_id[:12]}")
    
    # 等待服务启动
    print("⏳ 等待服务启动...")
    time.sleep(10)
    
    # 测试健康检查
    try:
        response = requests.get(f"http://localhost:{port}/ping", timeout=10)
        if response.status_code == 200:
            print("✅ /ping 端点响应正常")
            ping_result = True
        else:
            print(f"❌ /ping 端点异常: {response.status_code}")
            ping_result = False
    except Exception as e:
        print(f"❌ /ping 端点测试失败: {e}")
        ping_result = False
    
    # 测试健康检查端点
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ /health 端点响应正常: {health_data.get('status', 'unknown')}")
            health_result = True
        else:
            print(f"❌ /health 端点异常: {response.status_code}")
            health_result = False
    except Exception as e:
        print(f"❌ /health 端点测试失败: {e}")
        health_result = False
    
    # 测试根端点
    try:
        response = requests.get(f"http://localhost:{port}/", timeout=10)
        if response.status_code == 200:
            root_data = response.json()
            print(f"✅ 根端点响应正常: {root_data.get('app', 'unknown')}")
            root_result = True
        else:
            print(f"❌ 根端点异常: {response.status_code}")
            root_result = False
    except Exception as e:
        print(f"❌ 根端点测试失败: {e}")
        root_result = False
    
    # 获取容器日志
    log_command = f"docker logs test-audio2sub-{port}"
    log_success, logs, log_stderr = run_command(log_command)
    if log_success and logs:
        print("📋 容器日志:")
        print(logs[-1000:])  # 只显示最后1000个字符
    
    # 清理容器
    subprocess.run(f"docker stop test-audio2sub-{port}", shell=True, capture_output=True)
    subprocess.run(f"docker rm test-audio2sub-{port}", shell=True, capture_output=True)
    
    return ping_result and health_result and root_result

def main():
    """主测试函数"""
    print("🐳 Audio2Sub Docker配置测试")
    print("=" * 50)
    
    # 切换到backend目录
    backend_dir = Path(__file__).parent
    
    results = {}
    
    # 测试不同的Dockerfile
    dockerfiles = [
        ("Dockerfile", "audio2sub:main"),
        ("Dockerfile.cpu", "audio2sub:cpu"),
        # ("Dockerfile.gpu", "audio2sub:gpu"),  # 需要GPU环境，暂时跳过
    ]
    
    for dockerfile, tag in dockerfiles:
        print(f"\n🔍 测试 {dockerfile}")
        print("-" * 30)
        
        # 构建测试
        build_success = test_docker_build(dockerfile, tag)
        if not build_success:
            results[dockerfile] = {"build": False, "run": False}
            continue
        
        # 运行测试
        port = "8001" if "cpu" in dockerfile else "8002"
        run_success = test_docker_run(tag, port)
        results[dockerfile] = {"build": True, "run": run_success}
    
    # 输出结果摘要
    print("\n📊 测试结果摘要")
    print("=" * 50)
    
    all_passed = True
    for dockerfile, result in results.items():
        build_status = "✅" if result["build"] else "❌"
        run_status = "✅" if result["run"] else "❌"
        print(f"{dockerfile:20} 构建:{build_status} 运行:{run_status}")
        
        if not (result["build"] and result["run"]):
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有Docker配置测试通过！")
        return 0
    else:
        print("\n⚠️ 部分Docker配置存在问题，请检查上述错误信息")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
