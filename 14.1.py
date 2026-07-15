import requests
# 硅基流动 API 配置
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-tbpcgoxjnuewumfnqkjcmfvjbdyqgzyspcmlzocfotzabnqs" # 替换为你的真实 Key
# 读取学校资料（4 个 md 文件拼起来）
def load_school_data():
    files = ["01_新生入学.md", "02_办事流程.md", "03_电话黄页.md", "04_应急防骗.md"]
    data_dir = "data"
    content = ""
    for fname in files:
        path = f"{data_dir}/{fname}"
        try:
            with open(path, "r", encoding="utf-8") as f:
                content += f"\n\n=== {fname} ===\n" + f.read()
        except FileNotFoundError:
            print(f"⚠ 文件不存在：{path}")
    return content
# 根据身份选择 Prompt
def get_system_prompt(identity, school_data):
    # 别名词典（三套共用）
    alias_dict = """
【别名词典】
- "学校""航院""ZUA""郑航" = 郑州航空工业管理学院
- "新校区""龙湖""新校" = 龙子湖校区
- "卡""饭卡""校卡" = 校园一卡通
- "保安""门卫""校警" = 保卫处
- "迁户口""落户" = 户籍迁入/迁出
- "调宿舍""换宿舍" = 宿舍调整申请
- "证明""在读证明" = 在校学籍证明
"""
    # 防幻觉硬规则（三套共用）
    hard_rules = """
【防幻觉硬规则】
1. 只能根据【学校资料】回答，资料里没有的明说"这个我没收录，建议拨打 0371-61911000 总值班室问
一下"
2. 严禁编造电话号码、地址、办公时间、学费金额、人名
3. 涉及金钱/转账，无条件提示"先联系辅导员核实，任何要求转账的都是诈骗"
4. 涉及心理危机（自杀、不想活、活不下去等），立即给：12320-5 心理援助 + 学校心理咨询中心 + 告
诉辅导员
5. 不接入学校系统（教务/一卡通/财务），被问"查我的成绩/课表/卡余额"礼貌拒绝
6. 回答末尾标注 [来源:文件名]
"""
# 身份分流部分
    if identity == "新生":
        role = """你是"小航"，郑州航空工业管理学院的校园信息查询 AI 助手。
当前用户身份：大一新生。
你像一位热心的大二学长，语气详细、口语化、多给鼓励。
回答重点：把流程拆成具体步骤，涉及金钱/转账无条件提示防骗。"""
    elif identity == "在校生":
        role = """你是"小航"，郑州航空工业管理学院的校园信息查询 AI 助手。
当前用户身份：在校老生。
你像一位办事老司机学长，语气简洁。
回答重点：① 地点 ② 电话 ③ 所需材料 ④ 办结时间。"""
    elif identity == "教师":
         role = """你是"小航"，郑州航空工业管理学院的校园信息查询 AI 助手。
当前用户身份：教师。
语气专业礼貌。
代码讲解要点：
API_URL 是硅基流动的地址，不是智谱的。
model 用 Qwen/Qwen2.5-7B-Instruct ，不要写成 glm-4-flash 。
load_school_data() 把 4 个 md 文件拼成一段长文本，塞进 System Prompt。
get_system_prompt() 根据身份切换 Prompt，但防幻觉硬规则和别名词典三套都一样。
回答末尾要让 AI 自己标注 [来源:文件名]（硬规则第 6 条）。
回答重点：① 政策依据 ② 办事窗口 ③ 联系人。"""
    else:
        role = "你是小航校园助手。"
    return f"{role}\n{hard_rules}\n{alias_dict}\n【学校资料】\n{school_data}"
# 调用硅基流动 API
def ask_xiaohang(identity, question, school_data):
    system_prompt = get_system_prompt(identity, school_data)
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
}
    data = {
        "model": "meituan-longcat/LongCat-2.0",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
]
}
    response = requests.post(API_URL, headers=headers, json=data, timeout=30)
    result = response.json()
    answer = result["choices"][0]["message"]["content"]
    return answer
# 主程序
if __name__ == "__main__":
    school_data = load_school_data()
    print("=== 小航 · 校园信息查询 AI 助手 ===")
    print("请选择身份：1.新生 2.在校生 3.教师")
    choice = input("输入编号：")
    identity = {"1": "新生", "2": "在校生", "3": "教师"}.get(choice, "新生")
    question = input("你的问题：")
    answer = ask_xiaohang(identity, question, school_data)
    print(f"\n小航：{answer}")