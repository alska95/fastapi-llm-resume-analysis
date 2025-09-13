from fastapi import APIRouter, UploadFile, File

from service.resume_analysis.resume_core_analysis_service import analyze_resume, analyze_pdf_resume

router = APIRouter()


@router.get("/resume")
async def resume_analysis(resume_text: str, application_link: str) -> str:
    return await analyze_resume(resume_text=resume_text, application_link=application_link)


@router.get("/resume/pdf")
async def resume_pdf_analysis(
        application_link: str,
        resume_pdf_file: UploadFile = File(...)
) -> str:
    return await analyze_pdf_resume(resume_pdf_file=resume_pdf_file, application_link=application_link)
