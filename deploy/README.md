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

后端服务：

`systemctl status niuke-mianjing`

后端日志：

`journalctl -u niuke-mianjing -f`

部署目录：

`/opt/niuke-mianjing/current`

Nginx 配置：

`/etc/nginx/conf.d/niuke-mianjing.conf`
