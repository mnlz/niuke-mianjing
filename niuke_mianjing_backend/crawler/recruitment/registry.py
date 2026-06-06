from typing import Dict, Type

from .base import RecruitmentAdapter
from .bytedance import ByteDanceRecruitmentAdapter
from .tencent import TencentRecruitmentAdapter


ADAPTERS: Dict[str, Type[RecruitmentAdapter]] = {
    ByteDanceRecruitmentAdapter.source: ByteDanceRecruitmentAdapter,
    TencentRecruitmentAdapter.source: TencentRecruitmentAdapter,
}


def list_adapters():
    return sorted(ADAPTERS)


def create_adapter(source: str, **kwargs) -> RecruitmentAdapter:
    adapter_class = ADAPTERS.get(source.lower().strip())
    if not adapter_class:
        raise ValueError(f"不支持的招聘来源：{source}，可选：{', '.join(list_adapters())}")
    return adapter_class(**kwargs)
