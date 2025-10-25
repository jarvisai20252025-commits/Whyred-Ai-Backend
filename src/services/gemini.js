const { GoogleGenerativeAI } = require('@google/generative-ai');

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

class GeminiService {
  constructor() {
    this.models = {
      text: 'gemini-2.0-flash-exp',
      vision: 'gemini-2.0-flash-exp', 
      code: 'gemini-2.0-flash-exp',
      fallback: 'gemini-1.5-flash',
      // Alternative model names to try
      alternatives: [
        'gemini-2.0-flash-exp',
        'gemini-2.0-flash',
        'models/gemini-2.0-flash-exp',
        'models/gemini-2.0-flash'
      ]
    };
    
    this.retryConfig = {
      maxRetries: 3,
      baseDelay: 1000,
      maxDelay: 5000
    };
  }

  async generateText(prompt, modelType = 'text') {
    return this.executeWithRetry(async () => {
      let model = this.models[modelType] || this.models.text;
      console.log(`Using model: ${model} for prompt: ${prompt.substring(0, 50)}...`);
      
      // Try different model name formats if the first one fails
      const modelsToTry = [model, ...this.models.alternatives, this.models.fallback];
      let lastError;
      
      for (const modelName of modelsToTry) {
        try {
          const generativeModel = genAI.getGenerativeModel({ 
            model: modelName,
            generationConfig: {
              temperature: 0.7,
              topK: 40,
              topP: 0.95,
              maxOutputTokens: 8192,
            },
            safetySettings: [
              {
                category: 'HARM_CATEGORY_HARASSMENT',
                threshold: 'BLOCK_MEDIUM_AND_ABOVE',
              },
              {
                category: 'HARM_CATEGORY_HATE_SPEECH',
                threshold: 'BLOCK_MEDIUM_AND_ABOVE',
              },
            ],
          });

          const result = await generativeModel.generateContent(prompt);
          const response = result.response;
          
          if (!response || !response.text) {
            throw new Error('Empty response from Gemini API');
          }
          
          const text = response.text();
          console.log(`Generated response length: ${text.length} using model: ${modelName}`);
          return text;
        } catch (error) {
          lastError = error;
          console.log(`Model ${modelName} failed: ${error.message}`);
          if (!error.message.includes('not found') && !error.message.includes('404')) {
            throw error; // If it's not a model not found error, throw immediately
          }
        }
      }
      
      throw lastError; // All models failed
    });
  }

  async generateFromImage(prompt, imageData, mimeType = 'image/jpeg') {
    return this.executeWithRetry(async () => {
      console.log(`Generating image response for: ${prompt.substring(0, 50)}...`);
      
      const generativeModel = genAI.getGenerativeModel({ 
        model: this.models.vision,
        generationConfig: {
          temperature: 0.4,
          topK: 32,
          topP: 1,
          maxOutputTokens: 4096,
        }
      });

      const imageParts = [{
        inlineData: {
          data: imageData,
          mimeType: mimeType
        }
      }];

      const result = await generativeModel.generateContent([prompt, ...imageParts]);
      const response = result.response;
      
      if (!response || !response.text) {
        throw new Error('Empty response from Gemini Vision API');
      }
      
      return response.text();
    });
  }

  async generateCode(prompt) {
    const enhancedPrompt = `
You are an expert programmer. Generate clean, well-documented, and efficient code for the following request:

${prompt}

Requirements:
- Include proper error handling
- Add meaningful comments
- Follow best practices
- Provide working, production-ready code
- Include usage examples if applicable

Code:`;

    return this.generateText(enhancedPrompt, 'code');
  }

  async generateSearch(query) {
    const searchPrompt = `
Provide a comprehensive answer for the search query: "${query}"

Include:
- Direct answer to the question
- Key facts and details
- Relevant context and background
- Multiple perspectives if applicable
- Recent developments if relevant

Answer:`;

    return this.generateText(searchPrompt, 'text');
  }

  async executeWithRetry(operation) {
    let lastError;
    
    for (let attempt = 1; attempt <= this.retryConfig.maxRetries; attempt++) {
      try {
        console.log(`Attempt ${attempt}/${this.retryConfig.maxRetries}`);
        return await operation();
      } catch (error) {
        lastError = error;
        console.error(`Attempt ${attempt} failed:`, error.message);
        
        if (attempt === this.retryConfig.maxRetries) {
          break;
        }
        
        // Exponential backoff with jitter
        const delay = Math.min(
          this.retryConfig.baseDelay * Math.pow(2, attempt - 1),
          this.retryConfig.maxDelay
        ) + Math.random() * 1000;
        
        console.log(`Retrying in ${Math.round(delay)}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
    
    // If all retries failed, try fallback model
    if (lastError.message.includes('model') || lastError.message.includes('not found')) {
      console.log('Trying fallback model...');
      try {
        const generativeModel = genAI.getGenerativeModel({ model: this.models.fallback });
        const result = await generativeModel.generateContent('Hello, are you working?');
        return result.response.text();
      } catch (fallbackError) {
        console.error('Fallback model also failed:', fallbackError.message);
      }
    }
    
    throw new Error(`All attempts failed. Last error: ${lastError.message}`);
  }

  async healthCheck() {
    try {
      const response = await this.generateText('Hello, respond with "OK" if you are working.');
      return response.toLowerCase().includes('ok');
    } catch (error) {
      console.error('Health check failed:', error.message);
      return false;
    }
  }

  async listAvailableModels() {
    try {
      const { GoogleGenerativeAI } = require('@google/generative-ai');
      const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
      
      // This is a workaround since the SDK doesn't expose listModels directly
      // We'll try to generate with different models to see which ones work
      const testModels = [
        'gemini-2.0-flash-exp',
        'gemini-2.0-flash',
        'models/gemini-2.0-flash-exp',
        'models/gemini-2.0-flash',
        'gemini-1.5-flash',
        'gemini-1.5-pro'
      ];
      
      const workingModels = [];
      
      for (const modelName of testModels) {
        try {
          const model = genAI.getGenerativeModel({ model: modelName });
          await model.generateContent('test');
          workingModels.push(modelName);
        } catch (error) {
          // Model doesn't work, skip it
        }
      }
      
      return workingModels;
    } catch (error) {
      console.error('Error listing models:', error.message);
      return [];
    }
  }

  getModelInfo() {
    return {
      models: this.models,
      apiKeyConfigured: !!process.env.GEMINI_API_KEY,
      retryConfig: this.retryConfig
    };
  }
}

module.exports = new GeminiService();