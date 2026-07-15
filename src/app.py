import requests
import streamlit as st
from pathlib import Path
# 导入自定义Prompt工具
from src.prompts import load_school_info, get_system_prompt

# ===================== 配置区（自行修改硅基流动密钥）=====================
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-tbpcgoxjnuewumfnqkjcmfvjbdyqgzyspcmlzocfotzabnqs"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
# ======================================================================

# 页面标题
st.title("小航 · 郑州航院校园信息助手")
st.caption("基于硅基流动大模型，仅解答郑航校内相关问题")

# 1. 身份选择下拉框
role = st.selectbox("请选择你的身份：", ["新生", "在校生", "教师"])

# 2. 推荐快捷提问按钮（静态推荐问题）
st.subheader("快速提问推荐")
col1, col2, col3 = st.columns(3)
with col1:
    btn1 = st.button("新生报到流程")
with col2:
    btn2 = st.button("奖学金申请条件")
with col3:
    btn3 = st.button("教务处办公电话")

# 3. 文本输入框
question = st.text_input("有啥想问的？输入校园相关问题：")

# 绑定按钮快捷提问到输入框
if btn1:
    question = "新生报到流程"
if btn2:
    question = "奖学金申请条件"
if btn3:
    question = "教务处办公电话"

# 4. 加载校园知识库
school_data = load_school_info()
# 校验data文件夹是否存在md文件
if not school_data.strip():
    st.warning("⚠️ 数据文件缺失，请补齐 data/ 目录下的 md 校园资料文件！")
else:
    # 有问题才调用API
    if question and question.strip():
        with st.spinner("小航正在查询校园资料，请稍等..."):
            # 生成系统prompt
            sys_prompt = get_system_prompt(role, school_data)
            # 组装请求体
            payload = {
                "model": "Qwen/Qwen2.5-7B-Instruct",
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": question}
            ],
            "temperature": 0.1  # 低温度减少幻觉，更严谨
        }
        # 发起API请求
        resp = requests.post(API_URL, json=payload, headers=HEADERS)
        if resp.status_code == 200:
            ai_answer = resp.json()["choices"][0]["message"]["content"]
            st.success("小航回答：")
            st.write(ai_answer)
        else:
            st.error(f"API调用失败，错误码：{resp.status_code}，请检查API_KEY是否正确")

# 底部静态电话黄页
st.divider()
st.subheader("郑航常用办公电话（静态黄页）")
phone_info = """
- 教务处：0371-xxxxxxx
- 学生处/资助中心：0371-xxxxxxx
- 招生办公室：0371-xxxxxxx
- 后勤宿舍管理：0371-xxxxxxx
"""
st.text(phone_info)