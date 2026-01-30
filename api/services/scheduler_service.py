from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from sqlalchemy.orm import Session
from api.core.database import SessionLocal
from api.services.task_service import TaskService, TaskInstanceService, RecurringTaskService
from api.models.task import RecurringTask, TaskInstance
import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    """定时任务服务类"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()

    def start(self):
        """
        启动定时任务调度器
        """
        # 添加任务状态更新定时任务（每小时执行一次）
        self.scheduler.add_job(
            self.update_task_statuses,
            trigger=IntervalTrigger(hours=1),
            id='update_task_statuses',
            name='Update overdue task statuses',
            replace_existing=True
        )

        # 添加重复事项实例生成定时任务（每天执行一次）
        self.scheduler.add_job(
            self.generate_task_instances,
            trigger=IntervalTrigger(days=1),
            id='generate_task_instances',
            name='Generate task instances for recurring tasks',
            replace_existing=True
        )

        # 启动调度器
        self.scheduler.start()
        logger.info("Scheduler started with tasks:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.name} (id: {job.id})")

    def shutdown(self):
        """
        关闭定时任务调度器
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler shutdown")

    def update_task_statuses(self):
        """
        更新过期事项状态
        """
        logger.info("Running update_task_statuses job")
        db = SessionLocal()
        try:
            # 更新一次性事项的过期状态
            TaskService.update_overdue_tasks(db)
            # 更新重复事项实例的过期状态
            TaskInstanceService.update_overdue_instances(db)
            logger.info("Task statuses updated successfully")
        except Exception as e:
            logger.error(f"Error updating task statuses: {e}")
        finally:
            db.close()

    def generate_task_instances(self):
        """
        生成重复事项实例
        """
        logger.info("Running generate_task_instances job")
        db = SessionLocal()
        try:
            # 获取所有激活状态的重复事项
            active_recurring_tasks = db.query(RecurringTask).filter(
                RecurringTask.status == "active"
            ).all()

            for recurring_task in active_recurring_tasks:
                # 生成未来7天的实例
                self._generate_instances_for_task(db, recurring_task, days_ahead=7)

            logger.info(f"Task instances generated for {len(active_recurring_tasks)} recurring tasks")
        except Exception as e:
            logger.error(f"Error generating task instances: {e}")
        finally:
            db.close()

    def _generate_instances_for_task(self, db: Session, recurring_task: RecurringTask, days_ahead: int):
        """
        为单个重复事项生成实例
        """
        from datetime import timedelta

        # 计算结束日期
        end_date = datetime.utcnow() + timedelta(days=days_ahead)
        last_executed = datetime.utcnow()

        # 生成实例，直到达到结束日期或重复结束条件
        instances_generated = 0

        while True:
            # 计算下次执行时间
            next_occurrence = RecurringTaskService.calculate_next_occurrence(
                recurring_task, last_executed
            )

            if not next_occurrence:
                break

            # 检查是否超过结束日期
            if next_occurrence > end_date:
                break

            # 检查重复结束条件
            if recurring_task.recurrence_end_type == "on_date" and recurring_task.recurrence_end_date:
                if next_occurrence.date() > recurring_task.recurrence_end_date:
                    break

            if recurring_task.recurrence_end_type == "after_occurrences" and recurring_task.recurrence_occurrences:
                if instances_generated >= recurring_task.recurrence_occurrences:
                    break

            # 检查是否已经存在该时间的实例
            existing_instance = db.query(TaskInstance).filter(
                TaskInstance.recurring_task_id == recurring_task.id,
                TaskInstance.start_time == next_occurrence
            ).first()

            if not existing_instance:
                # 创建实例
                TaskInstanceService.create_task_instance(
                    db=db,
                    recurring_task_id=recurring_task.id,
                    title=recurring_task.title,
                    description=recurring_task.description,
                    priority=recurring_task.priority,
                    start_time=next_occurrence,
                    # 假设每个实例持续1小时
                    end_time=next_occurrence + timedelta(hours=1)
                )
                instances_generated += 1

            # 更新最后执行时间
            last_executed = next_occurrence

        if instances_generated > 0:
            logger.info(f"Generated {instances_generated} instances for recurring task {recurring_task.id}")

# 创建全局调度器实例
scheduler_service = SchedulerService()
