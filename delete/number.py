import hashlib

def generate_menu_code(text):
    # 移除所有空格和標點符號
    text = ''.join(e for e in text if e.isalnum())
    
    # 計算字串中所有字符的ASCII值總和
    ascii_sum = sum(ord(c) for c in text)
    
    # 使用ASCII總和的最後一位數字作為第一碼（確保是0-9之間）
    first_digit = str(ascii_sum % 10)
    
    # 生成原本的雜湊值（不含第一碼）
    hash_value = str(hash(text))
    
    # 取絕對值並保留7位數
    hash_value = str(abs(int(hash_value)))[-7:]
    
    # 組合第一碼數字和後面7碼
    code = first_digit + hash_value
    
    # 確保總長度為8位
    return code[:8].zfill(8)

# 使用示例
menu_items = [
    "小華堡餐(配中洋蔥圈)",
    "大麥克餐",
    "雞塊餐"
]

for item in menu_items:
    code = generate_menu_code(item)
    print(f"{item}: {code}")