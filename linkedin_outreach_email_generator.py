import os
import requests

PERSONAL_DETAILS = (
    "\n\nBest regards,\n"
    "Deepak Bhagat\n"
    "Contact: +917678124123\n"
    "LinkedIn: https://www.linkedin.com/in/deepakbhagatiitr/\n"
    "GitHub: https://github.com/deepakbhagatiitr"
)

def call_gemini_api(prompt):
    """
    Sends a POST request to the Gemini API with the given prompt and returns the generated text.
    """
    API_KEY = os.getenv('GEMINI_API_KEY')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={API_KEY}"
    
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "maxOutputTokens": 200
                }
            }
        )
        response.raise_for_status()
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")


# Gemini API call for email generation
def generate_email(to_email, role, message, skills, projects):
    API_KEY = os.getenv('GEMINI_API_KEY')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={API_KEY}"
    
    prompt = (
        "You are an AI assistant tasked with writing a professional cold email for LinkedIn outreach based on a job posting or message provided by the user. "
        "Carefully analyze the user’s message to extract the company name, role, required skills, preferred subject line, and any specific instructions (e.g., application process). "
        "Craft a concise (under 200 words), polite, and personalized email that:\n"
        "- Starts directly with the email content, without any salutation (e.g., no 'Dear Hiring Manager').\n"
        "- Expresses enthusiasm for the specified role at the company.\n"
        "- Highlights 2-3 relevant skills from the provided skills list that align with the job requirements.\n"
        "- Describes two relevant projects from the provided projects list, including their short descriptions (e.g., technologies, purpose) to demonstrate experience.\n"
        "- Incorporates specific details from the message to show familiarity with the role.\n"
        "- Uses the subject line specified in the message, if provided, or creates a concise, relevant one.\n"
        "- Excludes the sender’s name in the body, as it will be added in the signature.\n"
        "- Ensures the email is complete, professional, and not cut off.\n"
        "Details:\n"
        f"- Recipient Email: {to_email}\n"
        f"- Role: {role}\n"
        f"- User Message: {message}\n"
        f"- Relevant Skills: {skills}\n"
        f"- Relevant Projects: {projects}\n"
        "Return the output in this format:\n"
        "Subject: {subject}\n{body}"
    )
    
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "maxOutputTokens": 512
                }
            }
        )
        response.raise_for_status()
        result = response.json()
        generated_text = result['candidates'][0]['content']['parts'][0]['text']
        print(f"Gemini API response: {generated_text}")
        # Append personal details to the email body
        subject = generated_text.split('\n')[0].replace("Subject: ", "")
        body = '\n'.join(generated_text.split('\n')[1:]) + PERSONAL_DETAILS
        return f"Subject: {subject}\n{body}"
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")