from django.db import models

# Create your models here.

class LongSummary(models.Model):
    '''
    长期记忆表
    基础对话设置,包含性格设定,称呼,身份,个人爱好等
    以及过去对话记录的总结
    '''
    user_id = models.CharField(max_length=255)
    content = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

class Schedule(models.Model):
    '''
    计划表
    包含用户设置的计划,如提醒,待办事项等
    '''
    user_id = models.CharField(max_length=255) # 用户id
    content = models.TextField() # 计划内容
    schedule_time = models.DateTimeField() # 计划时间
    schedule_status = models.SmallIntegerField(default=0) # 计划状态,0:未完成,1:已完成
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

class ChatLog(models.Model):
    '''
    聊天记录表
    包含用户与AI的每次对话记录
    '''
    user_id = models.CharField(max_length=255) # 用户id
    ask_content = models.TextField() # 对话内容
    answer_content = models.TextField() # 回答内容
    total_tokens = models.IntegerField(default=0) # 总token数
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)