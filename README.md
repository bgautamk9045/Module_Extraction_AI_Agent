# Module_Extraction_AI_Agent

An AI-powered Streamlit application designed to crawl documentation websites, extract their content, and infer a structured representation of modules and submodules. This tool is particularly useful for understanding the hierarchical structure of large documentation sets.

## ✨ Features

* **Web Crawling:** Recursively crawls specified documentation URLs, respecting `robots.txt` (though not explicitly implemented in the provided code, it's a good practice for web scrapers) and politeness delays.
* **Content Extraction:** Uses BeautifulSoup to parse HTML and extract the main textual content from web pages, filtering out common non-content elements.
* **Module & Submodule Inference:** Heuristically infers modules and submodules based on HTML heading tags (H1, H2, H3) and surrounding paragraph text.
* **Interactive UI:** Built with Streamlit for an easy-to-use web interface.
* **JSON Output:** Provides the extracted hierarchical data in a clean JSON format, with a download option.
* **Domain Control:** Allows users to specify allowed domains for focused crawling.

## 🚀 Getting Started

Follow these instructions to set up and run the Module Extraction AI Agent on your local machine.

### Prerequisites

Before you begin, ensure you have the following installed:

* **Python 3.7+**
* **pip** (Python package installer)

### Installation

1.  **Clone the repository (or save the `app.py` file):**
    If this were a repository, you would clone it:
    ```bash
    git clone [https://github.com/your-username/module-extraction-ai-agent.git](https://github.com/your-username/module-extraction-ai-agent.git)
    cd module-extraction-ai-agent
    ```
    Since you provided the code as `app.py`, just save the provided code into a file named `app.py
    
2.  **Install the required Python packages:**
    ```
    streamlit
    requests
    beautifulsoup4
    ```
    Install these using pip

### Execution

To run the Streamlit application, navigate to the directory where `app.py` is located in your terminal and execute:

```bash
streamlit run app.py

### This is how the output is looking for one of the website that i have used for testing "https://fastapi.tiangolo.com/"

![image](https://github.com/user-attachments/assets/38342bc8-64d6-4438-9344-6205a00e037d)
