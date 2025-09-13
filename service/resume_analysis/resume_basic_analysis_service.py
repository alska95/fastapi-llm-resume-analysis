from model.resume_analysis.resume_basic_analysis import CandidateProfile
from service.chat_completion.chat_completion_service import get_chat_completion_response, get_chat_completion_json


async def basic_resume_analysis(resume_text: str, job_requirements: str) -> CandidateProfile:

    system_prompt = """
    You are an expert HR manager. Your primary task is to analyze a candidate's resume in the context of a specific job description.
    You must evaluate how well the candidate's skills and experience align with the job requirements.
    The final output must be a single, valid JSON object that includes both the parsed resume data AND an analysis of the candidate's suitability for the job.
    Do not include any text, markdown, or explanations outside of the JSON structure.

    - For `resume_data`, parse the resume text accurately. If a field is not found, use null for single fields or an empty array [] for lists.
    - For `job_fit_analysis`, perform a detailed comparison between the resume and the job requirements.
    - The `overall_score` should be a quantitative measure of the candidate's fit for the role.
    - `strengths` should list specific evidence from the resume that matches the job requirements.
    - `gaps` should list key requirements from the job description that are not clearly met by the resume.

    JSON Structure to follow:
    {
      "resume_data": {
        "contact_info": {
          "name": "Full Name",
          "email": "Email Address",
          "phone": "Phone Number",
          "github": "GitHub Profile URL",
          "portfolio": "Portfolio or Personal Website URL"
        },
        "summary": "A brief professional summary of the candidate.",
        "work_experience": [
          {
            "company": "Company Name",
            "title": "Job Title",
            "period": "Employment Period (e.g., '2022.01 - 2024.03')",
            "achievements": [
              "A specific, quantifiable achievement.",
              "Another key responsibility or accomplishment."
            ]
          }
        ],
        "skills": ["Python", "JavaScript", "React", "Django", "PostgreSQL", "MongoDB", "AWS"]
        "projects": [
          {
            "name": "Project Name",
            "period": "Project Period (e.g., '2025.05 - 2025.09')",
            "description": "A brief description of the project.",
            "role": "My role in the project.",
            "tech_stack": ["React", "Node.js"]
          }
        ],
        "education": [
          {
            "institution": "University Name",
            "degree": "Degree (e.g., 'Bachelor of Science')",
            "major": "Major (e.g., 'Computer Science')",
            "graduation_year": "Year of graduation"
          }
        ]
      },
      "job_fit_analysis": {
        "overall_score": 85, // Match score (0-100). Scores of 80+ are considered strong candidates for an interview.        
        "match_summary": "A concise, professional summary explaining why the candidate is a good or weak fit for the role, referencing both the resume and job requirements.",
        "strengths": [
          "Possesses 5 years of Python experience as required by the job description.",
          "Direct experience with AWS and Docker, which are key technologies listed in the requirements.",
          "Managed a project similar in scope to the responsibilities mentioned."
        ],
        "weaknesses": [
          "No explicit mention of Kubernetes experience.",
          "Lacks experience with Java, which is a secondary language requirement."
        ]
      }
    }
    """

    user_prompt = f"""
    --- JOB REQUIREMENTS ---
    {job_requirements}

    --- RESUME ---
    {resume_text}
    """

    return await get_chat_completion_json(
        prompt=user_prompt,
        system_prompt=system_prompt,
        response_model=CandidateProfile
    )