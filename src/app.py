
# -*- coding: utf-8 -*-
"""
郑州航院 校园AI助手「小航」
单文件完整版：整合界面、API、Prompt、知识库读取、快捷按钮、电话黄页
无需 prompts.py 依赖，开箱即用
"""
import requests
import streamlit as st
from pathlib import Path

# ====================== 配置区（请自行修改）======================
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-tbpcgoxjnuewumfnqkjcmfvjbdyqgzyspcmlzocfotzabnqs"  # 替换为自己的密钥
MODEL_NAME = "Pro/zai-org/GLM-5.1"
TEMPERATURE = 0.3
# =================================================================

# ---------------------- 角色提示词配置 ----------------------
ROLE_PROMPTS = {
    "新生": "你像热心的大二学长，语气详细、口语化、多给鼓励。涉及金钱/转账无条件提示「先联系辅导员核实」",
    "在校生": "你像办事老司机学长，语气简洁。优先给：① 地点 ② 电话 ③ 所需材料 ④ 办结时间",
    "教师": "你面向教师，语气专业礼貌。优先给：① 政策依据 ② 办事窗口 ③ 联系人",
}

# ---------------------- 校园同义词别名库 ----------------------
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

# ---------------------- 快捷问题按钮库 ----------------------
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

# ---------------------- 静态兜底电话黄页 ----------------------
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

# ---------------------- 黄页弹窗函数 ----------------------
@st.dialog("📞 校园电话黄页（离线兜底）")
def show_yellow_page():
    st.caption("AI查询异常、无收录时，可直接拨打官方电话咨询")
    st.markdown(YELLOW_PAGE)

# ---------------------- 工具函数：读取知识库 ----------------------
def load_school_info():
    """读取根目录 data 文件夹下所有 md 知识库"""
    data_dir = Path("data")
    if not data_dir.exists():
        return "暂无校园知识库，请在项目根目录创建 data 文件夹并放入 md 文件"
    file_list = sorted(data_dir.glob("*.md"))
    if not file_list:
        return "data 文件夹内暂无知识库文件"
    content_list = []
    for file in file_list:
        file_text = file.read_text(encoding="utf-8")
        content_list.append(f"==== 知识库文件：{file.name} ====\n{file_text}")
    return "\n\n".join(content_list)

# ---------------------- 工具函数：组装系统提示词 ----------------------
def get_system_prompt(role, info):
    full_prompt = f"""你是郑州航院校园信息助手「小航」。
{ROLE_PROMPTS[role]}
{ALIAS_DICT}

【硬规则】
1. 只能根据下面【学校资料】回答，没有的明说"我没收录，建议拨打 0371-61911000 总值班室"
2. 严禁编造电话号码、地址、办公时间、学费金额、人名
3. 涉及金钱/转账无条件提示"先联系辅导员核实，任何要求转账的都是诈骗"
4. 涉及心理危机(自杀、不想活等)，立即给：12320-5 心理援助 + 学校心理咨询中心 + 告诉辅导员
5. 不接入学校系统(教务/一卡通/财务)，被问"查我的 xx"礼貌拒绝
6. 回答末尾标注 [来源:文件名]

【学校资料】
{info}
"""
    return full_prompt

# ====================== 页面主体逻辑 ======================
st.set_page_config(page_title="小航 - 郑航校园助手", layout="wide")
st.title("小航 · 郑州航院校园信息助手")

# 身份选择
role = st.selectbox("你的身份", ["新生", "在校生", "教师"])

# 初始化会话状态
if "question" not in st.session_state:
    st.session_state["question"] = ""
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# 输入框
user_question = st.text_input("有什么校园问题想问我？", value=st.session_state["question"])

# 快捷提问按钮
st.markdown("#### 💡 快捷提问（一键点击）")
cols = st.columns(4)
q_list = PRESET_QUESTIONS[role]
for idx, q in enumerate(q_list):
    with cols[idx % 4]:
        if st.button(q, key=f"preset_{role}_{idx}"):
            st.session_state["question"] = q
            st.rerun()

# AI问答逻辑
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

    with st.spinner("小航正在查阅校园资料，请稍候..."):
        try:
            res = requests.post(API_URL, json=payload, headers=headers, timeout=30)
            res_json = res.json()
            answer = res_json["choices"][0]["message"]["content"]
            st.success("回答完成！")
            st.markdown("### 📌 小航回答：")
            st.markdown(answer)
            
            history = st.session_state["chat_history"]
            if not history or history[-1]["question"] != user_question:
                history.append({
                    "role": role,
                    "question": user_question,
                    "answer": answer,
                    "timestamp": f"{res.elapsed.total_seconds():.2f}s"
                })
        except Exception as e:
            st.error(f"AI接口请求失败：{str(e)}")
            show_yellow_page()

# 问答历史记录
if st.session_state["chat_history"]:
    st.divider()
    with st.expander(f"📜 问答历史（共 {len(st.session_state['chat_history'])} 条）", expanded=False):
        for idx, item in enumerate(reversed(st.session_state["chat_history"]), 1):
            with st.expander(f"Q{len(st.session_state['chat_history']) - idx + 1}: {item['question'][:30]}...", expanded=False):
                st.markdown(f"**身份**: {item['role']}")
                st.markdown(f"**问题**: {item['question']}")
                st.markdown(f"**回答**: {item['answer']}")
                st.caption(f"响应耗时: {item['timestamp']}")
        
        if st.button("🗑️ 清空历史记录"):
            st.session_state["chat_history"] = []
            st.rerun()

# 手动查看黄页按钮
st.divider()
if st.button("📞 查看校园电话黄页"):
    show_yellow_page()
    