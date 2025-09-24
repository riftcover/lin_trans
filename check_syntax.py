#!/usr/bin/env python3
"""
检查Python文件语法的脚本
"""

import ast
import sys
import traceback

def check_file_syntax(file_path):
    """检查单个文件的语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试解析AST
        ast.parse(content)
        print(f"✅ {file_path}: 语法正确")
        return True
    except SyntaxError as e:
        print(f"❌ {file_path}: 语法错误")
        print(f"   行 {e.lineno}: {e.text.strip() if e.text else ''}")
        print(f"   错误: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ {file_path}: 检查失败")
        print(f"   错误: {str(e)}")
        return False

def main():
    """主函数"""
    files_to_check = [
        'api_client.py',
        'nice_ui/ui/MainWindow.py',
        'nice_ui/ui/purchase_dialog.py',
        'nice_ui/ui/login.py',
        'nice_ui/ui/profile.py',
        'nice_ui/services/api_service.py',
        'nice_ui/services/token_service.py',
        'nice_ui/services/auth_service.py',
        'test_api_fix.py'
    ]
    
    print("检查Python文件语法...")
    print("=" * 50)
    
    all_good = True
    for file_path in files_to_check:
        if not check_file_syntax(file_path):
            all_good = False
    
    print("=" * 50)
    if all_good:
        print("✅ 所有文件语法检查通过！")
    else:
        print("❌ 发现语法错误，请修复后重试")
        sys.exit(1)

if __name__ == "__main__":
    main()
