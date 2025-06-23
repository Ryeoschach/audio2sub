#!/bin/bash

# 🔧 设置所有脚本的执行权限
# Usage: ./scripts/setup_permissions.sh

echo "🔧 设置脚本执行权限..."

# 设置所有 shell 脚本的执行权限
find scripts/ -name "*.sh" -type f -exec chmod +x {} \;

# 设置 Python 脚本的执行权限（如果有 shebang）
find scripts/ -name "*.py" -type f -exec grep -l "^#!/" {} \; | xargs chmod +x

echo "✅ 脚本权限设置完成！"

# 显示所有脚本及其权限
echo ""
echo "📋 脚本权限列表："
find scripts/ -type f \( -name "*.sh" -o -name "*.py" \) -exec ls -la {} \;
