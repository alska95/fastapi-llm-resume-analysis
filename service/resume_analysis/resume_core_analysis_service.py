from fastapi import UploadFile

from service.resume_analysis.resume_application_company_analysis_service import extract_job_requirements
from service.resume_analysis.resume_basic_analysis_service import basic_resume_analysis
from service.resume_analysis.resume_git_crawling_analysis_service import git_analysis_from_resume
from utils.pdf_to_text_converter import pdf_to_text


async def analyze_resume(resume_text: str, application_link: str):
    job_requirements = ""
    if application_link:
        job_requirements = await extract_job_requirements(application_link)
    basic_analysis_result = await basic_resume_analysis(resume_text, job_requirements)
    # github_analysis_result = git_analysis_from_resume(resume_text)
    return basic_analysis_result.model_dump_json()


async def analyze_pdf_resume(resume_pdf_file: UploadFile, application_link: str):
    pdf_bytes = await resume_pdf_file.read()
    resume_text = pdf_to_text(pdf_bytes)
    return analyze_resume(resume_text, application_link)
