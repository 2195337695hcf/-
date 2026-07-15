from openai import OpenAI

# ====================== 1. 全局配置 ======================
# 硅基流动API配置，请替换为你自己的密钥与地址
SILICON_API_BASE = "https://api.siliconflow.cn/v1"
SILICON_API_KEY = "sk-tbpcgoxjnuewumfnqkjcmfvjbdyqgzyspcmlzocfotzabnqs"
MODEL_NAME = "meituan-longcat/LongCat-2.0"

# MD知识库文件列表，对应data文件夹下4份文档
MD_FILES = [
    "01_新生入学.md",
    "02_办事流程.md",
    "03_电话黄页.md",
    "04_应急防骗.md"
]
DATA_DIR = "data"

# 每类用户4个推荐快捷问题（合计12个，匹配需求）
RECOMMEND_QUESTIONS = {
    "大一新生": [
        "学费什么时候交",
        "新生报到需要带什么材料",
        "宿舍热水供应时间",
        "军训请假流程是什么"
    ],
    "在校老生": [
        "怎么开在读证明",
        "奖学金申报截止时间",
        "图书馆开馆时间",
        "重修报名怎么操作"
    ],
    "教师": [
        "差旅怎么报销",
        "调课申请流程",
        "教室多媒体报修电话",
        "实验室使用审批材料"
    ]
}

# ====================== 2. 读取本地MD知识库函数 ======================
def load_all_knowledge() -> str:
    """读取data目录下全部4份MD知识库，拼接返回全文"""
    full_content = ""
    for filename in MD_FILES:
        file_path = f"{DATA_DIR}/{filename}"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                full_content += f"\n====== 资料来源：{filename} ======\n"
                full_content += f.read()
        except FileNotFoundError:
            print(f"警告：文件 {file_path} 不存在，已跳过")
    return full_content

def get_phone_book_static() -> str:
    """单独读取电话黄页，API挂掉时兜底静态展示"""
    phone_path = f"{DATA_DIR}/03_电话黄页.md"
    try:
        with open(phone_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "兜底咨询总机：0371-61911000"

# ====================== 3. 三套身份分流Prompt（严格满足任务要求） ======================
# 通用6条防幻觉硬规则（三套完全一致，一字未改）
BASE_RULES = """
【6条强制防幻觉硬规则，必须严格遵守】
1. 若知识库无对应资料，必须直白告知“当前未收录该信息”，同步提供咨询电话0371-61911000，不得编造时间、地点、流程。
2. 所有答复内容仅能从给定校园四份MD知识库提取，不得自行脑补政策、截止日期、办理材料。
3. 涉及缴费、证件代办、校外兼职、科研外包类问题，必须附加校园防骗提示，警惕第三方收费代办机构。
4. 识别到用户存在轻生、抑郁、自伤等负面情绪表述，立刻输出全国心理热线12320-5、本校心理咨询中心地址与对应帮扶渠道，优先安抚情绪再引导线下求助。
5. 任何情况下拒绝查询、调取、展示用户个人成绩、个人档案、隐私数据，礼貌回复无法处理该隐私需求，并指引线下对应职能部门办理。
6. 回答末尾必须标注信息对应的MD文件来源名称，无来源信息严格执行规则1，禁止模糊化推测。
"""

# 1）大一新生Prompt
PROMPT_FRESHMAN = f"""
你是服务郑州航院大一新生的校园AI助手「小航」，面向对校园完全不熟、容易信息焦虑、易受骗的新生；回答必须详细完整，缴费相关主动增加防骗提醒。
{BASE_RULES}
【别名词典】
{{
    "小航": "郑州航院校园AI助手",
    "迎新": "大一新生报到全流程",
    "学费/住宿费": "新生线上缴费业务",
    "军训": "新生入学军事训练安排",
    "公选课/通识课": "大一新生公共选修课",
    "校园卡": "新生一卡通，集成食堂、门禁、热水功能"
}}
应答要求：分步骤详细说明，主动增加反诈提示，结尾标注知识库来源文件名。
"""

# 2）在校老生Prompt
PROMPT_STUDENT = f"""
你是服务郑州航院在校老生的校园AI助手「小航」，面向追求办事效率、需要办理各类学籍业务的老生；回答简洁，优先给出地点、电话、材料、时间。
{BASE_RULES}
【别名词典】
{{
    "小航": "郑州航院校园AI助手",
    "在读证明": "在校生学籍证明办理业务",
    "奖学金/助学金": "学生奖助评审申报流程",
    "自习室/体育馆": "校园场馆线上预约系统",
    "重修/补考": "期末不及格课程补修考试业务",
    "四六级": "大学英语等级考试报名通道"
}}
应答要求：精简输出核心办事信息，结尾标注知识库来源文件名。
"""

# 3）教师Prompt
PROMPT_TEACHER = f"""
你是服务郑州航院教职工的校园AI助手「小航」，面向教学行政、科研场景；回答必须列明政策依据、办事窗口、对接联系人。
{BASE_RULES}
【别名词典】
{{
    "小航": "郑州航院校园AI助手",
    "差旅报销": "教职工公务出差费用核销流程",
    "调课/停课": "课程时间变更申请审批",
    "实验室审批": "教学实验室使用报备流程",
    "成绩录入": "教务系统学生成绩上传操作",
    "多媒体报修": "教室教学设备故障维修申报"
}}
应答要求：写明政策依据、窗口、对接人，结尾标注知识库来源文件名。
"""

# 身份-Prompt映射字典
PROMPT_MAP = {
    "大一新生": PROMPT_FRESHMAN,
    "在校老生": PROMPT_STUDENT,
    "教师": PROMPT_TEACHER
}

# ====================== 4. AI问答核心函数（调用硅基流动API） ======================
def chat_with_xiaohang(user_identity: str, user_question: str, knowledge_text: str):
    """
    :param user_identity: 用户身份，可选 "大一新生"/"在校老生"/"教师"
    :param user_question: 用户输入提问
    :param knowledge_text: 预加载的全部MD知识库文本
    :return: AI返回回答文本
    """
    client = OpenAI(
        base_url=SILICON_API_BASE,
        api_key=SILICON_API_KEY
    )
    # 拼接系统提示词 + 知识库参考资料
    system_content = PROMPT_MAP[user_identity] + f"\n【参考知识库全文】{knowledge_text}"
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_question}
            ],
            temperature=0.0
        )
        return resp.choices[0].message.content
    except Exception as e:
        # API故障兜底：直接返回电话黄页静态内容
        err_msg = f"AI服务暂时不可用（故障：{str(e)}），以下是电话黄页兜底信息：\n"
        err_msg += get_phone_book_static()
        return err_msg

# ====================== 5. 交互测试入口（可直接运行测试全部用例） ======================
if __name__ == "__main__":
    # 1. 预加载全部知识库
    print("正在加载校园知识库...")
    all_know = load_all_knowledge()
    print("知识库加载完成！\n")

    # 测试用例集合（覆盖任务要求全部必跑测试）
    test_cases = [
        ("大一新生", "学费什么时候交"),
        ("在校老生", "怎么开在读证明"),
        ("教师", "差旅怎么报销"),
        ("在校老生", "查我的成绩"),
        ("大一新生", "我不想活了"),
        ("教师", "食堂几点开门")
    ]

    # 批量执行测试
    for identity, question in test_cases:
        print("=" * 60)
        print(f"【用户身份】{identity} | 【提问】{question}")
        answer = chat_with_xiaohang(identity, question, all_know)
        print(f"\n【小航回答】\n{answer}\n")

    # 打印推荐快捷问题（对应P0功能3）
    print("=" * 60)
    print("推荐快捷问题列表（界面按钮可用）：")
    for user_type, q_list in RECOMMEND_QUESTIONS.items():
        print(f"\n{user_type}快捷提问：")
        for q in q_list:
            print(f" - {q}")