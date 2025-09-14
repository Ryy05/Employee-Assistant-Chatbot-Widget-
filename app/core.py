# In app/core.py

import os
import smtplib
import json
from datetime import date, timedelta
from email.message import EmailMessage
from langchain.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from sentence_transformers import SentenceTransformer, util
import torch
from dotenv import load_dotenv
import mimetypes

load_dotenv()

# --- Conversation State Manager ---
conversation_state = {}

# --- Helper Functions ---
def get_employee_data(employee_id):
    try:
        with open("data/employees.json", 'r') as f:
            employees = json.load(f)
            for emp in employees:
                if emp["employee_id"].lower() == employee_id.lower():
                    return emp
    except Exception as e:
        print(f"Error reading employee data: {e}")
        return None
    return None

def send_email(to_address, subject, body, attachment_path=None):
    # Load credentials from the .env file
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("❌ ERROR: SENDER_EMAIL or SENDER_PASSWORD not set in .env file. Cannot send real email.")
        # Fallback to simulation if credentials are not set
        print("--- SIMULATING EMAIL SEND ---")
        print(f"To: {to_address}\nSubject: {subject}\nBody:{body}")
        if attachment_path: print(f"Attachment: {attachment_path}")
        print("---------------------------")
        return False

    # Create the email message object
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_address

    # If there is an attachment, add it to the email
    if attachment_path and os.path.exists(attachment_path):
        ctype, encoding = mimetypes.guess_type(attachment_path)
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        with open(attachment_path, 'rb') as fp:
            msg.add_attachment(fp.read(),
                               maintype=maintype,
                               subtype=subtype,
                               filename=os.path.basename(attachment_path))
    
    # Connect to the Gmail server and send the email
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email successfully sent to {to_address}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

# --- Prompt Template (Unchanged) ---
custom_prompt_template = """Use the following pieces of context to answer the question at the end. 
If the context does not contain the answer, state that the information is not available in the provided policy.
Present the answer in clear, concise bullet points for easy readability.

Context: {context}

Question: {question}
Helpful Answer:"""

CUSTOM_PROMPT = PromptTemplate(
    template=custom_prompt_template, input_variables=["context", "question"]
)

# --- Main Chatbot Class ---
class ChatbotCore:
    def __init__(self, faiss_path="data/mpc_faiss_index"):
        print("Initializing ChatbotCore...")
        self._load_models(faiss_path)
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True, output_key="answer"
        )
        self._setup_chains()
        self._setup_manual_qa()
        print("✅ ChatbotCore Initialized.")
    
    def reset_conversation_state(self):
        global conversation_state
        conversation_state = {}
        print("Conversation task state cleared.")

    def _load_models(self, faiss_path):
        self.embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        self.db = FAISS.load_local(
            faiss_path, self.embedding_model, allow_dangerous_deserialization=True
        )
        api_key = os.getenv("TOGETHERAI_API_KEY")
        if not api_key:
            raise ValueError("TOGETHERAI_API_KEY environment variable not set.")
        self.llm = ChatOpenAI(
            openai_api_key=api_key, model_name="mistralai/Mistral-7B-Instruct-v0.2",
            base_url="https://api.together.xyz/v1", temperature=0.2, max_tokens=512
        )

    def _setup_chains(self):
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.db.as_retriever(search_kwargs={'k': 2}),
            memory=self.get_memory(),
            combine_docs_chain_kwargs={"prompt": CUSTOM_PROMPT}
        )

    def _setup_manual_qa(self):
        faq_path = "data/faqs.json"
        try:
            with open(faq_path, 'r') as f:
                self.manual_qa = json.load(f)
            print("✅ Manual FAQs loaded successfully from faqs.json.")
        except Exception:
            self.manual_qa = {}
        
        self.faq_encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.faq_questions = list(self.manual_qa.keys())
        self.faq_embeddings = self.faq_encoder.encode(self.faq_questions, convert_to_tensor=True)

    def get_memory(self):
        return self.memory

    def _get_manual_answer(self, query, threshold=0.75):
        if not self.faq_questions:
            return None
        query_embedding = self.faq_encoder.encode(query, convert_to_tensor=True)
        cosine_scores = util.pytorch_cos_sim(query_embedding, self.faq_embeddings)[0]
        top_result = torch.topk(cosine_scores, k=1)
        if top_result.values.item() >= threshold:
            return self.manual_qa[self.faq_questions[top_result.indices.item()]]
        return None

    def handle_leave_application(self, query):
        global conversation_state
        employee_data = conversation_state.get("employee_data", {})
        
        if conversation_state.get("leave_type") is None:
            possible_types = ["sick", "casual", "maternity", "paternity", "bereavement", "unpaid"]
            for leave_type in possible_types:
                if leave_type in query.lower():
                    conversation_state["leave_type"] = leave_type.capitalize()
                    break 
            if conversation_state.get("leave_type"):
                return f"Okay, a {conversation_state['leave_type']} leave. Please select the date or dates from the calendar."
            else:
                return "Sure. What type of leave do you want to apply for?"

        if conversation_state.get("dates") is None:
            conversation_state["dates"] = query
            leave_type, dates = conversation_state['leave_type'], conversation_state['dates']
            full_name, emp_id = employee_data.get("full_name", "N/A"), employee_data.get("employee_id", "N/A")
            return f"Please confirm: Apply for {leave_type} leave for '{dates}'. Name: {full_name}, Employee ID: {emp_id}. Is this correct? (Yes/No)"
        
        if not conversation_state.get("confirmed"):
            if "yes" in query.lower():
                conversation_state["confirmed"] = True
                subject = f"New Leave Request from {employee_data.get('full_name', 'N/A')}"
                body = f"Employee: {employee_data.get('full_name')} (ID: {employee_data.get('employee_id')})\nLeave Type: {conversation_state.get('leave_type')}\nDates: {conversation_state.get('dates')}"
                send_email("sunil.kumar2@mpccloudconsulting.com", subject, body)
                self.reset_conversation_state()
                return "Thank you. I have forwarded your leave request to the HR department. You will hear from them soon."
            else:
                self.reset_conversation_state()
                return "Okay, I've cancelled the leave application process."
        
        self.reset_conversation_state()
        return "Sorry, something went wrong. Let's start over."

    # --- NEW: Logic for handling the multi-step expense claim ---
    def handle_expense_claim(self, query):
        global conversation_state
        employee_data = conversation_state.get("employee_data", {})

        if conversation_state.get("expense_type") is None:
            # For simplicity, we assume the first response is the category. A real app might show choices.
            conversation_state["expense_type"] = query
            return "Got it. What was the total amount?"
        
        if conversation_state.get("amount") is None:
            conversation_state["amount"] = query
            return "Understood. Please select the date of the expense from the calendar."

        if conversation_state.get("date") is None:
            conversation_state["date"] = query
            return "Thank you. Now, please upload a photo or PDF of the receipt using the button that appears."

        if conversation_state.get("receipt_path") is None:
            if "receipt_uploaded:" in query:
                conversation_state["receipt_path"] = query.split(":", 1)[1].strip()
                exp_type = conversation_state['expense_type']
                amount = conversation_state['amount']
                exp_date = conversation_state['date']
                return f"Please confirm: Submit expense for {exp_type} of {amount} on {exp_date} for {employee_data.get('full_name')}. Is this correct? (Yes/No)"
            else:
                return "Please use the upload button to submit your receipt."

        if not conversation_state.get("confirmed"):
            if "yes" in query.lower():
                conversation_state["confirmed"] = True
                subject = f"New Expense Claim from {employee_data['full_name']}"
                body = f"Employee: {employee_data['full_name']} (ID: {employee_data['employee_id']})\nType: {conversation_state['expense_type']}\nAmount: {conversation_state['amount']}\nDate: {conversation_state['date']}"
                send_email("sunil.kumar2@mpccloudconsulting.com", subject, body, conversation_state["receipt_path"])
                self.reset_conversation_state()
                return "Thank you. Your expense claim has been submitted to the finance department for approval."
            else:
                self.reset_conversation_state()
                return "Okay, I've cancelled the expense claim."
        
        self.reset_conversation_state()
        return "Sorry, something went wrong with the claim process."

    # --- MODIFIED: The main "router" now understands expense claims ---
    def get_answer(self, query):
        global conversation_state

        # Priority 1: Handle an ongoing task
        current_task = conversation_state.get("task")
        if current_task == "apply_leave":
            return self.handle_leave_application(query)
        if current_task == "apply_expense":
            return self.handle_expense_claim(query)
        if current_task in ["awaiting_id_for_leave", "awaiting_id_for_expense"]:
            employee_data = get_employee_data(query)
            if employee_data:
                conversation_state["employee_data"] = employee_data
                employee_name = employee_data.get("full_name", "Employee")
                balance_info = f"Thank you, {employee_name}. You have {employee_data.get('annual_leave', 0)} Annual and {employee_data.get('sick_leave', 0)} Sick leave days remaining."
                
                if current_task == "awaiting_id_for_leave":
                    conversation_state["task"] = "apply_leave"
                    return f"{balance_info} What type of leave do you want to apply for?"
                else: # awaiting_id_for_expense
                    conversation_state["task"] = "apply_expense"
                    return f"{balance_info} I can help with your expense claim. What category does it fall under?"
            else:
                return "I couldn't find that Employee ID. Please try again or ask a general policy question."

        # Priority 2: Check for new task intents
        action_words = ["file", "claim", "submit", "add", "new"]
        topic_words_expense = ["expense", "reimbursement"]

        if any(word in query.lower() for word in action_words) and any(word in query.lower() for word in topic_words_expense):
            if "employee_data" not in conversation_state:
                conversation_state["task"] = "awaiting_id_for_expense"
                return "To file an expense, I first need your Employee ID please."
            else:
                conversation_state["task"] = "apply_expense"
                conversation_state["expense_type"], conversation_state["amount"], conversation_state["date"], conversation_state["receipt_path"], conversation_state["confirmed"] = None, None, None, None, False
                return "I can help with that. What category does this expense fall under? (e.g., Travel, Meals, Software)"

        if "apply" in query.lower() and "leave" in query.lower():
            if "employee_data" in conversation_state:
                employee_data = conversation_state["employee_data"]
                employee_name = employee_data.get("full_name", "Employee")
                conversation_state["task"] = "apply_leave"
                conversation_state["leave_type"], conversation_state["dates"], conversation_state["confirmed"] = None, None, False
                balance_info = f"Okay, {employee_name}. You have {employee_data.get('annual_leave', 0)} Annual and {employee_data.get('sick_leave', 0)} Sick leave days remaining."
                return f"{balance_info} What type of leave do you want to apply for?"
            else:
                conversation_state["task"] = "awaiting_id_for_leave"
                return "To apply for leave, I first need your Employee ID please."

        # Priority 3: Handle direct login or personal queries
        if "employee_data" not in conversation_state:
            employee_data = get_employee_data(query)
            if employee_data:
                conversation_state["employee_data"] = employee_data
                return f"Welcome, {employee_data['full_name']}! How can I help you today?"

        if "employee_data" in conversation_state:
            employee_data = conversation_state["employee_data"]
            query_lower = query.lower()
            if "my name" in query_lower:
                return f"Your name on record is {employee_data.get('full_name', 'not found')}."
            if "my id" in query_lower or "my employee id" in query_lower:
                return f"Your Employee ID is {employee_data.get('employee_id', 'not found')}."
            if "my leave" in query_lower or "how many leave" in query_lower:
                annual, sick = employee_data.get('annual_leave', 'N/A'), employee_data.get('sick_leave', 'N/A')
                return f"You have {annual} Annual and {sick} Sick leave days remaining."

        # Priority 4: Fallback to Manual FAQ and RAG
        manual_answer = self._get_manual_answer(query)
        if manual_answer:
            return manual_answer
        
        result = self.qa_chain.invoke({"question": query})
        return result['answer']