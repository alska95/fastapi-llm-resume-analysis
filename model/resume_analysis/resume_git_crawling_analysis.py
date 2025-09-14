from typing import List, Optional
from pydantic import BaseModel


class GithubAnalysisReport(BaseModel):
    project_name: Optional[str] = ""
    project_purpose: Optional[str] = ""
    core_functionality: List[str] = []
    architecture_design: Optional[str] = ""
    code_quality_assessment: Optional[str] = ""
    technology_stack: List[str] = []
    strengths: List[str] = []
    weaknesses: List[str] = []
    improvement_suggestions: List[str] = []
    repo_name: Optional[str] = ""
    repo_date: Optional[str] = ""
