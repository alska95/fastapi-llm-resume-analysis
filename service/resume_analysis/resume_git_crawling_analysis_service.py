import os
import re
import httpx
import json
import asyncio
from datetime import datetime

from service.chat_completion.chat_completion_service import get_chat_completion_response


async def git_analysis_from_resume(resume: str):
    github_username = await find_github_username_from_resume(resume)
    if not github_username:
        return ""

    return await git_crawling_analysis_parallel(github_username)


async def find_github_username_from_resume(resume: str):
    analyze_prompt = "Please find github username from following resume_analysis: " + resume
    raw_git_hub_username = await get_chat_completion_response(analyze_prompt)
    pattern = r'(https?://(?:www\.)?github\.com/([\w\-.]+))'
    match = re.search(pattern, raw_git_hub_username)
    if match:
        return match.group(2)
    else:
        pattern = r'github\.com/([\w\-.]+)'
        match = re.search(pattern, resume)
        if match:
            return match.group(1)
        match = re.search(r'github:\s*([\w\-.]+)', resume, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


async def get_repos_with_api_async(client: httpx.AsyncClient, username: str) -> list:
    repo_data_list = []
    api_url = f"https://api.github.com/users/{username}/repos"
    while api_url:
        try:
            response = await client.get(api_url, params={'per_page': 100})
            response.raise_for_status()
            repos_page_data = response.json()
            repo_data_list.extend(repos_page_data)
            api_url = response.links.get('next', {}).get('url')
        except httpx.RequestError as e:
            print(f"ERROR: An error occurred while fetching repositories: {e}")
            break
    return repo_data_list


async def get_file_content_async(client: httpx.AsyncClient, owner: str, repo_name: str, file_path: str) -> str:
    content_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{file_path}"
    try:
        response = await client.get(content_url)
        response.raise_for_status()
        return response.text
    except httpx.RequestError as e:
        print(f"ERROR: Failed to fetch content for {file_path}: {e}")
        return None


async def get_all_repo_files_async(client: httpx.AsyncClient, owner: str, repo_name: str, path: str = '') -> list:
    contents_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{path}"
    files = []
    try:
        response = await client.get(contents_url)
        response.raise_for_status()
        contents = response.json()

        tasks = []
        for item in contents:
            if item['type'] == 'file':
                files.append(item['path'])
            elif item['type'] == 'dir':
                tasks.append(get_all_repo_files_async(client, owner, repo_name, item['path']))

        if tasks:
            nested_files_list = await asyncio.gather(*tasks)
            for nested_files in nested_files_list:
                files.extend(nested_files)

    except httpx.RequestError as e:
        print(f"ERROR: Could not fetch repository contents for path '{path}': {e}")
    return files


async def analyze_repo_code_with_llm(combined_code: str, repo_name: str) -> dict:
    prompt = f"""
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
        "project_purpose": "A concise description of the project's goal.",
        "core_functionality": ["Function 1", "Function 2"],
        "architecture_design": "Feedback on architecture and project structure.",
        "code_quality_assessment": "Overall assessment of the code quality.",
        "technology_stack": ["Language", "Framework", "Key Library"],
        "strengths": ["Strength 1", "Strength 2"],
        "weaknesses": ["Weakness 1", "Weakness 2"],
        "improvement_suggestions": ["Suggestion 1", "Suggestion 2", "Suggestion 3"]
    }}

    ---
    Combined Code for '{repo_name}':
    ```
    {combined_code}
    ```
    """

    json_string_response = await get_chat_completion_response(prompt)
    try:
        return json.loads(json_string_response)
    except json.JSONDecodeError:
        print("ERROR: Failed to decode JSON from LLM response.")
        return {"error": "Invalid JSON response from LLM", "raw_response": json_string_response}


async def analyze_single_repo_async(client: httpx.AsyncClient, repo_data: dict) -> dict:
    file_extensions_to_analyze = ['.py', '.js', '.ts', '.java', '.go', '.rb', '.php', '.cs', '.c', '.cpp', '.h', '.hpp',
                                  'Dockerfile', 'docker-compose.yml']
    max_total_code_size = 300000

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

    combined_code_parts = []
    total_size = 0
    for file_path, content in zip(filtered_files, contents):
        if total_size > max_total_code_size:
            print(f"WARNING: Reached total code size limit for '{repo_name}'. Some files will be omitted.")
            break
        if content:
            file_header = f"--- START OF FILE: {file_path} ---\n"
            file_footer = f"\n--- END OF FILE: {file_path} ---\n\n"
            combined_code_parts.append(file_header + content + file_footer)
            total_size += len(content.encode('utf-8'))

    if not combined_code_parts:
        print(f"No suitable files found to analyze in '{repo_name}'.")
        return None

    combined_code_string = "".join(combined_code_parts)
    print(f"Total combined code size for '{repo_name}': {total_size / 1024:.2f} KB")

    print(f"  -> Sending combined code for '{repo_name}' to LLM for analysis...")
    analysis_result = await analyze_repo_code_with_llm(combined_code_string, repo_name)

    if "error" in analysis_result:
        print(f"Analysis failed for {repo_name}: {analysis_result.get('error')}")
        return None

    print(f"Analysis complete for: {repo_name}")
    return {
        "repo_name": repo_name,
        "repo_date": repo_date,
        "analysis": analysis_result
    }


async def git_crawling_analysis_parallel(target_username: str):
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("WARNING: GITHUB_TOKEN environment variable is not set. API requests will be severely rate-limited.")

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}"
    } if token else {"Accept": "application/vnd.github.v3+json"}

    max_repos_to_analyze = 5

    async with httpx.AsyncClient(headers=headers, timeout=50.0) as client:
        print(f"Fetching repositories for user '{target_username}'...")
        all_repos_data = await get_repos_with_api_async(client, target_username)

        if not all_repos_data:
            print("No repositories found.")
            return []

        all_repos_data.sort(key=lambda x: datetime.strptime(x['updated_at'], '%Y-%m-%dT%H:%M:%SZ'), reverse=True)
        print(f"Found and sorted {len(all_repos_data)} repositories. Analyzing top {max_repos_to_analyze}...")

        tasks = [
            analyze_single_repo_async(client, repo_data)
            for repo_data in all_repos_data[:max_repos_to_analyze]
        ]

        analysis_results = await asyncio.gather(*tasks)

        final_analysis_results = [result for result in analysis_results if result is not None]

    print("\n--- Analysis process finished ---")
    return final_analysis_results
