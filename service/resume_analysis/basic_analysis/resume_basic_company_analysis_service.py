import requests
from bs4 import BeautifulSoup
from service.chat_completion.chat_completion_service import get_chat_completion_json, get_chat_completion_response
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time


def scrape_job_posting_text(url: str):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    options.add_argument(f'user-agent={user_agent}')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        print("Starting headless browser to scrape the URL...")
        driver.get(url)
        time.sleep(5)

        body_element = driver.find_element(By.TAG_NAME, 'body')
        return body_element.text

    except Exception as e:
        print(f"ERROR: Failed to scrape the URL {url} with Selenium. Error: {e}")
        return ""
    finally:
        driver.quit()


async def extract_job_requirements(application_link: str) -> str:
    print(f"Step 1: Scraping text from {application_link}")
    job_text = scrape_job_posting_text(application_link)

    if not job_text:
        print(f"Scraping error.")
        return ""

    job_text = "Find and extract the full, original text for specific sections from the provided job posting: \n" + job_text

    print("Step 2: Scraped text successfully. Sending to LLM for extraction")

    system_prompt_for_extraction = """
    You are a data extraction tool. 
    Your task is to find and extract the full, original text for specific sections from the provided job posting.
    Do not summarize, paraphrase, or alter the content in any way. Copy the text exactly as it appears.
    """

    extracted_data = await get_chat_completion_response(
        prompt=job_text,
        system_prompt=system_prompt_for_extraction
    )
    return extracted_data
