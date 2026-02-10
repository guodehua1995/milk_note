import requests
from api.core import settings, get_logger
from .models import ToolInfo
from langchain.tools import tool
url = "https://api.bocha.cn/v1/web-search"

logger = get_logger(__name__)


def web_search(query: str,count: int = 10) -> str:
    '''
     联网查询
     使用Bocha Web Search API 进行网页搜索。
     搜索内容包括天气/网页/文章/视频等。

    参数:
    - query:String 搜索关键词 必填
    - count:Int 搜索结果数量,只能为10-50之间 默认10条 非必填


    返回:
    - 搜索结果的详细信息，包括网页标题、网页URL、网页摘要、网站名称、网页发布时间等。
    '''
    logger.debug(f"联网查询工具,查询关键词:{query},查询结果数量:{count}")

    headers = {
        'Authorization': f"Bearer {settings.ANSPIRE_API_KEY}", 
        'Content-Type': 'application/json'
    }

    data = {
        "query": query,
        "summary": True, # 是否返回长文本摘要
        "count": count
    }


    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        json_response = response.json()
        try:
            if json_response["code"] != 200 or not json_response["data"]:
                return f"搜索API请求失败，原因是: {response.msg or '未知错误'}"
            
            webpages = json_response["data"]["webPages"]["value"]
            if not webpages:
                return "未找到相关结果。"
            formatted_results = ""
            for idx, page in enumerate(webpages, start=1):
                formatted_results += (
                    f"引用: {idx}\n"
                    f"标题: {page['name']}\n"
                    f"URL: {page['url']}\n"
                    f"摘要: {page['summary']}\n"
                    f"网站名称: {page['siteName']}\n"
                    f"发布时间: {page['dateLastCrawled']}\n"
                )
            logger.debug(f"联网查询工具,搜索结果:{formatted_results.strip()}")
            return formatted_results.strip()
        except Exception as e:
            return f"搜索API请求失败，原因是：搜索结果解析失败 {str(e)}"
    else:
        return f"搜索API请求失败，状态码: {response.status_code}, 错误信息: {response.text}"





@tool
def web_search_tool(query: str,count: int = 10) -> str:
    '''
    联网查询工具
    使用Bocha Web Search API 进行网页搜索。
    搜索内容包括天气/网页/文章/视频等。

    参数:
    - query:String 搜索关键词 必填
    - count:Int 搜索结果数量,只能为10-50之间 默认10条 非必填

    返回:
    - 搜索结果的详细信息，包括网页标题、网页URL、网页摘要、网站名称、网页发布时间等。
    '''
    return web_search(query,count)

# 工具调用说明
web_search_tool_info = ToolInfo(
    tool_name="联网查询工具",
    func=web_search_tool,
    description="联网查询工具,支持按天/月/年和指定时间段联网查询资料。查询范围包括天气/网页/政策/新闻/热点等。"
)

