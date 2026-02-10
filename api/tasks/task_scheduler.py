from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from api.core import get_db, get_logger
from api.models import Task, TaskExecution
from api.services import TaskService, TaskExecutionService
from api.core.constants import TaskType, GoalStatus, ExecutionStatus
from datetime import date, datetime, timedelta


logger = get_logger(__name__)

class TaskScheduler:
    """
    任务调度器，用于定时处理目标相关的任务
    """
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
    
    def start(self):
        """
        启动调度器
        """
        # 添加每天0点执行的任务
        self.scheduler.add_job(
            self.update_execution_statuses,
            trigger=CronTrigger(hour=0, minute=0),
            id="update_execution_statuses",
            name="更新执行情况状态",
            replace_existing=True
        )
        
        self.scheduler.add_job(
            self.update_task_contexts,
            trigger=CronTrigger(day_of_week=0, hour=0, minute=0),
            id="update_task_contexts",
            name="更新目标上下文",
            replace_existing=True
        )
        
        # 添加每周一执行的任务（生成下一周的待办事项）
        self.scheduler.add_job(
            self.ai_plan_next_week_tasks,
            trigger=CronTrigger(day_of_week=0, hour=1, minute=0),  # 周日0点执行
            id="ai_plan_next_week_tasks",
            name="AI规划下一周的待办事项",
            replace_existing=True
        )
        
        # 启动调度器
        self.scheduler.start()
        logger.info("任务调度器已启动")
    
    def shutdown(self):
        """
        关闭调度器
        """
        self.scheduler.shutdown()
        logger.info("任务调度器已关闭")
    
    def update_execution_statuses(self):
        """
        更新所有执行情况的状态
        """
        logger.info("开始更新执行情况状态...")
        
        try:
            with next(get_db()) as db:
                # 获取所有用户的ID
                user_ids = db.query(Task.user_id).distinct().all()
                user_ids = [user_id[0] for user_id in user_ids]
                
                # 为每个用户更新执行情况状态
                for user_id in user_ids:
                    execution_service = TaskExecutionService(db, user_id)
                    updated_count = execution_service.update_all_executions_status()
                    logger.info(f"用户 {user_id} 更新了 {updated_count} 个执行情况状态")
                
                db.commit()
                logger.info("执行情况状态更新完成")
        except Exception as e:
            logger.error(f"更新执行情况状态失败: {str(e)}")
    
    def update_task_contexts(self):
        """
        更新目标上下文
        """
        logger.info("开始更新目标上下文...")
        
        try:
            with next(get_db()) as db:
                # 获取所有父目标
                parent_tasks = db.query(Task).filter(Task.parent_id.is_(None)).all()
                
                for task in parent_tasks:
                    try:
                        task_service = TaskService(db, task.user_id)
                        # 计算目标完成度，更新目标状态
                        progress = task_service.calculate_progress(task.id)
                        logger.debug(f"目标 {task.title} (ID: {task.id}) 完成度: {progress}%")
                    except Exception as e:
                        logger.error(f"更新目标 {task.title} (ID: {task.id}) 上下文失败: {str(e)}")
                        continue
                
                db.commit()
                logger.info("目标上下文更新完成")
        except Exception as e:
            logger.error(f"更新目标上下文失败: {str(e)}")
    
    def ai_plan_next_week_tasks(self):
        """
        AI规划下一周的待办事项
        """
        logger.info("开始AI规划下一周的待办事项...")
        
        try:
            with next(get_db()) as db:
                # 获取所有开启了AI规划的目标
                ai_planned_tasks = db.query(Task).filter(Task.is_ai_planned == True).all()
                
                for task in ai_planned_tasks:
                    try:
                        task_service = TaskService(db, task.user_id)
                        # 生成下一周的待办事项
                        executions = task_service.ai_plan_task(task.id)
                        logger.debug(f"为目标 {task.title} (ID: {task.id}) 生成了 {len(executions)} 个待办事项")
                    except Exception as e:
                        logger.error(f"为目标 {task.title} (ID: {task.id}) 规划待办事项失败: {str(e)}")
                        continue
                
                db.commit()
                logger.info("AI规划待办事项完成")
        except Exception as e:
            logger.error(f"AI规划待办事项失败: {str(e)}")


# 创建任务调度器实例
task_scheduler = TaskScheduler()