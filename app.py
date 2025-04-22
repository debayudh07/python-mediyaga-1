import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from langchain_groq import ChatGroq
from pydantic import BaseModel

# Initialize FastAPI
app = FastAPI(title="MediApp Customer Support API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Email Configuration
ADMIN_EMAIL = "mediyaga2025@gmail.com"
SUPPORT_EMAIL = "jeetdas3200@gmail.com"
EMAIL_PASSWORD = "kjkwxdjnviklonxw"
SMTP_SERVER =  "smtp.gmail.com"
SMTP_PORT = "587"

# Groq API Key for AI-powered support
GROQ_API = "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"
llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=GROQ_API)

# Common support categories for the app
support_categories = {
    "account": ["login", "password", "signup", "profile", "account", "delete", "register", "email"],
    "billing": ["payment", "subscription", "charge", "refund", "bill", "invoice", "price", "plan", "upgrade"],
    "app_features": ["feature", "app", "dashboard", "notification", "reminder", "appointment", "booking"],
    "technical": ["bug", "crash", "error", "not working", "issue", "problem", "glitch", "stuck"],
    "privacy": ["data", "privacy", "gdpr", "information", "security", "confidential"]
}

# Greetings list
greetings = ["hi", "hey", "hello", "greetings", "howdy", "hola", "good morning", "good afternoon", "good evening"]

# Default responses for fallback scenarios
DEFAULT_RESPONSES = {
    "account": "I understand you have a question about your account. For security reasons, I can only provide general guidance here. Please contact our support team at support@mediapp.com with your account details for personalized assistance.",
    "billing": "Thank you for your billing inquiry. For specific questions about your payments or subscription, please reach out to our billing department at support@mediapp.com with your account information and billing query details.",
    "app_features": "I'd be happy to help you learn more about our app features. MediApp offers appointment scheduling, medication reminders, and secure messaging with providers. If you need more specific guidance, please contact support@mediapp.com.",
    "technical": "I'm sorry you're experiencing technical difficulties. Please try restarting the app and ensuring you have the latest version installed. For ongoing issues, please email support@mediapp.com with details about your device, app version, and the specific problem you're encountering.",
    "privacy": "Your privacy and data security are our top priorities. MediApp follows strict GDPR and HIPAA guidelines for all user data. For specific privacy concerns or data requests, please contact our privacy team at support@mediapp.com.",
    "general": "Thank you for reaching out to MediApp support. We'd be happy to assist you with your query. For personalized help, please email our support team at support@mediapp.com with more details about your question or concern."
}

class SupportIssue(BaseModel):
    name: str
    email: str
    issue: str
    category: str = "general"

async def send_support_email(issue: SupportIssue):
    """
    Send support issue to the support email address.
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = ADMIN_EMAIL
        msg['To'] = SUPPORT_EMAIL
        msg['Subject'] = f"Support Request: {issue.category.capitalize()}"
        
        # Create email body
        body = f"""
        New Support Request:
        
        Name: {issue.name}
        Email: {issue.email}
        Category: {issue.category}
        
        Issue Details:
        {issue.issue}
        
        This email was automatically generated from the MediApp Support Chat.
        """
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            try:
                server.ehlo()  # Identify ourselves to the server
                server.starttls()  # Secure the connection
                server.ehlo()  # Re-identify after TLS
                server.login(ADMIN_EMAIL, EMAIL_PASSWORD)  # Login with credentials
                server.send_message(msg)
            except smtplib.SMTPException as smtp_error:
                print(f"SMTP error occurred: {smtp_error}")
                raise Exception(f"Email sending failed: {smtp_error}")
        
        return True
    except Exception as e:
        print(f"Email sending error: {str(e)}")
        return False

async def determine_category(query: str):
    """
    Determine the support category based on keywords in the query.
    """
    query_lower = query.lower().strip()
    
    # Check if it's a greeting
    if any(query_lower == greeting or query_lower.startswith(f"{greeting} ") for greeting in greetings):
        return "greeting"
    
    for category, keywords in support_categories.items():
        if any(keyword in query_lower for keyword in keywords):
            return category
    
    # If no category matches, use LLM to determine category
    try:
        response = llm.invoke(
            f"""Given this customer support query for a medical app: '{query}',
            what is the most appropriate category from this list:
            account, billing, app_features, technical, privacy?
            Respond with ONLY the category name in lowercase."""
        )
        determined_category = response.content.strip().lower()
        # Validate the category is one we support
        if determined_category in support_categories:
            return determined_category
        return "general"
    except Exception as e:
        print(f"Category determination error: {str(e)}")
        # Try to detect category by keywords in the query as fallback
        for category, keywords in support_categories.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return category
        return "general"

async def get_ai_support_response(query: str, category: str):
    """
    Get an AI-powered customer support response based on the query and category.
    """
    try:
        system_prompt = """You are MediApp Support Assistant, a helpful customer support specialist for a medical appointment booking app.
        
        Guidelines:
        1. Focus ONLY on app usage, account issues, billing, and technical support
        2. Do NOT provide any medical advice or information about health conditions
        3. Do NOT recommend doctors or medical specialists
        4. Be friendly, professional, and solution-oriented
        5. Keep responses concise and focused on resolving customer issues
        6. For complex technical issues, suggest submitting a support ticket
        7. For account-specific issues, advise contacting support with account details
        8. For billing issues, explain general policies but suggest contacting the billing department for specific cases
        
        Always end your response by providing the support email: jeetdas3200@gmail.com
        
        Remember: You are ONLY helping with app usage and technical support, not medical issues."""
        
        # Special handling for greetings - use hardcoded responses to avoid LLM issues
        if category == "greeting":
            return "Hi there! I'm your MediApp Support Assistant. How can I help you with the app today? If you need direct assistance, you can reach our support team at jeetdas3200@gmail.com"
        
        # For normal queries, use the LLM
        response = llm.invoke(
            f"""System: {system_prompt}
            
            Support Category: {category}
            User Query: {query}
            
            Assistant:"""
        )
        return response.content.strip()
    except Exception as e:
        print(f"Response generation error: {str(e)}")
        # Return a more helpful category-specific fallback response
        fallback_response = DEFAULT_RESPONSES.get(category, DEFAULT_RESPONSES["general"])
        return f"{fallback_response} If you need immediate assistance, please email our support team at support@mediapp.com."

@app.get("/support/chat/")
async def chat(query: str):
    """
    Customer support chat endpoint: Returns AI-generated customer support response.
    """
    try:
        # Determine the support category
        category = await determine_category(query)
        
        # Generate AI response for the category
        response = await get_ai_support_response(query, category)
        print(f"Query: {query}, Category: {category}, Response: {response}")
        return {
            "response": response,
            "category": category,
            "source": "ai"
        }
    except Exception as e:
        fallback_response = "Thank you for reaching out to MediApp support. We're experiencing some technical difficulties at the moment. Please try again or contact our support team directly at support@mediapp.com for immediate assistance."
        return {
            "response": fallback_response,
            "category": "technical",
            "source": "fallback"
        }

@app.post("/support/issue/")
async def submit_issue(issue: SupportIssue):
    """
    Endpoint to submit a support issue via email.
    """
    try:
        success = await send_support_email(issue)
        
        if success:
            return {
                "message": "Your support issue has been submitted successfully. Our team will contact you shortly.",
                "status": "success"
            }
        else:
            return {
                "message": "There was an issue submitting your support request. Please try again or email support@mediapp.com directly.",
                "status": "error"
            }
    except Exception as e:
        return {
            "message": f"Error submitting support issue: {str(e)}",
            "status": "error"
        }

# Run FastAPI Server
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5173))
    uvicorn.run("app:app", host="0.0.0.0", port=port, log_level="info")