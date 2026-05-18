"""
Experiment Agent - 实验执行Agent
负责训练、评测、图表生成
"""

from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response
from langgraph.prebuilt import create_react_agent
import json
import subprocess
from pydantic import BaseModel, Field


EXPERIMENT_PROMPT = """你是一个专业的机器学习实验Agent，负责设计、执行和分析实验。

你的职责：
1. 根据方法设计生成实验代码
2. 执行训练和评估流程
3. 生成可视化图表
4. 分析实验结果

实验工作流程：
1. 代码生成：基于方法设计生成可执行的Python代码
2. 环境准备：设置训练环境
3. 执行训练：运行模型训练
4. 结果收集：收集评估指标和日志
5. 可视化：生成结果图表
6. 分析总结：总结实验发现

输出格式要求：
- 代码应完整可运行
- 包含必要的导入和配置
- 有清晰的注释和日志输出
- 支持结果复现

注意事项：
- 使用Python和常用ML库（PyTorch/TensorFlow）
- 生成的结果文件保存到output目录
- 所有输出使用UTF-8编码"""


class CodeExecutionInput(BaseModel):
    code: str = Field(description="要执行的Python代码")
    timeout: int = Field(default=300, description="超时时间（秒）")


@tool("execute_python_code", args_schema=CodeExecutionInput, return_direct=True)
def execute_python_code(code: str, timeout: int = 300) -> str:
    """执行Python代码并返回结果"""
    import sys
    import io
    import json as json_module

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

    result = {
        "stdout": "",
        "stderr": "",
        "return_value": None,
        "error": None
    }

    try:
        exec_globals = {}
        exec(code, exec_globals)

        result["stdout"] = sys.stdout.getvalue()
        result["stderr"] = sys.stderr.getvalue()

        if "_return_" in exec_globals:
            result["return_value"] = exec_globals["_return_"]

    except Exception as e:
        import traceback
        result["error"] = str(e)
        result["stderr"] = sys.stderr.getvalue() + traceback.format_exc()

    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    return json_module.dumps(result, ensure_ascii=False, indent=2)


@tool("generate_latex_table", args_schema={"table_data": str, "caption": str}, return_direct=True)
def generate_latex_table(table_data: str, caption: str = "") -> str:
    """生成LaTeX表格"""
    try:
        data = json.loads(table_data)
        headers = data.get("headers", [])
        rows = data.get("rows", [])

        lines = ["\\begin{table}[h]", "  \\centering"]
        lines.append(f"  \\caption{{{caption}}}")
        col_format = "|" + "|".join(["c"] * len(headers)) + "|"
        lines.append(f"  \\begin{tabular}{{{col_format}}}")
        lines.append("  \\hline")

        lines.append("  " + " & ".join(headers) + " \\\\")
        lines.append("  \\hline")

        for row in rows:
            lines.append("  " + " & ".join(str(x) for x in row) + " \\\\")

        lines.append("  \\hline")
        lines.append("\\end{tabular}")
        lines.append("\\end{table}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error generating table: {str(e)}"


def create_experiment_agent(llm) -> any:
    """创建Experiment Agent"""
    experiment_agent = create_react_agent(
        model=llm,
        prompt=EXPERIMENT_PROMPT,
        tools=[execute_python_code, generate_latex_table]
    )
    return experiment_agent


def generate_experiment_code(method_design: dict, experiment_config: dict, llm) -> str:
    """生成实验代码"""

    prompt = f"""请为以下方法设计生成可执行的实验代码。

## 方法设计
{json.dumps(method_design, ensure_ascii=False, indent=2)}

## 实验配置
{json.dumps(experiment_config, ensure_ascii=False, indent=2)}

请生成完整的Python实验代码，包括：
1. 数据加载和预处理
2. 模型定义
3. 训练循环
4. 评估指标计算
5. 结果保存

要求：
- 使用PyTorch或TensorFlow
- 代码完整可运行
- 添加清晰的日志输出
- 结果保存到output目录
- 使用UTF-8编码

输出格式：直接输出Python代码，不要使用JSON或其他格式包装。"""

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content if hasattr(response, 'content') else str(response)

    if isinstance(content, list):
        for block in content:
            if hasattr(block, 'type') and block.type == 'text':
                return block.text
    return content


def run_simulation(code: str, llm) -> dict:
    """运行模拟实验（用于演示）"""
    agent = create_experiment_agent(llm)

    prompt = f"""请执行以下实验代码并返回结果：

```python
{code}
```

注意：这是一个模拟实验，用于验证代码逻辑。如果代码需要真实数据集或GPU，请生成模拟结果。
输出代码执行结果。"""

    response = agent.invoke({"messages": [HumanMessage(content=prompt)]})

    if response.get("messages"):
        output = response["messages"][-1].content
        try:
            return json.loads(output)
        except:
            return {"result": output}

    return {"error": "Execution failed"}


def generate_results_summary(experiment_results: dict, method_design: dict) -> str:
    """生成实验结果摘要"""

    metrics = experiment_results.get("metrics", {})
    config = experiment_results.get("config", {})

    lines = ["## 实验结果摘要\n"]

    lines.append("### 实验配置\n")
    for k, v in config.items():
        lines.append(f"- {k}: {v}")

    lines.append("\n### 评估指标\n")
    for metric_name, value in metrics.items():
        lines.append(f"- {metric_name}: {value}")

    lines.append("\n### 方法对比\n")
    baseline = method_design.get("baseline", {})
    if baseline:
        lines.append(f"- 基线方法 ({baseline.get('name', 'N/A')}): {baseline.get('expected_performance', 'N/A')}")

    proposed = method_design.get("proposed_method", {})
    if proposed:
        lines.append(f"- 提出方法 ({proposed.get('name', 'N/A')}): 见上方指标")

    return "\n".join(lines)


def create_mock_experiment_results(method_design: dict, num_runs: int = 3) -> dict:
    """创建模拟实验结果（用于演示）"""
    import random
    import time

    proposed = method_design.get("proposed_method", {})
    metrics_list = []

    for i in range(num_runs):
        seed = int(time.time()) + i
        random.seed(seed)

        metrics_list.append({
            "accuracy": random.uniform(0.85, 0.95),
            "f1_score": random.uniform(0.84, 0.94),
            "precision": random.uniform(0.83, 0.93),
            "recall": random.uniform(0.82, 0.92),
            "training_time": random.uniform(100, 500)
        })

    avg_metrics = {}
    for key in metrics_list[0].keys():
        avg_metrics[key] = sum(m[key] for m in metrics_list) / len(metrics_list)

    return {
        "experiment_name": proposed.get("name", "Experiment"),
        "num_runs": num_runs,
        "metrics": avg_metrics,
        "all_runs": metrics_list,
        "config": {
            "dataset": "Simulated CIFAR-10",
            "epochs": 100,
            "batch_size": 128
        }
    }