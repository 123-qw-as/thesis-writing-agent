from langchain_core.tools import tool
from pydantic import BaseModel, Field
import ast
import io
import sys
import json


class PythonExecuteInput(BaseModel):
    code: str = Field(description="Python code to execute")


@tool("python_repl", args_schema=PythonExecuteInput, return_direct=True)
def create_python_repl(code: str) -> str:
    """
    Execute Python code and return the output.
    Use this for data analysis, mathematical calculations,
    algorithm implementation, and generating visualizations.

    Args:
        code: Python code to execute

    Returns:
        Execution result including stdout, stderr, and return value
    """
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
        result["error"] = str(e)
        result["stderr"] = sys.stderr.getvalue()

    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    return json.dumps(result, ensure_ascii=False, indent=2)