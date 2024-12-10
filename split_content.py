import re

def split_interview_content(content):
    """
    将面经内容分割成句子
    使用多种分隔符和规则来分割文本：
    1. 常见的句子结束符号（。！？）
    2. 数字序号（1. 1、等）
    3. 特定关键词
    :param content: 原始面经内容
    :return: 分割后的句子列表
    """
    if not content or not isinstance(content, str):
        return []
    
    # 预处理：统一换行符和空格
    content = content.replace('\n', ' ').replace('\r', ' ')
    content = re.sub(r'\s+', ' ', content).strip()
    
    # 分割规则
    # 1. 保留分隔符的分割，用于后续判断是否为真正的句子结束
    splits = re.split(r'([。！？\n])', content)
    
    # 2. 合并分隔符与前面的内容
    sentences = []
    temp = ''
    for i in range(0, len(splits)-1, 2):
        if i+1 < len(splits):
            temp = splits[i] + splits[i+1]
        else:
            temp = splits[i]
        if temp.strip():
            sentences.append(temp.strip())
    # 处理最后一个片段
    if len(splits) % 2 == 1 and splits[-1].strip():
        sentences.append(splits[-1].strip())
    
    # 3. 对每个句子进行进一步分割
    final_sentences = []
    for sentence in sentences:
        # 按数字序号分割
        number_splits = re.split(r'(?<=\s)(?=\d+[\.、])', sentence)
        for split in number_splits:
            split = split.strip()
            if not split:
                continue
                
            # 按特定关键词分割（面试、问、答等）
            keyword_splits = re.split(r'(?<=[。！？])\s*(?=(?:面试|问|答|接下来|然后|首先|最后))', split)
            final_sentences.extend([s.strip() for s in keyword_splits if s.strip()])
    
    # 4. 清理和合并过短的句子
    cleaned_sentences = []
    temp_sentence = ''
    
    for sentence in final_sentences:
        # 如果句子太短，可能是误分割，与下一句合并
        if len(sentence) < 5 and cleaned_sentences:
            cleaned_sentences[-1] = cleaned_sentences[-1] + sentence
        else:
            cleaned_sentences.append(sentence)
    
    return cleaned_sentences

def format_interview_content(content):
    """
    格式化面经内容，使其更易读
    :param content: 原始面经内容
    :return: 格式化后的内容字符串
    """
    sentences = split_interview_content(content)
    return '\n'.join(f"{i+1}. {sentence}" for i, sentence in enumerate(sentences))

# 测试代码
if __name__ == "__main__":
    test_cases = [
        # 测试用例1：有明确数字序号的内容
        """11月19投递java后端开发日常一面：当天投当天面，只有一面，第二天就出结果1.自我介绍2.List、set、map区别3.普通类和抽象类的区别4.线程和进程的区别5.线程有几种状态全程20分钟11月19oc，拒""",
        
        # 测试用例2：纯文本描述
        """面试官很和善，先是自我介绍，然后问了项目经历。接下来问了一些基础知识，包括Java集合类。最后问了有什么想问他的。整个过程很顺利，面试官说等通知。""",
        
        # 测试用例3：混合格式
        """一面：先自我介绍。然后问八股文：1、JVM内存区域2、垃圾回收器3、HashMap底层。问项目：项目难点。问算法：反转链表。面试官很好，一直引导。""",
    ]
    
    print("=== 测试结果 ===")
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print("-" * 50)
        print("原文：")
        print(test_case)
        print("\n分割后：")
        print(format_interview_content(test_case))
        print("-" * 50)
