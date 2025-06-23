# c:\Users\Hp\Desktop\Nexus\core\ai_services_gemini.py
import google.generativeai as genai
from django.conf import settings
import logging
from PIL import Image # For image handling
import io # For image handling

logger = logging.getLogger(__name__)

try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    logger.info("Gemini AI API key configured.")

    # Attempt to list models to find a suitable one
    available_models = []
    for m in genai.list_models():
      if 'generateContent' in m.supported_generation_methods:
        available_models.append(m.name)
    
    logger.info(f"Available models supporting 'generateContent': {available_models}")

    # Prioritize 'gemini-1.5-flash-latest' or 'gemini-1.0-pro-latest' or 'gemini-pro' if available,
    # otherwise, try the first available one.
    # The newer models like "gemini-1.5-flash" are often recommended.
    preferred_models = ['models/gemini-1.5-flash-latest', 'models/gemini-1.0-pro-latest', 'models/gemini-pro', 'gemini-pro'] 
    chosen_model_name = None
    for model_name in preferred_models:
        if model_name in available_models:
            chosen_model_name = model_name
            break
    
    if not chosen_model_name and available_models:
        chosen_model_name = available_models[0] # Fallback to the first available model

    if chosen_model_name:
        gemini_model = genai.GenerativeModel(chosen_model_name)
        logger.info(f"Gemini AI configured successfully with model: {chosen_model_name}")
    else:
        logger.error("No suitable Gemini models found supporting 'generateContent'.")
        gemini_model = None

except Exception as e:
    logger.error(f"Failed to configure Gemini AI: {e}")
    gemini_model = None # Set to None if configuration fails

def generate_response_from_image_and_text(image_bytes, prompt_text):
    if not gemini_model: # Ensure this is a vision model
        logger.error("Gemini vision model is not available. Cannot generate response from image.")
        return "Error: AI model not available or not configured."

    # Explicitly check if the configured model is vision-capable
    # Models like 'gemini-1.5-pro-latest', 'gemini-1.5-flash-latest', and 'gemini-pro-vision' are multimodal/vision.
    vision_capable_keywords = ['vision', 'gemini-1.5'] # gemini-1.5 models are multimodal
    is_model_vision_capable = any(keyword in gemini_model.model_name for keyword in vision_capable_keywords)

    if not is_model_vision_capable:
        logger.error(f"Model {gemini_model.model_name} is not suitable for vision tasks. Attempted to use with an image.")
        return f"Error: Configured AI model ({gemini_model.model_name}) does not support image input."
    try:
        # Prepare the image for the API
        img = Image.open(io.BytesIO(image_bytes))
        
        # The new way to send multimodal content (image + text)
        # The prompt_text should guide what to do with the image.
        contents = [
            prompt_text, # Your text prompt
            img          # The PIL Image object
        ]
        
        response = gemini_model.generate_content(contents)
        return response.text
    except Exception as e:
        logger.error(f"Error calling Gemini API with image: {e}", exc_info=True)
        return f"Error generating response from image: {e}"

def generate_text_with_gemini(prompt_text):
    if not gemini_model:
        logger.error("Gemini model is not available. Cannot generate text.")
        return "Error: AI model not available or not configured."
    try:
        response = gemini_model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return f"Error generating text: {e}"