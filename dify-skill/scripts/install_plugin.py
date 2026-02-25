#!/usr/bin/env python3
"""
Dify 插件安装脚本
支持通过插件地址或插件名称安装插件
支持 Ubuntu 和 CentOS 操作系统
"""

import os
import sys
import subprocess
import shutil
import tempfile
import urllib.request
import json
import re
from pathlib import Path

DIFY_CLI_VERSION = "latest"
DIFY_CLI_RELEASES_URL = "https://api.github.com/repos/langgenius/dify-plugin-daemon/releases/latest"

COLORS = {
    'RED': '\033[0;31m',
    'GREEN': '\033[0;32m',
    'YELLOW': '\033[1;33m',
    'BLUE': '\033[0;34m',
    'NC': '\033[0m'
}

def print_color(color, message):
    print(f"{COLORS.get(color, '')}{message}{COLORS['NC']}")

def print_step(step, message):
    print_color('BLUE', f"\n[步骤 {step}] {message}")
    print("-" * 50)

def print_success(message):
    print_color('GREEN', f"✓ {message}")

def print_error(message):
    print_color('RED', f"✗ {message}")

def print_warning(message):
    print_color('YELLOW', f"⚠ {message}")

def run_command(cmd, cwd=None, check=True, capture_output=False):
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            print_error(f"命令执行失败: {cmd}")
            if e.stderr:
                print_error(f"错误信息: {e.stderr}")
            return None
        return e

def detect_os():
    system = sys.platform.lower()
    if system.startswith('linux'):
        return 'linux'
    elif system == 'darwin':
        return 'darwin'
    elif system.startswith('win'):
        return 'windows'
    return 'unknown'

def detect_arch():
    import platform
    machine = platform.machine().lower()
    if machine in ['x86_64', 'amd64']:
        return 'amd64'
    elif machine in ['arm64', 'aarch64']:
        return 'arm64'
    return 'unknown'

def install_dify_cli():
    print_step(1, "检查并安装 Dify CLI 工具")
    
    result = run_command("dify version", check=False, capture_output=True)
    if result and result.returncode == 0:
        print_success(f"Dify CLI 已安装: {result.stdout.strip()}")
        return True
    
    os_type = detect_os()
    arch = detect_arch()
    
    if os_type == 'unknown' or arch == 'unknown':
        print_error(f"不支持的系统或架构: {os_type}/{arch}")
        return False
    
    if os_type == 'linux':
        print("正在通过 Homebrew 安装...")
        result = run_command("which brew", check=False, capture_output=True)
        if result and result.returncode == 0:
            run_command("brew tap langgenius/dify")
            run_command("brew install dify")
        else:
            print("正在下载二进制文件...")
            cli_filename = f"dify-plugin-{os_type}-{arch}"
            download_url = f"https://github.com/langgenius/dify-plugin-daemon/releases/latest/download/{cli_filename}"
            
            download_path = "/tmp/dify"
            try:
                urllib.request.urlretrieve(download_url, download_path)
                os.chmod(download_path, 0o755)
                run_command(f"sudo mv {download_path} /usr/local/bin/dify")
                print_success("Dify CLI 安装完成")
            except Exception as e:
                print_error(f"下载失败: {e}")
                return False
    elif os_type == 'darwin':
        result = run_command("which brew", check=False, capture_output=True)
        if result and result.returncode == 0:
            run_command("brew tap langgenius/dify")
            run_command("brew install dify")
        else:
            print_warning("建议安装 Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            return False
    
    result = run_command("dify version", check=False, capture_output=True)
    if result and result.returncode == 0:
        print_success(f"Dify CLI 安装成功: {result.stdout.strip()}")
        return True
    
    return False

def check_python_version():
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 12):
        print_error(f"Python 版本过低 ({version.major}.{version.minor})，需要 3.12 或更高版本")
        return False
    print_success(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
    return True

def install_plugin_from_github(github_url, target_dir=None):
    print_step(2, f"从 GitHub 安装插件: {github_url}")
    
    if target_dir is None:
        target_dir = tempfile.mkdtemp()
    
    if github_url.endswith('.git'):
        repo_name = github_url.split('/')[-1].replace('.git', '')
    else:
        repo_name = github_url.split('/')[-1]
    
    plugin_dir = os.path.join(target_dir, repo_name)
    
    if os.path.exists(plugin_dir):
        shutil.rmtree(plugin_dir)
    
    result = run_command(f"git clone {github_url} {plugin_dir}", check=False)
    if result is None:
        print_error("克隆仓库失败")
        return None
    
    print_success(f"插件源码已下载到: {plugin_dir}")
    return plugin_dir

def install_plugin_from_local(local_path):
    print_step(2, f"从本地路径安装插件: {local_path}")
    
    if not os.path.exists(local_path):
        print_error(f"路径不存在: {local_path}")
        return None
    
    return os.path.abspath(local_path)

def package_plugin(plugin_dir):
    print_step(3, "打包插件")
    
    if not os.path.exists(os.path.join(plugin_dir, ".env")):
        env_example = os.path.join(plugin_dir, ".env.example")
        if os.path.exists(env_example):
            shutil.copy(env_example, os.path.join(plugin_dir, ".env"))
            print_success(".env 文件已创建")
    
    result = run_command(f"dify plugin package ./{os.path.basename(plugin_dir)}", 
                         cwd=os.path.dirname(plugin_dir), 
                         check=False, 
                         capture_output=True)
    
    if result and result.returncode == 0:
        print_success("插件打包成功")
        dify_pkg_path = os.path.join(os.path.dirname(plugin_dir), f"{os.path.basename(plugin_dir)}.difypkg")
        if os.path.exists(dify_pkg_path):
            print_success(f"插件包位置: {dify_pkg_path}")
            return dify_pkg_path
    
    print_error("插件打包失败")
    return None

def configure_dify_for_plugin(dify_dir):
    print_step(4, "配置 Dify 以支持插件")
    
    middleware_env = os.path.join(dify_dir, "docker", "middleware.env")
    
    if not os.path.exists(middleware_env):
        print_warning(f"middleware.env 文件不存在: {middleware_env}")
        return False
    
    with open(middleware_env, 'r') as f:
        content = f.read()
    
    if "force_verifying_signature" not in content:
        with open(middleware_env, 'a') as f:
            f.write("\n# 关闭插件签名验证（开发环境）\n")
            f.write("force_verifying_signature=false\n")
        print_success("已关闭插件签名验证")
    
    return True

def get_plugin_install_info():
    print_step(5, "获取插件安装信息")
    
    print("\n请按以下步骤获取插件安装信息:")
    print("1. 登录 Dify 控制台")
    print("2. 点击右上角的 '插件' 图标")
    print("3. 点击调试图标（虫子图标）")
    print("4. 复制 'API Key' 和 'Host Address'")
    
    api_key = input("\n请输入 API Key: ").strip()
    host_address = input("请输入 Host Address: ").strip()
    
    return api_key, host_address

def create_plugin_env(plugin_dir, api_key, host_address):
    env_file = os.path.join(plugin_dir, ".env")
    
    env_content = f"""INSTALL_METHOD=remote
REMOTE_INSTALL_HOST={host_address}
REMOTE_INSTALL_PORT=5003
REMOTE_INSTALL_KEY={api_key}
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print_success(".env 文件已配置")

def run_plugin_debug(plugin_dir):
    print_step(6, "运行插件调试")
    
    requirements_file = os.path.join(plugin_dir, "requirements.txt")
    if os.path.exists(requirements_file):
        print("正在安装依赖...")
        run_command(f"pip install -r {requirements_file}")
    
    print("正在启动插件...")
    run_command("python -m main", cwd=plugin_dir)

def install_plugin_from_marketplace(plugin_name, dify_dir):
    print_step(2, f"从 Marketplace 安装插件: {plugin_name}")
    
    print("\n请按以下步骤在 Dify 中安装插件:")
    print("1. 登录 Dify 控制台")
    print("2. 点击右上角的 '插件' 图标")
    print("3. 在 Marketplace 中搜索插件")
    print("4. 点击安装按钮")
    
    print_warning("Marketplace 插件安装需要通过 Dify Web 界面完成")
    return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Dify 插件安装脚本")
    parser.add_argument("source", help="插件来源: GitHub URL、本地路径或插件名称")
    parser.add_argument("--type", choices=["github", "local", "marketplace"], 
                        default="github", help="插件来源类型")
    parser.add_argument("--dify-dir", default=None, help="Dify 安装目录")
    parser.add_argument("--debug", action="store_true", help="启动调试模式")
    parser.add_argument("--package-only", action="store_true", help="仅打包插件，不安装")
    
    args = parser.parse_args()
    
    print_color('GREEN', "\n" + "=" * 50)
    print_color('GREEN', "Dify 插件安装脚本")
    print_color('GREEN', "=" * 50)
    
    if not check_python_version():
        sys.exit(1)
    
    if not install_dify_cli():
        sys.exit(1)
    
    plugin_dir = None
    
    if args.type == "github":
        if args.source.startswith("http"):
            plugin_dir = install_plugin_from_github(args.source)
        else:
            github_url = f"https://github.com/{args.source}"
            plugin_dir = install_plugin_from_github(github_url)
    elif args.type == "local":
        plugin_dir = install_plugin_from_local(args.source)
    elif args.type == "marketplace":
        install_plugin_from_marketplace(args.source, args.dify_dir)
        return
    
    if plugin_dir is None:
        print_error("插件目录获取失败")
        sys.exit(1)
    
    pkg_path = package_plugin(plugin_dir)
    
    if args.package_only:
        print_success(f"插件已打包: {pkg_path}")
        return
    
    if args.dify_dir:
        configure_dify_for_plugin(args.dify_dir)
    
    if args.debug:
        api_key, host_address = get_plugin_install_info()
        create_plugin_env(plugin_dir, api_key, host_address)
        run_plugin_debug(plugin_dir)
    else:
        print("\n插件打包完成！")
        print("请通过以下方式安装插件:")
        print("1. 登录 Dify 控制台")
        print("2. 点击右上角的 '插件' 图标")
        print("3. 点击 '安装插件' 按钮")
        print(f"4. 选择插件包: {pkg_path}")

if __name__ == "__main__":
    main()
