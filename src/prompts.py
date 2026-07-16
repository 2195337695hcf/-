from pathlib import Path


def load_school_info() -> str:
    data_dir = Path("data")
    if not data_dir.exists():
        return ""
    
    school_info = []
    for md_file in sorted(data_dir.glob("*.md")):
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
                school_info.append(f"## {md_file.stem}\n\n{content}")
        except Exception:
            pass
    
    return "\n\n".join(school_info)


def get_system_prompt(role: str, school_data: str) -> str:
    role_prompts = {
        "新生": "你是一位热心的郑州航院新生辅导员，专门解答新生入学相关问题，如报到流程、宿舍安排、军训注意事项等。",
        "在校生": "你是一位郑州航院在校生学长/学姐，熟悉校园生活，能解答选课、奖学金、日常学习生活等问题。",
        "教师": "你是郑州航院的一位教职工，熟悉学校各项政策和办公流程，能解答教学管理、科研相关等问题。"
    }
    
    role_desc = role_prompts.get(role, "你是郑州航院校园信息助手。")
    
    return f"""
你是小航，郑州航院校园信息助手。

{role_desc}

以下是郑州航院的校园知识库，请根据这些信息回答用户问题：

{school_data}

规则：
1. 只回答与郑州航院相关的问题，非校园问题请礼貌拒绝。
2. 优先使用知识库中的信息进行回答。
3. 如果知识库中没有相关信息，请明确说明。
4. 回答要简洁明了，重点突出。
"""
