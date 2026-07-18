# CI/CD 部署说明

本项目使用 GitHub Actions 部署到服务器。推送 `master` 分支后会自动执行：

1. 安装前端依赖并执行 `npm run build`
2. 检查后端 Python 语法
3. 打包后端源码、前端 `dist` 和线上 `.env`
4. 通过 SSH 上传到服务器
5. 在服务器安装/更新运行依赖、初始化数据库、配置 systemd 和 Nginx
6. 重启后端服务并做健康检查

## GitHub Secrets

进入 GitHub 仓库：

`Settings -> Secrets and variables -> Actions -> New repository secret`

需要配置：

| Secret | 说明 |
| --- | --- |
| `SERVER_HOST` | 服务器 IP，例如 `120.26.3.11` |
| `SERVER_USER` | SSH 用户，例如 `root` |
| `SERVER_PASSWORD` | SSH 密码。也可以不用这个，改用 `SERVER_SSH_KEY` |
| `SERVER_SSH_KEY` | SSH 私钥，可选。设置后优先使用私钥 |
| `SERVER_PORT` | SSH 端口，可选，不填默认 `22` |
| `SERVER_ENV` | 服务器运行用 `.env` 完整内容 |

`SERVER_PASSWORD` 和 `SERVER_SSH_KEY` 至少配置一个。

## SERVER_ENV 示例

复制 `deploy/server.env.example` 的内容到 `SERVER_ENV`，再把占位值改成真实值。

建议服务器数据库用户使用 `niuke_app`，不要用 MySQL `root`。

## 线上访问

默认部署到：

`http://120.26.3.11:8080`

如果域名 `mnls.cloud` 已解析到服务器，部署脚本也会配置：

`http://mnls.cloud/`

后端服务：

`systemctl status niuke-mianjing`

后端日志：

`journalctl -u niuke-mianjing -f`

部署目录：

`/opt/niuke-mianjing/current`

Nginx 配置：

`/etc/nginx/conf.d/niuke-mianjing.conf`

## 标准发布流程

以下流程已在 2026-07-18 的生产发布中实际验证。生产服务器当前使用 Python 3.11，系统自带的 Python 3.9 保留不动。

### 1. 发布前检查

确认当前分支、待提交文件和 GitHub 登录状态：

```bash
git status -sb
git diff --check
gh auth status
gh secret list
```

注意：

- 只有合并或推送到 `master` 才会触发部署，推送功能分支不会部署。
- 工作区有无关文件时不要执行 `git add -A`，只暂存本次发布文件。
- 每次部署都会使用 GitHub Secret `SERVER_ENV` 完整覆盖新版本的 `.env`。发布前必须确认它仍指向原生产数据库，且包含全部线上配置。
- 尽量避开爬虫和定时任务正在执行的时间。任务配置保存在 MySQL，不会因部署丢失，但正在执行的任务会被服务重启中断。

运行测试：

```bash
.venv/bin/python -m compileall -q niuke_mianjing_backend main.py
.venv/bin/python -m pytest -q

cd niuke-mianjing-frontend
npm test
npm run build
cd ..
```

### 2. 记录生产基线并备份数据库

连接服务器：

```bash
ssh root@120.26.3.11
```

确认当前服务健康：

```bash
systemctl is-active niuke-mianjing
curl -fsS http://127.0.0.1:8000/health
/opt/niuke-mianjing/current/.venv/bin/python --version
sha256sum /opt/niuke-mianjing/current/.env
```

加载数据库配置并记录核心数据量：

```bash
set -a
source /opt/niuke-mianjing/current/.env
set +a

for table in niuke scheduled_jobs scheduled_job_runs crawl_log app_users wechat_articles official_recruitment_jobs; do
  count=$(mysql -N -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" \
    -e "SELECT COUNT(*) FROM $table" 2>/dev/null)
  echo "$table=$count"
done

mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" \
  -e "SELECT id, job_id, schedule_type, schedule, next_run_time, status FROM scheduled_jobs ORDER BY id"
```

生产面经表名是 `niuke`，不是旧文档中曾出现的 `niuke_data`。

创建发布前整库备份：

```bash
set -o pipefail
stamp=$(date +%Y%m%d-%H%M%S)
mkdir -p /opt/niuke-mianjing/backups
umask 077

mysqldump --single-transaction --quick --routines --triggers \
  -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" \
  | gzip -1 > "/opt/niuke-mianjing/backups/predeploy-$stamp.sql.gz"

gzip -t "/opt/niuke-mianjing/backups/predeploy-$stamp.sql.gz"
ls -lh "/opt/niuke-mianjing/backups/predeploy-$stamp.sql.gz"
```

只有备份命令和 `gzip -t` 都成功后才继续发布。

### 3. 提交并触发部署

在功能分支提交并推送：

```bash
git add <本次发布文件>
git diff --cached --check
git commit -m "<发布说明>"
git push -u origin "$(git branch --show-current)"
```

创建 PR 并合并到 `master`：

```bash
gh pr create --base master --head "$(git branch --show-current)" --fill
gh pr view --web
gh pr merge <PR编号或URL> --merge
```

监控本次部署：

```bash
gh run list --workflow deploy.yml --limit 3
gh run watch <RUN_ID> --interval 5 --exit-status
```

不要只看到前端构建成功就结束，必须等待 `Upload and deploy` 和整个 workflow 成功。

### 4. 发布后验收

服务器内部检查：

```bash
systemctl is-active niuke-mianjing
systemctl status niuke-mianjing --no-pager -l
/opt/niuke-mianjing/current/.venv/bin/python --version
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8080/ | grep -o '<title>[^<]*</title>' | head -1
```

预期项目虚拟环境显示 Python 3.11，健康检查返回：

```json
{"status":"healthy"}
```

再次运行第 2 步的数据量和定时任务 SQL，确认：

- 原业务表数据量没有下降。
- `scheduled_jobs` 数量不变，任务仍为 `active` 或原有的 `paused` 状态。
- `next_run_time` 合理。
- `.env` 的 SHA-256 与发布前一致；若变化，立即核对 `SERVER_ENV` 和数据库目标。

检查启动日志：

```bash
journalctl -u niuke-mianjing --since "10 minutes ago" --no-pager \
  | grep -E 'Scheduler started|Added job|Application startup complete|ERROR|Traceback'
```

从外部检查真实访问链路：

```bash
curl -fsS http://120.26.3.11:8080/health
curl -fsS 'http://120.26.3.11:8080/api/recruitment/jobs?source=tencent&recruitment_type=campus&page=1&page_size=1'
```

### 5. 首次部署后的岗位数据

代码部署不会复制本地 MySQL 数据。首次创建 `official_recruitment_jobs` 后表为空是正常的，必须在后台岗位管理页执行一次官网刷新。

建议：

- 只启动一轮全量刷新，不要同时运行“全量刷新”和逐公司回填。
- 刷新期间查看 `official_recruitment_refresh_runs` 的 `running/success/suspicious/failed` 状态。
- 数量骤降或详情完整率不足时，质量门禁会把批次标记为 `suspicious`，不会用小批次覆盖已有完整数据。
- 不要为了消除 `suspicious` 盲目使用 `force_publish`；先确认官网确实只剩这些岗位。

查询最新岗位数量：

```bash
mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e '
SELECT source, recruitment_type, COUNT(*) AS total
FROM official_recruitment_jobs
WHERE is_latest = 1
GROUP BY source, recruitment_type
ORDER BY source, recruitment_type;'
```

## 失败与回滚

部署脚本会在切换版本前使用新虚拟环境导入 FastAPI 应用。导入失败时不会替换当前版本。

切换后若健康检查失败，脚本会自动：

1. 停止失败服务。
2. 将失败版本保留为 `/opt/niuke-mianjing/failed-时间戳`。
3. 将 `/opt/niuke-mianjing/current.previous` 恢复为 `current`。
4. 重新启动旧版本服务。

自动回滚后仍需确认：

```bash
systemctl is-active niuke-mianjing
curl -fsS http://127.0.0.1:8000/health
journalctl -u niuke-mianjing --no-pager -n 120
```

如需手动回滚，先保留失败目录，不要直接删除：

```bash
stamp=$(date +%Y%m%d-%H%M%S)
systemctl stop niuke-mianjing
mv /opt/niuke-mianjing/current "/opt/niuke-mianjing/failed-$stamp"
mv /opt/niuke-mianjing/current.previous /opt/niuke-mianjing/current
systemctl start niuke-mianjing
curl -fsS http://127.0.0.1:8000/health
```

## 本次发布踩坑记录

- 生产服务器原先使用 Python 3.9，新代码中的 `int | None` 注解在导入阶段失败。当前部署已改为 Python 3.11.13，并保留系统 Python 3.9。
- 原部署脚本只在切换后检查健康，失败时不会自动恢复；现在已经增加切换前应用导入和切换后自动回滚。
- `SERVER_ENV` 会完整替换新版本 `.env`，它是比数据库初始化脚本更需要关注的风险点。
- 数据库初始化只执行 `CREATE ... IF NOT EXISTS`，不会执行 `DROP`、`TRUNCATE` 或清空业务数据。
- GitHub Actions 的 Node.js 20 弃用提示目前只是 warning，不代表部署失败；仍应以后升级对应 Action 版本。
