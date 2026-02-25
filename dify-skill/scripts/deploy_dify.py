#!/usr/bin/env python3
"""
Dify 一键部署脚本
支持 Ubuntu 和 CentOS 操作系统
"""

import os
import sys
import subprocess
import platform
import shutil
import time
import urllib.request
import json

DIFY_VERSION = "main"
DIFY_REPO = "https://github.com/langgenius/dify.git"
DIFY_DOCKER_DIR = "docker"

MIN_CPU_CORES = 2
MIN_MEMORY_GB = 4

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
            sys.exit(1)
        return e

def detect_os():
    if os.path.exists('/etc/os-release'):
        with open('/etc/os-release', 'r') as f:
            content = f.read().lower()
            if 'ubuntu' in content:
                return 'ubuntu'
            elif 'centos' in content or 'rhel' in content or 'rocky' in content or 'almalinux' in content:
                return 'centos'
    return 'unknown'

def check_system_requirements():
    print_step(1, "检查系统要求")
    
    with open('/proc/cpuinfo', 'r') as f:
        cpu_cores = len([line for line in f if line.startswith('processor')])
    
    if cpu_cores < MIN_CPU_CORES:
        print_warning(f"CPU核心数({cpu_cores})低于推荐值({MIN_CPU_CORES})")
    else:
        print_success(f"CPU核心数: {cpu_cores}")
    
    with open('/proc/meminfo', 'r') as f:
        for line in f:
            if line.startswith('MemTotal'):
                mem_kb = int(line.split()[1])
                mem_gb = mem_kb / (1024 * 1024)
                break
    
    if mem_gb < MIN_MEMORY_GB:
        print_error(f"内存({mem_gb:.1f}GB)低于最低要求({MIN_MEMORY_GB}GB)")
        sys.exit(1)
    else:
        print_success(f"内存: {mem_gb:.1f}GB")
    
    os_type = detect_os()
    if os_type == 'unknown':
        print_error("不支持的操作系统，仅支持 Ubuntu 和 CentOS/RHEL 系列")
        sys.exit(1)
    print_success(f"操作系统: {os_type}")
    
    return os_type

def install_docker_ubuntu():
    print_step(2, "安装 Docker (Ubuntu)")
    
    run_command("apt-get update")
    run_command("apt-get install -y ca-certificates curl gnupg lsb-release")
    
    keyrings_dir = "/etc/apt/keyrings"
    os.makedirs(keyrings_dir, exist_ok=True)
    
    docker_gpg = f"{keyrings_dir}/docker.gpg"
    if not os.path.exists(docker_gpg):
        run_command(f"curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o {docker_gpg}")
    
    arch = subprocess.getoutput("dpkg --print-architecture")
    codename = subprocess.getoutput("lsb_release -cs")
    
    sources_list = "/etc/apt/sources.list.d/docker.list"
    with open(sources_list, 'w') as f:
        f.write(f"deb [arch={arch} signed-by={docker_gpg}] https://download.docker.com/linux/ubuntu {codename} stable\n")
    
    run_command("apt-get update")
    run_command("apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin")
    run_command("systemctl enable docker")
    run_command("systemctl start docker")
    
    print_success("Docker 安装完成")

def install_docker_centos():
    print_step(2, "安装 Docker (CentOS/RHEL)")
    
    run_command("yum install -y yum-utils")
    run_command("yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo")
    run_command("yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin")
    run_command("systemctl enable docker")
    run_command("systemctl start docker")
    
    print_success("Docker 安装完成")

def check_docker():
    result = run_command("docker --version", check=False, capture_output=True)
    if result.returncode == 0:
        print_success(f"Docker 已安装: {result.stdout.strip()}")
        return True
    return False

def check_docker_compose():
    result = run_command("docker compose version", check=False, capture_output=True)
    if result.returncode == 0:
        print_success(f"Docker Compose 已安装: {result.stdout.strip()}")
        return True
    return False

def clone_dify(install_dir):
    print_step(3, "获取 Dify 源码")
    
    if os.path.exists(os.path.join(install_dir, "dify")):
        print_warning("Dify 目录已存在，跳过克隆")
        return os.path.join(install_dir, "dify")
    
    run_command(f"git clone {DIFY_REPO} {install_dir}/dify")
    print_success("Dify 源码克隆完成")
    
    return os.path.join(install_dir, "dify")

def configure_env(dify_dir):
    print_step(4, "配置环境变量")
    
    docker_dir = os.path.join(dify_dir, DIFY_DOCKER_DIR)
    env_example = os.path.join(docker_dir, ".env.example")
    env_file = os.path.join(docker_dir, ".env")
    
    if not os.path.exists(env_example):
        print_error(f".env.example 文件不存在: {env_example}")
        sys.exit(1)
    
    if os.path.exists(env_file):
        print_warning(".env 文件已存在，跳过创建")
    else:
        shutil.copy(env_example, env_file)
        print_success(".env 文件已创建")
    
    return env_file

def start_dify(dify_dir):
    print_step(5, "启动 Dify 服务")
    
    docker_dir = os.path.join(dify_dir, DIFY_DOCKER_DIR)
    
    print("正在拉取 Docker 镜像...")
    run_command("docker compose pull", cwd=docker_dir)
    
    print("正在启动服务...")
    run_command("docker compose up -d", cwd=docker_dir)
    
    print_success("Dify 服务启动完成")

def check_service_status(dify_dir):
    print_step(6, "检查服务状态")
    
    docker_dir = os.path.join(dify_dir, DIFY_DOCKER_DIR)
    result = run_command("docker compose ps", cwd=docker_dir, capture_output=True)
    print(result.stdout)
    
    print_success("服务状态检查完成")

def get_access_info():
    print_step(7, "访问信息")
    
    print("\n" + "=" * 50)
    print_color('GREEN', "Dify 部署成功!")
    print("=" * 50)
    print("\n请通过以下地址访问 Dify:")
    print_color('YELLOW', "  本地环境: http://localhost/install")
    print_color('YELLOW', "  服务器环境: http://<服务器IP>/install")
    print("\n首次访问需要设置管理员账号。")
    print("\n常用命令:")
    print("  停止服务: cd dify/docker && docker compose down")
    print("  重启服务: cd dify/docker && docker compose restart")
    print("  查看日志: cd dify/docker && docker compose logs -f")
    print("  升级版本: cd dify && git pull && cd docker && docker compose pull && docker compose up -d")
    print("=" * 50)

def deploy_dify(install_dir=None):
    if install_dir is None:
        install_dir = os.getcwd()
    
    print_color('GREEN', "\n" + "=" * 50)
    print_color('GREEN', "Dify 一键部署脚本")
    print_color('GREEN', "=" * 50)
    
    os_type = check_system_requirements()
    
    if not check_docker():
        if os_type == 'ubuntu':
            install_docker_ubuntu()
        else:
            install_docker_centos()
    else:
        if not check_docker_compose():
            print_error("Docker Compose 未安装")
            sys.exit(1)
    
    dify_dir = clone_dify(install_dir)
    configure_env(dify_dir)
    start_dify(dify_dir)
    check_service_status(dify_dir)
    get_access_info()

def stop_dify(dify_dir):
    docker_dir = os.path.join(dify_dir, DIFY_DOCKER_DIR)
    run_command("docker compose down", cwd=docker_dir)
    print_success("Dify 服务已停止")

def restart_dify(dify_dir):
    docker_dir = os.path.join(dify_dir, DIFY_DOCKER_DIR)
    run_command("docker compose restart", cwd=docker_dir)
    print_success("Dify 服务已重启")

def upgrade_dify(dify_dir):
    print_step(1, "更新代码")
    run_command("git pull", cwd=dify_dir)
    
    print_step(2, "更新镜像")
    docker_dir = os.path.join(dify_dir, DIFY_DOCKER_DIR)
    run_command("docker compose pull", cwd=docker_dir)
    
    print_step(3, "重启服务")
    run_command("docker compose up -d", cwd=docker_dir)
    
    print_success("Dify 升级完成")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Dify 一键部署脚本")
    parser.add_argument("action", choices=["deploy", "stop", "restart", "upgrade"], 
                        help="执行的操作: deploy(部署), stop(停止), restart(重启), upgrade(升级)")
    parser.add_argument("--dir", default=None, help="安装目录，默认当前目录")
    
    args = parser.parse_args()
    
    if os.geteuid() != 0:
        print_error("请使用 root 权限运行此脚本")
        sys.exit(1)
    
    if args.action == "deploy":
        deploy_dify(args.dir)
    elif args.action == "stop":
        stop_dify(args.dir or os.path.join(os.getcwd(), "dify"))
    elif args.action == "restart":
        restart_dify(args.dir or os.path.join(os.getcwd(), "dify"))
    elif args.action == "upgrade":
        upgrade_dify(args.dir or os.path.join(os.getcwd(), "dify"))
