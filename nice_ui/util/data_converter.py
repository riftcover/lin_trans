# 数据格式转换
from pydantic import BaseModel, Field

from nice_ui.task import WORK_TYPE
from nice_ui.util.tools import VideoFormatInfo


class SrtEditDict(BaseModel):
    """
    定义数据格式，在column：5中传递的，用来在删除，编辑使用编辑器读取信息，使用SrtEditDictRole 角色存储信息
    """
    unid: str = Field(default="", description="文件指纹")
    media_path: str = Field(default="", description="媒体文件路径")
    srt_dirname: str = Field(default="", description="SRT文件路径")
    job_type: WORK_TYPE = Field(default="", description="任务类型")
    raw_noextname: str = Field(default="", description="无扩展名的原始文件名")


def convert_video_format_info_to_srt_edit_dict(video_info: VideoFormatInfo) -> SrtEditDict:
    """
        将 VideoFormatInfo 对象转换为 SrtEditDict 对象。

        Args:
            video_info (VideoFormatInfo): 输入的 VideoFormatInfo 对象

        Returns:
            SrtEditDict: 转换后的 SrtEditDict 对象
        """
    new_dict = SrtEditDict()
    job_t = video_info.work_type
    new_dict.srt_dirname = video_info.srt_dirname
    new_dict.unid = video_info.unid
    new_dict.job_type = job_t
    new_dict.raw_noextname = video_info.raw_noextname
    if job_t == 'asr':
        new_dict.media_path = video_info.raw_name
    elif job_t == 'trans':
        new_dict.media_path = ""

    return new_dict
