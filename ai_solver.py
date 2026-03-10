import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

def solve_quiz(image_path):
    # Convert image to base64
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    prompt = """
    Look at this screenshot carefully. 
    There is a quiz question on the screen.
    
    1. Tell me what the question is
    2. Tell me all the answer choices
    3. Tell me which answer is CORRECT
    4. Tell me exactly what text the correct answer says
    
    Be short and direct in your response.
    """

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openrouter/free",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}"
                            }
                        }
                    ]
                }
            ]
        }
    )

    result = response.json()
    
    if "error" in result:
        print("❌ Error:", result["error"]["message"])
        return None

    answer = result["choices"][0]["message"]["content"]
    print("=== AI Response ===")
    print(answer)
    return answer

if __name__ == "__main__":
    from screenshot import take_screenshot
    image_path = take_screenshot()
    solve_quiz(image_path)