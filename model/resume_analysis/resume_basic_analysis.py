from typing import List, Optional
from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    name: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    github: Optional[str] = ""
    portfolio: Optional[str] = ""


class WorkExperience(BaseModel):
    company: Optional[str] = ""
    title: Optional[str] = ""
    period: Optional[str] = ""
    achievements: List[str] = []


class Project(BaseModel):
    name: Optional[str] = ""
    period: Optional[str] = ""
    description: Optional[str] = ""
    role: Optional[str] = ""
    tech_stack: List[str] = []


class Education(BaseModel):
    institution: Optional[str] = ""
    degree: Optional[str] = ""
    major: Optional[str] = ""
    graduation_year: Optional[str] = ""


class ResumeData(BaseModel):
    contact_info: Optional[ContactInfo] = Field(default_factory=ContactInfo)
    summary: Optional[str] = ""
    work_experience: List[WorkExperience] = []
    skills: List[str] = []
    projects: List[Project] = []
    education: List[Education] = []


class JobFitAnalysis(BaseModel):
    overall_score: Optional[int] = 0
    match_summary: Optional[str] = ""
    strengths: List[str] = []
    weaknesses: List[str] = []


class CandidateBasicAnalysis(BaseModel):
    resume_data: Optional[ResumeData] = Field(default_factory=ResumeData)
    job_fit_analysis: Optional[JobFitAnalysis] = Field(default_factory=JobFitAnalysis)
