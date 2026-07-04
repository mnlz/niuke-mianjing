from typing import Dict, Type

from .base import RecruitmentAdapter
from .bytedance import ByteDanceRecruitmentAdapter
from .official_pages import (
    AlibabaRecruitmentAdapter,
    BaiduRecruitmentAdapter,
    HuaweiRecruitmentAdapter,
    JDRecruitmentAdapter,
    KuaishouRecruitmentAdapter,
    MeituanRecruitmentAdapter,
)
from .tencent import TencentRecruitmentAdapter


ADAPTERS: Dict[str, Type[RecruitmentAdapter]] = {
    AlibabaRecruitmentAdapter.source: AlibabaRecruitmentAdapter,
    BaiduRecruitmentAdapter.source: BaiduRecruitmentAdapter,
    ByteDanceRecruitmentAdapter.source: ByteDanceRecruitmentAdapter,
    HuaweiRecruitmentAdapter.source: HuaweiRecruitmentAdapter,
    JDRecruitmentAdapter.source: JDRecruitmentAdapter,
    KuaishouRecruitmentAdapter.source: KuaishouRecruitmentAdapter,
    MeituanRecruitmentAdapter.source: MeituanRecruitmentAdapter,
    TencentRecruitmentAdapter.source: TencentRecruitmentAdapter,
}


def list_adapters():
    return sorted(ADAPTERS)


def create_adapter(source: str, **kwargs) -> RecruitmentAdapter:
    adapter_class = ADAPTERS.get(source.lower().strip())
    if not adapter_class:
        raise ValueError(f"不支持的招聘来源：{source}，可选：{', '.join(list_adapters())}")
    return adapter_class(**kwargs)
