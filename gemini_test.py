
#for now using gemini apis 
from decouple import config
from google import genai

client = genai.Client(api_key=config("GEMINI_API_KEY"))

interaction = client.interactions.create(
    model= config("GEMINI_MODEL"),
    input="What is Python"
)
print(interaction.output_text)