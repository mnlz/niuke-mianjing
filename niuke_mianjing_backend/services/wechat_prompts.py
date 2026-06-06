"""AI prompt builders used by the WeChat article service."""

import json
from typing import Any, Dict


def _build_article_json_prompt(markdown_content: str, title: str, style: str) -> str:
    html_prompt = _build_stream_html_prompt(markdown_content, title, style)
    return f"""
请基于下面要求生成公众号稿件，并只返回 JSON：
{{
  "title": "不超过 30 字的公众号标题",
  "digest": "不超过 100 字的摘要",
  "html": "完整微信公众号 HTML",
  "cover_prompt": "英文封面图提示词，不含文字、logo、水印"
}}

HTML 生成要求：
{html_prompt}
""".strip()


def _build_stream_html_prompt(markdown_content: str, title: str, style: str) -> str:
    content_prompt = _wechat_content_type_prompt(style)
    length_prompt = _wechat_length_prompt(style)
    return f"""
请把原始素材改写成一篇适合微信公众号阅读的中文技术文章。

只输出微信公众号 HTML，不要输出 Markdown 代码块，不要解释。

核心目标：
{length_prompt}

通用内容要求：
1. 保留原始事实，不编造公司、岗位、轮次、结果。
2. 标题和开头要有钩子，但不要标题党，不要夸大数据或面试难度。
3. 使用真人技术号编辑口吻，可以有判断和提醒，但不要空泛说教。
4. 段落短一点，长段拆开；每一屏都要有小标题、列表或提示块形成视觉节奏。
5. 除“面试趋势分析”外，尽量少用表格；确需表格时最多 3-5 行，列数不超过 3，避免手机阅读横向拥挤。
6. 不要把原始面经逐段搬运，不要面面俱到；只选最能代表这场面试的内容。
7. 不要使用“A/B/C 复习优先级”“最后提醒”这类教案式章节名。
8. 允许有轻微幽默和技术圈梗，但要克制；像朋友吐槽面试，不要像段子号。
9. 结尾自然收住，可以给一个短行动清单或互动问题，不要写“最后提醒”。
10. 列表项必须有完整内容，禁止输出单独的“-”“*”“1.”“2.”这类空列表项。

本次内容类型模板：
{content_prompt}

去 AI 味要求：
1. 禁止出现：作为 AI、本文将、综上所述、希望对你有帮助、值得注意的是、事实上、不难发现、总体来说、综合来看。
2. 尽量不用：赋能、闭环、生态、抓手、底层逻辑、范式、沉淀、势能、护城河、降维打击。
3. 不要“首先、其次、最后”机械三段式；用更自然的过渡。
4. 读起来要像技术号编辑写给同学看的复盘，信息密度高，但不端着。
5. 可以使用少量生活化表达，比如“这题不是送分，是开门查户口”“背八股背到冒烟也不够”，但每篇最多 3-5 处。

排版要求：
1. 只能使用微信公众号兼容的 HTML 和内联 style。
2. 不要使用 style 标签、script、svg、canvas、外链 CSS、伪元素、Flexbox、Grid。
3. 不要使用 linear-gradient、rgba/hsla、box-shadow；颜色用 #RRGGBB 或 rgb(r,g,b) 纯色。
4. 复杂视觉块可以用 table 做外层布局，但正文内容不要滥用表格。
5. 用 HTML + CSS 绘制简单视觉块：导读卡片、重点提示、收藏清单、短行动清单。
6. 正文字号 15-16px，line-height 1.75-1.85，移动端阅读舒服。
7. 必须包含注释：<!-- WECHAT_ARTICLE_TITLE: {title} -->
8. 推荐白底、浅蓝/浅黄提示块、深蓝标题，不要大面积彩色背景。

默认标题：{title}

原始 Markdown：
{markdown_content[:12000]}
""".strip()


def _build_stream_markdown_prompt(markdown_content: str, title: str, style: str) -> str:
    content_prompt = _wechat_content_type_prompt(style)
    length_prompt = _wechat_length_prompt(style)
    return f"""
请把原始素材改写成一篇适合微信公众号阅读的中文技术文章。
只输出 Markdown，不要输出 HTML，不要包裹 ```markdown 代码块，不要解释你的处理过程。

默认标题：{title}

核心目标：
{length_prompt}

内容类型模板：
{content_prompt}

通用写作要求：
1. 保留原始事实，不编造公司、岗位、轮次、结果。
2. 标题和开头要有钩子，但不要标题党，不要夸大数据或难度。
3. 写得像技术号编辑复盘给同学看：信息密度高，有判断，但不端着。
4. 段落短一些，移动端好读；每个屏幕最好有小标题、列表、提示块或重点句。
5. 除“面试趋势分析”外，尽量少用表格；确实要用时最多 3-5 行、3 列以内。
6. 可以用 Markdown 标题、加粗、引用、编号列表、短清单、少量表格。
7. 不要写外链，不要写“原文链接”，不要写“作为 AI”“本文将”“综上所述”等 AI 腔。
8. 如果是“单篇面经解读”，需要尽量覆盖原文出现的主要问题，每个问题都给一句短评或答法抓手；但不要把每题展开成知识点教程。
9. 不要使用“A/B/C 复习优先级”“最后提醒”这类教案式章节名。
10. 允许有轻微幽默、贴吧感和技术圈梗，但要克制；像朋友在技术论坛认真吐槽面试，不要像段子号。
11. 结尾自然收住，不要硬写“评论区聊一句”，不要写“最后提醒”。
12. 列表项必须有完整内容，禁止输出单独的“-”“*”“1.”“2.”这类空列表项。

推荐 Markdown 结构：
# {title}

> 一段 50-80 字导读，直接告诉读者这篇最值得看的点。

## 这场面试最值得看的地方

## 问题逐个过一遍

## 面试官其实在筛什么

## 面试前怎么补，不要临场抓瞎

## 收个尾

原始 Markdown：
{markdown_content[:12000]}
""".strip()


def _wechat_content_type_prompt(content_type: str) -> str:
    prompts = {
        "single_interpretation": """
内容类型：单篇面经解读。
目标：把一篇真实面经写成“题题有回应、但不啰嗦”的公众号解读文。读者看完知道每个问题大概怎么接，也知道这场面试最该复盘什么。
推荐模板：
1. 开头钩子：80 字以内，直接点出“为什么这篇值得看”，不要铺背景。
2. 面经速览：用 3-5 个短 bullet 写公司、岗位、轮次、结果、难度。
3. 问题逐个过一遍：尽量覆盖原文出现的主要问题；每题用 2-4 句话回答，结构是“这题在问什么 / 答法抓手 / 别踩的坑”。
4. 如果题目很多，按“网络/Linux/数据库/Redis/项目/算法”等分组，每组内用短编号，不要每题都写大段小标题。
5. 面试官真正想看什么：总结 2-3 个判断，不要扩写成大段理论。
6. 复习建议：给 5 条以内的行动建议，不要叫 A/B/C 复习优先级。
7. 结尾：自然收住，不要硬写评论区互动。
8. 风格要有一点贴吧/技术论坛味：可以轻微吐槽、带梗，但别油腻。比如“这题表面是八股，实际是在查你项目户口”“Redis 问到这里，缓存同学已经开始冒汗了”。
表格限制：原则上不用表格；如果必须用，最多 3 行。
""",
        "knowledge_deep_dive": """
内容类型：技术知识点精讲。
目标：从一篇面经中挑 2-3 个最值得展开的知识点，写成短平快但有收获的技术精讲文。
推荐模板：
1. 开头钩子：指出这篇面经里最容易拉开差距的 2-3 个知识点。
2. 每个知识点独立成节，结构为：面试怎么问 / 30 秒答题模板 / 常见追问 / 易错点。
3. 核心原理只讲面试够用的版本，不写教科书长解释。
4. 结尾给“今晚先补哪几个点”的行动清单，最多 5 条，语气可以轻松一点。
表格限制：不要用大表格；知识点内容用小标题、列表、提示块呈现。
""",
        "manual_rewrite": """
内容类型：手动粘贴。
目标：根据用户粘贴的 Markdown 判断素材类型，并改写成一篇公众号文章。
推荐模板：
1. 如果素材是面经：按“单篇面经解读”写。
2. 如果素材是知识笔记：按“技术知识点精讲”写。
3. 如果素材是零散问题：整理成清单文，补充简答关键词和复习建议。
4. 如果素材已经是文章：优化标题、开头、节奏和移动端排版，保留核心观点。
5. 结尾给可执行建议或互动问题。
6. 如果素材偏严肃，可以适当加 2-3 句轻松吐槽，但不要牺牲准确性。
表格限制：默认不用表格；除非原素材强依赖表格，且表格要短。
""",
        "quick_checklist": """
内容类型：高频题速查清单。
目标：把一篇面经整理成适合收藏、临考前快速翻看的题目清单。
推荐模板：
1. 开头钩子：说明这份清单适合什么读者、什么时候看。
2. 速查规则：告诉读者每题只看三件事：问法、30 秒答法、易错点。
3. 清单正文：整理 8-10 个问题，每个问题用独立小块呈现：题目 / 30 秒答法 / 易错点 / 建议先看程度。
4. 如果问题很多，按 Java 基础、并发、数据库、框架、项目等分组。
5. 结尾给“今晚先背这 5 个”的短清单，不要额外扩写；可以用轻松标题，比如“今晚别硬刚，先背这几个”。
表格限制：不要做大表格；用编号卡片或短列表。不要写 A/B/C 复习优先级。
""",
        "interviewer_chain": """
内容类型：面试官追问链路。
目标：不是罗列题目，而是还原面试官如何从一个问题继续追问，帮助读者练“接招能力”。
推荐模板：
1. 开头钩子：指出很多人不是不会第一问，而是倒在第二问、第三问。
2. 选择 3-5 个核心问题，每个问题写成一条追问链。
3. 每条追问链结构：第一问 / 合格回答 / 面试官可能继续追问 1-3 个 / 追问背后的考察点 / 怎么答更稳 / 容易暴露的短板。
4. 加一节“被追问时别急着背八股”，讲表达策略。
5. 结尾给模拟练习方法，不要叫“最后提醒”。
6. 可以带一点轻松吐槽，比如“第一问会不算赢，第二问不慌才算稳”。
表格限制：不用表格；追问链用箭头、短段落和提示块呈现。
""",
        "trend_analysis": """
内容类型：面试趋势分析。
该类型通常由专门的高频分析接口生成。如果误走当前接口，请按“单篇素材中的趋势观察”处理，不要伪造频次。
""",
    }
    return prompts.get(content_type, prompts["single_interpretation"]).strip()


def _wechat_length_prompt(content_type: str) -> str:
    prompts = {
        "single_interpretation": """
写成“逐题短评”，不是长报告。
- 正文控制在 2200-3200 个中文字符左右，最多 5 个二级标题。
- 尽量覆盖原文出现的主要问题，但每题只写 2-4 句，别展开成百科。
- 开头 3 秒抓人：直接给结果、岗位、最值得看的考点或一个反常识判断。
- 每个小节都要短：能用 3 句话说清，就不要写 8 句话。
""",
        "knowledge_deep_dive": """
写成“轻精讲”，不是百科。
- 正文控制在 1500-2200 个中文字符左右，最多讲 3 个知识点。
- 原理只讲面试用得上的部分，少铺历史、定义和背景。
- 每个知识点必须给一个 30 秒答题模板，方便读者收藏。
""",
        "manual_rewrite": """
写成“可直接发的短稿”。
- 默认控制在 1200-2000 个中文字符左右。
- 如果原文很长，先做取舍，不要压缩式复述全文。
- 优先保留能吸引读者继续看下去的冲突点、结果、经验和清单。
""",
        "quick_checklist": """
写成“收藏型速查清单”。
- 正文控制在 1200-1800 个中文字符左右。
- 只保留 8-10 个最值得背的问题。
- 每题回答最多 80 字，重点是临考前能快速扫。
""",
        "interviewer_chain": """
写成“追问链训练稿”。
- 正文控制在 1500-2200 个中文字符左右。
- 只选 3 条最典型追问链，每条链最多 3 个追问。
- 重点写面试官为什么追问，不要展开成知识点大全。
""",
        "trend_analysis": """
写成“趋势短报告”。
- 正文控制在 1800-2600 个中文字符左右。
- 只展示最重要的频次结论和备考动作，不要堆满数据。
""",
    }
    return prompts.get(content_type, prompts["single_interpretation"]).strip()


def _build_question_analysis_html_prompt(analysis: Dict[str, Any]) -> str:
    title = analysis["title"]
    stats = analysis.get("stats", {})
    records = analysis.get("records", [])
    top_questions = stats.get("top_questions", [])
    categories = stats.get("categories", [])
    source_payload = {
        "title": title,
        "digest": analysis.get("digest"),
        "stats": stats,
        "top_questions": top_questions,
        "categories": categories,
        "records": records,
    }
    return f"""
请基于下面的真实牛客面经素材，直接分析并写成一篇适合微信公众号发布的中文技术选题文章。

只输出微信公众号 HTML，不要输出 Markdown 代码块，不要解释。

参考版式方向：
用户想要接近这类公众号报告文风：标题直给，正文是白底深蓝数据报告风；少用花哨卡片，多用分割线、居中小标题、表格榜单、频次数字加粗、分类清单。整体像“某公司某岗位高频题 TOP 清单 + 备考指南”，不是营销海报。

内容目标：
1. 你要真的读完 records 里的真实面经素材，综合面经语境、问题频次和知识点分类做判断，不要只改写统计字段。
2. 标题和开头要有点击欲，但不要标题党，不要夸大数据。
3. 开头 80 字内说清楚：统计了哪家公司、哪个岗位、什么时间范围、样本数、对读者有什么用。
4. 正文控制在 1800-2600 个中文字符左右，不要写成万字报告。
5. 文章必须包含：引子、数据结论、高频 TOP8 表格、分类 TOP 清单、最低限度备考清单、互动收尾。
6. 高频问题不能只罗列，要补充“为什么爱问 / 简答抓手”，每题解释控制在 60 字以内。
7. 需要有 2-3 句像真人编辑的观察，比如“最近更偏基础深挖还是项目追问”“哪些题看似八股但其实在考工程经验”。
8. 语气像有经验的技术号编辑，少一点 AI 腔，不要出现“作为 AI”“本文将”“综上所述”等套话。
9. 可以提醒数据来自当前库内面经样本，不代表全部面试。
10. 不要把 records 原文整段粘贴出来，要消化成“趋势 + 高频题 + 备考策略”。
11. 结尾要自然引导收藏和复盘，可以抛一个问题让读者留言，不要硬广。

去 AI 味要求：
1. 禁止出现：作为 AI、本文将、综上所述、希望对你有帮助、值得注意的是、事实上、不难发现、总体来说、综合来看。
2. 尽量不用：赋能、闭环、生态、抓手、底层逻辑、范式、沉淀、势能、护城河、降维打击。
3. 不要“首先、其次、最后”机械连接，过渡要像真人编辑写稿。

排版要求：
1. 只能使用微信公众号兼容的 HTML 和内联 style。
2. 不要使用 style 标签、script、svg、canvas、外链 CSS、伪元素、Flexbox、Grid。
3. 不要使用 linear-gradient、rgba/hsla、box-shadow；复杂布局尽量用 table，避免同步到微信后样式丢失。
4. 主色使用深蓝 rgb(15,76,129)，正文文字 rgb(63,63,63)，白底，不要渐变，不要大面积彩色背景。
5. 正文段落统一 14px、line-height 1.75、letter-spacing 0.08em-0.1em、margin 1.3em 8px、text-align justify。
6. H1 使用居中、下边框深蓝、display:table、padding:0 1em、font-size:16.8px。
7. H2 使用居中深蓝底白字小标签，margin:4em auto 2em，display:table，padding:0 0.4em，font-size:16.8px。
8. 章节之间使用 hr，样式为浅灰 2px 横线，margin:1.5em 0，不要使用 rgba。
9. 高频榜必须用 table，列包括“排名 / 高频题 / 频次 / 复习抓手”，最多 8 行。表格边框 #dfdfdf，单元格 padding 0.25em 0.5em，频次用深蓝 strong 加粗。
10. 分类部分可以继续用小表格或编号段落，避免一堆圆角卡片；最多使用 1 个浅蓝提示块作为收尾提示。
11. 必须包含注释：<!-- WECHAT_ARTICLE_TITLE: {title} -->

建议 HTML 样式骨架：
<section style="text-align:left;line-height:1.75;font-family:-apple-system-font,BlinkMacSystemFont,'Helvetica Neue','PingFang SC','Microsoft YaHei',Arial,sans-serif;font-size:14px;color:rgb(63,63,63);background:#fff;">
  <h1 style="font-size:16.8px;font-weight:bold;margin:2em auto 1em;text-align:center;display:table;padding:0 1em;color:rgb(63,63,63);border-bottom:2px solid rgb(15,76,129);">标题</h1>
  <p style="margin:1.5em 8px;text-align:justify;line-height:1.75;font-size:14px;letter-spacing:0.1em;color:rgb(63,63,63);">正文...</p>
  <hr style="border:0;border-top:2px solid #e5e7eb;height:0;margin:1.5em 0;" />
  <h2 style="font-size:16.8px;font-weight:bold;margin:4em auto 2em;text-align:center;display:table;padding:0 0.4em;color:#fff;background:rgb(15,76,129);">章节标题</h2>
</section>

默认标题：{title}

真实面经素材和轻量统计 JSON：
{json.dumps(source_payload, ensure_ascii=False)[:18000]}
""".strip()


def _build_question_analysis_markdown_prompt(analysis: Dict[str, Any]) -> str:
    title = analysis["title"]
    stats = analysis.get("stats", {})
    records = analysis.get("records", [])
    source_payload = {
        "title": title,
        "digest": analysis.get("digest"),
        "stats": stats,
        "records": records,
    }
    return f"""
请基于下面的真实牛客面经素材，写成一篇适合微信公众号发布的“面试趋势短报告”。

只输出 Markdown，不要输出 HTML，不要包裹 ```markdown 代码块，不要解释。

短稿要求：
1. 正文控制在 1800-2600 个中文字符左右。
2. 开头 80 字内说清：公司、岗位、时间范围、样本数、读者为什么要看。
3. 高频题最多写 TOP8，不要把所有题都展开。
4. 每个高频题只写：出现频次 / 为什么爱问 / 复习抓手，解释控制在 80 字以内。
5. 趋势观察只写 2-3 条，像真人编辑判断，不要写成数据论文。
6. 收尾给“今晚先补什么”的 5 条短清单，不要写“最后提醒”。
7. 不要使用“A/B/C 复习优先级”。
8. 可以加少量轻松吐槽或技术圈梗，比如“这不是八股，是项目体检”，但每篇最多 3-5 处。
9. 不要把 records 原文整段粘贴出来，不要写“作为 AI”“本文将”“综上所述”。

推荐结构：
# {title}

> 50-80 字导读。

## 先看数据结论

## 高频题 TOP8

## 面试官更在意什么

## 今晚先补这 5 个

真实面经素材和轻量统计 JSON：
{json.dumps(source_payload, ensure_ascii=False)[:18000]}
""".strip()


def _build_quick_checklist_html_prompt(analysis: Dict[str, Any]) -> str:
    title = analysis["title"]
    stats = analysis.get("stats", {})
    records = analysis.get("records", [])
    source_payload = {
        "title": title,
        "digest": analysis.get("digest"),
        "stats": stats,
        "records": records,
    }
    return f"""
请基于下面的真实牛客面经样本，写成一篇适合微信公众号发布的“高频题速查清单”。

只输出微信公众号 HTML，不要输出 Markdown 代码块，不要解释。

重要边界：
1. 这是 {stats.get("sample_mode", "样本抽取")}，范围是 {stats.get("range_label", "当前样本")}，样本数 {stats.get("record_count", 0)} 篇。
2. 不要写成“全网统计”或“全部面试趋势”，只能说“从当前样本看”。
3. 你要读 records 里的真实面经内容，结合轻量频次统计整理速查清单。

内容目标：
1. 开头 80 字内说清：公司、岗位、样本数、抽样方式、这篇适合谁收藏。
2. 正文控制在 1200-1800 个中文字符左右，输出 8-10 个最值得背的高频题。
3. 每题包括：题目、30 秒答法、易错点、建议先看程度；每题解释不要超过 100 字。
4. 如果题目多，按 Java 基础、并发、数据库、框架、项目、算法等分组。
5. 补充“今晚优先背哪 5 个”和“面试前 10 分钟怎么扫一遍”，都用短清单。
6. 语气像有经验的技术号编辑，短句多一点，适合手机快速阅读。

表格限制：
1. 不要做大表格，不要 4 列以上表格。
2. 正文清单用编号、小标题、浅色提示块呈现。
3. 最多允许一个 3 行以内的小表格，用来总结先看顺序。

排版要求：
1. 只能使用微信公众号兼容的 HTML 和内联 style。
2. 不要使用 style 标签、script、svg、canvas、外链 CSS、伪元素、Flexbox、Grid。
3. 不要使用 linear-gradient、rgba/hsla、box-shadow。
4. 白底，深蓝标题，正文 15-16px，line-height 1.75-1.85。
5. 必须包含注释：<!-- WECHAT_ARTICLE_TITLE: {title} -->

默认标题：{title}

真实面经样本 JSON：
{json.dumps(source_payload, ensure_ascii=False)[:18000]}
""".strip()


def _build_quick_checklist_markdown_prompt(analysis: Dict[str, Any]) -> str:
    title = analysis["title"]
    stats = analysis.get("stats", {})
    records = analysis.get("records", [])
    source_payload = {
        "title": title,
        "digest": analysis.get("digest"),
        "stats": stats,
        "records": records,
    }
    return f"""
请基于下面的真实牛客面经样本，写成一篇适合微信公众号发布的“高频题速查清单”。

只输出 Markdown，不要输出 HTML，不要包裹 ```markdown 代码块，不要解释。

重要边界：
1. 这是 {stats.get("sample_mode", "样本抽取")}，范围是 {stats.get("range_label", "当前样本")}，样本数 {stats.get("record_count", 0)} 篇。
2. 不要写成“全网统计”或“全部面试趋势”，只能说“从当前样本看”。
3. 正文控制在 1200-1800 个中文字符左右，适合手机快速阅读和收藏。

内容要求：
1. 开头 60-80 字内说清：公司、岗位、样本数、这篇适合谁收藏。
2. 只整理 8-10 个最值得背的高频题。
3. 每题固定三行：问法 / 30 秒答法 / 易错点。
4. 每题解释最多 100 字，不要展开成知识点长文。
5. 结尾给“面试前 10 分钟扫一遍”的 5 条短清单。
6. 不要写“作为 AI”“本文将”“综上所述”，不要硬广。

推荐结构：
# {title}

> 50-80 字导读。

## 这份清单怎么看

## 高频题速查

## 面试前 10 分钟扫这 5 个

真实面经样本 JSON：
{json.dumps(source_payload, ensure_ascii=False)[:18000]}
""".strip()


def _build_cover_prompt(title: str, markdown_content: str, style: str) -> str:
    cover_direction = _wechat_cover_direction(style)
    return f"""
Create a premium WeChat official account cover image for a Chinese technical interview article.
Canvas target: 900x500, clean 9:5 editorial composition, suitable for mobile feed preview.
Topic: {title}.
Visual direction: {cover_direction}.
Style: modern but restrained, crisp composition, high contrast focal area, no clutter.
Color: deep blue, white, light gray, small gold or cyan accent; avoid purple gradient and noisy neon.
Do not include readable Chinese/English text, logo, watermark, UI screenshot, cartoon character, or messy symbols.
""".strip()


def _wechat_cover_direction(content_type: str) -> str:
    directions = {
        "single_interpretation": "interview notes interpretation, document review, selected questions, subtle code and checklist elements",
        "knowledge_deep_dive": "deep technical knowledge explanation, layered architecture, code snippets as abstract shapes, focused learning atmosphere",
        "trend_analysis": "professional data report, question frequency analysis, clean charts, ranking list shapes, knowledge graph",
        "manual_rewrite": "editorial technology article, clean reading experience, abstract article layout and notebook elements",
        "quick_checklist": "compact study checklist, flash cards, priority markers, interview preparation notes",
        "interviewer_chain": "interviewer follow-up chain, conversation flow, connected question nodes, reasoning path",
    }
    return directions.get(content_type, directions["single_interpretation"])
