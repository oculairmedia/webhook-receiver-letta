import os
import logging
from dotenv import load_dotenv
from cerebras.cloud.sdk import Cerebras, CerebrasError

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging for this module
logger = logging.getLogger(__name__)

class CerebrasQwenClient:
    """
    A client to interact with the Cerebras Qwen model via the Cerebras Cloud SDK.
    """
    DEFAULT_MODEL = "qwen-3-32b"
    # The API key provided by the user in the initial request.
    # For production, this should ideally be in a secure vault or environment variable
    # accessible ONLY to the server-side application, not committed to frontend/client-side code.
    # The code prioritizes the CEREBRAS_API_KEY environment variable.
    # Example API Key (for reference, ensure it's set as an env var): csk-vwwe8jynnn8mkrxhy253r9f3n52j25dpjjd998fr44c9wd32

    def __init__(self, api_key: str = None, model: str = None):
        """
        Initializes the Cerebras client.

        Args:
            api_key: The Cerebras API key. If None, attempts to read from
                     the CEREBRAS_API_KEY environment variable.
            model: The model ID to use (e.g., "qwen-3-32b"). Defaults to Qwen.
        
        Raises:
            ValueError: If the API key is not provided or found.
        """
        self.api_key = api_key or os.environ.get("CEREBRAS_API_KEY")
        if not self.api_key:
            error_msg = "Cerebras API key not provided and CEREBRAS_API_KEY environment variable not set."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.model = model or self.DEFAULT_MODEL
        
        try:
            self.client = Cerebras(api_key=self.api_key)
            logger.info(f"Cerebras client initialized for model: {self.model}")
        except CerebrasError as e:
            logger.error(f"Failed to initialize Cerebras client: {e}")
            raise

    def generate_chat_completion(self, messages: list, max_tokens: int = 500, temperature: float = 0.7, response_format: dict = None):
        """
        Generates a chat completion using the configured Qwen model.

        Args:
            messages: A list of messages comprising the conversation so far.
                      Example: [{"role": "user", "content": "Hello!"}]
            max_tokens: The maximum number of tokens to generate.
            temperature: Sampling temperature.
            response_format: Optional. Controls the format of the model response, e.g., for JSON schema.
                             Example: { "type": "json_schema", "json_schema": { "name": "schema_name", "strict": true, "schema": {...} } }


        Returns:
            A dictionary containing:
                "content": The content of the assistant's message (str|None).
                "usage": A dictionary with token counts (prompt_tokens, completion_tokens, total_tokens),
                         or None if usage info is not available.
        
        Raises:
            CerebrasError: If the API call fails.
        """
        try:
            logger.debug(f"Sending chat completion request to model {self.model} with messages: {messages}")
            
            completion_params = {
                "messages": messages,
                "model": self.model,
                "max_completion_tokens": max_tokens,
                "temperature": temperature,
            }
            if response_format:
                completion_params["response_format"] = response_format

            chat_completion = self.client.chat.completions.create(**completion_params)
            
            logger.debug(f"Received chat completion response: {chat_completion}")

            message_content = None
            usage_info = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }

            if chat_completion.choices and len(chat_completion.choices) > 0:
                message_content = chat_completion.choices[0].message.content.strip() if chat_completion.choices[0].message else None
            else:
                logger.warning("Chat completion returned no choices.")

            if hasattr(chat_completion, 'usage') and chat_completion.usage:
                usage_info["prompt_tokens"] = chat_completion.usage.prompt_tokens if hasattr(chat_completion.usage, 'prompt_tokens') else 0
                usage_info["completion_tokens"] = chat_completion.usage.completion_tokens if hasattr(chat_completion.usage, 'completion_tokens') else 0
                usage_info["total_tokens"] = chat_completion.usage.total_tokens if hasattr(chat_completion.usage, 'total_tokens') else 0
                logger.debug(f"Token usage: {usage_info}")
            else:
                logger.warning("No usage information found in chat completion response.")
            
            return {
                "content": message_content,
                "usage": usage_info
            }
            
        except CerebrasError as e:
            logger.error(f"Cerebras API error during chat completion: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during chat completion: {e}")
            raise CerebrasError(f"Unexpected error: {e}")


if __name__ == '__main__':
    # Example Usage (requires CEREBRAS_API_KEY to be set in environment)
    # You would set it in your shell:
    # export CEREBRAS_API_KEY='your_api_key_here' 
    # For Windows (cmd.exe): set CEREBRAS_API_KEY=your_api_key_here
    # For Windows (PowerShell): $env:CEREBRAS_API_KEY="your_api_key_here"

    logging.basicConfig(level=logging.DEBUG)
    
    # load_dotenv() is called at the top of the module.
    
    api_key_env = os.environ.get("CEREBRAS_API_KEY")
    if not api_key_env:
        print("Please set the CEREBRAS_API_KEY environment variable to run this example.")
        print("Example: export CEREBRAS_API_KEY='your_api_key_here'")
    else:
        print(f"Attempting to use CEREBRAS_API_KEY: {api_key_env[:5]}...")
        try:
            qwen_client = CerebrasQwenClient()
            
            # Test 1: Simple chat
            print("\n--- Test 1: Simple Chat ---")
            messages_simple = [{"role": "user", "content": "Why is fast inference important for LLMs? /no_think"}]
            response_simple = qwen_client.generate_chat_completion(messages=messages_simple)
            print(f"Qwen Response (Simple): {response_simple}")

            # Test 2: Structured output (example schema)
            print("\n--- Test 2: Structured Output (JSON Schema) ---")
            messages_structured = [
                {"role": "system", "content": "You are a helpful assistant that extracts information into JSON."},
                {"role": "user", "content": "Extract the name and age from this sentence: John Doe is 30 years old."}
            ]
            json_schema_def = { # Renamed to avoid conflict
                "name": "user_details",
                "strict": True, 
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "The person's name"},
                        "age": {"type": "integer", "description": "The person's age"}
                    },
                    "required": ["name", "age"]
                }
            }
            response_format_structured = {"type": "json_schema", "json_schema": json_schema_def}
            
            response_structured = qwen_client.generate_chat_completion(
                messages=messages_structured,
                response_format=response_format_structured,
                temperature=0.2 
            )
            print(f"Qwen Response (Structured JSON): {response_structured}")
            
            if response_structured and response_structured.get("content"):
                import json # Moved import here
                try:
                    parsed_json = json.loads(response_structured["content"])
                    print(f"Parsed JSON: {parsed_json}")
                except json.JSONDecodeError as jde:
                    print(f"Failed to parse structured response content as JSON: {response_structured.get('content')}. Error: {jde}")
            elif response_structured:
                print(f"Structured response content is None or empty: {response_structured.get('content')}")
            else:
                print("No structured response received.")

        except ValueError as ve:
            print(f"Initialization Error: {ve}")
        except CerebrasError as ce:
            print(f"Cerebras API Error: {ce}")
        except Exception as ex:
            print(f"An unexpected error occurred: {ex}")