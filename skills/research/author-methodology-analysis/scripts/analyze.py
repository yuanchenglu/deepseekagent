#!/usr/bin/env python3
"""
作者方法论分析器
从多篇Markdown文章中提取写作方法论，生成可复用框架。
"""

import os
import re
import json
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime


def extract_metadata(content: str) -> dict:
    """从文章内容提取元数据"""
    lines = content.split('\n')
    title = ""
    word_count = len(content)
    
    # 提取标题（第一个#开头的行）
    for line in lines:
        if line.startswith('# '):
            title = line[2:].strip()
            break
    
    return {
        'title': title,
        'word_count': word_count,
        'line_count': len(lines)
    }


def analyze_title(title: str) -> dict:
    """分析标题模式"""
    patterns = []
    
    # 数字模式
    if re.search(r'\d+', title):
        patterns.append('数字')
    
    # 问号
    if '？' in title or '?' in title:
        patterns.append('疑问')
    
    # 感叹号
    if '！' in title or '!' in title:
        patterns.append('感叹')
    
    # 第一人称
    if '我' in title:
        patterns.append('第一人称')
    
    # 反常识词
   反常识词 = ['居然', '竟然', '没想到', '真相', '揭秘', '打脸', '颠覆']
    for word in 反常识词:
        if word in title:
            patterns.append('反常识')
            break
    
    # 具象词
    具象词 = ['工具', '方法', '技巧', '模板', '公式', '框架']
    for word in 具象词:
        if word in title:
            patterns.append('具象')
            break
    
    return {
        'length': len(title),
        'patterns': patterns
    }


def analyze_opening(content: str) -> dict:
    """分析开头模式"""
    # 去掉标题，取前500字
    lines = content.split('\n')
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith('# ') and i < 5:
            body_start = i + 1
            break
    
    opening = '\n'.join(lines[body_start:])[:500]
    
    patterns = []
    
    # 故事开头
    if re.search(r'我[曾经有一天]|有个|记得|上次', opening):
        patterns.append('故事')
    
    # 数据开头
    if re.search(r'\d+[%％]|\d+个|\d+万|\d+元', opening):
        patterns.append('数据')
    
    # 问题开头
    if '？' in opening or '?' in opening:
        patterns.append('问题')
    
    # 痛点开头
    痛点词 = ['烦恼', '困扰', '难题', '痛点', '焦虑', '迷茫']
    for word in 痛点词:
        if word in opening:
            patterns.append('痛点')
            break
    
    # 反常识开头
    if re.search(r'不是|其实|真相|你以为', opening):
        patterns.append('反常识')
    
    return {
        'text': opening[:200],
        'patterns': patterns
    }


def extract_golden_quotes(content: str) -> list:
    """提取金句"""
    quotes = []
    
    # 匹配引号内容
    for match in re.finditer(r'[""「](.+?)[""」]', content):
        quote = match.group(1)
        if 10 < len(quote) < 100:  # 金句长度范围
            quotes.append(quote)
    
    # 匹配独立成段的短句
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if 15 < len(line) < 60 and not line.startswith('#') and not line.startswith('-'):
            # 包含有意义的词汇
            if re.search(r'是|的|了|在|有|这|那|不|就|也|都|而|及|与|或', line):
                quotes.append(line)
    
    # 去重并限制数量
    unique_quotes = list(dict.fromkeys(quotes))
    return unique_quotes[:10]


def analyze_structure(content: str) -> dict:
    """分析文章结构"""
    lines = content.split('\n')
    
    headings = []
    lists = 0
    code_blocks = 0
    
    for line in lines:
        if line.startswith('#'):
            headings.append(line.strip())
        elif line.startswith('- ') or re.match(r'^\d+[\.\)]', line):
            lists += 1
        elif line.startswith('```'):
            code_blocks += 1
    
    return {
        'heading_count': len(headings),
        'headings': headings[:10],
        'list_items': lists,
        'code_blocks': code_blocks // 2  # 除以2因为有开始和结束
    }


def analyze_article(filepath: str) -> dict:
    """分析单篇文章"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    metadata = extract_metadata(content)
    title_analysis = analyze_title(metadata['title'])
    opening_analysis = analyze_opening(content)
    golden_quotes = extract_golden_quotes(content)
    structure_analysis = analyze_structure(content)
    
    return {
        'file': str(filepath),
        'metadata': metadata,
        'title_analysis': title_analysis,
        'opening_analysis': opening_analysis,
        'golden_quotes': golden_quotes,
        'structure_analysis': structure_analysis
    }


def aggregate_analysis(articles: list) -> dict:
    """聚合多篇文章的分析结果"""
    # 标题模式统计
    title_patterns = Counter()
    title_lengths = []
    
    # 开头模式统计
    opening_patterns = Counter()
    
    # 金句汇总
    all_quotes = []
    
    # 结构统计
    heading_counts = []
    list_counts = []
    
    for article in articles:
        # 标题
        for pattern in article['title_analysis']['patterns']:
            title_patterns[pattern] += 1
        title_lengths.append(article['title_analysis']['length'])
        
        # 开头
        for pattern in article['opening_analysis']['patterns']:
            opening_patterns[pattern] += 1
        
        # 金句
        all_quotes.extend(article['golden_quotes'])
        
        # 结构
        heading_counts.append(article['structure_analysis']['heading_count'])
        list_counts.append(article['structure_analysis']['list_items'])
    
    return {
        'article_count': len(articles),
        'title_patterns': title_patterns.most_common(5),
        'avg_title_length': sum(title_lengths) / len(title_lengths) if title_lengths else 0,
        'opening_patterns': opening_patterns.most_common(5),
        'golden_quotes': all_quotes[:20],
        'avg_headings': sum(heading_counts) / len(heading_counts) if heading_counts else 0,
        'avg_lists': sum(list_counts) / len(list_counts) if list_counts else 0
    }


def generate_framework(aggregation: dict) -> dict:
    """生成可复用框架"""
    framework = {
        'title_formulas': [],
        'opening_templates': [],
        'golden_quote_patterns': [],
        'checklist': []
    }
    
    # 标题公式
    for pattern, count in aggregation['title_patterns']:
        if pattern == '数字':
            framework['title_formulas'].append('用[数字]个[方法/技巧/工具]，[具体结果]')
        elif pattern == '疑问':
            framework['title_formulas'].append('[现象/问题]？[答案/反转]')
        elif pattern == '反常识':
            framework['title_formulas'].append('[常识]？[反转结论]')
        elif pattern == '第一人称':
            framework['title_formulas'].append('我发现/我用[数字]个[方法]，[具体结果]')
        elif pattern == '具象':
            framework['title_formulas'].append('[痛点]？[具象方案]帮你搞定')
    
    # 开头模板
    for pattern, count in aggregation['opening_patterns']:
        if pattern == '故事':
            framework['opening_templates'].append('用个人经历或案例引入，建立共鸣')
        elif pattern == '数据':
            framework['opening_templates'].append('用具体数据展示问题规模或效果')
        elif pattern == '问题':
            framework['opening_templates'].append('抛出读者关心的问题，引发思考')
        elif pattern == '痛点':
            framework['opening_templates'].append('描述读者的痛点，建立共情')
        elif pattern == '反常识':
            framework['opening_templates'].append('用反常识观点打破认知，制造好奇')
    
    # 检查清单
    framework['checklist'] = [
        '标题是否有数字或具象词？',
        '标题是否在20字以内？',
        '开头是否在3秒内抓住注意力？',
        '是否使用了第一人称增加信任感？',
        '是否有具体案例或数据支撑？',
        '段落是否长短交替，节奏感好？',
        '是否包含可引用的金句？',
        '结尾是否有行动号召或总结？'
    ]
    
    return framework


def generate_report(articles: list, aggregation: dict, framework: dict) -> str:
    """生成Markdown报告"""
    report = f"""# 作者方法论分析报告

**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**分析文章数**: {aggregation['article_count']}篇

---

## 概览

### 标题模式
"""
    
    for pattern, count in aggregation['title_patterns']:
        report += f"- {pattern}: {count}次\n"
    
    report += f"\n**平均标题长度**: {aggregation['avg_title_length']:.1f}字\n"
    
    report += "\n### 开头模式\n"
    for pattern, count in aggregation['opening_patterns']:
        report += f"- {pattern}: {count}次\n"
    
    report += "\n### 结构特点\n"
    report += f"- 平均小标题数: {aggregation['avg_headings']:.1f}\n"
    report += f"- 平均列表项数: {aggregation['avg_lists']:.1f}\n"
    
    report += "\n---\n\n## 金句摘录\n\n"
    for i, quote in enumerate(aggregation['golden_quotes'][:10], 1):
        report += f"{i}. 「{quote}」\n"
    
    report += "\n---\n\n## 可复用框架\n\n"
    
    report += "### 标题公式\n\n"
    for i, formula in enumerate(framework['title_formulas'], 1):
        report += f"{i}. {formula}\n"
    
    report += "\n### 开头模板\n\n"
    for i, template in enumerate(framework['opening_templates'], 1):
        report += f"{i}. {template}\n"
    
    report += "\n### 发布前检查清单\n\n"
    for item in framework['checklist']:
        report += f"- [ ] {item}\n"
    
    report += "\n---\n\n## 逐篇分析\n\n"
    for article in articles:
        report += f"### {article['metadata']['title']}\n\n"
        report += f"- 文件: {article['file']}\n"
        report += f"- 字数: {article['metadata']['word_count']}\n"
        report += f"- 标题模式: {', '.join(article['title_analysis']['patterns'])}\n"
        report += f"- 开头模式: {', '.join(article['opening_analysis']['patterns'])}\n"
        if article['golden_quotes']:
            report += f"- 金句: {article['golden_quotes'][0]}\n"
        report += "\n"
    
    return report


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python analyze.py <文章目录或文件> [输出文件]")
        print("示例: python analyze.py ~/output/博主名/ report.md")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "methodology_report.md"
    
    # 收集文章
    articles = []
    input_path = Path(input_path)
    
    if input_path.is_file():
        if input_path.suffix == '.md':
            articles.append(analyze_article(input_path))
    elif input_path.is_dir():
        for md_file in input_path.rglob('*.md'):
            articles.append(analyze_article(md_file))
    
    if not articles:
        print("未找到Markdown文件")
        sys.exit(1)
    
    print(f"分析了 {len(articles)} 篇文章")
    
    # 聚合分析
    aggregation = aggregate_analysis(articles)
    
    # 生成框架
    framework = generate_framework(aggregation)
    
    # 生成报告
    report = generate_report(articles, aggregation, framework)
    
    # 保存报告
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"报告已保存到: {output_file}")


if __name__ == '__main__':
    main()
