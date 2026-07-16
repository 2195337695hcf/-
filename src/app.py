# -*- coding: utf-8 -*-
"""
郑州航院校园AI助手「小航」方案二最终版
核心逻辑：
1.AI正常查询 → 仅展示回答，底部黄页折叠隐藏
2.AI接口报错失效 → 在报错区域直接展示完整电话黄页兜底
"""
import requests
import streamlit as st
from pathlib import Path
from datetime import datetime

# =====================【务必修改】硅基接口配置=====================
API_KEY = "sk-tbpcgoxjnuewumfnqkjcmfvjbdyqgzyspcmlzocfotzabnqs"
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
TEMPERATURE = 0.3
# =================================================================

# 角色提示词
ROLE_PROMPTS = {
    "新生": "你像热心的大二学长，语气详细、口语化、多给鼓励。涉及金钱/转账无条件提示「先联系辅导员核实」",
    "在校生": "你像办事老司机学长，语气简洁。优先给：① 地点 ② 电话 ③ 所需材料 ④ 办结时间",
    "教师": "你面向教师，语气专业礼貌。优先给：① 政策依据 ② 办事窗口 ③ 联系人",
}

# 校园同义词库
ALIAS_DICT = """
【同义词表】
- "学校" "航院" "ZUA" "郑航" ≈ 郑州航空工业管理学院
- "新校区" "龙湖" "新校" ≈ 龙子湖校区
- "卡" "饭卡" "校卡" ≈ 校园一卡通
- "保安" "门卫" "校警" ≈ 保卫处
- "迁户口" "落户" ≈ 户籍迁入/迁出
- "调宿舍" "换宿舍" ≈ 宿舍调整申请
- "证明" "在读证明" ≈ 在校学籍证明
"""

# 身份对应快捷提问
PRESET_QUESTIONS = {
    "新生": [
        "报到那天先去哪？",
        "学费什么时候交？",
        "宿舍是 4 人间还是 6 人间？",
        "有人冒充辅导员要钱怎么办？",
    ],
    "在校生": [
        "怎么开在读证明？",
        "校园卡丢了怎么补？",
        "转专业怎么转？",
        "图书馆几点关？",
    ],
    "教师": [
        "差旅怎么报销？",
        "调课怎么申请？",
        "教室设备坏了找谁？",
        "科研项目去哪申报？",
    ],
}

# 完整离线电话黄页
YELLOW_PAGE = """
| 部门 | 电话 |
|------|------|
| 校园110（保卫处24h） | 0371-61916110 △ 以官方为准 |
| 学校总值班室 | 0371-61911000 △ 以官方为准 |
| 后勤管理处 | 0371-61912800 △ 以官方为准 |
| 后勤服务热线/物业报修 | 0371-61913110 △ 以官方为准 |
| 校医院急诊（24h） | 0371-61912730 △ 以官方为准 |
| 招生办公室 | 0371-61916161 △ 以官方为准 |
| 信息管理中心（网信中心） | 0371-61912718 △ 以官方为准 |
"""

# 读取data文件夹知识库
def load_school_info():
    data_dir = Path("data")
    if not data_dir.exists():
        return "暂无校园知识库，请在项目根目录创建data文件夹并放入md文档"
    md_files = sorted(data_dir.glob("*.md"))
    if not md_files:
        return "data文件夹内暂无知识库文件"
    content_list = []
    for file in md_files:
        text = file.read_text(encoding="utf-8")
        content_list.append(f"==== 知识库：{file.name} ====\n{text}")
    return "\n\n".join(content_list)

# 组装系统提示词
def get_system_prompt(role, info):
    return f"""你是郑州航院校园信息助手「小航」。
{ROLE_PROMPTS[role]}
{ALIAS_DICT}

【硬规则】
1. 只能依据【学校资料】回答，无相关内容统一回复：我没收录，建议拨打总值班室0371-61911000。
2. 严禁编造电话、地址、费用、人名、办公时间。
3. 涉及转账缴费必须提示：先联系辅导员核实，转账类均为诈骗。
4. 心理危机问题，提供12320-5心理援助并建议告知辅导员。
5. 拒绝查询教务、一卡通、财务的个人隐私数据。
6. 回答末尾标注 [来源:文件名]

【学校资料】
{info}
"""

# =====================页面布局=====================
st.set_page_config(page_title="小航·郑航校园助手", layout="wide")
st.title("小航 · 郑州航院校园信息助手")

# 身份选择
role = st.selectbox("你的身份", ["新生", "在校生", "教师"])

# 会话缓存，快捷按钮回填输入框
if "question" not in st.session_state:
    st.session_state["question"] = ""
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
user_question = st.text_input("有什么校园问题想问我？", value=st.session_state["question"])

# 快捷提问按钮区
st.markdown("#### 💡 快捷提问（一键点击）")
cols = st.columns(4)
q_list = PRESET_QUESTIONS[role]
for idx, q in enumerate(q_list):
    with cols[idx % 4]:
        if st.button(q, key=f"q_{role}_{idx}"):
            st.session_state["question"] = q
            st.rerun()

# =====================AI核心逻辑（方案二关键）=====================
if user_question.strip():
    school_data = load_school_info()
    sys_prompt = get_system_prompt(role, school_data)
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_NAME,
        "temperature": TEMPERATURE,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_question}
        ]
    }
    with st.spinner("小航正在查阅校园资料..."):
        try:
            payload["stream"] = True
            with requests.post(API_URL, json=payload, headers=headers, timeout=60, stream=True) as res:
                res.raise_for_status()
                answer_placeholder = st.empty()
                st.markdown("### 📌 小航回答")
                full_answer = ""
                for line in res.iter_lines():
                    if line:
                        try:
                            data = line.decode("utf-8").strip()
                            if data.startswith("data: "):
                                data = data[6:]
                            if data == "[DONE]":
                                break
                            chunk = json.loads(data)
                            delta = chunk["choices"][0].get("delta")
                            content = delta.get("content", "") if delta else ""
                            full_answer += content
                            answer_placeholder.markdown(full_answer)
                        except json.JSONDecodeError:
                            continue
                
                st.success("✅ 查询完成")
                
                # 保存到历史记录
                history = st.session_state["chat_history"]
                if not history or history[-1]["question"] != user_question:
                    history.append({
                        "role": role,
                        "question": user_question,
                        "answer": full_answer,
                        "response_time": f"{res.elapsed.total_seconds():.2f}s",
                        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
        except requests.exceptions.Timeout:
            st.error("❌ 请求超时，请检查网络或稍后重试")
            st.subheader("📞 校园官方电话黄页（离线可用）")
            st.markdown(YELLOW_PAGE)
        except requests.exceptions.ConnectionError:
            st.error("❌ 网络连接失败，请检查网络设置")
            st.subheader("📞 校园官方电话黄页（离线可用）")
            st.markdown(YELLOW_PAGE)
        except Exception as e:
            st.error(f"❌ AI接口请求失败: {str(e)[:100]}")
            st.subheader("📞 校园官方电话黄页（离线可用）")
            st.markdown(YELLOW_PAGE)
            st.info("AI暂时无法查询，你可以拨打上方官方电话咨询校内事务")

# 问答历史记录
if st.session_state["chat_history"]:
    st.divider()
    with st.expander(f"📜 问答历史（共 {len(st.session_state['chat_history'])} 条）", expanded=False):
        for idx, item in enumerate(reversed(st.session_state["chat_history"]), 1):
            record_idx = len(st.session_state["chat_history"]) - idx
            st.markdown(f"---")
            col1, col2 = st.columns([10, 1])
            with col1:
                st.markdown(f"**【{item['role']}】** · {item['datetime']}")
            with col2:
                if st.button("🗑️", key=f"del_{record_idx}"):
                    st.session_state["chat_history"].pop(record_idx)
                    st.rerun()
            
            with st.chat_message("user"):
                st.markdown(item["question"])
            
            with st.chat_message("assistant"):
                st.markdown(item["answer"])
                st.caption(f"响应耗时: {item['response_time']}")
        
        if st.button("🗑️ 清空全部历史记录", key="btn_clear_history"):
            st.session_state["chat_history"] = []
            st.rerun()

# 页面底部：折叠式备用黄页，AI正常时不占用版面
st.divider()
with st.expander("📎 备用：校园电话黄页（点击展开）"):
    st.header("校园电话黄页（离线兜底）")
    st.caption("AI查询异常、信息无收录时可使用")
    st.markdown(YELLOW_PAGE)