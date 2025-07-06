# app.py (main Streamlit file)

import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import time
from collections import deque
import re

# --- Configuration ---
ALLOWED_DOMAINS = ["fastapi.tiangolo.com"] # Customize as needed
CRAWL_DELAY = 0.5 # seconds

# --- Helper Functions (Core Logic) ---

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def get_domain(url):
    return urlparse(url).netloc

def extract_content(soup):
    """
    Extracts the main content from a BeautifulSoup object for FastAPI documentation.
    """
    # Inspect FastAPI's HTML. The main content is usually within a div with class 'md-content'
    # or sometimes directly in a <article> tag.
    main_content_div = soup.find('div', class_='md-content') # This is often the key container
    if main_content_div:
        # Also try to find the article within it, sometimes helps to narrow down
        main_content = main_content_div.find('article', class_='md-content__inner') # This is more specific
        if not main_content: # Fallback if specific article not found inside md-content
            main_content = main_content_div

    if main_content:
        # Remove known non-content elements that might appear within the main content area
        # For FastAPI, you might see nav elements, tables of contents, or ad-like elements
        # within the main content div that you want to exclude.
        # Common elements to remove: header, footer, nav, aside, script, style, form
        # You might also want to remove 'md-toc' or similar table of contents if they are within main_content.
        for unwanted_tag in main_content(['header', 'footer', 'nav', 'aside', 'script', 'style', 'form', 'div[data-md-component="toc"]', 'nav.md-toc']):
             unwanted_tag.decompose()
        return main_content.get_text(separator='\n', strip=True)
    return soup.get_text(separator='\n', strip=True) # Fallback

def crawl_and_extract(start_urls, max_pages=50): # Added max_pages to prevent excessive crawling
    all_extracted_text = {} # Stores URL -> extracted text
    queue = deque(start_urls)
    visited = set()
    
    st.info(f"Starting crawl from: {', '.join(start_urls)}")
    progress_bar = st.progress(0)
    pages_crawled = 0

    while queue and pages_crawled < max_pages:
        current_url = queue.popleft()

        if current_url in visited:
            continue
        
        # Ensure we only crawl within the allowed domains
        if get_domain(current_url) not in ALLOWED_DOMAINS:
            st.warning(f"Skipping {current_url} - outside allowed domains.")
            continue

        visited.add(current_url)
        pages_crawled += 1
        st.write(f"Crawling: {current_url} ({pages_crawled}/{max_pages})")
        progress_bar.progress(pages_crawled / max_pages)

        try:
            response = requests.get(current_url, timeout=10)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract main content
            content = extract_content(soup)
            all_extracted_text[current_url] = content

            # Find new links to crawl
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(current_url, href)
                if is_valid_url(absolute_url) and get_domain(absolute_url) in ALLOWED_DOMAINS and absolute_url not in visited:
                    # Basic filtering for relevant links (e.g., avoid direct file downloads)
                    if not any(ext in absolute_url for ext in ['.pdf', '.zip', '.png', '.jpg']):
                        queue.append(absolute_url)
            
            time.sleep(CRAWL_DELAY) # Be polite
        except requests.exceptions.RequestException as e:
            st.error(f"Error crawling {current_url}: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred with {current_url}: {e}")
    
    progress_bar.progress(1.0)
    st.success(f"Finished crawling. Visited {len(visited)} pages.")
    return all_extracted_text

def infer_modules_and_submodules(extracted_content_map):
    """
    Infers modules and submodules from the extracted text content.
    This is a heuristic-based approach. For more robust results,
    consider NLP techniques (like spaCy for dependency parsing, or
    sentence transformers for semantic similarity).
    """
    modules_data = []
    
    # Combine all content into a single string for easier processing
    # In a real scenario, you'd process page by page and link modules across pages.
    # For simplicity here, we'll concatenate for a first pass.
    full_text = "\n\n".join(extracted_content_map.values())

    # Split content by major headings to find modules
    # This regex looks for lines that might be headings (uppercase, start of line, etc.)
    # You'll need to adapt this based on actual heading patterns on the target site.
    # For help.instagram.com, inspect their H1, H2, H3 tags.
    
    # A more robust approach would be to parse headings from the BeautifulSoup objects directly,
    # maintaining their hierarchy. Let's adjust extract_content to yield structured data instead of just text.

    # Re-designing the content extraction for better module/submodule inference
    structured_content_by_url = {}
    for url, raw_content in extracted_content_map.items():
        # This is a simplified re-extraction. In a full solution, you'd want to
        # do this during the initial `extract_content` phase with the BeautifulSoup object.
        soup = BeautifulSoup(raw_content, 'html.parser') # Re-parse the extracted text as if it were HTML
        
        # Example: Find all h2s and then subsequent h3s and paragraphs
        current_module = None
        for element in soup.find_all(['h1', 'h2', 'h3', 'p']):
            if element.name == 'h1':
                # Potentially a new product or major category
                pass
            elif element.name == 'h2':
                # This could be a module
                module_name = element.get_text(strip=True)
                current_module = {
                    "module": module_name,
                    "description": "", # Will fill this from subsequent paragraphs
                    "submodules": {}
                }
                modules_data.append(current_module)
            elif element.name == 'h3' and current_module:
                # This could be a submodule
                submodule_name = element.get_text(strip=True)
                current_module["submodules"][submodule_name] = "" # Will fill this from subsequent paragraphs
            elif element.name == 'p':
                # Assign paragraph text to the most recently active module/submodule
                if current_module:
                    if not current_module["description"]:
                        current_module["description"] = element.get_text(strip=True)
                    else:
                        # If a submodule is active, append to its description
                        last_submodule_key = list(current_module["submodules"].keys())[-1] if current_module["submodules"] else None
                        if last_submodule_key:
                            if not current_module["submodules"][last_submodule_key]:
                                current_module["submodules"][last_submodule_key] = element.get_text(strip=True)
                            else:
                                current_module["submodules"][last_submodule_key] += " " + element.get_text(strip=True)
                        else:
                            # If no submodule, and description already exists, append to module description
                            current_module["description"] += " " + element.get_text(strip=True)
    
    # Post-processing: Clean up descriptions (e.g., remove excessive newlines)
    for module in modules_data:
        module["description"] = re.sub(r'\s+', ' ', module["description"]).strip()
        for sub_key, sub_desc in module["submodules"].items():
            module["submodules"][sub_key] = re.sub(r'\s+', ' ', sub_desc).strip()

    # Basic filtering for empty descriptions/modules (might need more sophisticated logic)
    final_modules_data = []
    for module in modules_data:
        if module["description"] or module["submodules"]:
            final_modules_data.append(module)

    return final_modules_data


# --- Streamlit UI ---

st.set_page_config(layout="wide", page_title="Module Extraction AI Agent")

st.title("Module Extraction AI Agent")
st.write("Extracts structured module and submodule information from documentation websites.")

input_urls_str = st.text_area(
    "Enter one or more documentation URLs (separated by commas or newlines):",
    "https://help.instagram.com/",
    height=100
)

# Allow user to specify allowed domains if they want to override the default
st.markdown("---")
st.subheader("Advanced Settings (Optional)")
custom_domains_str = st.text_input(
    "Enter allowed domains for crawling (comma-separated, e.g., help.example.com):",
    ", ".join(ALLOWED_DOMAINS)
)
if custom_domains_str:
    ALLOWED_DOMAINS[:] = [d.strip() for d in custom_domains_str.split(',') if d.strip()]
    st.info(f"Allowed domains set to: {', '.join(ALLOWED_DOMAINS)}")
else:
    st.info(f"Using default allowed domains: {', '.join(ALLOWED_DOMAINS)}")

st.markdown("---")


if st.button("Extract Modules"):
    input_urls = [url.strip() for url in re.split(r'[,\n]+', input_urls_str) if url.strip()]
    
    if not input_urls:
        st.warning("Please enter at least one URL.")
    else:
        invalid_urls = [url for url in input_urls if not is_valid_url(url)]
        if invalid_urls:
            st.error(f"Invalid URL(s) detected: {', '.join(invalid_urls)}")
        else:
            st.subheader("Crawling and Content Extraction")
            with st.spinner("Crawling documentation... This may take a while for large sites."):
                extracted_content = crawl_and_extract(input_urls)
            
            if extracted_content:
                st.subheader("Module and Submodule Inference")
                with st.spinner("Inferring modules and submodules..."):
                    result_data = infer_modules_and_submodules(extracted_content)
                
                if result_data:
                    st.subheader("Extracted Modules (JSON Output)")
                    st.json(result_data)
                    
                    st.download_button(
                        label="Download JSON Output",
                        data=json.dumps(result_data, indent=2),
                        file_name="extracted_modules.json",
                        mime="application/json"
                    )
                else:
                    st.warning("No modules or submodules could be inferred from the extracted content.")
            else:
                st.error("Failed to extract any content from the provided URLs.")