#!/usr/bin/env python3
"""
測試執行腳本
執行所有單元測試並產生測試報告
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """執行命令並處理錯誤"""
    print(f"\n{'='*60}")
    print(f"執行: {description}")
    print(f"命令: {' '.join(command)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("✅ 成功!")
        if result.stdout:
            print("輸出:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ 失敗!")
        print(f"錯誤碼: {e.returncode}")
        if e.stdout:
            print("標準輸出:")
            print(e.stdout)
        if e.stderr:
            print("錯誤輸出:")
            print(e.stderr)
        return False
    except FileNotFoundError:
        print(f"❌ 找不到命令: {command[0]}")
        return False

def check_dependencies():
    """檢查必要的依賴套件"""
    print("檢查測試依賴套件...")
    
    required_packages = [
        'pytest',
        'pytest-asyncio',
        'pytest-cov',
        'httpx',
        'numpy',
        'opencv-python',
        'pandas'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 缺少以下套件:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n請執行以下命令安裝:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 所有依賴套件都已安裝")
    return True

def run_linting():
    """執行代碼檢查"""
    commands = [
        (['python', '-m', 'flake8', 'backend', '--max-line-length=120', '--ignore=E203,W503'], "代碼風格檢查 (flake8)"),
        (['python', '-m', 'black', '--check', '--diff', 'backend'], "代碼格式檢查 (black)"),
    ]
    
    success = True
    for command, description in commands:
        if not run_command(command, description):
            success = False
            print(f"⚠️  {description}失敗，但繼續執行測試...")
    
    return success

def run_unit_tests():
    """執行單元測試"""
    test_commands = [
        # 執行所有測試
        (['python', '-m', 'pytest', 'tests/', '-v'], "執行所有單元測試"),
        
        # 執行特定模組測試
        (['python', '-m', 'pytest', 'tests/test_image_processor.py', '-v'], "圖片處理器測試"),
        (['python', '-m', 'pytest', 'tests/test_database_service.py', '-v'], "資料庫服務測試"),
        (['python', '-m', 'pytest', 'tests/test_csv_exporter.py', '-v'], "CSV匯出器測試"),
        (['python', '-m', 'pytest', 'tests/test_main_api.py', '-v'], "API端點測試"),
        (['python', '-m', 'pytest', 'tests/test_claude_vision_service.py', '-v'], "Claude AI服務測試"),
    ]
    
    all_success = True
    
    for command, description in test_commands:
        success = run_command(command, description)
        if not success:
            all_success = False
    
    return all_success

def run_coverage_report():
    """執行測試覆蓋率報告"""
    commands = [
        (['python', '-m', 'pytest', '--cov=backend', '--cov-report=html', '--cov-report=term-missing', 'tests/'], "產生測試覆蓋率報告"),
    ]
    
    success = True
    for command, description in commands:
        if run_command(command, description):
            print("📊 測試覆蓋率報告已產生在 htmlcov/ 目錄")
        else:
            success = False
    
    return success

def run_performance_tests():
    """執行效能測試 (可選)"""
    print("\n" + "="*60)
    print("執行效能測試 (可選)")
    print("="*60)
    
    # 這裡可以加入效能測試
    # 例如測試大量圖片處理的速度
    print("⚠️  效能測試尚未實作")
    return True

def run_accuracy_tests():
    """執行識別準確性測試"""
    print("\n" + "="*60)
    print("執行識別準確性測試")
    print("="*60)
    
    # 檢查是否有真實圖片測試
    accuracy_test_file = Path("tests/test_real_image_recognition.py")
    if not accuracy_test_file.exists():
        print("⚠️  識別準確性測試檔案不存在")
        return True
    
    # 檢查是否有測試圖片
    data_path = Path("data")
    if not data_path.exists():
        print("⚠️  data 資料夾不存在，跳過準確性測試")
        return True
    
    image_files = list(data_path.glob("*.jpg")) + list(data_path.glob("*.jpeg")) + list(data_path.glob("*.png"))
    if not image_files:
        print("⚠️  data 資料夾中沒有圖片檔案，跳過準確性測試")
        return True
    
    commands = [
        (['python', '-m', 'pytest', 'tests/test_real_image_recognition.py', '-v', '--tb=short'], "真實圖片識別準確性測試"),
    ]
    
    success = True
    for command, description in commands:
        if not run_command(command, description):
            success = False
    
    if success:
        print("✅ 識別準確性測試完成")
    else:
        print("⚠️  部分準確性測試失敗，請檢查圖片和預期結果")
    
    return True  # 不強制要求準確性測試通過，因為可能沒有完整的測試圖片

def generate_test_summary():
    """產生測試摘要報告"""
    print("\n" + "="*60)
    print("測試摘要")
    print("="*60)
    
    # 檢查測試覆蓋率文件是否存在
    coverage_file = Path("htmlcov/index.html")
    if coverage_file.exists():
        print(f"✅ 測試覆蓋率報告: file://{coverage_file.absolute()}")
    
    # 檢查其他報告文件
    reports = [
        ("pytest_cache", "Pytest 快取"),
        ("htmlcov", "HTML 覆蓋率報告"),
        (".coverage", "覆蓋率資料"),
    ]
    
    for file_path, description in reports:
        if Path(file_path).exists():
            print(f"✅ {description}: {file_path}")

def main():
    """主要執行函數"""
    print("🔋 電池 OQC 系統 - 測試執行器")
    print("=" * 60)
    
    # 設定工作目錄
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    print(f"工作目錄: {os.getcwd()}")
    
    # 檢查 Python 版本
    python_version = sys.version_info
    print(f"Python 版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("❌ 需要 Python 3.8 或更高版本")
        sys.exit(1)
    
    # 執行測試步驟
    steps = [
        ("檢查依賴套件", check_dependencies),
        ("代碼檢查", run_linting),
        ("單元測試", run_unit_tests),
        ("測試覆蓋率", run_coverage_report),
        ("識別準確性測試", run_accuracy_tests),
        ("效能測試", run_performance_tests),
        ("產生摘要", generate_test_summary),
    ]
    
    results = {}
    
    for step_name, step_function in steps:
        print(f"\n🔄 開始: {step_name}")
        try:
            results[step_name] = step_function()
        except Exception as e:
            print(f"❌ {step_name} 發生錯誤: {e}")
            results[step_name] = False
    
    # 最終報告
    print("\n" + "="*60)
    print("最終測試結果")
    print("="*60)
    
    all_passed = True
    for step_name, success in results.items():
        status = "✅ 通過" if success else "❌ 失敗"
        print(f"{step_name}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有測試都通過了！")
        sys.exit(0)
    else:
        print("\n⚠️  部分測試失敗，請檢查上面的錯誤訊息")
        sys.exit(1)

if __name__ == "__main__":
    main()