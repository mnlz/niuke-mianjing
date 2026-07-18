# 招聘官网爬虫适配器

该目录负责从不同公司的官方招聘网站抓取岗位，并统一转换为
`JobPosting`。适配器只负责抓取和标准化，数据库去重、AI 标签和统计分析
由后续服务层处理。

## 已支持来源

| source | 公司 | 数据来源 |
| --- | --- | --- |
| `alibaba` | 阿里巴巴 | 阿里巴巴招聘官网公开入口 |
| `baidu` | 百度 | 百度招聘官网公开入口 |
| `bytedance` | 字节跳动 | 字节跳动招聘官网公开接口 |
| `huawei` | 华为 | 华为招聘官网公开入口 |
| `jd` | 京东 | 京东招聘官网公开入口 |
| `kuaishou` | 快手 | 快手招聘官网公开入口 |
| `meituan` | 美团 | 美团招聘官网公开入口 |
| `tencent` | 腾讯 | 腾讯招聘官网公开接口 |

统一字段包含岗位标题、分类、岗位族、地点、业务部门、岗位描述、任职要求、
亮点、原始链接、更新时间和原始响应数据。

## 命令行验证

在项目根目录执行：

```powershell
.\.venv\Scripts\python.exe -m niuke_mianjing_backend.crawler.recruitment.cli bytedance --pages 1 --page-size 5
.\.venv\Scripts\python.exe -m niuke_mianjing_backend.crawler.recruitment.cli tencent --keyword 后端 --recruitment-type campus --pages 1 --page-size 5
```

写入 UTF-8 JSON 文件：

```powershell
.\.venv\Scripts\python.exe -m niuke_mianjing_backend.crawler.recruitment.cli tencent --pages 1 --output jobs.json
```

腾讯列表接口不包含完整岗位描述。快速验证时可通过 `--no-detail` 跳过详情请求。

## Python 调用

```python
from niuke_mianjing_backend.crawler.recruitment import create_adapter

adapter = create_adapter("tencent")
jobs = adapter.fetch_all(keyword="后端", max_pages=2, page_size=20)

for job in jobs:
    print(job.company, job.title, job.location)
```

筛选参数会原样传给对应官网接口：

```python
adapter = create_adapter("bytedance")
filters = adapter.fetch_filters()
jobs = adapter.fetch_all(
    filters={"location_code_list": ["CT_125"]},
    max_pages=1,
)
```

## 扩展新公司

1. 继承 `RecruitmentAdapter`。
2. 实现 `fetch_page()`，返回统一的 `JobPage`。
3. 支持 `recruitment_type=campus/intern/social`，不支持的类型返回空列表。
4. 在 `registry.py` 的 `ADAPTERS` 中注册。
5. 保留官网原始岗位链接和 `raw_data`，方便后续追溯及重新分析。

适配器默认带有限速、超时、重试和项目代理配置。批量抓取时应保持低频，
只采集公开岗位信息，并遵守目标网站的使用规则。
