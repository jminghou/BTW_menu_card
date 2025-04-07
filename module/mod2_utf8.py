import os
import csv

# 定義函數來轉換 CSV 文件為 Unicode 文本文件
def convert_csv_to_unicode_txt(file_paths):
    for file_path in file_paths:
        # 確定輸出文件名
        base_name = os.path.splitext(file_path)[0]
        output_file = f"{base_name}.txt"
        
        # 讀取 CSV 並寫入到 TXT
        with open(file_path, 'r', encoding='utf-8-sig') as csv_file:
            reader = csv.reader(csv_file)
            with open(output_file, 'w', encoding='utf-8') as txt_file:
                for row in reader:
                    txt_file.write(' '.join(row) + '\n')

        print(f"已轉換: {output_file}")
