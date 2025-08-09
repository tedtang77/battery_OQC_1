#!/usr/bin/env python3
"""
開發環境啟動腳本
一鍵啟動整個電池 OQC 系統
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path
import threading
import webbrowser

class Colors:
    """終端顏色"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message, color=Colors.ENDC):
    """印出彩色訊息"""
    print(f"{color}{message}{Colors.ENDC}")

def print_banner():
    """印出系統橫幅"""
    banner = """
    ⚡ 電池 OQC 系統 開發環境啟動器 ⚡
    =====================================
    🔋 自動識別電池芯資訊並匯入資料庫
    =====================================
    """
    print_colored(banner, Colors.BLUE + Colors.BOLD)

def check_dependencies():
    """檢查系統依賴"""
    print_colored("🔍 檢查系統依賴...", Colors.YELLOW)
    
    dependencies = {
        'python': ['python', '--version'],
        'node': ['node', '--version'],
        'npm': ['npm', '--version'],
        'tesseract': ['tesseract', '--version'],
    }
    
    missing = []
    
    for name, command in dependencies.items():
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print_colored(f"  ✅ {name}: {version}", Colors.GREEN)
            else:
                missing.append(name)
        except FileNotFoundError:
            missing.append(name)
            print_colored(f"  ❌ {name}: 未安裝", Colors.RED)
    
    if missing:
        print_colored(f"\n❌ 缺少依賴: {', '.join(missing)}", Colors.RED)
        print_colored("請參考 SETUP.md 安裝必要的依賴", Colors.YELLOW)
        return False
    
    print_colored("✅ 所有依賴都已安裝", Colors.GREEN)
    return True

def check_data_folder():
    """檢查資料夾"""
    data_folder = Path("data")
    if not data_folder.exists():
        print_colored("❌ data 資料夾不存在", Colors.RED)
        return False
    
    image_files = list(data_folder.glob("*.jpg")) + list(data_folder.glob("*.png"))
    
    if not image_files:
        print_colored("⚠️  data 資料夾中沒有圖片檔案", Colors.YELLOW)
    else:
        print_colored(f"✅ 找到 {len(image_files)} 個圖片檔案", Colors.GREEN)
    
    return True

def setup_backend():
    """設置後端環境"""
    print_colored("🔧 設置 Backend 環境...", Colors.YELLOW)
    
    backend_dir = Path("backend")
    
    # 檢查虛擬環境
    venv_dir = backend_dir / "venv"
    if not venv_dir.exists():
        print_colored("  📦 建立虛擬環境...", Colors.BLUE)
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], cwd=backend_dir)
    
    # 安裝依賴
    pip_path = venv_dir / ("Scripts" if os.name == 'nt' else "bin") / "pip"
    print_colored("  📦 安裝 Python 套件...", Colors.BLUE)
    subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], cwd=backend_dir)
    
    # 檢查環境變數檔案
    env_file = backend_dir / ".env"
    env_example = backend_dir / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        print_colored("  ⚙️  建立環境變數檔案...", Colors.BLUE)
        subprocess.run(["cp", str(env_example), str(env_file)])
        print_colored("  ⚠️  請編輯 backend/.env 檔案設置正確的資料庫連線", Colors.YELLOW)
    
    print_colored("✅ Backend 環境設置完成", Colors.GREEN)

def setup_frontend():
    """設置前端環境"""
    print_colored("🔧 設置 Frontend 環境...", Colors.YELLOW)
    
    frontend_dir = Path("frontend")
    node_modules = frontend_dir / "node_modules"
    
    if not node_modules.exists():
        print_colored("  📦 安裝 Node.js 套件...", Colors.BLUE)
        subprocess.run(["npm", "install"], cwd=frontend_dir)
    
    print_colored("✅ Frontend 環境設置完成", Colors.GREEN)

class ServiceRunner:
    """服務執行器"""
    
    def __init__(self):
        self.processes = {}
        self.running = True
    
    def run_service(self, name, command, cwd=None, env=None):
        """執行服務"""
        print_colored(f"🚀 啟動 {name}...", Colors.BLUE)
        
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes[name] = process
            
            # 啟動輸出監控線程
            threading.Thread(
                target=self._monitor_output,
                args=(name, process),
                daemon=True
            ).start()
            
            return True
            
        except Exception as e:
            print_colored(f"❌ 啟動 {name} 失敗: {e}", Colors.RED)
            return False
    
    def _monitor_output(self, name, process):
        """監控服務輸出"""
        for line in iter(process.stdout.readline, ''):
            if self.running:
                # 過濾重要訊息
                if any(keyword in line.lower() for keyword in ['error', 'failed', 'exception']):
                    print_colored(f"[{name}] {line.strip()}", Colors.RED)
                elif any(keyword in line.lower() for keyword in ['running', 'started', 'listening']):
                    print_colored(f"[{name}] {line.strip()}", Colors.GREEN)
    
    def stop_all(self):
        """停止所有服務"""
        self.running = False
        print_colored("\n🛑 正在停止所有服務...", Colors.YELLOW)
        
        for name, process in self.processes.items():
            if process.poll() is None:
                print_colored(f"  停止 {name}...", Colors.BLUE)
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        print_colored("✅ 所有服務已停止", Colors.GREEN)

def wait_for_service(url, service_name, timeout=60):
    """等待服務啟動"""
    import requests
    
    print_colored(f"⏳ 等待 {service_name} 啟動...", Colors.YELLOW)
    
    for i in range(timeout):
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                print_colored(f"✅ {service_name} 已啟動", Colors.GREEN)
                return True
        except:
            pass
        
        time.sleep(1)
    
    print_colored(f"❌ {service_name} 啟動超時", Colors.RED)
    return False

def main():
    """主要執行函數"""
    print_banner()
    
    # 檢查依賴
    if not check_dependencies():
        sys.exit(1)
    
    # 檢查資料夾
    if not check_data_folder():
        sys.exit(1)
    
    # 設置環境
    setup_backend()
    setup_frontend()
    
    # 建立服務執行器
    runner = ServiceRunner()
    
    try:
        # 啟動 Backend
        backend_env = os.environ.copy()
        backend_env['PYTHONPATH'] = str(Path("backend").absolute())
        
        python_path = Path("backend/venv/bin/python")
        if not python_path.exists():
            python_path = Path("backend/venv/Scripts/python.exe")
        if not python_path.exists():
            python_path = Path(sys.executable)
        
        backend_success = runner.run_service(
            "Backend",
            [str(python_path), "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            cwd="backend",
            env=backend_env
        )
        
        if backend_success:
            # 等待 Backend 啟動
            if wait_for_service("http://localhost:8000", "Backend"):
                # 啟動 Frontend
                frontend_success = runner.run_service(
                    "Frontend",
                    ["npm", "run", "dev"],
                    cwd="frontend"
                )
                
                if frontend_success:
                    # 等待 Frontend 啟動
                    if wait_for_service("http://localhost:3000", "Frontend"):
                        print_colored("\n🎉 系統啟動成功！", Colors.GREEN + Colors.BOLD)
                        print_colored("📊 前端界面: http://localhost:3000", Colors.BLUE)
                        print_colored("🔧 後端 API: http://localhost:8000", Colors.BLUE)
                        print_colored("📚 API 文檔: http://localhost:8000/docs", Colors.BLUE)
                        
                        # 自動開啟瀏覽器
                        time.sleep(2)
                        webbrowser.open("http://localhost:3000")
                        
                        print_colored("\n按 Ctrl+C 停止系統", Colors.YELLOW)
                        
                        # 等待中斷信號
                        signal.signal(signal.SIGINT, lambda sig, frame: runner.stop_all())
                        
                        # 保持主線程運行
                        while runner.running:
                            time.sleep(1)
    
    except KeyboardInterrupt:
        runner.stop_all()
    except Exception as e:
        print_colored(f"❌ 系統啟動失敗: {e}", Colors.RED)
        runner.stop_all()
        sys.exit(1)

if __name__ == "__main__":
    main()