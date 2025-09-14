import asyncio

from fastapi import UploadFile

from service.resume_analysis.basic_analysis.resume_basic_core_analysis_service import basic_resume_analysis
from service.resume_analysis.resume_composite_analysis_service import composite_resume_analysis
from service.resume_analysis.git_crawling_analysis.resume_git_core_analysis_service import git_resume_analysis
from utils.pdf_to_text_converter import pdf_to_text


async def analyze_resume(resume_text: str, application_link: str):
    basic_analysis_result, github_analysis_result = await asyncio.gather(
        basic_resume_analysis(resume_text, application_link),
        git_resume_analysis(resume_text)
    )

    composite_analysis_result = await composite_resume_analysis(basic_analysis_result, github_analysis_result)
    return composite_analysis_result


async def analyze_pdf_resume(resume_pdf_file: UploadFile, application_link: str):
    pdf_bytes = await resume_pdf_file.read()
    resume_text = pdf_to_text(pdf_bytes)
    return await analyze_resume(resume_text, application_link)
