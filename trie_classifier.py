import json

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.category = None

class TrieClassifier:
    def __init__(self, keywords_file):
        self.root = TrieNode()
        # 加载关键词数据
        with open(keywords_file, 'r', encoding='utf-8') as f:
            keywords_dict = json.load(f)
        
        # 构建前缀树
        for category, keywords in keywords_dict.items():
            for keyword in keywords:
                self.insert(keyword.lower(), category)  # 转换为小写
    
    def insert(self, keyword, category):
        """将关键词插入前缀树"""
        node = self.root
        for char in keyword:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
        node.category = category
    
    def search(self, text):
        """在文本中搜索所有匹配的关键词及其类别"""
        text = text.lower()  # 转换为小写
        matches = set()  # 使用集合避免重复
        matched_keywords = {}  # 记录每个类别匹配到的关键词
        
        # 从每个字符开始尝试匹配
        for i in range(len(text)):
            node = self.root
            j = i
            current_word = ""
            while j < len(text) and text[j] in node.children:
                current_word += text[j]
                node = node.children[text[j]]
                if node.is_end:
                    if node.category not in matched_keywords:
                        matched_keywords[node.category] = set()
                    matched_keywords[node.category].add(current_word)
                    matches.add(node.category)
                j += 1
        
        # 如果匹配的类别超过两个，进行筛选
        if len(matches) > 2:
            # 1. 按照匹配关键词数量排序
            category_stats = []
            for category in matches:
                keywords = matched_keywords[category]
                total_length = sum(len(keyword) for keyword in keywords)
                category_stats.append((category, len(keywords), total_length))
            
            # 首先按关键词数量降序排序，如果数量相同则按总长度降序排序
            category_stats.sort(key=lambda x: (-x[1], -x[2]))
            
            # 只保留前两个类别
            matches = {stat[0] for stat in category_stats[:2]}
            # 更新matched_keywords，只保留最终匹配的类别
            matched_keywords = {k: v for k, v in matched_keywords.items() if k in matches}
        
        categories = list(matches) if matches else ["未知"]
        return categories, matched_keywords

def test_classifier():
    """测试分类器"""
    classifier = TrieClassifier('keywords.json')
    
    # 测试问题
    test_questions = [
        "3．List remove第一个元素之后后面的元素会移动吗？",
        "List",
        "Redis持久化机制",
        "使用Redis实现分布式锁",
        "Spring中如何使用Redis实现缓存？",  # 这个问题可能会匹配到多个类别
        "分布式系统中Redis的应用场景"  # 这个问题也可能匹配到多个类别
    ]
    
    # 对每个问题进行预测
    for question in test_questions:
        print(f"\n问题: {question}")
        categories, matched_keywords = classifier.search(question)
        print("匹配详情:")
        for category, keywords in matched_keywords.items():
            print(f"{category}: 匹配到的关键词 {keywords}")
            print(f"  - 匹配数量: {len(keywords)}")
            print(f"  - 关键词总长度: {sum(len(keyword) for keyword in keywords)}")
        print("最终匹配的类别:", categories)

if __name__ == "__main__":
    test_classifier()
