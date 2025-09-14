import asyncio

import httpx


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

    except Exception as e:
        print(f"ERROR: Could not fetch repository contents for path '{path}': {e}")
    return files
