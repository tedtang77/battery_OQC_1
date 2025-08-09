#!/usr/bin/env python3
"""
電池識別準確性測試執行器
專門測試真實照片的識別準確性和完整性
"""

import subprocess
import sys
import os
from pathlib import Path
import json
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message, color=Colors.ENDC):
    """印出彩色訊息"""
    print(f"{color}{message}{Colors.ENDC}")

def print_banner():
    """印出測試橫幅"""
    banner = """
    🔋 電池識別準確性測試器 🔋
    ================================
    📸 真實照片識別驗證
    🤖 Claude AI vs 傳統 OCR 比較
    📊 詳細準確性分析報告
    ================================
    """
    print_colored(banner, Colors.CYAN + Colors.BOLD)

def check_test_environment():
    """檢查測試環境"""
    print_colored("🔍 檢查測試環境...", Colors.YELLOW)
    
    # 檢查 data 資料夾
    data_path = Path("data")
    if not data_path.exists():
        print_colored("❌ data 資料夾不存在", Colors.RED)
        return False
    
    # 檢查測試圖片
    test_images = [
        "PXL_20250724_010217469.jpg",
        "PXL_20250724_010602031.jpg"
    ]
    
    missing_images = []
    for image in test_images:
        if not (data_path / image).exists():
            missing_images.append(image)
    
    if missing_images:
        print_colored(f"⚠️  缺少測試圖片: {', '.join(missing_images)}", Colors.YELLOW)
        print_colored("   測試將會跳過缺少的圖片", Colors.YELLOW)
    
    # 檢查所有圖片
    image_files = list(data_path.glob("*.jpg")) + list(data_path.glob("*.jpeg")) + list(data_path.glob("*.png"))
    print_colored(f"✅ 找到 {len(image_files)} 個圖片檔案", Colors.GREEN)
    
    # 檢查後端依賴
    backend_path = Path("backend")
    if not backend_path.exists():
        print_colored("❌ backend 資料夾不存在", Colors.RED)
        return False
    
    requirements_file = backend_path / "requirements.txt"
    if requirements_file.exists():
        print_colored("✅ 找到 requirements.txt", Colors.GREEN)
    
    return True

def run_accuracy_tests():
    """執行準確性測試"""
    test_commands = [
        {
            'name': '真實圖片識別測試',
            'command': ['python', '-m', 'pytest', 'tests/test_real_image_recognition.py::TestRealImageRecognition', '-v', '-s'],
            'description': '測試特定圖片的識別準確性'
        },
        {
            'name': '識別方法比較測試',
            'command': ['python', '-m', 'pytest', 'tests/test_real_image_recognition.py::TestRealImageRecognition::test_recognition_methods_comparison', '-v', '-s'],
            'description': '比較 Claude AI 和傳統 OCR 效果'
        },
        {
            'name': '批次識別測試',
            'command': ['python', '-m', 'pytest', 'tests/test_real_image_recognition.py::TestRealImageRecognition::test_all_data_images_basic_recognition', '-v', '-s'],
            'description': '測試所有圖片的基本識別能力'
        },
        {
            'name': '識別一致性測試',
            'command': ['python', '-m', 'pytest', 'tests/test_real_image_recognition.py::TestImageRecognitionAccuracy', '-v', '-s'],
            'description': '測試識別結果的穩定性和一致性'
        }
    ]
    
    results = {}
    total_tests = len(test_commands)
    
    for i, test_info in enumerate(test_commands, 1):
        print_colored(f"\n{'='*60}", Colors.BLUE)
        print_colored(f"執行測試 {i}/{total_tests}: {test_info['name']}", Colors.BLUE + Colors.BOLD)
        print_colored(f"說明: {test_info['description']}", Colors.BLUE)
        print_colored(f"命令: {' '.join(test_info['command'])}", Colors.BLUE)
        print_colored(f"{'='*60}", Colors.BLUE)
        
        try:
            result = subprocess.run(
                test_info['command'],
                capture_output=True,
                text=True,
                cwd=Path.cwd(),
                timeout=300  # 5分鐘超時
            )
            
            if result.returncode == 0:
                print_colored("✅ 測試通過!", Colors.GREEN)
                results[test_info['name']] = {
                    'status': 'PASSED',
                    'output': result.stdout,
                    'error': result.stderr
                }
            else:
                print_colored("❌ 測試失敗!", Colors.RED)
                results[test_info['name']] = {
                    'status': 'FAILED',
                    'output': result.stdout,
                    'error': result.stderr
                }
                print_colored("錯誤輸出:", Colors.RED)
                if result.stderr:
                    print(result.stderr)
                if result.stdout:
                    print(result.stdout)
            
            # 顯示測試輸出的重要部分
            if result.stdout:
                # 尋找測試結果摘要
                lines = result.stdout.split('\n')
                for line in lines:
                    if '===' in line and ('識別結果' in line or '測試' in line):
                        print_colored(line, Colors.CYAN)
                    elif '完美匹配' in line or '良好匹配' in line or '準確率' in line:
                        print_colored(f"  {line}", Colors.YELLOW)
                    elif '總結:' in line or '成功處理' in line:
                        print_colored(f"  {line}", Colors.GREEN)
        
        except subprocess.TimeoutExpired:
            print_colored("⏰ 測試超時", Colors.RED)
            results[test_info['name']] = {
                'status': 'TIMEOUT',
                'output': '',
                'error': 'Test timed out after 5 minutes'
            }
        except Exception as e:
            print_colored(f"💥 測試執行錯誤: {str(e)}", Colors.RED)
            results[test_info['name']] = {
                'status': 'ERROR',
                'output': '',
                'error': str(e)
            }
    
    return results

def generate_test_report(results: dict):
    """生成測試報告"""
    print_colored(f"\n{'='*80}", Colors.BLUE + Colors.BOLD)
    print_colored("📊 測試結果總結", Colors.BLUE + Colors.BOLD)
    print_colored(f"{'='*80}", Colors.BLUE + Colors.BOLD)
    
    passed = sum(1 for r in results.values() if r['status'] == 'PASSED')
    failed = sum(1 for r in results.values() if r['status'] == 'FAILED')
    errors = sum(1 for r in results.values() if r['status'] in ['ERROR', 'TIMEOUT'])
    total = len(results)
    
    print_colored(f"\n總測試數: {total}", Colors.BLUE)
    print_colored(f"✅ 通過: {passed}", Colors.GREEN)
    print_colored(f"❌ 失敗: {failed}", Colors.RED)
    print_colored(f"💥 錯誤: {errors}", Colors.RED)
    print_colored(f"📈 通過率: {(passed/total)*100:.1f}%", Colors.CYAN)
    
    print_colored(f"\n詳細結果:", Colors.BLUE)
    for test_name, result in results.items():
        status_color = {
            'PASSED': Colors.GREEN,
            'FAILED': Colors.RED,
            'ERROR': Colors.RED,
            'TIMEOUT': Colors.RED
        }.get(result['status'], Colors.YELLOW)
        
        print_colored(f"  {result['status']:8} | {test_name}", status_color)
    
    # 生成 JSON 報告
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'pass_rate': (passed/total)*100
        },
        'results': results
    }
    
    report_file = f"accuracy_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        print_colored(f"\n📋 詳細報告已儲存: {report_file}", Colors.CYAN)
    except Exception as e:
        print_colored(f"⚠️  無法儲存報告: {str(e)}", Colors.YELLOW)
    
    return passed == total

def provide_recommendations(results: dict):
    """提供改善建議"""
    failed_tests = [name for name, result in results.items() if result['status'] != 'PASSED']
    
    if not failed_tests:
        print_colored(f"\n🎉 所有測試都通過了！系統識別功能運作正常。", Colors.GREEN + Colors.BOLD)
        return
    
    print_colored(f"\n💡 改善建議:", Colors.YELLOW + Colors.BOLD)
    
    recommendations = {
        '真實圖片識別測試': [
            "檢查圖片品質是否足夠清晰",
            "確認預期結果資料是否正確",
            "調整 OCR 預處理參數",
            "如果有 Claude AI，嘗試使用 API Key"
        ],
        '識別方法比較測試': [
            "確認 Anthropic API Key 是否正確設定",
            "檢查網路連線是否穩定",
            "比較不同圖片的識別效果",
            "考慮調整 Claude AI 模型版本"
        ],
        '批次識別測試': [
            "檢查 data 資料夾中所有圖片",
            "確認圖片格式是否支援",
            "檢查是否有損壞的圖片檔案",
            "優化批次處理的錯誤處理機制"
        ],
        '識別一致性測試': [
            "檢查識別演算法的穩定性",
            "確認沒有隨機因素影響結果",
            "檢查圖片預處理的一致性",
            "考慮增加結果快取機制"
        ]
    }
    
    for failed_test in failed_tests:
        if failed_test in recommendations:
            print_colored(f"\n🔧 {failed_test}:", Colors.YELLOW)
            for recommendation in recommendations[failed_test]:
                print_colored(f"  • {recommendation}", Colors.YELLOW)

def main():
    """主要執行函數"""
    print_banner()
    
    # 設定工作目錄
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    print_colored(f"工作目錄: {os.getcwd()}", Colors.BLUE)
    
    # 檢查環境
    if not check_test_environment():
        print_colored("❌ 環境檢查失敗，請確認設定後重新執行", Colors.RED)
        sys.exit(1)
    
    # 執行測試
    print_colored("\n🚀 開始執行準確性測試...", Colors.GREEN + Colors.BOLD)
    results = run_accuracy_tests()
    
    # 生成報告
    all_passed = generate_test_report(results)
    
    # 提供建議
    provide_recommendations(results)
    
    # 結束提示
    print_colored(f"\n{'='*80}", Colors.BLUE)
    if all_passed:
        print_colored("🎊 恭喜！所有識別測試都通過了！", Colors.GREEN + Colors.BOLD)
        print_colored("系統準備就緒，可以開始處理真實的電池照片。", Colors.GREEN)
        sys.exit(0)
    else:
        print_colored("⚠️  部分測試未通過，請查看上方建議進行改善。", Colors.YELLOW + Colors.BOLD)
        print_colored("您仍然可以使用系統，但準確性可能不如預期。", Colors.YELLOW)
        sys.exit(1)

if __name__ == "__main__":
    main()