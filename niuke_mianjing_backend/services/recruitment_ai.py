from typing import List

from niuke_mianjing_backend.services.openai_client import extract_chat_completion_text, post_chat_completion


def job_brief(job: dict, reference: str = "JD-01") -> str:
    return f"""
资料编号：【{reference}】
公司：{job.get("company")}
岗位：{job.get("title")}
类型：{job.get("recruitment_type")}
方向：{job.get("display_category") or job.get("inferred_track_name") or job.get("category")}
统一岗位族：{job.get("role_family") or "未分类"}
专业方向：{'、'.join(job.get("specialties") or []) or "未提取"}
业务领域：{'、'.join(job.get("business_domains") or []) or "未提取"}
技术栈：{'、'.join(job.get("tech_stack") or []) or "未提取"}
地点：{job.get("location") or "未注明"}
岗位职责：
{(job.get("description") or "")[:2500]}
任职要求：
{(job.get("requirements") or "")[:2500]}
"""


def jobs_brief(jobs: List[dict]) -> str:
    if not jobs:
        return "暂无匹配岗位。"
    return "\n\n---\n\n".join(job_brief(job, f"JD-{index:02d}") for index, job in enumerate(jobs[:8], 1))


def interviews_brief(records: List[dict]) -> str:
    if not records:
        return "暂无匹配面经。"
    parts = []
    for index, item in enumerate(records[:12], 1):
        parts.append(
            f"资料编号：【面经-{index:02d}｜记录 #{item.get('id')}】\n标题：{item.get('title')}\n方向：{item.get('post')}\n时间：{item.get('edit_time')}\n内容：{(item.get('content') or '')[:2200]}"
        )
    return "\n\n---\n\n".join(parts)


def build_full_report_prompt(job_context: str, interviews: List[dict], resume: str) -> str:
    """Build a reading-first interview handbook from one exact JD, interviews, and a resume."""
    return f"""
请根据一个精确投递岗位、近期相关面经和候选人简历，生成一份可反复阅读的中文 Markdown《面试核心资料》。目标是让候选人清楚知道：简历会触发哪些八股、每个项目会被怎样深挖、该怎样忠于事实地回答、最近最可能出现哪些算法题，以及简历应怎样修改。

## 输出合同

1. 标题使用“{{公司}}｜{{精确岗位}}面试核心资料”，只分析输入的精确岗位，不做岗位推荐、岗位排序或投递优先级。
2. 重要判断在句末标注依据：【JD-01】、【面经-01】、【简历】或【AI推断】。引用面经时必须使用下方实际存在的编号。
3. 频率只能来自给定样本，并写成“出现于 5/12 篇”；同一主题合并计数时，同时列出对应面经编号。不得编造概率、命中率、内部题库或行业统计。
4. 不输出准备度、匹配分、雷达图、Offer 概率、冲刺日程、任务清单、模拟面试或验收标准。
5. 严禁编造 QPS、延迟、用户量、业务结果、个人职责、故障、技术实现和选型理由。简历没有的信息统一写成“【需本人替换：具体事实】”，并提供不依赖虚构事实的回答结构。
6. 排序只依据“岗位要求的重要性 + 近期面经出现频率 + 简历直接触发程度”。正文只保留最核心内容，其余放到附录。
7. 回答要像候选人现场能说出口的话，先结论再展开；少讲泛化方法论，不复述整段 JD 或面经，不输出 HTML。

## 固定报告结构

### 00｜本场必看
- 将项目、八股和算法混合排序，只列 8-12 个最可能决定面试结果的问题。
- 每项写：P0/P1、类型、具体问题、为什么会问、证据来源。不要在这里展开答案。

### 01｜近期高频题
- 先写样本总数和日期范围。
- 按实际出现次数从高到低列出题目或同义主题，写明样本计数和全部对应面经编号。
- 分开标记“面经直接出现”和“根据 JD/简历推断”，推断项不得进入频率统计。

### 02｜项目拷打地图
- 覆盖简历中的每个主要项目。站在面试官角度列出会拷打的设计、取舍、底层原理、异常分支、性能、数据一致性、观测、个人贡献与真实性验证点。
- 正文只展开每个项目最核心的 3-5 个问题，并按重要程度与面经频率排序；其余问题移到附录。
- 每个核心问题必须分层展示：①30 秒回答；②完整回答；③面试官连续追问；④事实边界与需要本人补充的内容。

### 03｜简历触发八股
- 每组都包含：经典问题、经典答案、结合该候选人项目的问法、结合项目的回答、可能补问。
- 只选择会被简历技术栈直接触发且对该岗位重要的主题，按 P0/P1 排序。

### 04｜最可能的算法题
- 只列具体题名或完整题意、优先级、最近出现的面经编号/日期、为何与岗位或简历相关。
- 优先收录近期面经直接出现的原题，其次才是简历触发的同类题。
- 本节绝对不要输出题解、思路、代码、复杂度、练习计划或验收方式。

### 05｜简历修改建议
- 使用左右对照表：左侧“原始写法”，右侧“推荐写法”。
- 每项追加小字说明：修改理由、使用的 SCQA/STAR/CAR 方法、必须由本人补齐的事实、改写后可能触发的新追问。
- 推荐写法必须忠于原简历；缺少数据时保留“【需本人替换：...】”，不得替候选人造数字。

### 06｜附录
- 收纳正文未展开的项目拷打点、较低频八股和补充追问，保持简洁并标注优先级，不重复正文。
- 最后列出数据边界：精确岗位、面经样本数与日期、简历范围，以及哪些内容属于 AI 推断。

## 目标岗位资料
{job_context}

## 近期相关面经
{interviews_brief(interviews)}

## 候选人确认后的简历
【简历】
{resume[:12000]}
""".strip()


def call_ai_report(prompt: str, model: str | None = None, model_id: int | None = None) -> str:
    response = post_chat_completion(
        [
            {
                "role": "system",
                "content": "你是站在候选人一侧的资深大厂技术面试官与简历教练。你的目标是让用户准确知道会被问什么、如何忠于事实地回答、简历如何修改；只使用给定资料，输出可追溯的中文 Markdown。",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        timeout=120,
        model=model,
        model_id=model_id,
    )
    if response.status_code >= 400:
        raise ValueError(f"AI 报告生成失败：{response.text[:500]}")
    return extract_chat_completion_text(response.json())
