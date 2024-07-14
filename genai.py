import telebot
from PyPDF2 import PdfReader
from docx import Document
import os
import google.generativeai as genai
from telebot import types
import time

# Replace with your actual Telegram bot token
TELEGRAM_BOT_TOKEN = "7411755119:AAHDcbgRwQHV0drYEoaUzeKyq9Ho0BBWl00"

# Initialize the Telegram bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Ensure temporary directories exist
temp_image_dir = "temp_images"
temp_document_dir = "temp_documents"
os.makedirs(temp_image_dir, exist_ok=True)
os.makedirs(temp_document_dir, exist_ok=True)

# Configure the Google Gemini AI API
os.environ['API_KEY'] = 'AIzaSyB-05YFFZUp98cmLygYAP3dIJCXByBp_YY'
genai.configure(api_key=os.environ['API_KEY'])

# Define GenerativeModels for text and image generation (adjust settings if needed)
generation_config = {
    "temperature": 0.7,  # Adjust for creativity (higher = more creative)
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
    "response_mime_type": "text/plain",
}

text_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    safety_settings={
        genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
        genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
    }
)

image_model = genai.GenerativeModel(
    model_name="gemini-1.0-pro-vision-latest",
    generation_config=generation_config,
)

# Start a chat session
chat_session = text_model.start_chat(history=[])


# --- Helper Functions ---

def upload_to_gemini(path, mime_type=None):
    return genai.upload_file(path, mime_type=mime_type)


def query_gemini_text(text):
    response = chat_session.send_message(text)
    return response.text


def query_gemini_image(path):
    gemini_file = upload_to_gemini(path, mime_type="image/jpeg")
    prompt = [
        "Please provide a detailed description of the object in the image, including its possible uses and any notable features.",
        "Object: ",
        gemini_file,
    ]
    response = image_model.generate_content(prompt)
    return response.text


def wait_for_files_active(files):
    print("Waiting for file processing...")
    for file in files:
        while True:
            file_status = genai.get_file(file.name)
            if file_status.state.name == "ACTIVE":
                print(f"File {file.name} is ready.")
                break
            elif file_status.state.name == "PROCESSING":
                print(f"File {file.name} is still processing, waiting...")
                time.sleep(5)
            else:
                raise Exception(f"File {file.name} failed to process: {file_status.state.name}")
    print("All files are ready.")


# --- Task-Specific Functions ---

def generate_product_description(image_path, target_audience):
    gemini_file = upload_to_gemini(image_path, mime_type="image/jpeg")
    prompt = [
        "Given an image of a product and its target audience, write an engaging marketing description.",
        "Product Image: ",
        gemini_file,
        "Target Audience: ",
        target_audience,
        "Marketing Description: ",
    ]
    response = image_model.generate_content(prompt)
    return response.text


def generate_food_recipe(image_path):
    gemini_file = upload_to_gemini(image_path, mime_type="image/jpeg")
    prompt = [
        "Please analyze the food in the image and provide a recipe based on the analysis.",
        "Food Image: ",
        gemini_file,
    ]
    response = image_model.generate_content(prompt)
    return response.text


def generate_fashion_advice(image_path):
    gemini_file = upload_to_gemini(image_path, mime_type="image/jpeg")
    prompt = [
        "Analyze the outfit in this image and provide fashion advice, suggesting accessories that would complement the look.",
        "Outfit Image: ",
        gemini_file,
    ]
    response = image_model.generate_content(prompt)
    return response.text


def generate_decor_suggestions(image_path):
    gemini_file = upload_to_gemini(image_path, mime_type="image/jpeg")
    prompt = [
        "Analyze the room in this image and provide home decor suggestions to enhance the space.",
        "Room Image: ",
        gemini_file,
    ]
    response = image_model.generate_content(prompt)
    return response.text


def generate_document_summary(doc_path, doc_type="pdf"):
    if doc_type == "pdf":
        reader = PdfReader(doc_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    elif doc_type == "docx":
        doc = Document(doc_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    else:
        return "Unsupported document type."

    summary = query_gemini_text(f"Summarize the following document:\n{text}")
    return summary


# --- User Interaction Flow ---

# Global variable to track user's current task
CURRENT_TASK = None


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message,
                 "Welcome to the AI Bot! What can I help you with today?\n"
                 "Here are some things I can do:\n"
                 "- Get a product description (send an image)\n"
                 "- Get a food recipe (send an image)\n"
                 "- Get fashion advice (send an image)\n"
                 "- Get home decor suggestions (send an image)\n"
                 "- Get a summary of a PDF or DOCX document (upload the file)\n"
                 )


# Handle text messages from users
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global CURRENT_TASK

    if CURRENT_TASK is None:  # No task in progress
        if "product description" in message.text.lower():
            CURRENT_TASK = "product_description"
            bot.reply_to(message, "Great! Please upload an image of the product.")
        elif "food recipe" in message.text.lower():
            CURRENT_TASK = "food_recipe"
            bot.reply_to(message, "Yummy! Send me a picture of the food.")
        elif "fashion advice" in message.text.lower():
            CURRENT_TASK = "fashion_advice"
            bot.reply_to(message, "Show off your style! Upload a picture of your outfit.")
        elif "decor suggestions" in message.text.lower() or "home decor" in message.text.lower():
            CURRENT_TASK = "decor_suggestions"
            bot.reply_to(message, "Let's spruce things up! Send me a picture of the room.")
        elif "summary" in message.text.lower():
            CURRENT_TASK = "document_summary"
            bot.reply_to(message, "Please upload the PDF or DOCX document you want me to summarize.")
        else:
            bot.reply_to(message, "I didn't quite get that. What would you like to do?")
    else:  # Task is in progress - handle accordingly
        handle_task(message)


# Handle files uploaded by users (images or documents)
@bot.message_handler(content_types=['photo', 'document'])
def handle_file(message):
    global CURRENT_TASK
    try:
        if CURRENT_TASK is not None:
            if message.content_type == 'photo':
                file_id = message.photo[-1].file_id
                file_info = bot.get_file(file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                file_path = os.path.join(temp_image_dir, f"{file_id}.jpg")
                with open(file_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
                handle_task(message, file_path=file_path)
            elif message.content_type == 'document':
                file_id = message.document.file_id
                file_info = bot.get_file(file_id)
                downloaded_file = bot.download_file(file_info.file_path)

                if message.document.mime_type == 'application/pdf':
                    file_path = os.path.join(temp_document_dir, f"{file_id}.pdf")
                    doc_type = "pdf"
                elif message.document.mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                    file_path = os.path.join(temp_document_dir, f"{file_id}.docx")
                    doc_type = "docx"
                else:
                    bot.reply_to(message, "Unsupported document type. Please upload a PDF or DOCX.")
                    CURRENT_TASK = None
                    return

                with open(file_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
                handle_task(message, file_path=file_path, doc_type=doc_type)
        else:
            bot.reply_to(message, "What would you like to do with this file?")
    except Exception as e:
        bot.reply_to(message, f"Error processing the file: {str(e)}")
        CURRENT_TASK = None


# Function to handle tasks based on user input and context
def handle_task(message, file_path=None, doc_type=None):
    global CURRENT_TASK

    if CURRENT_TASK == "product_description":
        if file_path is not None:
            bot.reply_to(message, "Got it! Now, tell me who the target audience for this product is.")
            bot.register_next_step_handler(message, lambda msg: handle_target_audience(msg, file_path))
        else:
            bot.reply_to(message, "Please upload an image of the product.")

    elif CURRENT_TASK == "food_recipe" and file_path is not None:
        bot.reply_to(message, "Let me see what I can cook up...")
        recipe = generate_food_recipe(file_path)
        bot.reply_to(message, recipe)
        CURRENT_TASK = None

    elif CURRENT_TASK == "fashion_advice" and file_path is not None:
        bot.reply_to(message, "Analyzing your style...")
        advice = generate_fashion_advice(file_path)
        bot.reply_to(message, advice)
        CURRENT_TASK = None

    elif CURRENT_TASK == "decor_suggestions" and file_path is not None:
        bot.reply_to(message, "Let's add some flair...")
        suggestions = generate_decor_suggestions(file_path)
        bot.reply_to(message, suggestions)
        CURRENT_TASK = None

    elif CURRENT_TASK == "document_summary" and file_path is not None:
        bot.reply_to(message, "Summarizing the document...")
        summary = generate_document_summary(file_path, doc_type)
        bot.reply_to(message, summary)
        CURRENT_TASK = None


def handle_target_audience(message, file_path):
    global CURRENT_TASK
    target_audience = message.text
    bot.reply_to(message, "Generating a product description...")
    description = generate_product_description(file_path, target_audience)
    bot.reply_to(message, description)
    CURRENT_TASK = None


# Start the bot
bot.polling(none_stop=True)
