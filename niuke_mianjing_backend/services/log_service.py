from typing import Optional, Dict, List
from niuke_mianjing_backend.repositories.niuke_repo import NiukeRepository
from niuke_mianjing_backend.repositories.crawl_log_repo import CrawlLogRepository
from niuke_mianjing_backend.utils.role_taxonomy import (
    AI_FAMILY_PRIORITY,
    ROLE_FAMILY_LABELS,
    ROLE_GROUP_LABELS,
    classify_interview_role,
)


def annotate_interview_role(record: Dict) -> Dict:
    classification = classify_interview_role(
        record.get("title") or "",
        record.get("post") or "",
        record.get("content") or "",
    )
    return {
        **record,
        "role_group": classification["role_group"],
        "role_family": classification["role_family"],
        "role_group_name": ROLE_GROUP_LABELS.get(classification["role_group"], "其他"),
        "role_family_name": ROLE_FAMILY_LABELS.get(classification["role_family"], "其他岗位"),
    }


def build_interview_role_groups(records: List[Dict]) -> List[Dict]:
    counts: Dict[str, Dict[str, int]] = {}
    for record in records:
        item = annotate_interview_role(record)
        families = counts.setdefault(item["role_group"], {})
        families[item["role_family"]] = families.get(item["role_family"], 0) + 1
    return [
        {
            "id": group,
            "name": ROLE_GROUP_LABELS[group],
            "count": sum(counts[group].values()),
            "role_families": [
                {"id": family, "name": ROLE_FAMILY_LABELS.get(family, "其他岗位"), "count": count}
                for family, count in sorted(
                    counts[group].items(),
                    key=lambda entry: (AI_FAMILY_PRIORITY.get(entry[0], len(AI_FAMILY_PRIORITY)), -entry[1], entry[0]),
                )
            ],
        }
        for group in ROLE_GROUP_LABELS
        if group in counts
    ]


class LogService:
    def __init__(self):
        self.niuke_repo = NiukeRepository()
        self.log_repo = CrawlLogRepository()

    async def init_table(self):
        await self.log_repo.init_table()

    async def get_crawl_logs(
        self,
        post: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        return await self.log_repo.get_logs(post, status, start_date, end_date, limit)

    async def get_stats(self) -> Dict:
        stats_data = await self.niuke_repo.get_stats()
        return {
            "total_records": stats_data["total_records"],
            "active_records": stats_data["active_records"],
            "post_stats": stats_data["post_stats"],
        }

    async def get_niuke_data(
        self,
        post: Optional[str] = None,
        company: Optional[str] = None,
        role_group: Optional[str] = None,
        role_family: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict:
        if role_group or role_family:
            # ponytail: in-memory scan is enough for ~1k rows; persist indexed roles if this becomes slow.
            candidates = [
                annotate_interview_role(item)
                for item in await self.niuke_repo.get_classification_rows(post, company)
            ]
            matched = [
                item for item in candidates
                if (not role_group or item["role_group"] == role_group)
                and (not role_family or item["role_family"] == role_family)
            ]
            rows = await self.niuke_repo.get_by_ids(
                [item["id"] for item in matched[offset:offset + limit]],
                limit,
            )
            return {"data": [annotate_interview_role(item) for item in rows], "total": len(matched)}
        result = await self.niuke_repo.get_data(post, company, limit, offset)
        result["data"] = [annotate_interview_role(item) for item in result["data"]]
        return result

    async def get_niuke_record(self, record_id: int) -> Optional[Dict]:
        record = await self.niuke_repo.get_by_id(record_id)
        return annotate_interview_role(record) if record else None

    async def get_filters(self, company: Optional[str] = None) -> Dict:
        filters = await self.niuke_repo.get_filters()
        filters["role_groups"] = build_interview_role_groups(
            await self.niuke_repo.get_classification_rows(company=company)
        )
        return filters
