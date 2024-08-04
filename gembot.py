import os
import google.generativeai as genai
import logging
import asyncio
from typing import List, Dict
from pydantic_settings import BaseSettings  # Updated import
from crewai_tools import SerperDevTool  # Import SerperDevTool

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Settings(BaseSettings):
    api_key: str
    serper_api_key: str
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    max_output_tokens: int = 2048
    response_mime_type: str = "text/plain"

    class Config:
        env_file = ".env"

settings = Settings()

genai.configure(api_key=settings.api_key)

generation_config = {
    "temperature": settings.temperature,
    "top_p": settings.top_p,
    "top_k": settings.top_k,
    "max_output_tokens": settings.max_output_tokens,
    "response_mime_type": settings.response_mime_type,
}

# Define the model
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    generation_config=generation_config,
    safety_settings={
        genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
        genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
    }
)

# Initialize SerperDevTool
serper_tool = SerperDevTool(
    search_url="https://google.serper.dev/scholar",
    n_results=2,
)

class AdvancedChatbot:
    def __init__(self, model: genai.GenerativeModel, serper_tool: SerperDevTool):
        """
        Initialize the chatbot with a generative model and SerperDevTool.
        """
        self.model = model
        self.serper_tool = serper_tool
        self.history: List[Dict[str, str]] = []

    async def generate_response(self, user_input: str) -> str:
        """
        Generate a response based on user input and conversation history.
        """
        try:
            # Include history in the prompt
            context = "\n".join([f"User: {entry['user']}\nBot: {entry['bot']}" for entry in self.history])
            full_prompt = f"{context}\nUser: {user_input}\nBot:"
            
            # Generate a response using the model
            response = await asyncio.to_thread(self.model.generate_content, full_prompt)
            response_text = response.text
            
            # If the response is not satisfactory, use SerperDevTool to search the web
            if "Sorry, I encountered an error" in response_text or "I don't know" in response_text:
                search_results = self.serper_tool.run(search_query=user_input)
                response_text = self.process_search_results(search_results)
            
            # Update history
            self.history.append({'user': user_input, 'bot': response_text})
            return response_text
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return "Sorry, I encountered an error while generating a response."

    def process_search_results(self, search_results: Dict) -> str:
        """
        Process search results from SerperDevTool and generate a response.
        """
        try:
            # Extract relevant information from search results
            snippets = [result['snippet'] for result in search_results['results']]
            combined_snippets = " ".join(snippets)
            
            # Generate a response using the AI model
            response = self.model.generate_content(combined_snippets)
            return response.text
        except Exception as e:
            logging.error(f"An error occurred while processing search results: {e}")
            return "Sorry, I encountered an error while processing the search results."

    def clear_history(self) -> None:
        """
        Clear the conversation history.
        """
        self.history = []

    async def run(self) -> None:
        """
        Run the chatbot in an interactive loop.
        """
        print("#---Welcome To Gemini Pro Bot---#")
        print("---------------------------------")
        print("Chatbot is running. Type 'exit' to stop.")
        while True:
            user_input = input("\033[92mYou: \033[0m")  # Green color for user input
            if user_input.lower() == 'exit':
                break
            response = await self.generate_response(user_input)
            print("\033[94mBot:\033[0m", response)  # Blue color for bot response

if __name__ == "__main__":
    chatbot = AdvancedChatbot(model, serper_tool)
    asyncio.run(chatbot.run())
