from pypinyin import lazy_pinyin
import re
import hashlib

def convert_to_code(name):
    # 移除所有符號和空格，只保留字母和數字
    name = re.sub(r'[^\w\s\u4e00-\u9fff]', '', name)
    
    # 檢查是否包含中文字符
    if any('\u4e00' <= char <= '\u9fff' for char in name):
        # 轉換中文為拼音，並取得首字母
        pinyin = ''.join([word[0] for word in lazy_pinyin(name)])
    else:
        # 如果是英文，移除所有空格
        pinyin = re.sub(r'\s+', '', name)
    
    # 轉換為大寫並取前5個字符
    return pinyin.upper()[:5]

def generate_menu_code(text):
    """
    根據餐點名稱生成固定的編碼
    格式：2位數字 + 6位英文字母
    """
    # 移除所有空格和標點符號
    text = ''.join(e for e in text if e.isalnum())
    
    # 使用 MD5 生成雜湊值
    hash_obj = hashlib.md5(text.encode('utf-8'))
    hash_value = hash_obj.hexdigest()
    
    # 使用前4個字符生成2位數字（00-99）
    numbers = ''.join([
        str(int(hash_value[i:i+2], 16) % 10)
        for i in range(0, 4, 2)
    ])[:2]
    
    # 使用剩餘的雜湊值生成6位英文字母（A-Z）
    letters = ''.join([
        chr(65 + int(hash_value[i:i+2], 16) % 26)
        for i in range(4, 16, 2)
    ])[:6]
    
    # 組合編碼：2位數字 + 6位英文字母
    return numbers + letters

def process_menu_codes(file_path):
    """
    處理Excel文件並生成編號
    返回新文件路徑或錯誤訊息
    """
    import pandas as pd
    import os
    
    try:
        # 檢查文件是否存在
        if not os.path.exists(file_path):
            return None, "文件不存在"
            
        # 讀取Excel檔案
        df = pd.read_excel(file_path)
        
        if df.empty:
            return None, "文件是空的"
        
        # 尋找必要的欄位
        menu_name_col = None
        restaurant_col = None
        for col in df.columns:
            if "餐點名稱" in col:
                menu_name_col = col
            if "餐廳" in col:
                restaurant_col = col
        
        if menu_name_col is None:
            return None, "找不到'餐點名稱'欄位"
            
        if restaurant_col is None:
            return None, "找不到'餐廳'欄位"

        # 生成餐點編號
        df["餐點編號"] = df[menu_name_col].astype(str).apply(generate_menu_code)
        
        # 生成餐廳編號
        df["餐廳編號"] = df[restaurant_col].astype(str).apply(convert_to_code)
        
        # 組合完整編號
        df["菜牌編號"] = df["餐廳編號"] + "-" + df["餐點編號"]
        
        # 生成新檔名
        file_dir = os.path.dirname(file_path)
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        new_file_path = os.path.join(file_dir, f"{file_name}_with_codes.xlsx")
        
        # 儲存新檔案
        df.to_excel(new_file_path, index=False)
        
        return new_file_path, None
        
    except pd.errors.EmptyDataError:
        return None, "文件是空的或格式不正確"
    except Exception as e:
        return None, f"處理文件時發生錯誤: {str(e)}" 