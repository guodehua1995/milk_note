from django.core.management.base import BaseCommand
from chat.views import update_issue_memory

class Command(BaseCommand):
    """
    管理命令：更新所有事项的长期记忆
    每30分钟在后台自动调用一次
    """
    help = '更新所有事项的长期记忆'
    
    def handle(self, *args, **options):
        """执行命令"""
        self.stdout.write('开始更新事项长期记忆...')
        update_issue_memory()
        self.stdout.write(self.style.SUCCESS('事项长期记忆更新完成！'))