from openai import OpenAI

SYSTEM_PROMPT = """
You are a deployment instruction parser. The user will provide a natural language description of how they want their application deployed. Your job is to extract key information from their request and produce a well-formed JSON object only.

The JSON object must contain these fields:

cloud_provider (e.g., "aws", "gcp", "azure")
application_type (e.g., "flask", "django", "nodejs")
resource_size (optional, for instance type or VM size)
Important:

Do not include any extra commentary, explanations, or markdown.
Make sure your JSON is valid and properly formatted (use double quotes around strings, no trailing commas, etc.).
If you’re not sure about a particular field, return a sensible default or a null value.

**Example**:
User: "Hey, please deploy my Node.js app on an AWS EC2 instance."
Ideal JSON:
{
  "cloud_provider": "aws",
  "application_type": "nodejs",
  "resource_size": "small",
}
"""

client = OpenAI()

def process_deployment_request(user_text: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        temperature=0.0  # Keeps output deterministic
    )

    if response.choices:
        output_text = response.choices[0].message.content
    else:
        output_text = "Sorry, I couldn't understand your request."
    
    import json
    try:
        return json.loads(output_text)
    except json.JSONDecodeError:
        # Fallback if GPT doesn't return valid JSON
        return {"cloud_provider": "aws", "application_type": None, "resource_size": None}