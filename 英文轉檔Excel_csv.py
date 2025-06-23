#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CSV BOM转换工具

这个脚本用于将普通CSV文件转换为带BOM的UTF-8格式CSV文件。
主要解决在某些应用程序（如Microsoft Excel）中打开含有中文的CSV文件时出现乱码的问题。
"""

import os
import codecs
import shutil
from datetime import datetime

def ensure_directory_exists(directory):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"已创建目录: {directory}")

def convert_csv_to_bom(input_path, output_path):
    """将CSV文件转换为带BOM的UTF-8格式"""
    try:
        # 读取原始CSV文件
        with open(input_path, 'r', encoding='utf-8') as input_file:
            content = input_file.read()
        
        # 写入带BOM的UTF-8文件
        with codecs.open(output_path, 'w', encoding='utf-8-sig') as output_file:
            output_file.write(content)
        
        print(f"✅ 成功转换: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
        return True
    except Exception as e:
        print(f"❌ 转换失败: {os.path.basename(input_path)}")
        print(f"   错误信息: {str(e)}")
        return False

def main():
    # 设置输入和输出目录
    input_dir = "input/01_下載/英文轉檔/in"
    output_dir = "input/01_下載/英文轉檔/out"
    
    # 确保目录存在
    ensure_directory_exists(input_dir)
    ensure_directory_exists(output_dir)
    
    # 获取当前日期作为文件名后缀
    date_suffix = datetime.now().strftime("%Y%m%d")
    
    # 获取输入目录中的所有CSV文件
    csv_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.csv')]
    
    if not csv_files:
        print(f"⚠️ 警告: 在 {input_dir} 目录中没有找到CSV文件")
        return
    
    success_count = 0
    
    # 处理每个CSV文件
    for csv_file in csv_files:
        input_path = os.path.join(input_dir, csv_file)
        
        # 生成输出文件名: 原文件名_日期_BOM.csv
        file_name_without_ext = os.path.splitext(csv_file)[0]
        output_file = f"{file_name_without_ext}_{date_suffix}_BOM.csv"
        output_path = os.path.join(output_dir, output_file)
        
        # 转换文件
        if convert_csv_to_bom(input_path, output_path):
            success_count += 1
    
    # 输出转换结果摘要
    if success_count > 0:
        print(f"\n转换完成! 共处理 {len(csv_files)} 个文件，成功转换 {success_count} 个。")
        print(f"转换后的文件已保存到: {os.path.abspath(output_dir)}")
    else:
        print("\n⚠️ 警告: 没有成功转换任何文件")

if __name__ == "__main__":
    main() 