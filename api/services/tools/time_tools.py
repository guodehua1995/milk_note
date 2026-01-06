from .models import ToolInfo
from langchain.tools import tool
from datetime import datetime

@tool
def get_current_time():
    '''
        获取当前时间
    '''
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

get_current_time_tool = ToolInfo(
    tool_name="获取当前时间",
    func=get_current_time,
    description="用途: 获取系统当前时间。 当用户有时效性要求时,可以调用此工具获取当前时间。例如: 最近几天/现在/明天等。",
    empty_param=True
)