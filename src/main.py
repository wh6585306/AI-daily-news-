#!/usr/bin/env python3
"""
AI Daily News System - 主程序 (增强版)
每日AI动态报送系统

特性:
- 50+新闻源采集
- 100+条原始信息处理
- 影响力评估模型
- 智能筛选5-20条精选新闻
"""
import os
import sys
import json
from datetime import datetime
import pytz

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.collector import collect_news, NewsCollector
from src.processor import process_news, NewsProcessor, ImpactScorer
from src.storage import save_news, NewsStorage
from config import TIMEZONE, MIN_NEWS_PER_CATEGORY, MAX_NEWS_PER_CATEGORY


def run_daily_news():
    """运行每日新闻采集和处理"""
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    
    print("=" * 70)
    print(f"🚀 AI每日动态报送系统 - 增强版")
    print(f"📅 运行时间: {now.strftime('%Y-%m-%d %H:%M:%S')} ({TIMEZONE})")
    print(f"🎯 目标: 采集100+条 → 精选{MIN_NEWS_PER_CATEGORY}-{MAX_NEWS_PER_CATEGORY}条")
    print("=" * 70)
    print()
    
    # 步骤1: 采集新闻
    print("📡 步骤1: 多源新闻采集...")
    print("-" * 50)
    try:
        raw_news = collect_news()
        raw_total = len(raw_news.get('domestic', [])) + len(raw_news.get('international', []))
        print(f"\n✅ 采集完成! 共 {raw_total} 条原始信息")
    except Exception as e:
        print(f"❌ 采集失败: {e}")
        raw_news = {"domestic": [], "international": []}
    
    print()
    
    # 步骤2: 智能处理
    print("🤖 步骤2: 影响力评估 + LLM智能分析...")
    print("-" * 50)
    try:
        processed_data = process_news(raw_news)
        print(f"\n✅ 处理完成!")
        print(f"   - 国内精选: {len(processed_data.get('domestic', []))} 条")
        print(f"   - 国际精选: {len(processed_data.get('international', []))} 条")
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        processed_data = {
            "date": now.strftime("%Y-%m-%d"),
            "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "domestic": [],
            "international": [],
            "summary": "处理失败"
        }
    
    print()
    
    # 步骤3: 保存数据
    print("💾 步骤3: 保存数据...")
    print("-" * 50)
    try:
        save_news(processed_data)
        print(f"\n✅ 保存完成!")
    except Exception as e:
        print(f"❌ 保存失败: {e}")
    
    print()
    
    # 步骤4: 生成报告
    print("📊 步骤4: 生成报告...")
    print("-" * 50)
    processor = NewsProcessor()
    report = processor.format_report(processed_data)
    print(report)
    
    # 保存文本报告
    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "daily",
        f"{processed_data['date']}_report.txt"
    )
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n📄 文本报告已保存: {report_path}")
    
    print()
    print("=" * 70)
    print("✨ 每日新闻采集任务完成!")
    print("=" * 70)
    
    return processed_data


def run_with_demo_data():
    """使用演示数据运行（用于测试和展示）"""
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    today = now.strftime("%Y-%m-%d")
    month_day = f"{now.month}月{now.day}日"
    
    # 模拟100+条原始数据的统计
    raw_stats = {
        "raw_domestic": 45,
        "raw_international": 68,
        "raw_total": 113
    }
    
    # 演示数据 - 国内动态 (10条)
    demo_domestic = [
        {
            "index": 1,
            "title": "国务院发布《人工智能产业高质量发展行动计划》",
            "summary": f"{month_day}消息，国务院正式发布《人工智能产业高质量发展行动计划（2024-2027）》，提出到2027年我国人工智能核心产业规模超过万亿元，培育10家以上具有国际竞争力的AI企业，形成完整的人工智能产业链。",
            "importance": "高",
            "reason": "国家级重大政策，影响全行业发展方向",
            "tags": ["政策", "国务院", "产业规划"],
            "url": "https://www.gov.cn/",
            "source": "中国政府网",
            "impact_score": 98.5
        },
        {
            "index": 2,
            "title": "智谱AI发布GLM-5基座大模型",
            "summary": f"{month_day}消息，智谱AI正式发布新一代基座大模型GLM-5，参数规模达到1.8万亿，在多项权威基准测试中超越GPT-4 Turbo，支持128K超长上下文，并宣布向开发者开放API接口。",
            "importance": "高",
            "reason": "国产大模型重大突破，性能对标国际顶级水平",
            "tags": ["智谱AI", "GLM-5", "大模型", "开放API"],
            "url": "https://www.zhipuai.cn/",
            "source": "智谱AI官方",
            "impact_score": 92.0
        },
        {
            "index": 3,
            "title": "百度发布文心一言5.0及ERNIE 4.5 Turbo",
            "summary": f"{month_day}消息，百度在AI开发者大会上发布文心一言5.0版本和ERNIE 4.5 Turbo模型，推理速度提升3倍，API调用成本降低60%，并宣布文心一言用户数突破3亿。",
            "importance": "高",
            "reason": "头部厂商重大产品更新，推动大模型普及",
            "tags": ["百度", "文心一言", "ERNIE", "降价"],
            "url": "https://yiyan.baidu.com/",
            "source": "百度",
            "impact_score": 88.5
        },
        {
            "index": 4,
            "title": "华为发布昇腾910C AI芯片",
            "summary": f"{month_day}消息，华为正式发布新一代昇腾910C AI训练芯片，采用先进制程工艺，算力达到640 TFLOPS，较上代提升80%，将大规模应用于国产AI服务器和智算中心。",
            "importance": "高",
            "reason": "国产AI芯片重大突破，填补算力缺口",
            "tags": ["华为", "昇腾", "AI芯片", "算力"],
            "url": "https://www.huawei.com/",
            "source": "华为",
            "impact_score": 90.0
        },
        {
            "index": 5,
            "title": "阿里通义千问开源Qwen2.5-Max模型",
            "summary": f"{month_day}消息，阿里云宣布开源通义千问Qwen2.5-Max模型，提供1100亿参数版本，在代码生成、数学推理等任务上达到业界领先水平，并在Hugging Face平台开放下载。",
            "importance": "高",
            "reason": "超大规模模型开源，推动AI民主化",
            "tags": ["阿里", "通义千问", "开源", "Qwen2.5"],
            "url": "https://tongyi.aliyun.com/",
            "source": "阿里达摩院",
            "impact_score": 85.0
        },
        {
            "index": 6,
            "title": "商汤科技发布日日新SenseNova 6.0",
            "summary": f"{month_day}消息，商汤科技发布日日新SenseNova 6.0大模型体系，实现端到端多模态统一架构，支持视频理解和生成，并推出面向企业的定制化解决方案。",
            "importance": "中",
            "reason": "多模态技术演进，企业级应用拓展",
            "tags": ["商汤科技", "日日新", "多模态"],
            "url": "https://www.sensetime.com/",
            "source": "商汤科技",
            "impact_score": 72.0
        },
        {
            "index": 7,
            "title": "字节跳动豆包大模型月活突破1亿",
            "summary": f"{month_day}消息，字节跳动宣布旗下AI助手豆包月活跃用户突破1亿，成为国内用户规模最大的AI原生应用，同时推出豆包专业版，面向开发者和企业用户。",
            "importance": "中",
            "reason": "用户规模里程碑，验证C端AI应用需求",
            "tags": ["字节跳动", "豆包", "用户增长"],
            "url": "https://www.doubao.com/",
            "source": "字节跳动",
            "impact_score": 68.0
        },
        {
            "index": 8,
            "title": "科大讯飞星火大模型V4.5发布",
            "summary": f"{month_day}消息，科大讯飞发布星火大模型V4.5版本，在教育、医疗、政务等垂直领域能力显著提升，并宣布与50家行业伙伴达成战略合作。",
            "importance": "中",
            "reason": "垂直领域应用深化，产业生态扩展",
            "tags": ["科大讯飞", "星火", "垂直应用"],
            "url": "https://xinghuo.xfyun.cn/",
            "source": "科大讯飞",
            "impact_score": 65.0
        },
        {
            "index": 9,
            "title": "北京发布全国首个AI大模型应用地方标准",
            "summary": f"{month_day}消息，北京市市场监管局发布《人工智能大模型应用规范》地方标准，成为全国首个针对大模型应用的地方标准，为行业规范发展提供指引。",
            "importance": "中",
            "reason": "首个地方标准出台，推动合规发展",
            "tags": ["北京", "地方标准", "监管"],
            "url": "https://www.beijing.gov.cn/",
            "source": "北京市政府",
            "impact_score": 62.0
        },
        {
            "index": 10,
            "title": "清华大学团队发布新型视觉语言模型",
            "summary": f"{month_day}消息，清华大学计算机系团队在Nature子刊发表论文，提出创新的视觉-语言对齐架构，在视觉问答任务上取得SOTA性能，论文已获最佳论文奖提名。",
            "importance": "中",
            "reason": "学术突破，提升国际影响力",
            "tags": ["清华大学", "学术", "视觉语言模型"],
            "url": "https://www.tsinghua.edu.cn/",
            "source": "清华大学",
            "impact_score": 58.0
        }
    ]
    
    # 演示数据 - 国际动态 (12条)
    demo_international = [
        {
            "index": 1,
            "title": "美国发布AI芯片出口新规，限制范围扩大",
            "summary": f"{month_day}消息，美国商务部工业与安全局(BIS)发布更新的半导体出口管制规则，将AI芯片出口限制扩展至更多国家和地区，同时收紧对先进制造设备的管控，新规将于90天后生效。",
            "importance": "高",
            "reason": "重大政策变化，影响全球AI产业供应链",
            "tags": ["美国", "出口管制", "AI芯片", "制裁"],
            "url": "https://www.commerce.gov/",
            "source": "US Commerce Dept",
            "impact_score": 100.0
        },
        {
            "index": 2,
            "title": "OpenAI正式发布GPT-5",
            "summary": f"{month_day}消息，OpenAI正式发布GPT-5大语言模型，采用全新的混合架构，在推理、编程、多模态理解等方面实现重大突破，上下文窗口扩展至100万tokens，CEO Sam Altman称其为'迈向AGI的关键一步'。",
            "importance": "高",
            "reason": "旗舰产品发布，定义AI能力新标杆",
            "tags": ["OpenAI", "GPT-5", "AGI", "重大发布"],
            "url": "https://openai.com/",
            "source": "OpenAI Blog",
            "impact_score": 98.0
        },
        {
            "index": 3,
            "title": "英伟达发布Blackwell Ultra芯片",
            "summary": f"{month_day}消息，英伟达在GTC大会上发布新一代Blackwell Ultra AI芯片，算力达到40 PFLOPS，较H100提升5倍，同时公布与多家云厂商的部署计划，预计明年Q1量产。",
            "importance": "高",
            "reason": "算力基础设施重大升级，影响AI训练效率",
            "tags": ["英伟达", "Blackwell", "AI芯片", "算力"],
            "url": "https://www.nvidia.com/",
            "source": "NVIDIA AI",
            "impact_score": 95.0
        },
        {
            "index": 4,
            "title": "谷歌DeepMind发布Gemini 2.5 Ultra",
            "summary": f"{month_day}消息，谷歌DeepMind发布Gemini 2.5 Ultra多模态大模型，在数学、科学推理、代码生成等任务上超越GPT-5基准版，支持实时视频理解和多轮对话记忆。",
            "importance": "高",
            "reason": "顶级厂商竞争升级，多模态能力新突破",
            "tags": ["谷歌", "Gemini", "多模态", "DeepMind"],
            "url": "https://deepmind.google/",
            "source": "DeepMind Blog",
            "impact_score": 92.0
        },
        {
            "index": 5,
            "title": "欧盟《人工智能法案》正式全面生效",
            "summary": f"{month_day}消息，欧盟《人工智能法案》(AI Act)正式全面生效，成为全球首部全面监管AI的立法。高风险AI系统需在6个月内完成合规，违规企业将面临最高3500万欧元或全球营收7%的罚款。",
            "importance": "高",
            "reason": "全球首部AI监管法律生效，影响深远",
            "tags": ["欧盟", "AI Act", "监管", "合规"],
            "url": "https://ec.europa.eu/",
            "source": "EU AI Policy",
            "impact_score": 90.0
        },
        {
            "index": 6,
            "title": "Anthropic发布Claude 4 Opus",
            "summary": f"{month_day}消息，Anthropic发布Claude 4 Opus模型，在安全性和有用性之间取得更好平衡，长文本处理能力显著提升，同时推出企业版API，支持私有化部署。",
            "importance": "高",
            "reason": "顶级竞品更新，AI安全领域引领者",
            "tags": ["Anthropic", "Claude", "AI安全"],
            "url": "https://www.anthropic.com/",
            "source": "Anthropic",
            "impact_score": 88.0
        },
        {
            "index": 7,
            "title": "Meta开源Llama 4模型家族",
            "summary": f"{month_day}消息，Meta正式开源Llama 4系列模型，包含8B到400B多个规格，采用混合专家架构(MoE)，在开源社区反响热烈，24小时内下载量突破100万次。",
            "importance": "高",
            "reason": "超大规模开源，推动AI民主化进程",
            "tags": ["Meta", "Llama 4", "开源", "MoE"],
            "url": "https://ai.meta.com/",
            "source": "Meta AI",
            "impact_score": 85.0
        },
        {
            "index": 8,
            "title": "xAI完成新一轮120亿美元融资",
            "summary": f"{month_day}消息，Elon Musk旗下xAI宣布完成新一轮120亿美元融资，估值达到500亿美元，所融资金将用于扩建超算中心和Grok模型研发。",
            "importance": "高",
            "reason": "史上最大AI融资之一，验证行业热度",
            "tags": ["xAI", "融资", "Elon Musk", "Grok"],
            "url": "https://x.ai/",
            "source": "Bloomberg Technology",
            "impact_score": 82.0
        },
        {
            "index": 9,
            "title": "MIT研究团队实现量子-经典混合AI突破",
            "summary": f"{month_day}消息，MIT研究团队在Nature发表论文，首次实现量子计算与经典神经网络的高效混合架构，在特定优化问题上实现指数级加速，被评为'年度重大科学突破'。",
            "importance": "高",
            "reason": "基础研究重大突破，开辟新技术路径",
            "tags": ["MIT", "量子计算", "学术突破", "Nature"],
            "url": "https://news.mit.edu/",
            "source": "MIT News AI",
            "impact_score": 80.0
        },
        {
            "index": 10,
            "title": "微软Azure AI推出GPT-5托管服务",
            "summary": f"{month_day}消息，微软宣布Azure OpenAI Service支持GPT-5模型托管，提供企业级SLA保障，同时推出新的成本优化方案，API调用成本降低40%。",
            "importance": "中",
            "reason": "云服务升级，降低企业AI使用门槛",
            "tags": ["微软", "Azure", "GPT-5", "云服务"],
            "url": "https://azure.microsoft.com/",
            "source": "Microsoft AI Blog",
            "impact_score": 72.0
        },
        {
            "index": 11,
            "title": "RAND智库发布AI地缘政治影响报告",
            "summary": f"{month_day}消息，美国兰德公司发布《人工智能与地缘政治竞争》研究报告，分析AI技术发展对国际关系格局的影响，建议美国加强与盟友的AI合作。",
            "importance": "中",
            "reason": "权威智库分析，政策参考价值高",
            "tags": ["RAND", "智库", "地缘政治", "战略"],
            "url": "https://www.rand.org/",
            "source": "RAND Corporation AI",
            "impact_score": 68.0
        },
        {
            "index": 12,
            "title": "斯坦福HAI发布2024 AI指数年度报告",
            "summary": f"{month_day}消息，斯坦福大学人类中心人工智能研究院(HAI)发布年度AI指数报告，数据显示全球AI投资总额达2000亿美元，生成式AI占比首次超过50%。",
            "importance": "中",
            "reason": "权威年度报告，全景展示行业发展",
            "tags": ["斯坦福", "HAI", "报告", "投资"],
            "url": "https://hai.stanford.edu/",
            "source": "Stanford HAI",
            "impact_score": 65.0
        }
    ]
    
    # 精简版数据（每类5条）
    demo_domestic_brief = [
        {"index": 1, "importance": "高", "summary": f"{month_day}消息，国务院正式发布《人工智能产业高质量发展行动计划（2024-2027）》，提出到2027年我国人工智能核心产业规模超过万亿元。"},
        {"index": 2, "importance": "高", "summary": f"{month_day}消息，智谱AI正式发布新一代基座大模型GLM-5，参数规模达到1.8万亿，在多项权威基准测试中超越GPT-4 Turbo。"},
        {"index": 3, "importance": "高", "summary": f"{month_day}消息，百度发布文心一言5.0版本和ERNIE 4.5 Turbo模型，API调用成本降低60%，用户数突破3亿。"},
        {"index": 4, "importance": "高", "summary": f"{month_day}消息，华为正式发布新一代昇腾910C AI训练芯片，算力达到640 TFLOPS，较上代提升80%。"},
        {"index": 5, "importance": "高", "summary": f"{month_day}消息，阿里云宣布开源通义千问Qwen2.5-Max模型，1100亿参数版本在代码生成、数学推理等任务上达到业界领先。"}
    ]
    
    demo_international_brief = [
        {"index": 1, "importance": "高", "summary": f"{month_day}消息，美国商务部工业与安全局发布更新的半导体出口管制规则，将AI芯片出口限制扩展至更多国家和地区。"},
        {"index": 2, "importance": "高", "summary": f"{month_day}消息，OpenAI正式发布GPT-5大语言模型，采用全新混合架构，上下文窗口扩展至100万tokens。"},
        {"index": 3, "importance": "高", "summary": f"{month_day}消息，英伟达发布新一代Blackwell Ultra AI芯片，算力达到40 PFLOPS，较H100提升5倍。"},
        {"index": 4, "importance": "高", "summary": f"{month_day}消息，欧盟《人工智能法案》正式全面生效，成为全球首部全面监管AI的立法。"},
        {"index": 5, "importance": "高", "summary": f"{month_day}消息，Meta正式开源Llama 4系列模型，包含8B到400B多个规格，24小时内下载量突破100万次。"}
    ]
    
    demo_data = {
        "date": today,
        "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "domestic": demo_domestic,
        "international": demo_international,
        "domestic_brief": demo_domestic_brief,
        "international_brief": demo_international_brief,
        "summary": f"今日从{raw_stats['raw_total']}条原始信息中精选出{len(demo_domestic)}条国内动态和{len(demo_international)}条国际动态，其中12条为高重要性。重点关注：国务院发布AI产业规划；美国更新芯片出口管制；OpenAI发布GPT-5。",
        "statistics": {
            **raw_stats,
            "final_domestic": len(demo_domestic),
            "final_international": len(demo_international)
        }
    }
    
    print("=" * 70)
    print(f"🚀 AI每日动态报送系统 - 增强版 (演示模式)")
    print(f"📅 运行时间: {now.strftime('%Y-%m-%d %H:%M:%S')} ({TIMEZONE})")
    print(f"🎯 模拟数据: {raw_stats['raw_total']}条原始 → {len(demo_domestic)+len(demo_international)}条精选")
    print("=" * 70)
    print()
    
    # 保存数据
    print("💾 保存演示数据...")
    save_news(demo_data)
    
    # 生成报告
    processor = NewsProcessor()
    report = processor.format_report(demo_data)
    print(report)
    
    # 保存文本报告
    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "daily",
        f"{demo_data['date']}_report.txt"
    )
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 文本报告已保存: {report_path}")
    print("\n✨ 演示数据生成完成!")
    
    return demo_data


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='AI每日动态报送系统 - 增强版')
    parser.add_argument('--demo', action='store_true', help='使用演示数据运行')
    args = parser.parse_args()
    
    if args.demo:
        run_with_demo_data()
    else:
        run_daily_news()
