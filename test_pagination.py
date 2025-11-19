import os
import sys
import django

# 添加项目web目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web'))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'milk_note.settings')
django.setup()

# 导入必要的模块
from chat.services.memory_manager import MemoryManager

def test_pagination():
    """测试分页查询功能"""
    print("开始测试分页功能...")
    
    # 假设使用用户ID为1进行测试
    user_id = 1
    
    # 创建MemoryManager实例
    memory_manager = MemoryManager(user_id)
    
    # 测试第一页，每页5条数据
    print("\n测试第1页，每页5条数据:")
    result1 = memory_manager.get_user_conversations(page=1, page_size=5)
    print(f"总记录数: {result1['pagination']['total_items']}")
    print(f"总页数: {result1['pagination']['total_pages']}")
    print(f"当前页码: {result1['pagination']['page']}")
    print(f"每页大小: {result1['pagination']['page_size']}")
    print(f"是否有下一页: {result1['pagination']['has_next']}")
    print(f"是否有上一页: {result1['pagination']['has_prev']}")
    print(f"当前页记录数: {len(result1['items'])}")
    
    # 如果有下一页，测试第二页
    if result1['pagination']['has_next']:
        print("\n测试第2页，每页5条数据:")
        result2 = memory_manager.get_user_conversations(page=2, page_size=5)
        print(f"当前页码: {result2['pagination']['page']}")
        print(f"当前页记录数: {len(result2['items'])}")
        print(f"是否有下一页: {result2['pagination']['has_next']}")
    
    # 测试无效的页码（应该自动修正为第一页）
    print("\n测试无效的页码（0）:")
    result_invalid = memory_manager.get_user_conversations(page=0, page_size=5)
    print(f"实际页码: {result_invalid['pagination']['page']}")
    
    # 测试向后兼容（只使用limit参数）
    print("\n测试向后兼容（只使用limit参数）:")
    result_compat = memory_manager.get_user_conversations(limit=3)
    print(f"总记录数: {result_compat['pagination']['total_items']}")
    print(f"每页大小: {result_compat['pagination']['page_size']}")
    print(f"当前页记录数: {len(result_compat['items'])}")
    
    print("\n分页功能测试完成！")

if __name__ == "__main__":
    test_pagination()