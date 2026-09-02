from cred import perplexity
from langchain_core.prompts import ChatPromptTemplate
from langchain_perplexity import ChatPerplexity
import json

llm = ChatPerplexity(
    model="sonar",
    api_key=perplexity,
    temperature=0.5,
    max_tokens=1024,
)

# Load JSON files as context
with open("best_clicks_low_cpc_input_changes_top5.json", "r") as f1:
    clicks_context = json.load(f1)
with open("ranked_filtered_top5_conversions.json", "r") as f2:
    conversions_context = json.load(f2)

# Convert context to string (truncate if too large)
clicks_context_str = json.dumps(clicks_context, indent=2)[:2000]  # adjust length as needed
conversions_context_str = json.dumps(conversions_context, indent=2)[:2000]

# Add context to the system prompt
context_message = (
    "You are a chatbot. Here is some context data for reference:\n"
    f"Clicks Data:\n{clicks_context_str}\n\n"
    f"Conversions Data:\n{conversions_context_str}"
)

# Now you can ask your question
user_question = (
    "Based on the above data of increasing clicks and decreasing Cost per click.\n"
    "And data of increasing conversion and decreasing cost per conversion.\n"
    "The knowledge from Google Ads how they work and www.Vending.com business.\n"
    "Use Google’s Keyword Planner to find relevant keywords and estimate their performance.\n"
    "Can you provide the exact keywords and negative keywords for increasing conversion and decreasing cost/conversions?\n"
    "And for increasing click and decreasing Cost per click?\n"
    "Always respond with a JSON object in the following format:\n"
    "{\n"
    "  \"keywords_for_increasing_clicks_and_decreasing_cpc\": [ ... ],\n"
    "  \"negative_keywords_for_increasing_clicks_and_decreasing_cpc\": [ ... ],\n"
    "  \"keywords_for_increasing_conversions_and_decreasing_cost_per_conversion\": [ ... ],\n"
    "  \"negative_keywords_for_increasing_conversions_and_decreasing_cost_per_conversion\": [ ... ]\n"
    "}\n"
    "Do not include any explanation or extra text, only the JSON object."
)
message = [
    ("system", context_message),
    ("user", user_question)
]

import re
# 

response = llm.invoke(message)
print(response.content)


# Extract the largest JSON block from the response and save to genai.json
try:
    # Find the first '{' and last '}' to extract the JSON block
    start = response.content.find('{')
    end = response.content.rfind('}')
    if start != -1 and end != -1:
        json_str = response.content[start:end+1]
        data = json.loads(json_str)
        with open("genai.json", "w") as out_file:
            json.dump(data, out_file, indent=2)
        print("JSON extracted and saved to genai.json")
    else:
        print("No JSON found in response.")
except Exception as e:
    print(f"Error extracting JSON: {e}")