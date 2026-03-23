from langchain_core.messages import AIMessageChunk
class BaseAgent:
    '''
    智能体通用方法
    '''
    def __init__(self):
        pass
    
    def format_stream_message(self,message, meta_data) -> dict:
        '''
            格式化消息
        '''
        # 如果是AIMessageChunk
        if isinstance(message, AIMessageChunk):
            # 工具调用消息
            if(len(message.tool_calls) > 0):
                tool_names = []
                for tool_call in message.tool_calls:
                    tool_names.append(tool_call['name'])
                return {"type": "tool", "content": f"调用工具: {', '.join(tool_names)}"}
            else:
                # 检查meta_data中是否存在tags键，避免KeyError
                if meta_data.get("tags") and "stream_to_user" in meta_data["tags"]:
                    return {"type": "assistant", "content": message.content or ""}
                else:
                    return {"type": "assistant", "content": ""}

        return {"type": "assistant", "content": ""}