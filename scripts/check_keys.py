import os
from dotenv import load_dotenv

load_dotenv()

print('Checking LLM API keys:')
openai_key = os.getenv('OPENAI_API_KEY')
anthropic_key = os.getenv('ANTHROPIC_API_KEY')

print(f'  OPENAI_API_KEY: {"set" if openai_key else "NOT SET"}')
print(f'  ANTHROPIC_API_KEY: {"set" if anthropic_key else "NOT SET"}')