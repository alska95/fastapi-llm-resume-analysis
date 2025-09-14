import asyncio
import json
from typing import List

import httpx

from model.resume_analysis.resume_git_crawling_analysis import GithubAnalysisReport
from service.chat_completion.chat_completion_service import get_chat_completion_json
from service.resume_analysis.git_crawling_analysis.resume_git_fetch_repo_content_service import \
    get_all_repo_files_async, get_file_content_async


async def analyze_repo_code_with_llm(combined_code: str, repo_name: str) -> GithubAnalysisReport:
    prompt = f"""
    ---
    Combined Code for '{repo_name}':
    ```
    {combined_code}
    ```
    """

    system_prompt = f"""
        As a senior software architect, please conduct a analysis of the provided source code for the repository named '{repo_name}'.
    The code below is a concatenation of all relevant source files from the repository.

    Based on the entire codebase, please evaluate the following:
    1.  **Repository Purpose & Core Functionality**:
        * What is the primary goal of this project? What problem does it solve?
        * Identify the main features and functionalities.

    2.  **Architecture & Design**:
        * Describe the overall architecture (e.g., Monolithic, Microservices, MVC).
        * Evaluate the project structure, modularity, and separation of concerns.

    3.  **Code Quality**:
        * Assess readability, consistency in coding style, and use of comments.
        * Identify any major code smells, anti-patterns, or areas with high technical debt.
        * Evaluate error handling and robustness.

    4.  **Technology Stack & Dependencies**:
        * Identify the main programming languages, frameworks, and key libraries used.
        * Comment on the appropriateness of the tech stack for the project's purpose.

    5.  **Overall Assessment & Suggestions**:
        * Provide a summary of the project's strengths and weaknesses.
        * Offer 3-5 concrete, high-level suggestions for improvement (e.g., refactoring specific parts, improving documentation, adding tests).

    Provide the final analysis in a valid JSON format with the following structure:
    {{
        "project_name": "Project's name.",
        "project_purpose": "A concise description of the project's goal.",
        "core_functionality": ["Function 1", "Function 2"],
        "architecture_design": "Feedback on architecture and project structure.",
        "code_quality_assessment": "Overall assessment of the code quality.",
        "technology_stack": ["Language", "Framework", "Key Library"],
        "strengths": ["Strength 1", "Strength 2"],
        "weaknesses": ["Weakness 1", "Weakness 2"],
        "improvement_suggestions": ["Suggestion 1", "Suggestion 2", "Suggestion 3"]
    }}"""

    return await get_chat_completion_json(prompt=prompt, system_prompt=system_prompt,
                                          response_model=GithubAnalysisReport)


async def analyze_single_repo_async(client: httpx.AsyncClient, repo_data: dict) -> GithubAnalysisReport:
    file_extensions_to_analyze = ['.py', '.js', '.ts', '.java', '.go', '.rb', '.php', '.cs', '.c', '.cpp', '.h', '.hpp',
                                  'Dockerfile', 'docker-compose.yml', '.txt']
    max_chunk_size = 300000  # max token size 272000

    owner = repo_data['owner']['login']
    repo_name = repo_data['name']
    repo_date = repo_data['updated_at']
    print(f"Analyzing repository: {repo_name}")

    all_files = await get_all_repo_files_async(client, owner, repo_name)
    if not all_files:
        print(f"No files found in repository '{repo_name}'. Skipping.")
        return None

    filtered_files = [f for f in all_files if any(f.endswith(ext) for ext in file_extensions_to_analyze)]

    content_tasks = [get_file_content_async(client, owner, repo_name, file_path) for file_path in filtered_files]
    contents = await asyncio.gather(*content_tasks)

    code_chunks = []
    current_chunk_parts = []
    current_chunk_size = 0

    for file_path, content in zip(filtered_files, contents):
        if not content:
            continue

        file_header = f"--- START OF FILE: {file_path} ---\n"
        file_footer = f"\n--- END OF FILE: {file_path} ---\n\n"
        full_file_str = file_header + content + file_footer
        file_size = len(full_file_str.encode('utf-8'))

        if file_size > max_chunk_size:
            print(
                f"WARNING: File '{file_path}' is larger ({file_size / 1024:.2f} KB) than max_chunk_size and will be skipped.")
            continue

        if current_chunk_size + file_size > max_chunk_size and current_chunk_parts:
            code_chunks.append("".join(current_chunk_parts))
            current_chunk_parts = []
            current_chunk_size = 0

        current_chunk_parts.append(full_file_str)
        current_chunk_size += file_size

    if current_chunk_parts:
        code_chunks.append("".join(current_chunk_parts))

    if not code_chunks:
        print(f"No suitable files found to analyze in '{repo_name}'.")
        return None

    print(f"Total code split into {len(code_chunks)} chunk(s) for '{repo_name}'.")

    analysis_tasks = [analyze_repo_code_with_llm(chunk, repo_name) for chunk in code_chunks]
    partial_analysis_results = await asyncio.gather(*analysis_tasks)

    final_report = await merge_analysis_results(list(partial_analysis_results))
    final_report.repo_date = repo_date
    final_report.repo_name = repo_name

    print(f"Successfully analyzed and merged {len(code_chunks)} chunk(s) for '{repo_name}'.")
    return final_report


async def merge_analysis_results(reports: List[GithubAnalysisReport]) -> GithubAnalysisReport:
    if not reports:
        return GithubAnalysisReport()
    if len(reports) == 1:
        return reports[0]

    print(f"Merging {len(reports)} partial reports using LLM...")

    partial_reports_json_str = ""
    for i, report in enumerate(reports):
        report_dict = report.model_dump()
        partial_reports_json_str += f"--- Partial Report {i + 1} ---\n"
        partial_reports_json_str += json.dumps(report_dict, indent=2)
        partial_reports_json_str += "\n\n"

    repo_name = reports[0].project_name if reports[0].project_name else "Unknown Repository"

    system_prompt = f"""
        You are an expert senior software architect. Your task is to synthesize multiple partial code analysis reports for the repository '{repo_name}' into a single, final, and comprehensive report.

        The user will provide a series of JSON objects, each representing an analysis of a different part of the same codebase.
        Your goal is to intelligently merge the information. Consolidate findings, remove duplicates, and produce a holistic overview.

        When synthesizing the `weaknesses` from different reports, pay close attention to how they might be interconnected or complementary. Identify if one weakness is a root cause of another to reveal deeper, underlying issues in the project. For example, a weakness in 'lack of documentation' might be directly related to a weakness in 'difficult onboarding for new developers'. Your analysis should capture these relationships.

        Provide the final analysis in a valid JSON format with the following structure:
        {{
            "project_name": "{repo_name}",
            "project_purpose": "A concise description of the project's goal.",
            "core_functionality": ["Function 1", "Function 2"],
            "architecture_design": "Feedback on architecture and project structure.",
            "code_quality_assessment": "Overall assessment of the code quality.",
            "technology_stack": ["Language", "Framework", "Key Library"],
            "strengths": ["Strength 1", "Strength 2"],
            "weaknesses": ["Weakness 1", "Weakness 2"],
            "improvement_suggestions": ["Suggestion 1", "Suggestion 2", "Suggestion 3"]
        }}
        """

    prompt = f"""
    Please synthesize the following {len(reports)} partial analysis reports for the repository '{repo_name}' into one final report.
    Ensure the final report is comprehensive and cohesive.

    --- Combined Partial Reports ---
    {partial_reports_json_str}
    --- End of Combined Partial Reports ---
    """

    final_report = await get_chat_completion_json(
        prompt=prompt,
        system_prompt=system_prompt,
        response_model=GithubAnalysisReport
    )

    return final_report
