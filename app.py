#!/usr/bin/env python3

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from reddit_anthropic_insights import run_pipeline


def _get_secret(name: str, fallback: str = "") -> str:
    env_value = os.getenv(name)
    if env_value:
        return env_value.strip()

    try:
        secret_value = st.secrets.get(name)
    except StreamlitSecretNotFoundError:
        secret_value = None

    if secret_value is not None:
        return str(secret_value).strip()
    return fallback.strip()


st.set_page_config(page_title="Reddit Insight Analyzer", page_icon=":mag:", layout="wide")
st.title("Reddit Insight Analyzer")
st.caption("输入研究问题，自动抓取并分析 Reddit 语义信号，输出双报告")

# Server-side only secrets (no UI fields)
server_reddit_client_id = _get_secret("REDDIT_CLIENT_ID")
server_reddit_client_secret = _get_secret("REDDIT_CLIENT_SECRET")
server_reddit_user_agent = _get_secret("REDDIT_USER_AGENT", "reddit-insight-app/1.0 by service")
server_claude_base_url = _get_secret("CLAUDE_BASE_URL")
server_claude_api_key = _get_secret("CLAUDE_API_KEY")
server_claude_model = _get_secret("CLAUDE_MODEL", "claude-opus-4-5")
access_passcode = _get_secret("ACCESS_PASSCODE")

missing = []
if not server_reddit_client_id:
    missing.append("REDDIT_CLIENT_ID")
if not server_reddit_client_secret:
    missing.append("REDDIT_CLIENT_SECRET")
if not server_reddit_user_agent:
    missing.append("REDDIT_USER_AGENT")
if not server_claude_base_url:
    missing.append("CLAUDE_BASE_URL")
if not server_claude_api_key:
    missing.append("CLAUDE_API_KEY")

if missing:
    st.error(
        "服务端凭证未配置完整。缺失: " + ", ".join(missing) +
        "。请在部署平台环境变量或 .streamlit/secrets.toml 中设置。"
    )

if access_passcode:
    if "authorized" not in st.session_state:
        st.session_state.authorized = False
    if not st.session_state.authorized:
        st.subheader("访问验证")
        entered_code = st.text_input("请输入同伴验证码", type="password")
        if st.button("验证并进入"):
            if entered_code.strip() == access_passcode:
                st.session_state.authorized = True
                st.rerun()
            else:
                st.error("验证码错误。")
        st.stop()

with st.form("insight_form"):
    st.subheader("研究参数")
    research_question = st.text_area(
        "研究问题",
        value="想研究家庭咖啡机用户在购买前最看重什么，以及最常见顾虑是什么？",
        height=100,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        subreddit = st.text_input("Subreddit", value="all")
        limit = st.number_input("总抓取数量", min_value=10, max_value=300, value=60, step=10)
    with col2:
        task_count = st.number_input("LLM 拆解任务数", min_value=1, max_value=8, value=4, step=1)
        sort = st.selectbox("排序", options=["new", "relevance", "hot", "top", "comments"], index=0)
        time_filter = st.selectbox(
            "时间范围",
            options=["year", "month", "week", "day", "hour", "all"],
            index=0,
        )
    with col3:
        model = st.text_input("Claude 模型", value=server_claude_model)
        output_dir = st.text_input("输出目录", value="reports")

    submitted = st.form_submit_button("开始分析", disabled=bool(missing))

if submitted:
    if not research_question.strip():
        st.error("研究问题不能为空。")
    else:
        try:
            with st.spinner("分析中，请稍候..."):
                outputs = run_pipeline(
                    research_question=research_question.strip(),
                    subreddit=subreddit.strip() or "all",
                    limit=int(limit),
                    task_count=int(task_count),
                    sort=sort,
                    time_filter=time_filter,
                    model=model.strip() or server_claude_model,
                    output_dir=output_dir.strip() or "reports",
                    reddit_client_id=server_reddit_client_id,
                    reddit_client_secret=server_reddit_client_secret,
                    reddit_user_agent=server_reddit_user_agent,
                    anthropic_api_key=server_claude_api_key,
                    anthropic_base_url=server_claude_base_url,
                )

            report_path = Path(outputs["report_path"])
            raw_path = Path(outputs["raw_labeled_path"])

            st.success(
                "报告已生成：\n"
                f"- 综合报告: {report_path}\n"
                f"- 原声+打标: {raw_path}"
            )

            report_text = report_path.read_text(encoding="utf-8")
            raw_text = raw_path.read_text(encoding="utf-8")

            st.download_button(
                label="下载综合分析报告",
                data=report_text,
                file_name=report_path.name,
                mime="text/markdown",
            )
            st.download_button(
                label="下载原声+打标明细",
                data=raw_text,
                file_name=raw_path.name,
                mime="text/markdown",
            )
            st.markdown("### 报告预览")
            st.markdown(report_text)
        except Exception as exc:  # noqa: BLE001
            st.error(f"执行失败：{exc}")
