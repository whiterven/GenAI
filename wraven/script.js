const functions = require('firebase-functions');
const axios = require('axios');

const GEMINI_API_ENDPOINT = 'https://your-gemini-api-endpoint.com';
const SERPER_API_ENDPOINT = 'https://serpapi.com/search';
const SERPER_API_KEY = 'your-serper-api-key';

exports.chat = functions.https.onRequest(async (request, response) => {
  const { message } = request.body;

  // Check if web search is needed
  const needsWebSearch = message.toLowerCase().includes('latest') || 
                         message.toLowerCase().includes('current') || 
                         message.toLowerCase().includes('news');

  let webSearchResult = null;
  let isSearching = false;

  if (needsWebSearch) {
    isSearching = true;
    try {
      const searchResponse = await axios.get(SERPER_API_ENDPOINT, {
        params: {
          q: message,
          api_key: SERPER_API_KEY
        }
      });
      webSearchResult = searchResponse.data;
    } catch (error) {
      console.error('Error searching web:', error);
    }
  }

  // Get response from Gemini
  try {
    const geminiResponse = await axios.post(GEMINI_API_ENDPOINT, {
      message,
      webSearchResult
    });

    response.json({
      response: geminiResponse.data.response,
      isSearching
    });
  } catch (error) {
    console.error('Error getting Gemini response:', error);
    response.status(500).json({ error: 'An error occurred while processing your request.' });
  }
});
