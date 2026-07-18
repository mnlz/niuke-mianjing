import argparse
import json

from .registry import create_adapter, list_adapters


def main():
    parser = argparse.ArgumentParser(description="验证大厂招聘官网适配器")
    parser.add_argument("source", choices=list_adapters())
    parser.add_argument("--keyword", default="")
    parser.add_argument("--recruitment-type", choices=["campus", "intern", "social"], default="campus")
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=5)
    parser.add_argument("--no-detail", action="store_true", help="腾讯适配器不请求职位详情")
    parser.add_argument("--output", help="可选：将结果写入 JSON 文件")
    args = parser.parse_args()

    adapter = create_adapter(args.source, sleep_interval=0.2)
    jobs = adapter.fetch_all(
        keyword=args.keyword,
        max_pages=args.pages,
        page_size=args.page_size,
        recruitment_type=args.recruitment_type,
        include_detail=not args.no_detail,
    )
    payload = [job.model_dump(mode="json") for job in jobs]
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as output_file:
            output_file.write(text)
        print(f"已写入 {args.output}，共 {len(payload)} 条岗位")
    else:
        print(text)


if __name__ == "__main__":
    main()
