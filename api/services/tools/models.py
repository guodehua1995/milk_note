

class ToolInfo:
    '''
    工具描述
    tool_name: 工具名称
    func 工具函数
    description: 工具描述
    empty_param: 是否为空参数
    '''
    def __init__(self, tool_name: str, func: callable, description: str, empty_param: bool = False):
        self.tool_name = tool_name
        self.func = func
        self.description = description
        self.empty_param = empty_param
        
    
    
    