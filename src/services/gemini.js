const { GoogleGenerativeAI } = require('@google/generative-ai');

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

class GeminiService {
  async generateText(prompt, model = 'gemini-pro') {
    try {
      const generativeModel = genAI.getGenerativeModel({ model });
      const result = await generativeModel.generateContent(prompt);
      return result.response.text();
    } catch (error) {
      throw new Error(`Gemini API error: ${error.message}`);
    }
  }

  async generateFromImage(prompt, imageData, model = 'gemini-pro-vision') {
    try {
      const generativeModel = genAI.getGenerativeModel({ model });
      const result = await generativeModel.generateContent([
        prompt,
        {
          inlineData: {
            data: imageData,
            mimeType: 'image/jpeg'
          }
        }
      ]);
      return result.response.text();
    } catch (error) {
      throw new Error(`Gemini Vision API error: ${error.message}`);
    }
  }

  async generateCode(prompt) {
    const codePrompt = `Generate clean, well-commented code for: ${prompt}`;
    return this.generateText(codePrompt);
  }
}

module.exports = new GeminiService();