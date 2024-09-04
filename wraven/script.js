// Import required Firebase modules
import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.22.1/firebase-app.js';
import { getAuth, signInAnonymously } from 'https://www.gstatic.com/firebasejs/9.22.1/firebase-auth.js';
import { getFirestore, collection, addDoc, serverTimestamp, query, orderBy, limit, onSnapshot } from 'https://www.gstatic.com/firebasejs/9.22.1/firebase-firestore.js';

// Firebase configuration
const firebaseConfig = {
  // Your Firebase configuration object goes here
  apiKey: "AIzaSyDYPftGpXA9JOC0H3DpZB39Rjmi7zQoT60",
  authDomain: "raven-66a9c.firebaseapp.com",
  projectId: "raven-66a9c",
  storageBucket: "raven-66a9c.appspot.com",
  messagingSenderId: "874389474153",
  appId: "1:874389474153:web:d5e379fba5a642bf038bf8",
  measurementId: "G-L0MK8DVLHP"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

// Configuration
const GEMINI_API_KEY = 'AIzaSyC7rRzi3oeNbDPGr7g_-QyJVOHFwIDkZQo';
const SERPER_API_KEY = '6cb5adbbf344d229c4be55e7789e3b1004583cd7';

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const featureButtons = document.querySelectorAll('.feature-button');

// Event Listeners
sendButton.addEventListener('click', handleUserInput);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleUserInput();
    }
});

featureButtons.forEach(button => {
    button.addEventListener('click', () => {
        const feature = button.dataset.feature;
        userInput.value = `Use ${feature} to find information about `;
        userInput.focus();
    });
});

// Sign in anonymously
signInAnonymously(auth).catch((error) => {
  console.error("Error signing in:", error);
});

// Main function to handle user input
async function handleUserInput() {
    const userMessage = userInput.value.trim();
    if (userMessage === '') return;

    addMessageToChat('user', userMessage);
    userInput.value = '';

    const botResponse = await generateBotResponse(userMessage);
    addMessageToChat('bot', botResponse);

    // Save the conversation to Firestore
    await saveConversation(userMessage, botResponse);
}

// Function to add messages to the chat
function addMessageToChat(sender, message) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', `${sender}-message`);
    messageElement.textContent = message;
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Function to generate bot response
async function generateBotResponse(userMessage) {
    try {
        if (userMessage.toLowerCase().startsWith('use ')) {
            const feature = userMessage.split(' ')[1];
            const query = userMessage.split('about ')[1];
            switch (feature) {
                case 'search':
                    return await performWebSearch(query);
                case 'news':
                    return await performNewsSearch(query);
                case 'places':
                    return await performPlacesSearch(query);
                case 'jobs':
                    return await performJobsSearch(query);
                case 'scholar':
                    return await performScholarSearch(query);
                default:
                    return "I'm not sure how to process that request. Can you please try again?";
            }
        } else {
            // Use Gemini API for general chat
            const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${GEMINI_API_KEY}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    contents: [{ parts: [{ text: userMessage }] }],
                    generationConfig: {
                        temperature: 0.9,
                        topK: 1,
                        topP: 1,
                        maxOutputTokens: 2048,
                    },
                }),
            });

            const data = await response.json();
            return data.candidates[0].content.parts[0].text;
        }
    } catch (error) {
        console.error('Error generating bot response:', error);
        return "I'm sorry, there was an error processing your request. Please try again later.";
    }
}

// Function to perform web search using Serper API
async function performWebSearch(query) {
    try {
        const response = await fetch(`https://serpapi.com/search.json?q=${encodeURIComponent(query)}&api_key=${SERPER_API_KEY}`);
        const data = await response.json();
        const results = data.organic_results;
        if (results && results.length > 0) {
            return `Here's what I found:\n\n${results[0].snippet}\n\nSource: ${results[0].link}`;
        }
        return "I couldn't find any relevant information for your query.";
    } catch (error) {
        console.error('Error searching the web:', error);
        return "There was an error performing the web search. Please try again later.";
    }
}

// Function to perform news search using Serper API
async function performNewsSearch(query) {
    try {
        const response = await fetch(`https://serpapi.com/search.json?q=${encodeURIComponent(query)}&tbm=nws&api_key=${SERPER_API_KEY}`);
        const data = await response.json();
        const results = data.news_results;
        if (results && results.length > 0) {
            return `Here's the latest news:\n\n${results[0].title}\n\n${results[0].snippet}\n\nSource: ${results[0].link}`;
        }
        return "I couldn't find any relevant news for your query.";
    } catch (error) {
        console.error('Error searching news:', error);
        return "There was an error performing the news search. Please try again later.";
    }
}

// Function to perform places search using Serper API
async function performPlacesSearch(query) {
    try {
        const response = await fetch(`https://serpapi.com/search.json?q=${encodeURIComponent(query)}&tbm=lcl&api_key=${SERPER_API_KEY}`);
        const data = await response.json();
        const results = data.local_results;
        if (results && results.length > 0) {
            return `Here's a place I found:\n\n${results[0].title}\n${results[0].address}\n\nRating: ${results[0].rating}\nReviews: ${results[0].reviews}`;
        }
        return "I couldn't find any relevant places for your query.";
    } catch (error) {
        console.error('Error searching places:', error);
        return "There was an error performing the places search. Please try again later.";
    }
}

// Function to perform jobs search using Serper API
async function performJobsSearch(query) {
    try {
        const response = await fetch(`https://serpapi.com/search.json?q=${encodeURIComponent(query)}&tbm=jobs&api_key=${SERPER_API_KEY}`);
        const data = await response.json();
        const results = data.jobs_results;
        if (results && results.length > 0) {
            return `Here's a job posting I found:\n\n${results[0].title}\n${results[0].company_name}\n\nLocation: ${results[0].location}\nDescription: ${results[0].description}`;
        }
        return "I couldn't find any relevant job postings for your query.";
    } catch (error) {
        console.error('Error searching jobs:', error);
        return "There was an error performing the jobs search. Please try again later.";
    }
}

// Function to perform Google Scholar search using Serper API
async function performScholarSearch(query) {
    try {
        const response = await fetch(`https://serpapi.com/search.json?q=${encodeURIComponent(query)}&engine=google_scholar&api_key=${SERPER_API_KEY}`);
        const data = await response.json();
        const results = data.organic_results;
        if (results && results.length > 0) {
            return `Here's a scholarly article I found:\n\n${results[0].title}\n\nAuthors: ${results[0].publication_info.summary}\n\nAbstract: ${results[0].snippet}\n\nSource: ${results[0].link}`;
        }
        return "I couldn't find any relevant scholarly articles for your query.";
    } catch (error) {
        console.error('Error searching Google Scholar:', error);
        return "There was an error performing the Google Scholar search. Please try again later.";
    }
}

// Function to save conversation to Firestore
async function saveConversation(userMessage, botResponse) {
    try {
        await addDoc(collection(db, "conversations"), {
            user: userMessage,
            bot: botResponse,
            timestamp: serverTimestamp()
        });
    } catch (error) {
        console.error("Error saving conversation:", error);
    }
}

// Function to load recent conversations from Firestore
function loadRecentConversations() {
    const q = query(collection(db, "conversations"), orderBy("timestamp", "desc"), limit(10));
    onSnapshot(q, (querySnapshot) => {
        chatMessages.innerHTML = ''; // Clear existing messages
        querySnapshot.forEach((doc) => {
            const data = doc.data();
            addMessageToChat('user', data.user);
            addMessageToChat('bot', data.bot);
        });
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
}

// Initialize the chat with a welcome message
function initializeChat() {
    addMessageToChat('bot', "Hello! I'm an advanced AI chatbot. How can I assist you today? You can ask me questions or use the buttons above to search for specific information.");
    loadRecentConversations();
}

// Call initializeChat when the page loads
window.addEventListener('load', initializeChat);

// Error handling for API key configuration
function checkApiKeys() {
    if (!GEMINI_API_KEY || GEMINI_API_KEY === 'YOUR_GEMINI_API_KEY') {
        console.error('Gemini API key is not set. Please set it in the script.js file.');
        addMessageToChat('bot', 'Error: Gemini API key is not configured. Please contact the administrator.');
    }
    if (!SERPER_API_KEY || SERPER_API_KEY === 'YOUR_SERPER_API_KEY') {
        console.error('Serper API key is not set. Please set it in the script.js file.');
        addMessageToChat('bot', 'Error: Serper API key is not configured. Please contact the administrator.');
    }
}

// Call checkApiKeys when the page loads
window.addEventListener('load', checkApiKeys);