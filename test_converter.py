#!/usr/bin/env python3
"""
测试Revit到FBX转换器的基本功能
"""

import os
import sys
import tempfile

def test_basic_functionality():
    """测试基本功能"""
    print("=== 测试Revit到FBX转换器 ===")
    
    # 检查文件是否存在
    test_file = "Room.rvt"
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        print("请确保Room.rvt文件在当前目录中")
        return False
    
    print(f"✅ 找到测试文件: {test_file}")
    
    # 检查文件大小
    file_size = os.path.getsize(test_file)
    print(f"文件大小: {file_size} 字节 ({file_size / 1024 / 1024:.2f} MB)")
    
    # 检查文件扩展名
    file_ext = os.path.splitext(test_file)[1].lower()
    if file_ext == '.rvt':
        print(f"✅ 文件格式正确: {file_ext}")
    else:
        print(f"⚠️ 文件格式可能不支持: {file_ext}")
    
    return True

def test_imports():
    """测试必要的导入"""
    print("\n=== 测试导入 ===")
    
    try:
        import requests
        print("✅ requests 模块导入成功")
    except ImportError:
        print("❌ requests 模块导入失败")
        print("请运行: pip3 install requests")
        return False
    
    try:
        import base64
        import json
        import time
        import os
        import sys
        print("✅ 标准库模块导入成功")
    except ImportError as e:
        print(f"❌ 标准库模块导入失败: {e}")
        return False
    
    return True

def test_script_syntax():
    """测试脚本语法"""
    print("\n=== 测试脚本语法 ===")
    
    try:
        import py_compile
        py_compile.compile("revit_to_fbx_converter.py", doraise=True)
        print("✅ 主脚本语法正确")
    except Exception as e:
        print(f"❌ 主脚本语法错误: {e}")
        return False
    
    try:
        py_compile.compile("debug_converter.py", doraise=True)
        print("✅ 调试脚本语法正确")
    except Exception as e:
        print(f"❌ 调试脚本语法错误: {e}")
        return False
    
    return True

def main():
    """主测试函数"""
    print("开始测试Revit到FBX转换器...\n")
    
    tests = [
        test_imports,
        test_script_syntax,
        test_basic_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ 测试通过\n")
            else:
                print("❌ 测试失败\n")
        except Exception as e:
            print(f"❌ 测试异常: {e}\n")
    
    print(f"=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！可以运行转换器了。")
        print("\n使用方法:")
        print("python3 revit_to_fbx_converter.py Room.rvt")
        print("或")
        print("python3 debug_converter.py Room.rvt")
    else:
        print("⚠️ 部分测试失败，请检查上述问题。")

if __name__ == "__main__":
    main()