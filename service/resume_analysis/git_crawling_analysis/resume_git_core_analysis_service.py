import os
import re
from typing import List

import httpx
import json
import asyncio
from datetime import datetime

from model.resume_analysis.resume_git_crawling_analysis import GithubAnalysisReport
from service.chat_completion.chat_completion_service import get_chat_completion_response, get_chat_completion_json
from service.resume_analysis.git_crawling_analysis.resume_git_single_repo_analysis_service import analyze_single_repo_async


async def git_resume_analysis(resume: str) -> List[GithubAnalysisReport]:
    github_username = await find_github_username_from_resume(resume)
    if not github_username:
        return []

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
        except Exception as e:
            print(f"ERROR: An error occurred while fetching repositories: {e}")
            break
    return repo_data_list


async def git_crawling_analysis_parallel(target_username: str) -> List[GithubAnalysisReport]:
    token = os.getenv('github_token_1')
    if not token:
        print("WARNING: github_token environment variable is not set. API requests will be severely rate-limited.")

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}"
    } if token else {"Accept": "application/vnd.github.v3+json"}

    max_repos_to_analyze = 10

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
