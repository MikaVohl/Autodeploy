from openai import OpenAI
import json

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
User: "Hey, please deploy my Flask app on AWS."
Ideal JSON:
{
  "cloud_provider": "aws",
  "application_type": "nodejs",
  "resource_size": "small",
}
"""

STRUCTURE_PROMPT = """
You are a project structure analyst. The user will provide a tree structure of their project and the framework they are using. Your job is to extract key information about the project structure.

The JSON object must contain these fields:

dependency_manifest_path (e.g., "app/requirements.txt", "package.json")
main_file_path (e.g., "app/main.py", "server.js")

Important:
Do not include any extra commentary, explanations, or markdown.
Make sure your JSON is valid and properly formatted (use double quotes around strings, no trailing commas, etc.).

**Example 1**:
Input:
hello_world-main
├── .gitignore
├── README.md
└── app
    ├── app.py
    ├── requirements.txt
    ├── static
    │   └── style.css
    └── templates
        └── index.html
Ideal JSON:
{
  "dependency_manifest_path": "app/requirements.txt",
  "main_file_path": "app/app.py"
}

**Example 2**:
Input:
project
├── .gitignore
├── README.md
├── package.json
├── src
│   ├── main.js
│   ├── components
│   │   ├── Header.js
│   │   └── Footer.js
│   └── styles
│       └── main.css
└── public
    └── index.html
Ideal JSON:
{
  "dependency_manifest_path": package.json",
  "main_file_path": "src/main.js"
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
    
    try:
        return json.loads(output_text)
    except json.JSONDecodeError:
        # Fallback if GPT doesn't return valid JSON
        return {"cloud_provider": "aws", "application_type": None, "resource_size": None}
    
def get_repo_structure(root_dir, tree, framework):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": STRUCTURE_PROMPT},
            {"role": "user", "content": f"Framework: {framework}\nTree:\n{root_dir}\n{tree}"}
        ],
        temperature=0.0  # Keeps output deterministic
    )

    if response.choices:
        output_text = response.choices[0].message.content
    else:
        output_text = "Sorry, I couldn't understand your request."
    
    try:
        return json.loads(output_text)
    except json.JSONDecodeError:
        # Fallback if GPT doesn't return valid JSON
        return {"dependency_manifest_path": None, "main_file_path": None}