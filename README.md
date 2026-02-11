# Reddit + Anthropic Insight Pipeline

这个工具会：
- 输入一个研究问题，由 LLM 自动分解成 Reddit 抓取任务
- 用 Anthropic LLM 提取使用场景、购买动机、购买顾虑/摩擦
- 产出两份 Markdown：综合分析报告 + 原声打标明细
- Web 前端不暴露凭证，凭证仅走服务端环境变量

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 配置服务端凭证（必填）

```bash
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_client_secret"
export REDDIT_USER_AGENT="your_app_name/1.0 by your_reddit_username"
export CLAUDE_BASE_URL="http://your-claude-gateway:8080"
export CLAUDE_API_KEY="your_claude_key"
export CLAUDE_MODEL="claude-opus-4-5"
```

说明：
- `REDDIT_CLIENT_ID/SECRET`：在 Reddit 应用后台创建 script app 获取
- `REDDIT_USER_AGENT`：必须是明确且唯一的 UA
- `CLAUDE_BASE_URL`：Anthropic Messages 兼容网关地址
- `CLAUDE_API_KEY`：该网关 API Key
- `ACCESS_PASSCODE`：可选，同伴访问验证码（配置后页面先校验验证码）

## 3. 运行

### 方式 0：一键启动（自动创建 venv）

```bash
./run.sh
```

默认凭证读取：
- 应用会优先读取 `/.streamlit/secrets.toml`
- 示例见 `/.streamlit/secrets.example.toml`
- 如果凭证缺失，页面会直接报错并禁用运行按钮

### 方式 A：Web 界面（推荐）

```bash
streamlit run app.py
```

启动后在浏览器中填写：
- 研究问题、subreddit、抓取数量、任务拆解数、排序、时间窗口、模型

点击“开始分析”后会自动生成并可下载两份 Markdown 报告。

### 方式 B：命令行

```bash
python reddit_anthropic_insights.py \
  --question "家庭咖啡机用户在购买前最看重什么，最常见顾虑是什么？" \
  --subreddit all \
  --limit 60 \
  --task-count 4 \
  --sort new \
  --time-filter year \
  --model claude-opus-4-5 \
  --output-dir reports
```

运行成功后会输出：
- `reports/reddit_insight_report_<question_slug>_<timestamp>.md`
- `reports/reddit_raw_labeled_<question_slug>_<timestamp>.md`

## 4. 线上部署（推荐 Docker）

仓库已包含 `Dockerfile`，可部署到 Render / Railway / Fly.io / ECS 等容器平台。

### Render 示例
1. 新建 `Web Service`，连接本仓库。
2. 选择 `Docker` 部署方式。
3. 在环境变量中配置：
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`
   - `REDDIT_USER_AGENT`
   - `CLAUDE_BASE_URL`
   - `CLAUDE_API_KEY`
   - `CLAUDE_MODEL`（可选，默认 `claude-opus-4-5`）
   - `ACCESS_PASSCODE`（可选，建议开启）
4. 部署完成后直接通过公网 URL 访问。

### 本地用 Docker 验证
```bash
docker build -t reddit-insight-app .
docker run --rm -p 8501:8501 \
  -e REDDIT_CLIENT_ID="xxx" \
  -e REDDIT_CLIENT_SECRET="xxx" \
  -e REDDIT_USER_AGENT="reddit-insight-app/1.0 by service" \
  -e CLAUDE_BASE_URL="http://host.docker.internal:8080" \
  -e CLAUDE_API_KEY="xxx" \
  -e CLAUDE_MODEL="claude-opus-4-5" \
  reddit-insight-app
```

## 5. 报告内容

报告包含：
- 抓取任务拆解计划（LLM 分解结果）
- 量化统计（相关性/阶段/情绪分布、均值/中位数）
- 使用场景/动机/摩擦 Top 因素频次
- Meta 广告角度与关键原声引用
- 每条帖子的结构化语义分析

## 6. 参数说明

- `--question`：研究问题（必填，`--keyword` 仅兼容旧用法）
- `--subreddit`：子版块，不填默认 `all`
- `--limit`：最大抓取帖子数，默认 `40`
- `--task-count`：LLM 拆解抓取任务数量，默认 `4`
- `--sort`：`relevance|hot|top|new|comments`，默认 `new`
- `--time-filter`：`all|day|hour|month|week|year`，默认 `year`
- `--model`：Anthropic 模型名，默认 `claude-opus-4-5`
- `--output-dir`：输出目录，默认 `reports`
