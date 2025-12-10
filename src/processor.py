"""
LLM智能处理模块 - 增强版
包含影响力评估模型，支持100+原始信息处理，输出5-20条精选新闻
"""
import json
import os
import sys
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL,
    MIN_NEWS_PER_CATEGORY, MAX_NEWS_PER_CATEGORY,
    IMPACT_KEYWORDS, SOURCE_WEIGHTS
)


class ImpactScorer:
    """
    影响力评估模型
    基于关键词权重、来源权重和内容分析进行综合评分
    """
    
    def __init__(self):
        self.impact_keywords = IMPACT_KEYWORDS
        self.source_weights = SOURCE_WEIGHTS
    
    def calculate_score(self, news: Dict) -> Tuple[float, str, List[str]]:
        """
        计算新闻的影响力评分
        返回: (分数, 重要性等级, 匹配的标签)
        """
        title = news.get("title", "").lower()
        summary = news.get("summary", "").lower()
        source = news.get("source", "")
        content = f"{title} {summary}"
        
        base_score = 0
        matched_tags = []
        category_scores = {}
        
        # 1. 关键词匹配计分
        for category, config in self.impact_keywords.items():
            weight = config["weight"]
            keywords = config["keywords"]
            
            for keyword in keywords:
                if keyword.lower() in content:
                    if category not in category_scores:
                        category_scores[category] = 0
                    category_scores[category] += weight
                    matched_tags.append(keyword)
        
        # 取最高类别分数作为基础分
        if category_scores:
            base_score = max(category_scores.values())
        
        # 2. 来源权重加成
        source_multiplier = 1.0
        for tier, config in self.source_weights.items():
            if source in config.get("sources", []):
                source_multiplier = config["multiplier"]
                break
        
        # 3. 计算最终分数
        final_score = base_score * source_multiplier
        
        # 4. 额外加分规则
        # 标题中包含重要词汇额外加分
        important_title_words = [
            "breaking", "exclusive", "official", "confirmed",
            "突发", "独家", "官宣", "重磅", "首发"
        ]
        for word in important_title_words:
            if word.lower() in title:
                final_score += 20
        
        # 涉及多个重要主题额外加分
        if len(category_scores) >= 2:
            final_score += 15 * (len(category_scores) - 1)
        
        # 5. 确定重要性等级
        importance = self._determine_importance(final_score)
        
        # 去重标签
        matched_tags = list(set(matched_tags))[:5]
        
        return final_score, importance, matched_tags
    
    def _determine_importance(self, score: float) -> str:
        """根据分数确定重要性等级"""
        if score >= 80:
            return "高"
        elif score >= 40:
            return "中"
        else:
            return "低"
    
    def rank_news(self, news_list: List[Dict]) -> List[Dict]:
        """对新闻列表进行排序和评分"""
        scored_news = []
        
        for news in news_list:
            score, importance, tags = self.calculate_score(news)
            news_copy = news.copy()
            news_copy["impact_score"] = score
            news_copy["importance"] = importance
            news_copy["auto_tags"] = tags
            scored_news.append(news_copy)
        
        # 按分数降序排序
        scored_news.sort(key=lambda x: x["impact_score"], reverse=True)
        
        return scored_news


class NewsProcessor:
    """新闻处理器 - 增强版"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL
        ) if OPENAI_API_KEY else None
        self.model = OPENAI_MODEL
        self.scorer = ImpactScorer()
    
    def process_news(self, raw_news: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """处理原始新闻数据（100+条 -> 5-20条精选）"""
        today = datetime.now().strftime("%Y-%m-%d")
        month = datetime.now().month
        day = datetime.now().day
        
        # 统计原始数据
        raw_domestic_count = len(raw_news.get("domestic", []))
        raw_international_count = len(raw_news.get("international", []))
        total_raw = raw_domestic_count + raw_international_count
        
        print(f"\n📊 原始数据统计:")
        print(f"   - 国内原始新闻: {raw_domestic_count} 条")
        print(f"   - 国际原始新闻: {raw_international_count} 条")
        print(f"   - 总计: {total_raw} 条")
        
        result = {
            "date": today,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "domestic": [],
            "international": [],
            "summary": "",
            "statistics": {
                "raw_domestic": raw_domestic_count,
                "raw_international": raw_international_count,
                "raw_total": total_raw
            }
        }
        
        # 步骤1: 影响力评分和初步排序
        print("\n🎯 步骤1: 影响力评分...")
        domestic_scored = self.scorer.rank_news(raw_news.get("domestic", []))
        international_scored = self.scorer.rank_news(raw_news.get("international", []))
        
        print(f"   - 国内高分新闻: {len([n for n in domestic_scored if n['importance'] == '高'])} 条")
        print(f"   - 国际高分新闻: {len([n for n in international_scored if n['importance'] == '高'])} 条")
        
        # 步骤2: LLM精细处理
        if self.client:
            print("\n🤖 步骤2: LLM智能分析...")
            result["domestic"] = self._process_with_llm(
                domestic_scored[:50],  # 取前50条给LLM处理
                "国内"
            )
            result["international"] = self._process_with_llm(
                international_scored[:50],
                "国际"
            )
        else:
            print("\n⚠️ 无LLM，使用规则处理...")
            result["domestic"] = self._rule_based_process(domestic_scored)
            result["international"] = self._rule_based_process(international_scored)
        
        # 步骤3: 翻译国际新闻为中文
        print("\n🌐 步骤3: 翻译国际新闻...")
        result["international"] = self._translate_international_news(result["international"])
        
        # 步骤4: 生成精简版（每类3-8条）
        print("\n📝 步骤4: 生成精简版...")
        result["domestic_brief"] = self._generate_brief(result["domestic"], 5)
        result["international_brief"] = self._generate_brief(result["international"], 5)
        
        # 步骤5: 生成总结
        result["summary"] = self._generate_summary(result)
        
        # 更新统计
        result["statistics"]["final_domestic"] = len(result["domestic"])
        result["statistics"]["final_international"] = len(result["international"])
        
        return result
    
    def _translate_international_news(self, news_list: List[Dict]) -> List[Dict]:
        """翻译国际新闻为中文"""
        if not news_list:
            return news_list
        
        today = datetime.now()
        month_day = f"{today.month}月{today.day}日"
        
        for news in news_list:
            summary = news.get("summary", "")
            # 如果是英文摘要，尝试用LLM翻译
            if self.client and summary and not self._is_chinese(summary):
                try:
                    translated = self._translate_with_llm(summary, month_day)
                    if translated:
                        news["summary"] = translated
                except:
                    # 翻译失败时保持原文
                    pass
            # 确保格式正确
            if not news.get("summary", "").startswith(f"{today.month}月"):
                news["summary"] = f"{month_day}消息，{news.get('summary', '')}"
        
        return news_list
    
    def _is_chinese(self, text: str) -> bool:
        """检查文本是否主要是中文"""
        if not text:
            return False
        chinese_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        return chinese_count > len(text) * 0.3
    
    def _translate_with_llm(self, text: str, month_day: str) -> str:
        """使用LLM翻译英文为中文"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是专业的AI新闻翻译，将英文新闻翻译成简洁流畅的中文。"},
                    {"role": "user", "content": f"将以下新闻翻译成中文，以'{month_day}消息，'开头，保持简洁专业：\n\n{text[:500]}"}
                ],
                temperature=0.3,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except:
            return None
    
    def _generate_brief(self, news_list: List[Dict], count: int = 5) -> List[Dict]:
        """生成精简版（纯文字，3-8条）"""
        brief = []
        # 优先选择高重要性的
        high = [n for n in news_list if n.get("importance") == "高"]
        medium = [n for n in news_list if n.get("importance") == "中"]
        
        selected = (high + medium)[:count]
        
        for i, news in enumerate(selected):
            brief.append({
                "index": i + 1,
                "summary": news.get("summary", ""),
                "importance": news.get("importance", "中")
            })
        
        return brief
    
    def _process_with_llm(self, scored_news: List[Dict], category: str) -> List[Dict]:
        """使用LLM处理已评分的新闻"""
        if not scored_news:
            return []
        
        # 准备新闻数据
        news_text = "\n\n".join([
            f"【{i+1}】[影响力分数: {n.get('impact_score', 0):.1f}] [初步等级: {n.get('importance', '中')}]\n"
            f"标题: {n['title']}\n"
            f"摘要: {n.get('summary', '')[:300]}\n"
            f"来源: {n.get('source', 'N/A')}\n"
            f"自动标签: {', '.join(n.get('auto_tags', []))}"
            for i, n in enumerate(scored_news[:30])
        ])
        
        prompt = f"""你是一位资深的AI行业首席分析师，专注于全球AI产业动态、政策法规、学术突破和商业发展。

请分析以下{category}AI新闻，执行以下任务：

## 筛选标准（按重要性排序）：
1. 🔴 **重大政策与法规**: 政府行政令、AI法案、制裁禁令、出口管制、反垄断调查
2. 🟠 **重大产品发布**: 旗舰AI模型发布(如GPT-5, Gemini 3)、重要芯片发布(H200, B100)
3. 🟡 **重大学术突破**: 突破性研究成果、SOTA性能、重要论文、学术奖项
4. 🟢 **重大商业动态**: 大额融资(10亿+)、重要并购、战略合作
5. 🔵 **安全与伦理**: AI安全事件、重大伦理争议

## 输出要求：
- 从中筛选 {MIN_NEWS_PER_CATEGORY}-{MAX_NEWS_PER_CATEGORY} 条最重要的新闻
- 严格按重要性排序（最重要的排在最前面）
- 为每条新闻撰写专业摘要（80-150字），格式："X月X日消息，[核心内容]..."
- 标注重要性等级：高(必读)/中(重要)/低(关注)
- 提取3-5个标签

## 新闻列表:
{news_text}

请以JSON格式返回:
{{
    "news": [
        {{
            "index": 1,
            "title": "新闻标题",
            "summary": "专业摘要（80-150字）",
            "importance": "高/中/低",
            "reason": "入选理由（简短说明为何重要）",
            "tags": ["标签1", "标签2", "标签3"]
        }}
    ],
    "analysis": "整体分析（2-3句话概括今日{category}AI动态趋势）"
}}

重要提示：
- 只返回纯JSON，不要包含markdown代码块
- 至少返回{MIN_NEWS_PER_CATEGORY}条新闻
- 优先选择涉及政策、产品发布、学术突破的新闻
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "你是全球顶尖的AI产业分析师，拥有深厚的技术背景和政策洞察力。你需要从大量信息中筛选出最具影响力的新闻。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            
            # 尝试解析JSON
            try:
                # 移除可能的markdown代码块标记
                content = re.sub(r'^```json\s*', '', content)
                content = re.sub(r'\s*```$', '', content)
                result = json.loads(content)
            except json.JSONDecodeError:
                # 尝试提取JSON部分
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise ValueError("无法解析LLM返回的JSON")
            
            processed_news = result.get("news", [])
            
            # 补充原始信息
            for i, item in enumerate(processed_news):
                item["index"] = i + 1
                if i < len(scored_news):
                    item["url"] = scored_news[i].get("url", "")
                    item["source"] = scored_news[i].get("source", item.get("source", ""))
                    item["original_pub_date"] = scored_news[i].get("pub_date", "")
                    item["impact_score"] = scored_news[i].get("impact_score", 0)
            
            print(f"   ✓ {category}新闻处理完成: {len(processed_news)} 条")
            
            return processed_news[:MAX_NEWS_PER_CATEGORY]
            
        except Exception as e:
            print(f"   ✗ LLM处理{category}新闻失败: {e}")
            return self._rule_based_process(scored_news)
    
    def _rule_based_process(self, scored_news: List[Dict]) -> List[Dict]:
        """基于规则的处理（无LLM时使用）"""
        today = datetime.now()
        processed = []
        
        # 确保高分新闻优先
        high_importance = [n for n in scored_news if n.get("importance") == "高"]
        medium_importance = [n for n in scored_news if n.get("importance") == "中"]
        low_importance = [n for n in scored_news if n.get("importance") == "低"]
        
        # 组合：优先高分，然后中分
        selected = high_importance[:MAX_NEWS_PER_CATEGORY]
        if len(selected) < MIN_NEWS_PER_CATEGORY:
            remaining = MIN_NEWS_PER_CATEGORY - len(selected)
            selected.extend(medium_importance[:remaining])
        if len(selected) < MIN_NEWS_PER_CATEGORY:
            remaining = MIN_NEWS_PER_CATEGORY - len(selected)
            selected.extend(low_importance[:remaining])
        
        for i, news in enumerate(selected[:MAX_NEWS_PER_CATEGORY]):
            summary = news.get("summary", "")[:200]
            if not summary.startswith(f"{today.month}月"):
                summary = f"{today.month}月{today.day}日消息，{summary}"
            
            processed.append({
                "index": i + 1,
                "title": news["title"],
                "summary": summary,
                "importance": news.get("importance", "中"),
                "reason": f"影响力评分: {news.get('impact_score', 0):.1f}",
                "tags": news.get("auto_tags", [])[:5],
                "url": news.get("url", ""),
                "source": news.get("source", ""),
                "original_pub_date": news.get("pub_date", ""),
                "impact_score": news.get("impact_score", 0)
            })
        
        return processed
    
    def _generate_summary(self, result: Dict) -> str:
        """生成每日总结"""
        stats = result.get("statistics", {})
        domestic = result.get("domestic", [])
        international = result.get("international", [])
        
        # 统计各等级数量
        high_count = sum(1 for n in domestic + international if n.get("importance") == "高")
        
        # 提取高重要性新闻标题
        high_news = [n["title"] for n in domestic + international if n.get("importance") == "高"][:3]
        
        summary_parts = [
            f"今日从{stats.get('raw_total', 0)}条原始信息中精选出"
            f"{len(domestic)}条国内动态和{len(international)}条国际动态，"
            f"其中{high_count}条为高重要性。"
        ]
        
        if high_news:
            summary_parts.append(f"重点关注：{'；'.join(high_news)}。")
        
        return " ".join(summary_parts)
    
    def format_report(self, processed_data: Dict) -> str:
        """格式化为文本报告"""
        lines = []
        lines.append("=" * 70)
        lines.append(f"AI每日动态 - {processed_data['date']}")
        lines.append(f"生成时间: {processed_data['generated_at']}")
        
        stats = processed_data.get("statistics", {})
        lines.append(f"数据来源: 从 {stats.get('raw_total', 0)} 条原始信息中精选")
        lines.append("=" * 70)
        lines.append("")
        
        # ========== 精简版 ==========
        lines.append("╔" + "═" * 68 + "╗")
        lines.append("║" + " " * 25 + "📋 精简版报告" + " " * 26 + "║")
        lines.append("╚" + "═" * 68 + "╝")
        lines.append("")
        
        # 精简版国内动态
        lines.append("国内动态：")
        domestic_brief = processed_data.get("domestic_brief", processed_data.get("domestic", [])[:5])
        for i, news in enumerate(domestic_brief[:8]):
            idx = news.get("index", i + 1)
            summary = news.get("summary", "")
            lines.append(f"{idx}、{summary}")
        lines.append("")
        
        # 精简版国际动态
        lines.append("国际动态：")
        international_brief = processed_data.get("international_brief", processed_data.get("international", [])[:5])
        for i, news in enumerate(international_brief[:8]):
            idx = news.get("index", i + 1)
            summary = news.get("summary", "")
            lines.append(f"{idx}、{summary}")
        lines.append("")
        lines.append("")
        
        # ========== 完整版 ==========
        lines.append("╔" + "═" * 68 + "╗")
        lines.append("║" + " " * 25 + "📰 完整版报告" + " " * 26 + "║")
        lines.append("╚" + "═" * 68 + "╝")
        lines.append("")
        
        # 国内动态
        lines.append("【国内动态】")
        lines.append("-" * 50)
        for news in processed_data.get("domestic", []):
            icon = self._get_importance_icon(news.get("importance", "中"))
            lines.append(f"{news['index']}、{icon} {news['summary']}")
            if news.get("reason"):
                lines.append(f"   📋 入选理由: {news['reason']}")
            lines.append(f"   📰 来源: {news.get('source', 'N/A')} | 🔗 {news.get('url', 'N/A')}")
            if news.get("tags"):
                lines.append(f"   🏷️ 标签: {', '.join(news['tags'])}")
            lines.append("")
        
        lines.append("")
        
        # 国际动态
        lines.append("【国际动态】")
        lines.append("-" * 50)
        for news in processed_data.get("international", []):
            icon = self._get_importance_icon(news.get("importance", "中"))
            lines.append(f"{news['index']}、{icon} {news['summary']}")
            if news.get("reason"):
                lines.append(f"   📋 入选理由: {news['reason']}")
            lines.append(f"   📰 来源: {news.get('source', 'N/A')} | 🔗 {news.get('url', 'N/A')}")
            if news.get("tags"):
                lines.append(f"   🏷️ 标签: {', '.join(news['tags'])}")
            lines.append("")
        
        lines.append("")
        lines.append("=" * 70)
        lines.append(f"📊 今日总结: {processed_data.get('summary', '')}")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def _get_importance_icon(self, importance: str) -> str:
        """获取重要性图标"""
        icons = {
            "高": "🔥",
            "中": "📌",
            "低": "📄"
        }
        return icons.get(importance, "📄")


def process_news(raw_news: Dict[str, List[Dict]]) -> Dict[str, Any]:
    """处理新闻的主函数"""
    processor = NewsProcessor()
    return processor.process_news(raw_news)


if __name__ == "__main__":
    # 测试影响力评分
    scorer = ImpactScorer()
    
    test_news = [
        {
            "title": "美国发布新行政令限制AI芯片出口",
            "summary": "白宫宣布新的出口管制措施，限制向中国出售先进AI芯片",
            "source": "Reuters Technology"
        },
        {
            "title": "OpenAI发布GPT-5",
            "summary": "OpenAI正式发布GPT-5大模型，性能全面超越前代",
            "source": "OpenAI Blog"
        },
        {
            "title": "某公司推出AI助手",
            "summary": "一家初创公司推出了新的AI助手产品",
            "source": "TechBlog"
        }
    ]
    
    for news in test_news:
        score, importance, tags = scorer.calculate_score(news)
        print(f"\n标题: {news['title']}")
        print(f"分数: {score:.1f} | 等级: {importance}")
        print(f"标签: {tags}")
