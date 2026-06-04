import json
from pathlib import Path
from typing import Dict, Optional, List


_JOB_MAP: Optional[Dict[str, int]] = None
_JOB_TREE: Optional[List[dict]] = None


def _load_job_data():
    global _JOB_MAP, _JOB_TREE
    if _JOB_MAP is not None:
        return
    job_json_path = Path(__file__).parent.parent.parent / "job.json"
    with open(job_json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    _JOB_MAP = {}
    _JOB_TREE = []
    result_list = raw.get("data", {}).get("result", [])
    for top_level in result_list:
        top_info = top_level.get("jobInfo", {})
        _JOB_TREE.append({
            "id": top_info["id"],
            "name": top_info["name"],
            "level": top_info["level"],
            "children": [],
        })
        for sub in top_level.get("subJobs", []):
            sub_info = sub.get("jobInfo", {})
            _JOB_MAP[sub_info["name"]] = sub_info["id"]
            _JOB_TREE[-1]["children"].append({
                "id": sub_info["id"],
                "name": sub_info["name"],
                "level": sub_info["level"],
            })


def get_job_id(post: str) -> Optional[int]:
    _load_job_data()
    return _JOB_MAP.get(post)


def get_all_posts() -> List[Dict[str, int]]:
    _load_job_data()
    return [{"name": name, "jobId": jid} for name, jid in _JOB_MAP.items()]


def get_job_tree() -> List[dict]:
    _load_job_data()
    return _JOB_TREE
