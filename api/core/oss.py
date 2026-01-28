import alibabacloud_oss_v2 as oss
from api.core import settings,get_logger
from fastapi import HTTPException

logger = get_logger(__name__)

def create_oss_client():
    '''
    创建OSS客户端
    '''
    # 从环境变量中加载凭证信息，用于身份验证
    credentials_provider = oss.credentials.StaticCredentialsProvider(
        access_key_id=settings.OSS_ACCESS_KEY_ID,
        access_key_secret=settings.OSS_ACCESS_KEY_SECRET
    )

    cfg = oss.config.load_default()
    cfg.region = 'cn-beijing'
    cfg.credentials_provider = credentials_provider

    return oss.Client(cfg)

class OSSClient:
    def __init__(self):
        self.client = create_oss_client()
        self.bucket = settings.OSS_BUCKET_NAME

    def upload_file(self, object_name: str,file_content:bytes):
        '''
        上传文件到OSS
        '''
        self.client.put_object(oss.PutObjectRequest(
        bucket=self.bucket,
        key=object_name,
        body=file_content,
        )
    )

    def download_file(self, file_key:str)-> tuple[str, bytes]:
        '''
        从OSS下载文件
        返回：(文件名, 文件内容字节)
        '''
        result = self.client.get_object(oss.GetObjectRequest(
        bucket=self.bucket,
        key=file_key
        ))

        if result is None:
            raise HTTPException(status_code=404, detail="文件不存在或无权访问")

        if result.status_code != 200:
            logger.error(f"下载文件 {file_key} 失败，状态码：{result.status_code}，描述：{result.status_description}")
            raise HTTPException(status_code=500, detail="下载文件失败")
        
        with result.body as body_stream:
            file_content = body_stream.read()

        # 返回两个值：文件名和文件内容
        return file_key, file_content

    def path_for_download(self, file_key:str)-> str:
        '''
        生成下载文件的URL
        '''
        logger.info(f"文件键: {file_key}")
        pre_result = self.client.presign(
        oss.GetObjectRequest(
            bucket=self.bucket,  # 指定存储空间名称
            key=file_key,        # 指定对象键名
        )  )
        return pre_result.url if pre_result else None

oss_client = OSSClient()