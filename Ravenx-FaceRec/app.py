from flask import Flask, request, jsonify
from PIL import Image, ImageEnhance
import cv2
import os
import time
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import logging

app = Flask(__name__)

# Initialize Google AI
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Setup logging
logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

def upload_to_gemini(path, mime_type=None):
    file = genai.upload_file(path, mime_type=mime_type)
    return file

def enhance_image(image_path):
    image = Image.open(image_path)
    enhancer = ImageEnhance.Contrast(image)
    enhanced_image = enhancer.enhance(2)  # Increase contrast
    enhanced_image.save(image_path)

def detect_face(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    return len(faces) > 0

def scrape_google_image_search(image_path):
    driver = webdriver.Chrome()
    driver.get('https://images.google.com/')
    search_box = driver.find_element(By.CSS_SELECTOR, 'input[type="file"]')
    search_box.send_keys(image_path)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    links = []
    for item in soup.select('a[jsname="hSRGPd"]'):
        title = item.get_text()
        url = item['href']
        links.append({'title': title, 'url': url})
    return links

def scrape_linkedin(image_path):
    # Implement LinkedIn scraping
    return [{'title': 'LinkedIn Profile 1', 'url': 'https://www.linkedin.com/in/example1'}]

def scrape_facebook(image_path):
    # Implement Facebook scraping
    return [{'title': 'Facebook Profile 1', 'url': 'https://www.facebook.com/profile.php?id=example1'}]

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})

    image = request.files['image']
    filename = os.path.join('uploads', image.filename)
    image.save(filename)

    # Enhance image and check for face
    enhance_image(filename)
    if not detect_face(filename):
        return jsonify({'success': False, 'message': 'No face detected in the image'})

    # Upload image to Gemini
    gemini_file = upload_to_gemini(filename, mime_type="image/jpeg")

    # Scrape Google, LinkedIn, and Facebook in parallel
    with ThreadPoolExecutor() as executor:
        google_future = executor.submit(scrape_google_image_search, filename)
        linkedin_future = executor.submit(scrape_linkedin, filename)
        facebook_future = executor.submit(scrape_facebook, filename)

        google_results = google_future.result()
        linkedin_results = linkedin_future.result()
        facebook_results = facebook_future.result()

    # Combine results
    results = google_results + linkedin_results + facebook_results

    return jsonify({'success': True, 'links': results})

if __name__ == '__main__':
    app.run(debug=True)
