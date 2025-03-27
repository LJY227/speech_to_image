import os
import sys
import subprocess
import importlib.util

def check_module(module_name):
    """检查模块是否已安装"""
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except ImportError:
        return False

def install_module(module_name):
    """安装Python模块"""
    print(f"正在安装 {module_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
        print(f"{module_name} 安装成功")
        return True
    except subprocess.CalledProcessError:
        print(f"{module_name} 安装失败")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("Whisper语音识别节点依赖安装")
    print("=" * 50)
    
    # 检查并安装必要的Python模块
    required_modules = [
        "pyaudio",
        "numpy",
        "faster-whisper"
    ]
    
    missing_modules = []
    for module in required_modules:
        module_name = module.split("==")[0]
        if not check_module(module_name):
            missing_modules.append(module)
    
    if missing_modules:
        print(f"缺少以下模块: {', '.join(missing_modules)}")
        for module in missing_modules:
            install_module(module)
    else:
        print("所有必要的Python模块都已安装")
    
    print("\n安装完成！请重启ComfyUI来加载Whisper语音识别节点。")
    
if __name__ == "__main__":
    main()
    input("按Enter键退出...") 