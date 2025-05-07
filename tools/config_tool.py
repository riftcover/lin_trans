#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理工具

用于管理应用程序配置的命令行工具
"""

import os
import sys
import argparse
import yaml
from utils.config_manager import ConfigManager

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)


def show_config(args):
    """显示当前配置"""
    config_manager = ConfigManager()
    api_config = config_manager.get_api_config()

    print(f"当前环境: {config_manager.current_env}")

    # 显示API配置
    print("\nAPI配置:")
    for key, value in api_config.items():
        if key != 'web_urls':
            print(f"  {key}: {value}")

    # 显示网页URL配置
    if 'web_urls' in api_config:
        print("\n网页URL配置:")
        for key, value in api_config['web_urls'].items():
            print(f"  {key}: {value}")


def set_environment(args):
    """设置当前环境"""
    config_manager = ConfigManager()

    # 获取可用环境
    api_config_path = os.path.join(config_manager.config_dir, 'api_config.yaml')
    with open(api_config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)

    available_envs = [k for k in config_data.keys() if k != 'default']

    if args.env not in available_envs:
        print(f"错误: 环境 '{args.env}' 不存在")
        print(f"可用环境: {', '.join(available_envs)}")
        return

    # 设置默认环境
    config_data['default'] = args.env

    with open(api_config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)

    print(f"已将默认环境设置为: {args.env}")


def set_api_url(args):
    """设置API基础URL"""
    config_manager = ConfigManager()

    # 获取当前配置
    api_config_path = os.path.join(config_manager.config_dir, 'api_config.yaml')
    with open(api_config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)

    env = args.env or config_data.get('default', 'development')

    if env not in config_data:
        print(f"错误: 环境 '{env}' 不存在")
        return

    # 更新API基础URL
    config_data[env]['api_base_url'] = args.url

    with open(api_config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)

    print(f"已将环境 '{env}' 的API基础URL设置为: {args.url}")


def add_environment(args):
    """添加新环境"""
    config_manager = ConfigManager()

    # 获取当前配置
    api_config_path = os.path.join(config_manager.config_dir, 'api_config.yaml')
    with open(api_config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)

    if args.env in config_data:
        print(f"错误: 环境 '{args.env}' 已存在")
        return

    # 添加新环境 - 只包含URL配置
    config_data[args.env] = {
        'api_base_url': args.url,
        'web_base_url': args.web_base_url
    }

    with open(api_config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)

    print(f"已添加新环境: {args.env}")
    print(f"API基础URL: {args.url}")
    print(f"超时时间: {args.timeout}秒")
    print(f"网页基础URL: {args.web_base_url}")


def set_web_url(args):
    """设置网页URL"""
    config_manager = ConfigManager()

    # 获取当前配置
    api_config_path = os.path.join(config_manager.config_dir, 'api_config.yaml')
    with open(api_config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)

    env = args.env or config_data.get('default', 'development')

    if env not in config_data:
        print(f"错误: 环境 '{env}' 不存在")
        return

    # 如果是基础URL，直接更新环境配置
    if args.url_type == 'base':
        config_data[env]['web_base_url'] = args.url
        print(f"已将环境 '{env}' 的网页基础URL设置为: {args.url}")
    else:
        # 确保共享配置中有web_paths
        if 'common' not in config_data:
            config_data['common'] = {}
        if 'web_paths' not in config_data['common']:
            config_data['common']['web_paths'] = {}

        # 更新路径
        config_data['common']['web_paths'][args.url_type] = args.url
        print(f"已将所有环境的网页路径 '{args.url_type}' 设置为: {args.url}")

    with open(api_config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='配置管理工具')
    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # 显示配置命令
    show_parser = subparsers.add_parser('show', help='显示当前配置')

    # 设置环境命令
    env_parser = subparsers.add_parser('set-env', help='设置当前环境')
    env_parser.add_argument('env', help='环境名称')

    # 设置API URL命令
    url_parser = subparsers.add_parser('set-url', help='设置API基础URL')
    url_parser.add_argument('url', help='API基础URL')
    url_parser.add_argument('--env', help='环境名称（默认为当前环境）')

    # 设置网页URL命令
    web_url_parser = subparsers.add_parser('set-web-url', help='设置网页URL')
    web_url_parser.add_argument('url_type', choices=['base', 'forgot_password', 'register', 'terms', 'privacy', 'help'], help='URL类型')
    web_url_parser.add_argument('url', help='URL值')
    web_url_parser.add_argument('--env', help='环境名称（默认为当前环境）')

    # 添加环境命令
    add_parser = subparsers.add_parser('add-env', help='添加新环境')
    add_parser.add_argument('env', help='环境名称')
    add_parser.add_argument('url', help='API基础URL')
    add_parser.add_argument('--timeout', type=float, default=15.0, help='超时时间（秒）')
    add_parser.add_argument('--web-base-url', default='http://localhost:4000', help='网页基础URL')

    args = parser.parse_args()

    if args.command == 'show':
        show_config(args)
    elif args.command == 'set-env':
        set_environment(args)
    elif args.command == 'set-url':
        set_api_url(args)
    elif args.command == 'set-web-url':
        set_web_url(args)
    elif args.command == 'add-env':
        add_environment(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
