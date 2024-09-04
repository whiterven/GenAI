// Configuration
const GEMINI_API_KEY = 'YOUR_GEMINI_API_KEY';
const SERPER_API_KEY = 'YOUR_SERPER_API_KEY';

// Initialize Gemini API
const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);

// Initialize LangChain
const { ChatGoogleGenerativeAI, HumanMessage, SystemMessage } = langchain;

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

// Gemini Chat Model
const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

// LangChain Chat Model
const llm = new ChatGoogleGenerativeAI("gemini-pro");

// Main function to handle user input
async function handleUserInput() {
    const userMessage = userInput.value.trim();
    if (userMessage === '') return;

    addMessageToChat('user', userMessage);
    userInput.value = '';

    const botResponse = await generateBotResponse(userMessage);
    addMessageToChat('bot', botResponse);
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
            const chat = model.startChat({
                history: [],
                generationConfig: {
                    temperature: 0.9,
                    topK: 1,
                    topP: 1,
                    maxOutputTokens: 2048,
                },
            });

            const result = await chat.sendMessage(userMessage);
            return result.response.text();
        }
    } catch (error) {
        console.error('Error generating bot response:', error);
        return "I'm sorry, there was an error processing your request. Please try again later.";
    }
}

// Function to perform web search using Serper API
async function performWebSearch(query) {
    try {
        const response = await axios.get('https://serpapi.com/search', {
            params: {
                q: query,
                api_key: SERPER_API_KEY,
            },
        });

        const results = response.data.organic_results;
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
        const response = await axios.get('https://serpapi.com/search', {
            params: {
                q: query,
                api_key: SERPER_API_KEY,
                tbm: 'nws',
            },
        });

        const results = response.data.news_results;
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
        const response = await axios.get('https://serpapi.com/search', {
            params: {
                q: query,
                api_key: SERPER_API_KEY,
                tbm: 'lcl',
            },
        });

        const results = response.data.local_results;
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
        const response = await axios.get('https://serpapi.com/search', {
            params: {
                q: query,
                api_key: SERPER_API_KEY,
                tbm: 'jobs',
            },
        });

        const results = response.data.jobs_results;
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
        const response = await axios.get('https://serpapi.com/search', {
            params: {
                q: query,
                api_key: SERPER_API_KEY,
                engine: 'google_scholar',
            },
        });

        const results = response.data.organic_results;
        if (results && results.length > 0) {
            return `Here's a scholarly article I found:\n\n${results[0].title}\n\nAuthors: ${results[0].publication_info.summary}\n\nAbstract: ${results[0].snippet}\n\nSource: ${results[0].link}`;
        }
        return "I couldn't find any relevant scholarly articles for your query.";
    } catch (error) {
        console.error('Error searching Google Scholar:', error);
        return "There was an error performing the Google Scholar search. Please try again later.";
    }
}

// Initialize the chat with a welcome message
addMessageToChat('bot', "Hello! I'm an advanced AI chatbot. How can I assist you today? You can ask me questions or use the buttons above to search for specific information.");
