from google import genai

client = genai.Client(
    api_key="AIzaSyBgI06_mINTbm_rTrCAiP-J6dKevTlJRpY"
)

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Give 3 health tips"
)

print(response.text)
from google import genai

client = genai.Client(api_key="AIzaSyBgI06_mINTbm_rTrCAiP-J6dKevTlJRpY")

response = client.models.generate_content(
    model="gemini-1.5-flash",
    contents="Give 3 health tips"
)

print(response.text)