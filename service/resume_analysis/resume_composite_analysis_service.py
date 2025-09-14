import json
from typing import List, Dict, Any

from model.resume_analysis.resume_basic_analysis import CandidateBasicAnalysis
from model.resume_analysis.resume_composite_analysis import CompositeAnalysisReport
from model.resume_analysis.resume_git_crawling_analysis import GithubAnalysisReport
from service.chat_completion.chat_completion_service import get_chat_completion_response, get_chat_completion_json


async def composite_resume_analysis(
    basic_analysis_result: CandidateBasicAnalysis,
    github_analysis_reports: List[GithubAnalysisReport]
) -> CompositeAnalysisReport:

    system_prompt = """
    You are a highly experienced senior software engineer and a tech hiring manager.
    Your task is to synthesize information from a candidate's basic resume analysis and detailed analyses of their GitHub projects to create a comprehensive, evidence-based final evaluation.
    Go beyond simple summaries. Your analysis must provide deep insights into the candidate's true capabilities by using the GitHub analysis as concrete proof.

    Specifically, you need to evaluate the following:
    1.  **Strength Validation**: Does the GitHub evidence (code quality, architecture, tech stack) support the strengths identified in the resume and job fit analysis? Provide specific examples.
    2.  **Gap Mitigation Potential**: Can the candidate's work on GitHub suggest they have the foundational knowledge or learning ability to overcome the gaps/weaknesses identified?
    3.  **Learning Agility**: Based on the project timelines and the variety of technologies used, assess how quickly the candidate learns and adapts to new technologies.
    4.  **Technical Depth**: Evaluate if the candidate can handle technically complex tasks. Look for evidence of good architectural design, solving non-trivial problems, and high-quality code in their GitHub projects.

    The final output must be a single, valid JSON object. Do not include any text, markdown, or explanations outside of the JSON structure provided below.

    JSON Structure to follow:
    {
      "candidate_name": "Full Name from basic analysis",
      "overall_assessment": "A comprehensive summary of the candidate's profile, integrating insights from the resume, job fit, and GitHub projects. This should be your final verdict.",
      "evidence_based_analysis": {
        "strength_validation": "Analysis of how GitHub projects provide concrete evidence for the strengths mentioned. Be specific.",
        "gap_mitigation_potential": "Assessment of whether GitHub projects show potential to overcome the identified weaknesses. Explain your reasoning.",
        "learning_agility": "Evaluation of the candidate's learning speed and adaptability, citing evidence from projects.",
        "technical_depth_and_problem_solving": "Assessment of the candidate's ability to handle complex technical challenges, based on their GitHub projects."
      },
      "revised_job_fit": {
          "updated_score": 85, // A revised score (0-100) based on these new insights.
          "justification": "A brief explanation for any change from the initial score, highlighting key factors from the GitHub analysis."
      },
      "red_flags": [ // Optional: List any inconsistencies or major concerns found when comparing the resume and GitHub.
        "Example: The resume claims expertise in 'Project X', but the corresponding GitHub repository is minimal and lacks significant commits."
      ]
    }
    """

    basic_analysis_str = basic_analysis_result.model_dump_json(indent=2)
    github_analysis_reports_as_dicts = [report.model_dump() for report in github_analysis_reports]
    github_reports_str= json.dumps(github_analysis_reports_as_dicts, indent=2, ensure_ascii=False)

    prompt = f"""
    Here is the candidate's information. Please perform a composite analysis based on the system instructions.

    --- BASIC RESUME AND JOB FIT ANALYSIS ---
    {basic_analysis_str}

    --- DETAILED GITHUB PROJECT ANALYSIS ---
    {github_reports_str}
    """

    return await get_chat_completion_json(
        prompt=prompt,
        response_model=CompositeAnalysisReport,
        system_prompt=system_prompt
    )