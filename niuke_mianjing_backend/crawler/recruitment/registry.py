from typing import Dict, Type

from .base import RecruitmentAdapter
from .bytedance import ByteDanceRecruitmentAdapter
from .official_pages import (
    AlibabaRecruitmentAdapter,
    BaiduRecruitmentAdapter,
    DeepSeekRecruitmentAdapter,
    HuaweiRecruitmentAdapter,
    JDRecruitmentAdapter,
    KimiRecruitmentAdapter,
    KuaishouRecruitmentAdapter,
    MeituanRecruitmentAdapter,
    MiniMaxRecruitmentAdapter,
    PDDRecruitmentAdapter,
    XiaomiRecruitmentAdapter,
    XiaohongshuRecruitmentAdapter,
    ZhipuRecruitmentAdapter,
)
from .tencent import TencentRecruitmentAdapter


ADAPTERS: Dict[str, Type[RecruitmentAdapter]] = {
    AlibabaRecruitmentAdapter.source: AlibabaRecruitmentAdapter,
    BaiduRecruitmentAdapter.source: BaiduRecruitmentAdapter,
    ByteDanceRecruitmentAdapter.source: ByteDanceRecruitmentAdapter,
    DeepSeekRecruitmentAdapter.source: DeepSeekRecruitmentAdapter,
    HuaweiRecruitmentAdapter.source: HuaweiRecruitmentAdapter,
    JDRecruitmentAdapter.source: JDRecruitmentAdapter,
    KimiRecruitmentAdapter.source: KimiRecruitmentAdapter,
    KuaishouRecruitmentAdapter.source: KuaishouRecruitmentAdapter,
    MeituanRecruitmentAdapter.source: MeituanRecruitmentAdapter,
    MiniMaxRecruitmentAdapter.source: MiniMaxRecruitmentAdapter,
    PDDRecruitmentAdapter.source: PDDRecruitmentAdapter,
    TencentRecruitmentAdapter.source: TencentRecruitmentAdapter,
    XiaomiRecruitmentAdapter.source: XiaomiRecruitmentAdapter,
    XiaohongshuRecruitmentAdapter.source: XiaohongshuRecruitmentAdapter,
    ZhipuRecruitmentAdapter.source: ZhipuRecruitmentAdapter,
}


def list_adapters():
    return sorted(ADAPTERS)


def create_adapter(source: str, **kwargs) -> RecruitmentAdapter:
    adapter_class = ADAPTERS.get(source.lower().strip())
    if not adapter_class:
        raise ValueError(f"不支持的招聘来源：{source}，可选：{', '.join(list_adapters())}")
    return adapter_class(**kwargs)
