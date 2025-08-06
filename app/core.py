# In app/core.py

import os
from langchain.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from sentence_transformers import SentenceTransformer, util
import torch
from dotenv import load_dotenv

load_dotenv()

# --- MODIFIED: Updated the prompt to ask for bullet points ---
custom_prompt_template = """Use the following pieces of context to answer the question at the end. 
If the context does not contain the answer, state that the information is not available in the provided policy.
Present the answer in clear, concise bullet points for easy readability.

Context: {context}

Question: {question}
Helpful Answer:"""

CUSTOM_PROMPT = PromptTemplate(
    template=custom_prompt_template, input_variables=["context", "question"]
)
# -----------------------------------------------------------


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
        # --- MODIFIED: Connected the custom prompt to the chain ---
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.db.as_retriever(search_kwargs={'k': 2}),
            memory=self.get_memory(),
            # This crucial line applies our custom instructions
            combine_docs_chain_kwargs={"prompt": CUSTOM_PROMPT}
        )
        # ---------------------------------------------------------

    def _setup_manual_qa(self):
        self.manual_qa = {
            "How do I raise a technical support ticket?": "To raise a technical support ticket, please email IT at itsupport@mpccloudconsulting.com with a short description and any screenshots of the issue.",
            "Who do I contact if my biometric punch-in is not recorded?": "If your punch-in is missed, please reach out to your reporting manager and send an email to attendance@mpccloudconsulting.com.",
            "Where can I check my leave balance?": "You can check your leave balance on the internal HRMS portal. If you don't have access, drop a note to hrsupport@mpccloudconsulting.com.",
            "Is there a canteen or food arrangement at the office?": "Yes, we have a pantry with tea and coffee. For meals, employees usually step out or order online. No full canteen service is available currently.",
            "What should I do if I forget my ID card?": "If you forget your ID card, inform your team lead and security. A temporary entry slip can be issued for the day.",
            "Are there any team outings or events planned?": "Team outings are planned on a quarterly basis. Keep an eye on the internal Teams channels or WhatsApp Group for any announcements.",
            "How do I get my Form 16?": "Form 16s are emailed directly by the finance team at the end of each financial year. You can request a duplicate from finance@mpccloudconsulting.com.",
            "Can I work remotely permanently?": "Permanent WFH is not currently offered. However, hybrid flexibility can be discussed with your reporting manager.",
            "Who do I talk to about payroll discrepancies?": "For payroll-related queries, email payroll@mpccloudconsulting.com. They usually respond within 1–2 business days.",
            "Hi":"Hi there, How can I help you today?",
            "Hello":"Hi there, How can I help you today?",
            "Thanks":"Thank You!",
            "Office Timings?":"The Office timings are from 9:30 AM to 6:30 PM with a 30 minute Break in between, from Monday to Friday",
            "What is the probation period?": "The standard probation period is 3 months, but it may vary based on role or department. Please check with your HR.",
            "Are internships paid?": "No, internships are generally not paid. The stipend amount is communicated in your offer letter or onboarding email if any.",
            "What’s the procedure for resignation?": "Resignation must be submitted via email to your reporting manager and HR. A notice period of 30–60 days applies.",
            "Can I change my shift timing?": "Shift changes can be requested through your manager and are approved based on team requirements.",
            "How are public holidays decided?": "Public holidays are based on the company’s annual holiday calendar, usually aligned with regional guidelines.",
            "Is there any shuttle facility for work hours?": "Yes, there is the shuttle provided by the building that transports employees from metro station to the office building. The shuttle offers services every 15/20 minutes.",
            "Can I bring a guest to the office?": "Visitors must be approved by your team lead and the Admin team in advance. ID verification is required.",
            "Where do I submit travel reimbursement bills?": "All travel bills must be uploaded to the Travel module of the HRMS within 7 days of the trip.",
            "What’s the policy for internal transfers?": "Internal transfers can be requested after 6 months of tenure, subject to approval from both departments.",
            "Are Saturdays off?": "Yes! the office has a 5-day work week from Monday to Friday. Saturdays and Sundays are off"
            "Saturdays working?":"No, Saturday and Sundays are off. Office is from Monday to Friday",
        }
        self.faq_encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.faq_questions = list(self.manual_qa.keys())
        self.faq_embeddings = self.faq_encoder.encode(self.faq_questions, convert_to_tensor=True)

    def get_memory(self):
        return self.memory

    def _get_manual_answer(self, query, threshold=0.75):
        """Checks for a match in the pre-defined FAQ."""
        query_embedding = self.faq_encoder.encode(query, convert_to_tensor=True)
        cosine_scores = util.pytorch_cos_sim(query_embedding, self.faq_embeddings)[0]
        top_result = torch.topk(cosine_scores, k=1)
        if top_result.values.item() >= threshold:
            return self.manual_qa[self.faq_questions[top_result.indices.item()]]
        return None

    def get_answer(self, query):
        manual_answer = self._get_manual_answer(query)
        if manual_answer:
            return manual_answer
        
        result = self.qa_chain.invoke({"question": query})
        return result['answer']