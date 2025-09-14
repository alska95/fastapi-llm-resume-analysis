from typing import List

from pydantic import BaseModel


class EvidenceBasedAnalysis(BaseModel):
    strength_validation: str = ""
    gap_mitigation_potential: str = ""
    learning_agility: str = ""
    technical_depth_and_problem_solving: str = ""


class RevisedJobFit(BaseModel):
    updated_score: int = 0
    justification: str = ""


class CompositeAnalysisReport(BaseModel):
    candidate_name: str = ""
    overall_assessment: str = ""
    evidence_based_analysis: EvidenceBasedAnalysis = EvidenceBasedAnalysis()
    revised_job_fit: RevisedJobFit = RevisedJobFit()
    red_flags: List[str] = []
