from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from langchain.messages import AnyMessage
from sqlalchemy.orm import Session
from api.models import Task, TaskExecution
from api.core import get_logger
from api.core.constants import TaskType, GoalStatus, ExecutionStatus
from api.agents import TaskPlanAgent, TaskChatAgent

logger = get_logger(__name__)

class TaskService:
    def __init__(self, db: Session, user_id: int):
        '''
        初始化TaskService
        
        Args:
            db: 数据库会话
            user_id: 用户ID
        '''
        self.db = db
        self.user_id = user_id
    
    def create_task(self, title: str, description: str, task_type: str, 
                   start_date: date, end_date: date, repeat_cycle: Optional[str] = None, 
                   is_ai_planned: bool = False, parent_id: Optional[int] = None, 
                   document_ids: Optional[str] = None) -> Task:
        '''
        创建目标
        
        Args:
            title: 目标标题
            description: 目标描述
            task_type: 目标类型（once/repeat/complex）
            start_date: 开始日期
            end_date: 结束日期
            repeat_cycle: 重复周期（仅重复目标需要）
            is_ai_planned: 是否开启AI规划
            parent_id: 父目标ID（仅子目标需要）
            document_ids: 绑定的文档ID列表，用逗号分隔
            
        Returns:
            创建的Task对象
        '''
        try:
            # 验证参数
            if start_date > end_date:
                raise ValueError("开始日期不能晚于结束日期")
            
            # 创建目标
            task = Task(
                user_id=self.user_id,
                title=title,
                description=description,
                type=task_type,
                context=f"## 用户目标:\n{title}\n ## 目标描述:\n{description}",
                status=GoalStatus.NOT_STARTED, 
                start_date=start_date,
                end_date=end_date,
                repeat_cycle=repeat_cycle,
                is_ai_planned=is_ai_planned,
                progress=0,
                parent_id=parent_id,
                document_ids=document_ids
            )
            
            self.db.add(task)
            self.db.flush()  # 获取task.id但不提交事务
            
            execution_service = TaskExecutionService(self.db, self.user_id)
            # 对于一次性目标，自动创建执行情况
            if task_type == TaskType.ONCE:
                execution_service.create_execution(
                    task_id=task.id,
                    title=title,
                    content=description,
                    execution_date=start_date
                )
            
            # 对于开启AI规划的目标，生成初始执行情况
            if is_ai_planned:
                if task_type == TaskType.COMPLEX:
                    subtasks = self._generate_subtask(task)
                    for subtask in subtasks:
                        self.db.add(subtask)
                        self.db.flush()
                        executions = self.ai_plan_task(subtask.id)
                else:
                    executions = self.ai_plan_task(task.id)
                    executions = execution_service.batch_create_executions(task.id, executions)

            self.db.commit()
            return task
        except Exception as e:
            logger.error(f"创建目标失败: {str(e)}")
            raise
    
    def get_tasks(self, skip: int = 0, limit: int = 100, include_subtasks: bool = False) -> List[Task]:
        '''
        获取目标列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            include_subtasks: 是否包含子目标
            
        Returns:
            Task对象列表
        '''
        try:
            if include_subtasks:
                return Task.get_tasks_by_user_id(self.db, self.user_id, skip, limit)
            else:
                return Task.get_parent_tasks_by_user_id(self.db, self.user_id, skip, limit)
        except Exception as e:
            logger.error(f"获取目标列表失败: {str(e)}")
            raise
    
    def get_task_detail(self, task_id: int) -> Optional[Task]:
        '''
        获取目标详情
        
        Args:
            task_id: 目标ID
            
        Returns:
            Task对象或None
        '''
        try:
            task = Task.get_task_by_id(self.db, task_id)
            if not task or task.user_id != self.user_id:
                return None
            return task
        except Exception as e:
            logger.error(f"获取目标详情失败: {str(e)}")
            raise
    
    def update_task(self, task_id: int, **kwargs) -> Optional[Task]:
        '''
        更新目标
        
        Args:
            task_id: 目标ID
            kwargs: 要更新的字段
            
        Returns:
            更新后的Task对象或None
        '''
        try:
            task = Task.get_task_by_id(self.db, task_id)
            if not task or task.user_id != self.user_id:
                return None
            
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            
            # 如果更新了开始/结束日期，重新计算进度
            if "start_date" in kwargs or "end_date" in kwargs:
                self.calculate_progress(task_id)
            
            return task
        except Exception as e:
            logger.error(f"更新目标失败: {str(e)}")
            raise
    
    def cancel_task(self, task_id: int) -> Optional[Task]:
        '''
        取消目标
        
        Args:
            task_id: 目标ID
            
        Returns:
            取消后的Task对象或None
        '''
        try:
            task = Task.get_task_by_id(self.db, task_id)
            if not task or task.user_id != self.user_id:
                return None
            
            # 更新目标状态
            task.status = GoalStatus.CANCELLED
            
            # 同时取消关联的执行情况
            execution_service = TaskExecutionService(self.db, self.user_id)
            for execution in task.executions:
                execution_service.cancel_execution(execution.id)
            
            # 同时取消子目标
            for subtask in task.subtasks:
                self.cancel_task(subtask.id)
            
            return task
        except Exception as e:
            logger.error(f"取消目标失败: {str(e)}")
            raise
    
    def calculate_progress(self, task_id: int) -> int:
        '''
        计算目标完成度
        
        Args:
            task_id: 目标ID
            
        Returns:
            完成度（0-100）
        '''
        try:
            task = Task.get_task_by_id(self.db, task_id)
            if not task or task.user_id != self.user_id:
                return 0
            
            # 1. 如果目标有子目标，基于子目标是否完成计算
            if task.subtasks:
                completed_subtasks = sum(1 for subtask in task.subtasks if subtask.status == GoalStatus.COMPLETED)
                total_subtasks = len(task.subtasks)
                progress = int((completed_subtasks / total_subtasks) * 100)
            
            # 2. 没有子目标的情况下，基于执行情况计算
            else:
                executions = TaskExecution.get_executions_by_task_id(self.db, task_id)
                if not executions:
                    progress = 0
                else:
                    # 3. 一次性目标的完成度直接基于执行情况的数量
                    if task.type == TaskType.ONCE:
                        completed_count = sum(1 for e in executions if e.status == ExecutionStatus.COMPLETED)
                        total_count = len(executions)
                        progress = int((completed_count / total_count) * 100)
                    
                    # 4. 重复目标的完成度需要综合计算
                    elif task.type == TaskType.REPEAT:
                        # 计算已完成的执行情况数量
                        completed_count = sum(1 for e in executions if e.status == ExecutionStatus.COMPLETED)
                        total_count = len(executions)
                        
                        # 计算时间进度
                        today = date.today()
                        total_days = (task.end_date - task.start_date).days + 1
                        elapsed_days = (min(today, task.end_date) - task.start_date).days + 1
                        time_progress = min(100, int((elapsed_days / total_days) * 100))
                        
                        # 计算执行情况进度
                        execution_progress = int((completed_count / total_count) * 100) if total_count > 0 else 0
                        
                        # 综合计算完成度，给予时间进度和执行情况进度相同的权重
                        progress = int((time_progress + execution_progress) / 2)
                    
                    # 其他类型目标的完成度计算
                    else:
                        completed_count = sum(1 for e in executions if e.status == ExecutionStatus.COMPLETED)
                        total_count = len(executions)
                        progress = int((completed_count / total_count) * 100)
            
            # 更新目标进度
            task.progress = progress
            
            # 此处应调用ai更新上下文
            context = self._summary_task_context(task, executions)
            
            # 更新目标上下文
            task.context = context

            # 更新目标状态
            if progress == 100:
                task.status = GoalStatus.COMPLETED
            elif progress > 0:
                task.status = GoalStatus.IN_PROGRESS
            else:
                task.status = GoalStatus.NOT_STARTED
            
            return progress
        except Exception as e:
            logger.error(f"计算目标完成度失败: {str(e)}")
            raise
    
    def _summary_task_context(self, task: Task, executions: List[TaskExecution]) -> None:
        '''
        总结目标上下文
        
        Args:
            task_id: 目标ID
        '''
        task_agent = TaskPlanAgent()
        return task_agent.summary_task_context(task, executions)
        
    def _generate_executions_for_period(self, task_id: int, start_date: date, end_date: date) -> List[TaskExecution]:
        '''
        为指定时间段生成执行情况
        
        Args:
            task_id: 目标ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            生成的TaskExecution对象列表
        '''
        executions = []
        execution_service = TaskExecutionService(self.db, self.user_id)
        task = Task.get_task_by_id(self.db, task_id)
        
        # 解析repeat_cycle
        repeat_cycle = task.repeat_cycle or "never"
        if(repeat_cycle == "never"):
            return []

        # 生成执行情况
        if(task.is_ai_planned):
            task_agent = TaskPlanAgent()
            executions = task_agent.repeat_task_plan(task)
        else:
            current_date = start_date
            while current_date <= end_date:
                # 根据repeat_cycle判断是否生成执行情况
                if self._should_generate_execution(current_date, repeat_cycle):
                    execution = execution_service.create_execution(
                        task_id=task.id,
                        title=f"{task.title} - {current_date.strftime('%Y-%m-%d')}",
                        content=task.description,
                        execution_date=current_date
                    )
                    executions.append(execution)
                current_date += timedelta(days=1)
        
        return executions
    
    def _should_generate_execution(self, current_date: date, repeat_cycle: str) -> bool:
        '''
        根据repeat_cycle判断是否应该为当前日期生成执行情况
        
        Args:
            current_date: 当前日期
            repeat_cycle: 重复周期，格式为never/weekly:1,3,5/monthly:1,15,20
            
        Returns:
            是否应该生成执行情况
        '''
        if repeat_cycle == "never":
            return False
        
        # 处理weekly格式
        if repeat_cycle.startswith("weekly:"):
            # 提取星期几，1-7表示周一到周日
            days_str = repeat_cycle.split(":")[1]
            days = [int(day) for day in days_str.split(",") if day.isdigit()]
            # current_date.isoweekday()返回1-7，表示周一到周日
            return current_date.isoweekday() in days
        
        # 处理monthly格式
        elif repeat_cycle.startswith("monthly:"):
            # 提取每月的日期
            days_str = repeat_cycle.split(":")[1]
            days = [int(day) for day in days_str.split(",") if day.isdigit()]
            # 获取当前日期的天数
            day_of_month = current_date.day
            # 检查当月是否有这一天
            if day_of_month in days:
                # 验证当月是否真的有这一天（例如2月可能没有30日）
                try:
                    # 尝试构造一个同月份的日期，如果成功则表示当月有这一天
                    date(current_date.year, current_date.month, day_of_month)
                    return True
                except ValueError:
                    # 当月没有这一天
                    return False
        
        return False
    
    def _generate_subtask(self, task: Task) -> List[Task]:
        '''
        生成复杂目标的子目标
        
        Args:
            task: 复杂目标对象
            
        Returns:
            生成的子目标对象列表
        '''
        task_agent = TaskAgent()
        return task_agent.complex_task_plan(task)
        
    def ai_plan_task(self, task_id: int) -> List[TaskExecution]:
        '''
        AI规划目标的待办事项
        
        Args:
            task_id: 目标ID
            
        Returns:
            生成的TaskExecution对象列表
        '''
        try:
            task = Task.get_task_by_id(self.db, task_id)
            if not task or task.user_id != self.user_id:
                return []
            logger.debug(f"AI规划目标: {task_id},标题: {task.title}")
            
            executions = []
            
            # 根据目标类型生成执行情况
            if task.type == TaskType.REPEAT:
                # 生成未来一周的执行情况
                today = date.today()
                # 确保类型一致，转换为date类型进行比较
                task_end_date = task.end_date
                if hasattr(task_end_date, 'date'):
                    task_end_date = task_end_date.date()
                task_start_date = task.start_date
                if hasattr(task_start_date, 'date'):
                    task_start_date = task_start_date.date()
                end_date = min(today + timedelta(days=7), task_end_date)
                start_date = max(today, task_start_date)
                logger.debug(f"生成重复任务执行列表: {start_date} 到 {end_date}")
                executions = self._generate_executions_for_period(task_id, start_date, end_date)
            
            elif task.type == TaskType.COMPLEX:
                # 复杂目标需要生成子目标，这里简化处理
                # 实际应该根据OKR规则生成子目标
                pass
            
            return executions
        except Exception as e:
            logger.error(f"AI规划目标失败: {str(e)}")
            raise
    
    def get_child_tasks(self, task_id: int) -> List[Task]:
        '''
        获取子目标列表
        
        Args:
            task_id: 目标ID
            
        Returns:
            子目标对象列表
        '''
        return Task.get_subtasks_by_task_id(self.db, task_id)

    def bind_documents_to_task(self, task_id: int, document_ids: List[int]) -> None:
        '''
        将文档绑定到任务
        
        Args:
            task_id: 任务ID
            document_ids: 文档ID列表
        '''
        task = self.get_task_detail(task_id)
        if not task or task.user_id != self.user_id:
            raise ValueError("目标不存在或无权操作")
        task.document_ids = ",".join(map(str, document_ids))
    

class TaskExecutionService:
    def __init__(self, db: Session, user_id: int):
        '''
        初始化TaskExecutionService
        
        Args:
            db: 数据库会话
            user_id: 用户ID
        '''
        self.db = db
        self.user_id = user_id
    
    def create_execution(self, task_id: int, title: str, content: Optional[str] = None, 
                        execution_date: date = None) -> TaskExecution:
        '''
        创建执行情况
        
        Args:
            task_id: 目标ID
            title: 执行情况标题
            content: 执行情况内容
            execution_date: 执行日期
            
        Returns:
            创建的TaskExecution对象
        '''
        try:
            # 验证目标是否存在且属于当前用户
            task = Task.get_task_by_id(self.db, task_id)
            if not task or task.user_id != self.user_id:
                raise ValueError("目标不存在或无权操作")
            
            # 创建执行情况
            execution = TaskExecution(
                task_id=task_id,
                title=title,
                content=content,
                status=ExecutionStatus.NOT_STARTED,
                execution_date=execution_date or date.today(),
                execution_result=None
            )
            
            self.db.add(execution)
            return execution
        except Exception as e:
            logger.error(f"创建执行情况失败: {str(e)}")
            raise
    
    def get_executions(self, task_id: int, skip: int = 0, limit: int = 100) -> List[TaskExecution]:
        '''
        获取执行情况列表
        
        Args:
            task_id: 目标ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            TaskExecution对象列表
        '''
        try:
            # 验证目标是否存在且属于当前用户
            task = Task.get_task_by_id(self.db, task_id)
            if not task or task.user_id != self.user_id:
                return []
            
            return TaskExecution.get_executions_by_task_id(self.db, task_id, skip, limit)
        except Exception as e:
            logger.error(f"获取执行情况列表失败: {str(e)}")
            raise
    
    def get_execution_detail(self, execution_id: int) -> Optional[TaskExecution]:
        '''
        获取执行情况详情
        
        Args:
            execution_id: 执行情况ID
            
        Returns:
            TaskExecution对象或None
        '''
        try:
            execution = TaskExecution.get_execution_by_id(self.db, execution_id)
            if not execution:
                return None
            
            # 验证目标是否属于当前用户
            task = Task.get_task_by_id(self.db, execution.task_id)
            if not task or task.user_id != self.user_id:
                return None
            
            return execution
        except Exception as e:
            logger.error(f"获取执行情况详情失败: {str(e)}")
            raise
    
    def update_execution(self, execution_id: int, **kwargs) -> Optional[TaskExecution]:
        '''
        更新执行情况
        
        Args:
            execution_id: 执行情况ID
            kwargs: 要更新的字段
            
        Returns:
            更新后的TaskExecution对象或None
        '''
        try:
            execution = TaskExecution.get_execution_by_id(self.db, execution_id)
            if not execution:
                return None
            
            # 验证目标是否属于当前用户
            task = Task.get_task_by_id(self.db, execution.task_id)
            if not task or task.user_id != self.user_id:
                return None
            
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(execution, key):
                    setattr(execution, key, value)
            
            # 如果更新了状态为已完成，计算目标完成度
            if "status" in kwargs and kwargs["status"] == ExecutionStatus.COMPLETED:
                task_service = TaskService(self.db, self.user_id)
                task_service.calculate_progress(execution.task_id)
            
            return execution
        except Exception as e:
            logger.error(f"更新执行情况失败: {str(e)}")
            raise
    
    def cancel_execution(self, execution_id: int) -> Optional[TaskExecution]:
        '''
        取消执行情况
        
        Args:
            execution_id: 执行情况ID
            
        Returns:
            取消后的TaskExecution对象或None
        '''
        try:
            execution = TaskExecution.get_execution_by_id(self.db, execution_id)
            if not execution:
                return None
            
            # 验证目标是否属于当前用户
            task = Task.get_task_by_id(self.db, execution.task_id)
            if not task or task.user_id != self.user_id:
                return None
            
            # 更新执行情况状态
            execution.status = ExecutionStatus.CANCELLED
            
            # 重新计算目标完成度
            task_service = TaskService(self.db, self.user_id)
            task_service.calculate_progress(execution.task_id)
            
            return execution
        except Exception as e:
            logger.error(f"取消执行情况失败: {str(e)}")
            raise
    
    def update_execution_status(self, execution_id: int) -> Optional[TaskExecution]:
        '''
        更新执行情况状态
        
        Args:
            execution_id: 执行情况ID
            
        Returns:
            更新后的TaskExecution对象或None
        '''
        try:
            execution = TaskExecution.get_execution_by_id(self.db, execution_id)
            if not execution:
                return None
            
            # 验证目标是否属于当前用户
            task = Task.get_task_by_id(self.db, execution.task_id)
            if not task or task.user_id != self.user_id:
                return None
            
            today = date.today()
            
            # 更新状态
            if execution.status == ExecutionStatus.NOT_STARTED:
                if execution.execution_date < today:
                    execution.status = ExecutionStatus.OVERDUE
                elif execution.execution_date == today:
                    execution.status = ExecutionStatus.IN_PROGRESS
            
            return execution
        except Exception as e:
            logger.error(f"更新执行情况状态失败: {str(e)}")
            raise
    
    def batch_create_executions(self, task_id: int, executions_data: List[dict]) -> List[TaskExecution]:
        '''
        批量创建执行情况
        
        Args:
            task_id: 目标ID
            executions_data: 执行情况数据列表，每个元素包含title、content、execution_date等字段
            
        Returns:
            创建的TaskExecution对象列表
        '''
        try:
            # 验证目标是否存在且属于当前用户
            task = Task.get_task_by_id(self.db, task_id)
            if not task or task.user_id != self.user_id:
                raise ValueError("目标不存在或无权操作")
            
            # 批量创建执行情况
            created_executions = []
            for execution_data in executions_data:
                execution = TaskExecution(
                    task_id=task_id,
                    title=execution_data.get("title"),
                    content=execution_data.get("content"),
                    status=ExecutionStatus.NOT_STARTED,
                    execution_date=execution_data.get("execution_date") or date.today(),
                    execution_result=None
                )
                self.db.add(execution)
                created_executions.append(execution)
            
            return created_executions
        except Exception as e:
            logger.error(f"批量创建执行情况失败: {str(e)}")
            raise
    
    def update_all_executions_status(self) -> int:
        '''
        更新所有执行情况的状态
        
        Returns:
            更新的执行情况数量
        '''
        try:
            # 获取用户的所有执行情况
            from sqlalchemy import and_
            executions = self.db.query(TaskExecution).join(Task).filter(
                and_(Task.user_id == self.user_id, 
                     TaskExecution.status.in_([ExecutionStatus.NOT_STARTED, ExecutionStatus.IN_PROGRESS]))
            ).all()
            
            updated_count = 0
            for execution in executions:
                if self.update_execution_status(execution.id):
                    updated_count += 1
            
            return updated_count
        except Exception as e:
            logger.error(f"更新所有执行情况状态失败: {str(e)}")
            raise
