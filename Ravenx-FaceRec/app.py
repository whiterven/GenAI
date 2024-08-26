from flask import Flask, request, jsonify
from PIL import Image, ImageEnhance
import os
import time
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import face_recognition  # Using face_recognition instead of OpenCV for face detection
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
    # Use face_recognition library for face detection
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    return len(face_locations) > 0


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
    # Implement LinkedIn scraping using Selenium
    driver = webdriver.Chrome()
    driver.get('https://www.linkedin.com/')
    time.sleep(3)

    # Assume user is already logged in or login steps are implemented
    search_box = driver.find_element(By.CSS_SELECTOR, 'input[placeholder="Search"]')
    search_box.send_keys('Image Search')
    search_box.submit()
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    # Extract LinkedIn profiles
    profiles = []
    for item in soup.select('a[href*="/in/"]'):
        title = item.get_text()
        url = item['href']
        profiles.append({'title': title, 'url': url})
    return profiles


def scrape_facebook(image_path):
    # Implement Facebook scraping using Selenium
    driver = webdriver.Chrome()
    driver.get('https://www.facebook.com/')
    time.sleep(3)

    # Assume user is already logged in or login steps are implemented
    search_box = driver.find_element(By.CSS_SELECTOR, 'input[placeholder="Search"]')
    search_box.send_keys('Image Search')
    search_box.submit()
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    # Extract Facebook profiles
    profiles = []
    for item in soup.select('a[href*="facebook.com/profile.php?id="]'):
        title = item.get_text()
        url = item['href']
        profiles.append({'title': title, 'url': url})
    return profiles


# Updated upload function to include logging and error handling
@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        logging.error("No file uploaded")
        return jsonify({'success': False, 'message': 'No file uploaded'})

    try:
        image = request.files['image']
        filename = os.path.join('uploads', image.filename)
        image.save(filename)

        logging.info(f"Image uploaded: {filename}")

        # Enhance image and check for face
        enhance_image(filename)
        if not detect_face(filename):
            logging.warning(f"No face detected in image: {filename}")
            return jsonify({'success': False, 'message': 'No face detected in the image'})

        # Upload image to Gemini
        gemini_file = upload_to_gemini(filename, mime_type="image/jpeg")
        logging.info(f"Image uploaded to Gemini: {filename}")

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

        logging.info(f"Search completed for image: {filename}")
        return jsonify({'success': True, 'links': results})

    except Exception as e:
        logging.error(f"Error processing image: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred during processing'})


if __name__ == '__main__':
    app.run(debug=True)