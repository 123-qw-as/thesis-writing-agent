from langchain_core.tools import tool
from pydantic import BaseModel, Field
from pathlib import Path
import json


class LatexWriterInput(BaseModel):
    content: str = Field(description="LaTeX document content")
    output_path: str = Field(description="Output file path (.tex)")


class MarkdownWriterInput(BaseModel):
    content: str = Field(description="Markdown content")
    output_path: str = Field(description="Output file path (.md)")


@tool("write_latex", args_schema=LatexWriterInput, return_direct=True)
def create_latex_writer(content: str, output_path: str) -> str:
    """
    Write content to a LaTeX file. Use this for formal academic papers
    that require precise formatting.

    Args:
        content: LaTeX document content
        output_path: Path to save the .tex file

    Returns:
        Success message with file path or error message
    """
    try:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return json.dumps({
            "status": "success",
            "file_path": str(path.absolute()),
            "message": f"LaTeX file saved successfully"
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@tool("write_markdown", args_schema=MarkdownWriterInput, return_direct=True)
def create_markdown_writer(content: str, output_path: str) -> str:
    """
    Write content to a Markdown file. Use this for drafts, notes,
    or converting to other formats later.

    Args:
        content: Markdown content
        output_path: Path to save the .md file

    Returns:
        Success message with file path or error message
    """
    try:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return json.dumps({
            "status": "success",
            "file_path": str(path.absolute()),
            "message": f"Markdown file saved successfully"
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})