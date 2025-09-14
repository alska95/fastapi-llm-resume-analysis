import asyncio
import base64

import httpx


async def get_file_content_async(client: httpx.AsyncClient, owner: str, repo: str, path: str) -> str:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"

    try:
        response = await client.get(api_url)
        response.raise_for_status()

        file_data = response.json()

        if 'content' in file_data and file_data.get('encoding') == 'base64':
            encoded_content = file_data['content']

            decoded_bytes = base64.b64decode(encoded_content)

            return decoded_bytes.decode('utf-8')
        else:
            print(f"Warning: No 'content' or unsupported encoding for file {path}")
            return None

    except httpx.HTTPStatusError as e:
        print(f"Error fetching file content for '{path}': {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching '{path}': {e}")
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
