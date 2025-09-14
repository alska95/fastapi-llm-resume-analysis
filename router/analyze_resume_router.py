from fastapi import APIRouter, UploadFile, File, Form

from model.resume_analysis.resume_analysis_request import ResumeAnalysisRequest
from model.resume_analysis.resume_composite_analysis import CompositeAnalysisReport
from service.resume_analysis.resume_core_analysis_service import analyze_resume, analyze_pdf_resume

router = APIRouter()


@router.post("/resume")
async def resume_analysis(resume_text: str, application_link: str) -> CompositeAnalysisReport:
    return await analyze_resume(resume_text=resume_text, application_link=application_link)


@router.post("/resume/pdf")
async def resume_pdf_analysis(
        application_link: str = Form(...),
        resume_pdf_file: UploadFile = File(...)
) -> CompositeAnalysisReport:
    return await analyze_pdf_resume(
        resume_pdf_file=resume_pdf_file,
        application_link=application_link
    )

