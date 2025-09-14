# FastAPI LLM Resume Analysis

This project uses a Large Language Model (LLM) to analyze a candidate's resume and GitHub repositories, providing a comprehensive evaluation of their skills and potential fit for a specific company
## How to Run

1.  **Set Environment Variables:**
    To run the application in your local environment, you need to set the following environment variables.

    ```bash
    export github_token_1="your_github_personal_access_token"
    export chat_gpt_api_key_1="your_openai_api_key"
    ```

    *Alternatively, you can hardcode your token and key directly in the source code.*

2.  **Start the Server:**
    Run the following command to start the FastAPI development server:

    ```bash
    fastapi dev main.py
    ```
3.  **Test the API:**
    You can access the interactive API documentation by navigating to `http://127.0.0.1:8000/docs` in your web browser. From this page, you can run resume analysis.

## Analysis Flow

The analysis is performed in three main stages:

1.  **Resume & Company Fit Analysis:**
    The system first analyzes the candidate's resume (PDF) to extract key information. Simultaneously, it crawls the provided job application link to understand the company's needs and requirements, evaluating the candidate's fit.

2.  **GitHub Repository Analysis:**
Next, it analyzes up to 10 (Configurable) of the candidate's public GitHub repositories. If a repository's codebase exceeds the language model's maximum token limit, it is broken down into smaller chunks. Each chunk is analyzed separately, and the results are then intelligently merged by the LLM into a single, cohesive report.
3.  **Comprehensive Candidate Report:**
    Finally, based on the results from the first two stages, the system generates a final, holistic diagnosis of the candidate. This report evaluates their potential beyond the surface level of a traditional resume.

## Performance Note

While many operations run in parallel to optimize for speed, there are inherent dependencies between the analysis stages (e.g., the final report requires the resume and GitHub analyses to be complete). Due to these dependencies, a full analysis typically takes **at least 3 minutes** to complete.