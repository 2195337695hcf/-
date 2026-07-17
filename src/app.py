import requests
import streamlit as st
import time
from pathlib import Path
from prompts import load_school_info, get_system_prompt

# 硅基流动API配置
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-tbpcgoxjnuewumfnqkjcmfvjbdyqgzyspcmlzocfotzabnqs"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# 本地输入替换别名词典
INPUT_ALIAS = {
    "ZUA": "郑州航空工业管理学院",
    "郑航": "郑州航空工业管理学院",
    "航院": "郑州航空工业管理学院"
}

# ========== 会话状态初始化（多轮对话messages） ==========
if "user_q" not in st.session_state:
    st.session_state.user_q = ""
# 全局提问历史
if "question_history" not in st.session_state:
    st.session_state.question_history = []
# 多轮上下文对话存储
if "messages" not in st.session_state:
    st.session_state["messages"] = []
# 问答历史记录（包含时间、身份、问题）
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# 全局仅加载一次知识库
kb_data = load_school_info()
md_files = list(Path("data").glob("*.md"))

# 页面标题
st.title("小航 · 郑州航院校园信息助手")

# 身份下拉选择
user_role = st.selectbox("你的身份：", ["新生", "在校生", "教师"])

# 【功能5 4分类标签页】
st.markdown("### 快捷提问（点击自动填充并查询AI）")
tab1, tab2, tab3, tab4 = st.tabs(["新生指南", "办事流程", "应急防骗", "交通出行"])

# 标签1：新生指南
with tab1:
    new_qs = ["报到流程是什么？","学费怎么缴纳？","宿舍规格几人间？","军训需要准备什么？"]
    cols = st.columns(2)
    for idx, q in enumerate(new_qs):
        with cols[idx % 2]:
            if st.button(q, key=f"tab_new_{idx}"):
                st.session_state.user_q = q
                st.rerun()

# 标签2：办事流程
with tab2:
    process_qs = ["在读证明怎么开？","校园卡丢失补办流程？","转专业申请渠道？","图书馆开放时间？","差旅报销流程？","调课申请怎么提交？"]
    cols = st.columns(2)
    for idx, q in enumerate(process_qs):
        with cols[idx % 2]:
            if st.button(q, key=f"tab_proc_{idx}"):
                st.session_state.user_q = q
                st.rerun()

# 标签3：应急防骗
with tab3:
    safe_qs = ["冒充辅导员转账怎么防？","教室设备故障报修？","科研项目申报入口？","校外兼职骗局如何识别？"]
    cols = st.columns(2)
    for idx, q in enumerate(safe_qs):
        with cols[idx % 2]:
            if st.button(q, key=f"tab_safe_{idx}"):
                st.session_state.user_q = q
                st.rerun()

# 标签4：交通出行（6个快捷键）
with tab4:
    traffic_qs = [
        "怎么坐地铁去学校？",
        "到郑航可以坐哪几路公交？",
        "郑州东站怎么到龙子湖校区？",
        "新生报到有迎新大巴吗？",
        "自驾入校停车怎么收费？",
        "学校有没有校内通勤校车？"
    ]
    cols = st.columns(2)
    for idx, q in enumerate(traffic_qs):
        with cols[idx % 2]:
            if st.button(q, key=f"tab_traffic_{idx}"):
                st.session_state.user_q = q
                st.rerun()

# 问题输入框
user_input = st.text_input("输入你的问题：", value=st.session_state.user_q)

# 快捷按钮回填逻辑
if st.session_state.user_q and st.session_state.user_q.strip() != "":
    user_input = st.session_state.user_q
    st.session_state.user_q = ""

# 双列布局：新对话按钮 + 导出对话按钮
col_btn1, col_btn2 = st.columns([1, 1])
with col_btn1:
    if st.button("🆕 开启新对话（清空上下文记忆）"):
        st.session_state["messages"] = []
        st.rerun()
with col_btn2:
    # 挑战2：导出对话txt文件
    export_text = ""
    if st.session_state["messages"]:
        export_text += "===== 郑州航院小航对话记录 =====\n\n"
        # 遍历上下文对话列表，拼接文本
        for msg in st.session_state["messages"]:
            if msg["role"] == "user":
                export_text += f"【用户提问】{msg['content']}\n"
            elif msg["role"] == "assistant":
                export_text += f"【AI回答】{msg['content']}\n"
                export_text += "----------------------------------------\n\n"
    # 生成带日期的文件名
    file_name = f"小航对话记录_{time.strftime('%Y%m%d')}.txt"
    st.download_button(
        label="📥 导出对话记录",
        data=export_text,
        file_name=file_name,
        mime="text/plain"
    )

# 别名替换预处理
def replace_alias(text):
    for k, v in INPUT_ALIAS.items():
        text = text.replace(k, v)
    return text
process_text = replace_alias(user_input.strip())

# 知识库缺失校验
if not md_files:
    st.warning("⚠️ data目录知识库md文件缺失，请补齐文档（包含05_交通出行.md）")
else:
    if process_text == "":
        st.info("💡 请输入你的问题或点击上方快捷提问按钮")

    # 提问历史区域（标题右侧清空按钮）
    st.divider()
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader("📜 提问历史")
    with col2:
        if st.button("清空全部历史记录"):
            st.session_state["chat_history"] = []
            st.rerun()

    if len(st.session_state["chat_history"]) == 0:
        st.info("暂无提问记录，输入问题开始查询吧")
    else:
        for idx, record in enumerate(reversed(st.session_state["chat_history"])):
            with st.expander(f"🔹 [{record['time']}] {record['question'][:25]}{'...' if len(record['question']) > 25 else ''}", expanded=False):
                st.write(f"**身份**: {record['role']}")
                st.write(f"**问题**: {record['question']}")
                st.write(f"**回答**: {record['answer']}")
                if st.button("重新提问", key=f"reask_{idx}"):
                    st.session_state.user_q = record['question']
                    st.rerun()
    st.divider()

    # 历史记录区域（仅显示时间、身份、问题）
    st.subheader("📝 历史记录")
    if len(st.session_state["chat_history"]) == 0:
        st.info("暂无历史记录")
    else:
        for idx, record in enumerate(reversed(st.session_state["chat_history"])):
            st.write(f"**时间**: {record['time']} | **身份**: {record['role']} | **问题**: {record['question']}")
    st.divider()

    if process_text:
        # 超长文本提醒
        if len(process_text) > 600:
            st.warning("⚠️ 问题文本过长，建议拆分为2段提问，减少超时概率；当前仍可提交尝试")

        # 存入全局提问历史
        if process_text not in st.session_state.question_history:
            st.session_state.question_history.append(process_text)

        # 构造多轮对话完整messages（系统词 + 历史对话 + 当前提问）
        system_prompt = get_system_prompt(user_role, kb_data)
        full_messages = [{"role": "system", "content": system_prompt}] + st.session_state["messages"]
        full_messages.append({"role": "user", "content": process_text})

        request_body = {
            "model": "deepseek-ai/DeepSeek-V3.2",
            "max_tokens": 600,
            "temperature": 0.01,
            "messages": full_messages
        }

        with st.spinner("🤖 小航正在思考中..."):
            max_retry = 2
            retry_count = 0
            success_flag = False
            res = None
            ans = ""
            skip_render = False
            start = time.time()

            # 超时重试循环
            while retry_count <= max_retry and not success_flag:
                try:
                    res = requests.post(API_URL, headers=HEADERS, json=request_body, timeout=90)
                    success_flag = True
                except requests.exceptions.Timeout:
                    retry_count += 1
                    if retry_count <= max_retry:
                        st.warning(f"请求超时，正在第{retry_count}次重试...")
                    else:
                        st.error("❌ 多次请求超时，网络延迟过高，请拆分简短问题或切换手机热点重试")
                        skip_render = True
                        break
                except requests.exceptions.ConnectionError:
                    st.error("❌ 网络连接失败，无法访问AI接口")
                    skip_render = True
                    break

            if skip_render:
                pass
            else:
                # HTTP状态校验
                if res.status_code == 401:
                    st.error("❌ API Key鉴权失败，请重新填写硅基流动密钥")
                elif res.status_code >= 500:
                    st.error("❌ AI服务器故障，请稍后重试")
                elif res.status_code == 403:
                    st.error("❌ 当前账号无接口访问权限")
                elif res.status_code == 404:
                    st.error("❌ API接口地址错误，请核对链接")
                elif res.status_code != 200:
                    st.error(f"❌ 接口异常，状态码：{res.status_code}")
                else:
                    try:
                        json_data = res.json()
                    except requests.exceptions.JSONDecodeError:
                        st.error("❌ 接口返回文本解析失败")
                    else:
                        if "choices" not in json_data or len(json_data["choices"]) == 0:
                            st.error("❌ AI未生成有效回答，请缩短问题长度重试")
                        else:
                            ans = json_data["choices"][0]["message"].get("content", "").strip()
                            end = time.time()
                            cost_time = end - start
                            if not ans:
                                st.error("❌ AI返回回答为空，请拆分长提问重新发送")
                            else:
                                # 输出回答
                                st.subheader("🤖小航回答：")
                                st.write(ans)
                                # 功能6：字数耗时小字展示
                                st.caption(f"回答字数：{len(ans)} 字 · 耗时：{cost_time:.1f} 秒")
                                # 保存本轮问答到上下文，实现多轮记忆
                                st.session_state["messages"].append({"role": "user", "content": process_text})
                                st.session_state["messages"].append({"role": "assistant", "content": ans})
                                # 保存到问答历史记录（时间、身份、问题、答案）
                                st.session_state["chat_history"].append({
                                    "time": time.strftime("%H:%M:%S"),
                                    "role": user_role,
                                    "question": process_text,
                                    "answer": ans
                                })

# 离线电话黄页
st.divider()
st.header("📞 校园电话黄页（离线兜底，无需联网）")
st.caption("AI接口故障时，可直接查看官方联系电话")
yellow_page_text = """
| 部门 | 24h/办公电话 |
|------|------|
| 校园保卫处110 | 0371-61916110 |
| 学校总值班室 | 0371-61911000 |
| 后勤物业报修 | 0371-61913110 |
| 校医院急诊 | 0371-61912730 |
| 招生办公室 | 0371-61916161 |
| 网信中心 | 0371-61912718 |
"""
st.markdown(yellow_page_text)