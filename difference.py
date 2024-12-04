def calculate_menu_difference(menu_a: list, menu_b: list, encoding='utf-8') -> list:
    """
    計算兩個菜單的差集 (B - A)
    
    參數:
        menu_a: 11月菜單列表
        menu_b: 12月菜單列表
        encoding: 文件編碼格式
    
    返回:
        list: 只在B菜單中出現的菜品列表
    """
    # 將菜單轉換為集合
    set_a = set(menu_a)
    set_b = set(menu_b)
    
    # 計算差集
    menu_c = set_b - set_a
    
    # 轉回列表並排序
    return sorted(list(menu_c))

# 從文件讀取菜單的範例
def read_menu_from_file(filename: str, encoding='utf-8') -> list:
    with open(filename, encoding=encoding) as f:
        return [line.strip() for line in f if line.strip()]

# 寫入結果到文件的範例
def write_menu_to_file(menu: list, filename: str, encoding='utf-8'):
    with open(filename, 'w', encoding=encoding) as f:
        for item in menu:
            f.write(f"{item}\n")

# 使用示例
if __name__ == "__main__":
    # 從文件讀取菜單
    menu_a = read_menu_from_file('menu_a.txt')
    menu_b = read_menu_from_file('menu_b.txt')
    
    # 計算差集
    menu_c = calculate_menu_difference(menu_a, menu_b)
    
    # 寫入結果
    write_menu_to_file(menu_c, 'menu_c.txt')
    
    # 印出統計資訊
    print(f"A菜單數量: {len(menu_a)}")
    print(f"B菜單數量: {len(menu_b)}")
    print(f"C菜單數量 (B-A): {len(menu_c)}")