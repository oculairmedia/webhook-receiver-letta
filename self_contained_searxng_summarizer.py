import json
import requests
import os
import sys
import uuid
import logging # For Cerebras client and general logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Embedded CerebrasQwenClient Start ---
# Original imports for CerebrasQwenClient that are still needed:
# import os # Already imported above
# import logging # Already imported above
# from dotenv import load_dotenv # NOT NEEDED for self-contained version
from cerebras.cloud.sdk import Cerebras, CerebrasError # This needs cerebras-cloud-sdk installed

# Configure basic logging if Qwen client relies on it.
# This will be used by the embedded client's logger.
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())
script_logger = logging.getLogger(__name__) # Logger for this script

class EmbeddedCerebrasQwenClient:
    """
    A client to interact with the Cerebras Qwen model via the Cerebras Cloud SDK.
    Self-contained version with hardcoded API key.
    """
    DEFAULT_MODEL = "qwen-3-32b"
    HARDCODED_API_KEY = "csk-vwwe8jynnn8mkrxhy253r9f3n52j25dpjjd998fr44c9wd32"

    def __init__(self, model: str = None):
        """
        Initializes the Cerebras client with a hardcoded API key.
        Args:
            model: The model ID to use (e.g., "qwen-3-32b"). Defaults to Qwen.
        Raises:
            ValueError: If the hardcoded API key is somehow empty (should not happen).
        """
        self.api_key = self.HARDCODED_API_KEY
        if not self.api_key:
            # This case should ideally not be reached with a hardcoded key
            error_msg = "Hardcoded Cerebras API key is empty."
            script_logger.error(error_msg) # Use script_logger
            raise ValueError(error_msg)
        
        self.model = model or self.DEFAULT_MODEL
        
        try:
            self.client = Cerebras(api_key=self.api_key)
            script_logger.info(f"EmbeddedCerebrasQwenClient initialized for model: {self.model} using hardcoded API key.")
        except CerebrasError as e:
            script_logger.error(f"Failed to initialize EmbeddedCerebrasQwenClient: {e}")
            raise
        except Exception as e: # Catch any other SDK init errors
            script_logger.error(f"Unexpected error initializing EmbeddedCerebrasQwenClient: {e}")
            # Wrap in CerebrasError or a custom error if preferred for consistency
            raise CerebrasError(f"Unexpected SDK init error: {e}")


    def generate_chat_completion(self, messages: list, max_tokens: int = 500, temperature: float = 0.7, response_format: dict = None):
        """
        Generates a chat completion using the configured Qwen model.
        """
        try:
            script_logger.debug(f"Sending chat completion request to model {self.model} with messages: {messages}")
            
            completion_params = {
                "messages": messages,
                "model": self.model,
                "max_completion_tokens": max_tokens,
                "temperature": temperature,
            }
            if response_format:
                completion_params["response_format"] = response_format

            chat_completion = self.client.chat.completions.create(**completion_params)
            
            script_logger.debug(f"Received chat completion response: {chat_completion}")

            message_content = None
            usage_info = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }

            if chat_completion.choices and len(chat_completion.choices) > 0:
                message_content = chat_completion.choices[0].message.content.strip() if chat_completion.choices[0].message else None
            else:
                script_logger.warning("Chat completion returned no choices.")

            if hasattr(chat_completion, 'usage') and chat_completion.usage:
                usage_info["prompt_tokens"] = chat_completion.usage.prompt_tokens if hasattr(chat_completion.usage, 'prompt_tokens') else 0
                usage_info["completion_tokens"] = chat_completion.usage.completion_tokens if hasattr(chat_completion.usage, 'completion_tokens') else 0
                usage_info["total_tokens"] = chat_completion.usage.total_tokens if hasattr(chat_completion.usage, 'total_tokens') else 0
                script_logger.debug(f"Token usage: {usage_info}")
            else:
                script_logger.warning("No usage information found in chat completion response.")
            
            return {
                "content": message_content,
                "usage": usage_info
            }
            
        except CerebrasError as e:
            script_logger.error(f"Cerebras API error during chat completion: {e}")
            raise 
        except Exception as e:
            script_logger.error(f"Unexpected error during chat completion: {e}")
            raise CerebrasError(f"Unexpected error: {e}")
# --- Embedded CerebrasQwenClient End ---

def search_searxng_with_llm_summary(query: str) -> str: # Renamed function
    """
    Perform a search against SearxNG, summarize results with an LLM, and provide tool metadata.
    """
    if query == "__tool_info__":
        info = {
            "name": "search_searxng_with_llm_summary", # Updated name
            "description": "Perform a search using SearxNG and summarize top results with Cerebras Qwen LLM.",
            "args": {
                "query": {
                    "type": "string",
                    "description": "The search query or __tool_info__",
                    "required": True
                }
            }
        }
        return json.dumps(info)

    if not query:
        return json.dumps({"error": "Query cannot be empty"})

    base_url = os.environ.get("SEARXNG_BASE_URL", "http://192.168.50.90:8287")
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    search_params = {'q': query, 'format': 'json'}

    try:
        response = session.get(f"{base_url}/search", params=search_params, timeout=10)
        response.raise_for_status()
        raw_results = response.json()

        llm_compressed_summary = "LLM summary not generated (Cerebras client error or no results)."
        search_results_text_for_llm = ""
        # Summarize top 5 results
        for item in raw_results.get('results', [])[:5]: 
            title = item.get('title', 'No Title')
            snippet = item.get('content', 'No Snippet') # SearxNG uses 'content' for snippet
            search_results_text_for_llm += f"Title: {title}\nSnippet: {snippet}\n\n"

        if not search_results_text_for_llm.strip():
            llm_compressed_summary = "No search results provided to LLM for summarization."
        else:
            try:
                qwen_client = EmbeddedCerebrasQwenClient() # Uses hardcoded key
                
                qwen_messages = [
                    {"role": "system", "content": "You are an AI assistant skilled at creating concise, neutral summaries of web search results. Extract only the key factual information. Focus on summarizing the provided snippets."},
                    {"role": "user", "content": f"Please provide a very concise summary of the key information from the following web search result snippets. Present it as a brief, neutral overview. Do not refer to the summarization task itself, just provide the summary of the content:\n\n{search_results_text_for_llm}"}
                ]
                
                script_logger.debug(f"Sending to Qwen for summarization: {json.dumps(qwen_messages, indent=2)}")

                qwen_response = qwen_client.generate_chat_completion(
                    messages=qwen_messages, 
                    max_tokens=250, 
                    temperature=0.3
                )
                
                if qwen_response and qwen_response.get("content"):
                    llm_compressed_summary = qwen_response["content"].strip()
                    script_logger.info(f"LLM Summary generated: {llm_compressed_summary[:100]}...")
                else:
                    llm_compressed_summary = "LLM summary generation failed or returned no content."
                    script_logger.warning("Cerebras Qwen client did not return content for summary.")
            
            except CerebrasError as ce:
                llm_compressed_summary = f"LLM Error: {str(ce)}"
                script_logger.error(f"Cerebras API error during summary generation - {str(ce)}")
            except Exception as e: 
                llm_compressed_summary = f"LLM Error: Unexpected error ({type(e).__name__}) - {str(e)}"
                script_logger.error(f"Unexpected error during LLM summary generation - {str(e)}")

        block_id = str(uuid.uuid4())
        block_label = f"research_cache_{block_id}"
        # These might still be useful if the webhook expects them, or for logging
        conversation_id = os.environ.get("CONVERSATION_ID", "unknown_conversation_id")
        turn_count = int(os.environ.get("TURN_COUNT", "0"))

        cache_data = {
            'query': query,
            'timestamp': raw_results.get('search_time', ''),
            'raw_results': raw_results,
            'llm_summary': llm_compressed_summary,
            'block_label': block_label,
            'conversationId': conversation_id,
            'turnCount': turn_count
        }

        try:
            webhook_url = os.environ.get("RESEARCH_WEBHOOK_URL", 'http://100.81.139.20:5006/process-research')
            webhook_response = requests.post(webhook_url, json=cache_data, timeout=10)
            webhook_response.raise_for_status()

            formatted_top_results = []
            for item in raw_results.get('results', [])[:3]:
                formatted_top_results.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', '')
                })

            return json.dumps({
                'llm_summary': llm_compressed_summary,
                'top_results_preview': formatted_top_results,
                'total_results': len(raw_results.get('results', [])),
                'block_reference': block_label,
                'cache_status': 'stored_and_processed'
            })

        except requests.RequestException as webhook_err:
            script_logger.warning(f"Failed to store/process results via webhook - {str(webhook_err)}")
            
            fallback_formatted_results = []
            for item in raw_results.get('results', [])[:10]:
                fallback_formatted_results.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'content': item.get('content', '')[:150] + '...'
                })

            return json.dumps({
                'llm_summary': llm_compressed_summary,
                'results_preview': fallback_formatted_results,
                'total_results': len(raw_results.get('results', [])),
                'shown_results_preview': len(fallback_formatted_results),
                'cache_status': 'fallback_raw_results_returned'
            })

    except requests.RequestException as e:
        return json.dumps({"error": f"SearxNG Network or HTTP error - {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"SearxNG Unexpected error - {str(e)}"})

if __name__ == "__main__":
    # This script now requires 'cerebras-cloud-sdk' to be installed.
    # Example: pip install cerebras-cloud-sdk requests
    
    # For testing, SEARXNG_BASE_URL and RESEARCH_WEBHOOK_URL can be set as env vars
    # or defaults will be used. The Cerebras API key is hardcoded.
    
    print(f"--- Testing Tool Info ---")
    tool_info = search_searxng_with_llm_summary("__tool_info__")
    print(tool_info)
    
    test_query = "latest advancements in quantum computing"
    print(f"\n--- Testing SearxNG with LLM summary for query: '{test_query}' ---")
    # Set a higher log level for testing if desired, e.g., logging.getLogger().setLevel(logging.DEBUG)
    result = search_searxng_with_llm_summary(test_query)
    print("\nFormatted result with LLM summary:")
    try:
        parsed_result = json.loads(result)
        print(json.dumps(parsed_result, indent=2))
    except json.JSONDecodeError:
        print("Error: Result was not valid JSON.")
        print(result)

    test_query_empty = ""
    print(f"\n--- Testing with empty query: '{test_query_empty}' ---")
    result_empty = search_searxng_with_llm_summary(test_query_empty)
    print(result_empty)
    
    # Test with a query that might yield few results
    test_query_obscure = "supercalifragilisticexpialidocious etymology obscure details"
    print(f"\n--- Testing SearxNG with LLM summary for obscure query: '{test_query_obscure}' ---")
    result_obscure = search_searxng_with_llm_summary(test_query_obscure)
    print("\nFormatted result for obscure query:")
    try:
        parsed_result_obscure = json.loads(result_obscure)
        print(json.dumps(parsed_result_obscure, indent=2))
    except json.JSONDecodeError:
        print("Error: Obscure query result was not valid JSON.")
        print(result_obscure)