#!/usr/bin/env python3
"""
测试 Celery 配置和连接的脚本
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config():
    """测试配置加载"""
    print("🔧 测试配置加载...")
    try:
        from app.config import settings
        print(f"✅ 配置加载成功")
        print(f"   Redis Host: {settings.REDIS_HOST}")
        print(f"   Redis Port: {settings.REDIS_PORT}")
        print(f"   Celery Broker: {settings.CELERY_BROKER_URL}")
        print(f"   Celery Backend: {settings.CELERY_RESULT_BACKEND}")
        return True
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

def test_celery_app():
    """测试 Celery 应用创建"""
    print("\n🔧 测试 Celery 应用...")
    try:
        from celery_app import celery_app
        print(f"✅ Celery 应用创建成功")
        print(f"   App Name: {celery_app.main}")
        print(f"   Broker: {celery_app.conf.broker_url}")
        print(f"   Backend: {celery_app.conf.result_backend}")
        return True
    except Exception as e:
        print(f"❌ Celery 应用创建失败: {e}")
        return False

def test_tasks_import():
    """测试任务模块导入"""
    print("\n🔧 测试任务模块导入...")
    try:
        from app.tasks import create_transcription_task
        print(f"✅ 任务模块导入成功")
        print(f"   Task Name: {create_transcription_task.name}")
        return True
    except Exception as e:
        print(f"❌ 任务模块导入失败: {e}")
        return False

def test_redis_connection():
    """测试 Redis 连接"""
    print("\n🔧 测试 Redis 连接...")
    try:
        from app.config import settings
        import redis
        
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        # 测试连接
        r.ping()
        print(f"✅ Redis 连接成功")
        
        # 测试基本操作
        r.set("test_key", "test_value")
        value = r.get("test_key")
        r.delete("test_key")
        
        if value == "test_value":
            print(f"✅ Redis 读写测试成功")
            return True
        else:
            print(f"❌ Redis 读写测试失败")
            return False
            
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        print(f"   请确保 Redis 服务正在运行:")
        print(f"   - macOS: brew services start redis")
        print(f"   - Ubuntu: sudo systemctl start redis")
        print(f"   - Docker: docker run -d -p 6379:6379 redis:7-alpine")
        return False

def main():
    """主测试函数"""
    print("🚀 Audio2Sub Celery 配置测试")
    print("=" * 50)
    
    tests = [
        ("配置加载", test_config),
        ("Celery 应用", test_celery_app),
        ("任务导入", test_tasks_import),
        ("Redis 连接", test_redis_connection),
    ]
    
    results = []
    for test_name, test_func in tests:
        success = test_func()
        results.append((test_name, success))
        if not success:
            print(f"\n⚠️  {test_name} 失败，可能影响后续测试")
    
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    
    all_passed = True
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {test_name}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有测试通过！Celery 配置正确。")
        print("\n💡 现在可以启动 Celery worker:")
        print("   uv run celery -A celery_app.celery_app worker --loglevel=info --pool=solo")
    else:
        print("\n❌ 部分测试失败，请检查配置和依赖。")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
