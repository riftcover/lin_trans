"""
阿里云OSS客户端
用于将本地文件上传到阿里云OSS并获取URL，为ASR任务提供服务

使用阿里云OSS SDK V2实现，参考文档：
https://help.aliyun.com/zh/oss/developer-reference/get-started-with-oss-sdk-for-python-v2
"""
import mimetypes
import os
import time
import uuid
from typing import Tuple, Optional, Callable

import alibabacloud_oss_v2 as oss

from app.cloud_asr import aliyun_sdk
from utils import logger


class AliyunOSSClientV2:
    """阿里云OSS客户端 (使用SDK V2)"""

    def __init__(self, access_key_id: str, access_key_secret: str, region: str, bucket_name: str):
        """
        初始化OSS客户端

        Args:
            access_key_id: 阿里云访问密钥ID
            access_key_secret: 阿里云访问密钥Secret
            region: OSS区域，如 'cn-beijing'
            bucket_name: OSS存储桶名称
        """
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.region = region
        self.bucket_name = bucket_name

        # 创建认证提供者
        self.credentials_provider = oss.credentials.StaticCredentialsProvider(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret
        )

        # 创建OSS客户端配置
        self.cfg = oss.config.load_default()
        self.cfg.credentials_provider = self.credentials_provider
        self.cfg.region = region

        # 创建OSS客户端
        self.client = oss.Client(self.cfg)

    def upload_file(self,
                    local_file_path: str,
                    oss_path: Optional[str] = None,
                    progress_callback: Optional[Callable[[int], None]] = None
                    ) -> Tuple[bool, str, str]:
        """
        上传文件到OSS

        Args:
            local_file_path: 本地文件路径
            oss_path: OSS上的文件路径，如果不指定，将自动生成
            progress_callback: 进度回调函数，参数为上传进度（0-100）

        Returns:
            Tuple[bool, str, str]: (是否成功, OSS文件路径, 错误信息)
        """
        logger.info(f"正在上传文件到OSS: {local_file_path}")

        # 检查文件是否存在
        if not os.path.exists(local_file_path):
            error_msg = f"文件不存在: {local_file_path}"
            logger.error(error_msg)
            return False, "", error_msg

        try:
            # 如果没有指定OSS路径，则自动生成
            if not oss_path:
                file_ext = os.path.splitext(local_file_path)[1]
                timestamp = int(time.time())
                random_str = str(uuid.uuid4()).replace("-", "")[:8]
                oss_path = f"audio/{timestamp}_{random_str}{file_ext}"

            # 获取文件的MIME类型
            content_type, _ = mimetypes.guess_type(local_file_path)
            if not content_type:
                content_type = 'application/octet-stream'

            # 设置元数据
            metadata = {
                "Content-Type": content_type
            }

            # 上传文件
            with open(local_file_path, 'rb') as file_obj:
                data = file_obj.read()

                # 如果有进度回调，模拟进度
                if progress_callback:
                    progress_callback(10)  # 开始上传

                # 执行上传
                result = self.client.put_object(oss.PutObjectRequest(
                    bucket=self.bucket_name,
                    key=oss_path,
                    body=data,
                    metadata=metadata
                ))

                if progress_callback:
                    progress_callback(100)  # 上传完成

                if result.status_code == 200:
                    logger.info(f"文件上传成功: {oss_path}")
                    return True, oss_path, ""
                else:
                    error_msg = f"上传失败，状态码: {result.status_code}"
                    logger.error(error_msg)
                    return False, "", error_msg

        except Exception as e:
            error_msg = f"上传文件时发生错误: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg

    def generate_url(self, oss_path: str, expires: int = 3600) -> str:
        """
        生成文件的访问链接

        Args:
            oss_path: OSS上的文件路径
            expires: 链接的有效期（秒），默认为1小时

        Returns:
            str: 访问链接URL

        Raises:
            Exception: 生成URL时发生错误
        """
        if not oss_path:
            error_msg = "生成URL失败: OSS路径不能为空"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            return self._generate_url(oss_path, expires)
        except Exception as e:
            error_msg = f"生成文件访问链接时发生错误: {str(e)}"
            logger.error(error_msg)
            raise ValueError(e) from e

    def _generate_url(self, oss_path, expires):
        """
        生成文件的访问链接

        Args:
            oss_path: oss文件路径
            expires: 有效时间

        Returns: 签名文件路径

        """
        logger.info("开始生成文件的访问链接")

        pre_result = self.client.presign(
            oss.GetObjectRequest(
                bucket=self.bucket_name,  # 指定存储空间名称
                key=oss_path,  # 指定对象键名
                expires=expires  # 设置链接有效期
            )

        )

        # 打印预签名请求的详细信息
        logger.info("生成预签名请求成功:")
        logger.info(f"  - URL: {pre_result.url}")

        return pre_result.url

    def upload_and_generate_url(self,
                                local_file_path: str,
                                oss_path: Optional[str] = None,
                                expires: int = 24 * 3600,  # 默认24小时
                                progress_callback: Optional[Callable[[int], None]] = None
                                ) -> Tuple[bool, str, str]:
        """
        上传文件并生成访问链接

        Args:
            local_file_path: 本地文件路径
            oss_path: OSS上的文件路径，如果不指定，将自动生成
            expires: 链接的有效期（秒），默认为24小时
            progress_callback: 进度回调函数，参数为上传进度（0-100）

        Returns:
            Tuple[bool, str, str]: (是否成功, 访问链接, 错误信息)
        """
        # 记录开始时间
        start_time = time.time()

        # 检查文件路径
        if not local_file_path:
            error_msg = "上传文件失败: 本地文件路径不能为空"
            logger.error(error_msg)
            return False, "", error_msg

        # 检查文件是否存在
        if not os.path.exists(local_file_path):
            error_msg = f"上传文件失败: 文件不存在: {local_file_path}"
            logger.error(error_msg)
            return False, "", error_msg

        try:
            # 记录文件大小
            file_size = os.path.getsize(local_file_path)
            file_name = os.path.basename(local_file_path)
            logger.info(f"开始上传文件: {file_name}, 大小: {file_size/1024/1024:.2f}MB")

            # 上传文件
            success, oss_path, error = self.upload_file(local_file_path, oss_path, progress_callback)
            if not success:
                return False, "", error

            logger.info(f"文件上传成功: {oss_path}")

            try:
                # 生成访问链接
                url = self.generate_url(oss_path, expires)

                # 记录结束时间和耗时
                end_time = time.time()
                elapsed_time = end_time - start_time
                logger.info(f"上传文件并生成URL完成，耗时: {elapsed_time:.2f}秒")

                return True, url, ""
            except Exception as e:
                error_msg = f"生成URL时发生错误: {str(e)}"
                logger.error(error_msg)
                return False, "", error_msg

        except Exception as e:
            error_msg = f"上传文件过程中发生错误: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg


def create_oss_client() -> Optional[AliyunOSSClientV2]:
    """
    从配置中创建OSS客户端实例

    Returns:
        Optional[AliyunOSSClientV2]: OSS客户端实例，如果配置不完整则返回None
    """
    # 从配置中获取阿里云OSS的凭证
    access_key_id = aliyun_sdk.aki
    access_key_secret = aliyun_sdk.aks
    region = aliyun_sdk.region
    bucket_name = aliyun_sdk.bucket

    # 检查配置是否完整
    if not access_key_id or not access_key_secret or not bucket_name:
        logger.warning("阿里云OSS配置不完整，请检查配置中的阿里云OSS凭证")
        return None

    try:
        return AliyunOSSClientV2(access_key_id, access_key_secret, region, bucket_name)
    except Exception as e:
        logger.error(f"创建OSS客户端实例失败: {str(e)}")
        return None


def upload_file_for_asr(local_file_path: str, progress_callback: Optional[Callable[[int], None]] = None, expires: int = 24 * 3600) -> Tuple[bool, str, str]:
    """
    上传文件到OSS并生成URL，为ASR任务提供服务

    Args:
        local_file_path: 本地文件路径
        progress_callback: 进度回调函数，参数为上传进度（0-100）
        expires: 链接的有效期（秒），默认为24小时

    Returns:
        Tuple[bool, str, str]: (是否成功, 访问链接, 错误信息)
    """
    try:
        client = create_oss_client()
        if not client:
            error_msg = "创建OSS客户端失败，请检查阿里云OSS配置"
            logger.error(error_msg)
            return False, "", error_msg

        # 为segment_data文件生成特定的OSS路径
        file_name = os.path.basename(local_file_path)
        timestamp = int(time.time())
        oss_path = f"nlp_segments/{timestamp}_{file_name}"

        logger.info(f"开始上传segment_data文件到OSS: {oss_path}")

        # 上传文件并生成URL
        success, url, error = client.upload_and_generate_url(
            local_file_path=local_file_path,
            oss_path=oss_path,
            expires=expires,
            progress_callback=progress_callback
        )

        if success:
            logger.info(f"segment_data文件上传成功: {url}")
        else:
            logger.error(f"segment_data文件上传失败: {error}")

        # success = True
        # url = 'https://asr-file-tth.oss-cn-beijing.aliyuncs.com/nlp_segments/1755866850_test_zh_segment_data.json?x-oss-signature-version=OSS4-HMAC-SHA256&x-oss-date=20250822T124732Z&x-oss-expires=900&x-oss-credential=LTAI5t7eCsZFb4AnqJFX5e3v%2F20250822%2Fcn-beijing%2Foss%2Faliyun_v4_request&x-oss-signature=2d74321fcf22191c5837a8a34be6e13fa1c03dc39093d454808d64632c4d874c'
        # error =None

        return success, url, error

    except Exception as e:
        error_msg = f"上传segment_data文件时发生异常: {str(e)}"
        logger.error(error_msg)
        return False, "", error_msg


if __name__ == "__main__":
    # 定义进度回调函数
    def progress_callback(progress):
        print(f"\r上传进度: {progress}%", end="")


    file = "C:/Users/gaosh/Downloads/Video/tt.wav"
    # 上传文件并生成URL
    print("开始上传文件:")
    success, url, error = upload_file_for_asr(file, progress_callback)
