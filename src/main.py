"""
Thesis Writing Agent - CLI Entry Point

用法:
    python -m src.main                    # 交互模式，自动选择可用模型
    python -m src.main --model gpt-4o     # 指定模型
    python -m src.main --model deepseek-chat --api-key sk-xxx  # 指定模型和Key
    python -m src.main --mode enhanced    # 增强模式 (质量评估+迭代)
    python -m src.main --mode basic       # 基础模式 (默认)
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage
from src.graph import create_thesis_workflow
from src.llm_config import (
    create_llm, auto_select_llm, MODEL_REGISTRY,
    get_providers, get_recommended_models, get_models_by_provider
)


def print_model_list():
    """打印所有可用模型"""
    print("=" * 60)
    print("可用模型列表")
    print("=" * 60)
    for provider in get_providers():
        models = get_models_by_provider(provider)
        print(f"\n[{provider.upper()}]")
        for name, config in models.items():
            rec = " [推荐]" if config.is_recommended else ""
            print(f"  {name:30s} {rec}  ({config.context_window:,} ctx)")
    print()


def main():
    parser = argparse.ArgumentParser(
        description='毕设论文写作 Agent 系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 交互模式，自动选择可用模型
  python -m src.main

  # 列出所有可用模型
  python -m src.main --list-models

  # 指定模型
  python -m src.main --model gpt-4o

  # 指定模型和API Key
  python -m src.main --model deepseek-chat --api-key sk-xxx
"""
    )

    parser.add_argument('--model', '-m', help='指定模型名称')
    parser.add_argument('--api-key', '-k', help='指定API Key')
    parser.add_argument('--list-models', '-l', action='store_true', help='列出所有可用模型')
    parser.add_argument('--topic', '-t', help='直接指定论文主题（非交互模式）')
    parser.add_argument('--mode', choices=['basic', 'enhanced'], default='basic',
                        help='运行模式: basic=基础(快速生成), enhanced=增强(质量评估+迭代)')

    args = parser.parse_args()

    if args.list_models:
        print_model_list()
        return

    print("=" * 60)
    print("毕设论文写作 Agent 系统")
    print("=" * 60)

    # 初始化LLM
    llm = None
    model_name = args.model

    if model_name:
        # 指定模型
        try:
            llm = create_llm(
                model_name=model_name,
                api_key=args.api_key,
                temperature=0.7,
            )
            print(f"使用模型: {model_name}")
        except ValueError as e:
            print(f"模型初始化失败: {e}")
            print_model_list()
            sys.exit(1)
    else:
        # 自动选择可用模型
        model_name, llm = auto_select_llm(temperature=0.7)
        if llm:
            print(f"自动选择模型: {model_name}")
        else:
            print("未找到可用的API Key，请设置以下环境变量之一:")
            for provider in get_providers():
                models = get_models_by_provider(provider)
                for name, config in models.items():
                    if config.is_recommended:
                        print(f"  {config.api_key_env} ({config.name})")
                        break
            print()
            print("或使用 --model 和 --api-key 参数指定")
            sys.exit(1)

    app = create_thesis_workflow(llm)

    print("\n请输入你的论文主题，例如：")
    print("  - 基于深度学习的图像去雾算法研究")
    print("  - 面向智能交通系统的路径规划优化")
    print("  - 基于注意力机制的自然语言处理模型研究")
    print(f"\n当前模式: {'基础 (快速生成)' if args.mode == 'basic' else '增强 (质量评估+迭代)'}")
    print("输入 'exit' 退出程序")
    print("-" * 60)

    while True:
        topic = input("\n请输入论文主题: ").strip()

        if topic.lower() == "exit":
            print("感谢使用，再见！")
            break

        if not topic:
            print("主题不能为空，请重新输入")
            continue

        print("\n正在启动工作流...\n")

        if args.mode == "basic":
            app = create_thesis_workflow(llm)
            result = app.invoke({
                "messages": [HumanMessage(content=topic)],
                "current_task": "research",
                "research_results": "",
                "code_results": "",
                "thesis_content": "",
                "feedback": ""
            })
            thesis = result.get("thesis_content", "")
        else:
            import asyncio
            from src.workflows.enhanced_pipeline import EnhancedResearchPipeline

            async def run_pipeline():
                pipeline = EnhancedResearchPipeline(llm)
                return await pipeline.run(topic, max_iterations=3, enable_comparison=True)

            result = asyncio.run(run_pipeline())
            thesis = result.get("thesis", "")

            # Print evaluation summary
            if result.get("evaluation_report"):
                report = result["evaluation_report"]
                print("\n" + "=" * 60)
                print("质量评估报告")
                print("=" * 60)
                print(f"综合评分: {result.get('quality_score', 0):.1f}/10")
                print(f"AIGC率: {result.get('aigc_score', 0):.1f}%")
                print(f"数据真实性: {result.get('data_authenticity', 0):.1f}%")
                print(f"通过状态: {'✅ 通过' if result.get('is_pass') else '❌ 未通过'}")
                print(f"迭代次数: {result.get('iterations', 0)}")
                print(f"运行时间: {result.get('duration_seconds', 0):.1f}秒")
                if result.get("docx_path"):
                    print(f"Word文档: {result['docx_path']}")
                if result.get("pdf_path"):
                    print(f"PDF文档: {result['pdf_path']}")
                print("=" * 60)

        print("\n" + "=" * 60)
        print("工作流执行完成")
        print("=" * 60)

        if thesis:
            print("\n生成的论文内容:")
            print(thesis[:2000] + "..." if len(thesis) > 2000 else thesis)


if __name__ == "__main__":
    main()
