# c:\Users\Hp\Desktop\Nexus\core\ai_services_gemini.py
import os
# Limit threads for libraries like numpy/onnxruntime to reduce memory overhead in workers
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions # Import google exceptions
import logging
from PIL import Image,ImageEnhance # For image handling
import io # For image handling
from rembg import remove, new_session
import json # For parsing structured JSON responses

logger = logging.getLogger(__name__)

try:
    from django.conf import settings # Moved import here
    
    api_key = getattr(settings, 'GEMINI_API_KEY', None)

    if not api_key:
        logger.warning("GEMINI_API_KEY is missing in settings. AI features will be disabled.")
        gemini_model = None
    elif str(api_key).strip() == 'your_actual_api_key_here':
        logger.error("GEMINI_API_KEY is set to the placeholder value. Please update your .env file with a valid key from Google AI Studio.")
        gemini_model = None
    else:
        genai.configure(api_key=api_key)
        logger.info("Gemini AI API key configured.")

        # We use a hardcoded model name to avoid blocking network calls (list_models) during app startup.
        # 'gemini-2.5-flash' is the current preferred model.
        # If it's not available, the API call will fail later, which is better than crashing startup.
        chosen_model_name = 'models/gemini-2.5-flash'
        
        # Fallback logic can be implemented here if needed, but usually standard models are always available.
        # If you want to be safer, you could use 'models/gemini-1.5-flash' as a fallback if the 2.5 one fails at runtime.
        logger.info(f"Configuring Gemini AI with preferred model: {chosen_model_name}")

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
    from django.conf import settings # Add import here for safety
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

def get_chatbot_response(prompt_text: str) -> dict | None:
    """
    Calls the Gemini API with a prompt expecting a structured JSON response for the chatbot.
    This uses function calling/structured output to determine user intent.
    """
    if not gemini_model:
        logger.error("Gemini model is not available. Cannot generate chatbot response.")
        return None

    try:
        # The google-generativeai library now uses a specific generation_config
        # for JSON output. We also need to ensure the prompt itself asks for JSON.
        generation_config = genai.GenerationConfig(response_mime_type="application/json")
        
        # Send the prompt to the model
        response = gemini_model.generate_content(prompt_text, generation_config=generation_config)
        
        # The response text should be a JSON string.
        if not response.text:
            logger.error("Gemini chatbot response was empty.")
            return None
            
        response_json = json.loads(response.text)
        return response_json
    except google_exceptions.ResourceExhausted as e:
        logger.error(f"Gemini API quota exceeded: {e}", exc_info=True)
        # Return a specific error structure that the view can handle
        return {"error": "The AI assistant is currently unavailable due to high traffic. Please try again in a few moments."}
    except json.JSONDecodeError as e:
        # Use response.text if it exists, otherwise show that it was empty.
        logger.error(f"Gemini chatbot response was not valid JSON. Response text: '{getattr(response, 'text', '<EMPTY RESPONSE>')}'. Error: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Error calling Gemini API for chatbot structured response: {e}", exc_info=True)
    return None

def generate_structured_text_with_gemini(prompt_text: str) -> dict | None:
    """
    Calls the Gemini API with a prompt expecting a JSON response and attempts to parse it.
    """
    if not gemini_model:
        logger.error("Gemini model is not available. Cannot generate structured text.")
        return None

    try:
        # Configure the model to output JSON
        generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
        response = gemini_model.generate_content(prompt_text, generation_config=generation_config)
        
        # The response text should be a JSON string.
        response_json = json.loads(response.text)
        return response_json
    except json.JSONDecodeError as e:
        logger.error(f"Gemini API response was not valid JSON. Response text: '{response.text}'. Error: {e}")
    except Exception as e:
        logger.error(f"Error calling Gemini API for structured response: {e}", exc_info=True)
    return None

def remove_image_background(image_bytes):
    """Removes the background from an image using the rembg library."""
    try:
        input_img = Image.open(io.BytesIO(image_bytes))
        # Use the 'u2netp' model which is optimized for low memory usage (~40MB vs ~170MB)
        session = new_session("u2netp")
        output_img = remove(input_img, session=session)
        
        img_byte_arr = io.BytesIO()
        output_img.save(img_byte_arr, format='PNG') # Or JPEG, depending on needs
        return img_byte_arr.getvalue()
    except Exception as e:
        logger.error(f"Error removing background: {e}", exc_info=True)
        return None


def enhance_image_with_gemini(image_bytes: bytes) -> bytes | None:
    """
    Placeholder function to enhance an image.
    This uses Pillow to apply a sharpness filter as a simulation.
    Replace this with a real call to a Gemini or other AI image enhancement API.
    """
    try:
        logger.info("Simulating AI image enhancement with Pillow.")
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Convert to RGB if it's not, to ensure compatibility with filters
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Apply a sharpness enhancement
            enhancer = ImageEnhance.Sharpness(img)
            enhanced_img = enhancer.enhance(2.0) # Increase sharpness

            # Save the enhanced image to a byte stream
            byte_arr = io.BytesIO()
            enhanced_img.save(byte_arr, format='JPEG', quality=95)
            return byte_arr.getvalue()
    except Exception as e:
        logger.error(f"Pillow image enhancement placeholder failed: {e}", exc_info=True)
        return None