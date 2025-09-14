# Employee Policy & HR Assistant 🧑‍💼🤖

An **AI-powered conversational assistant** that transforms static HR policy documents into a **dynamic, intelligent, and interactive chatbot**.  
The Employee Policy Assistant empowers employees by giving them instant access to HR policies, personalized assistance, and automated workflows — all from a modern, embeddable chat widget.  

Whether it’s **checking leave balances, applying for leave, filing expense claims, or asking FAQs**, this assistant streamlines employee services and automates repetitive HR tasks.  

---

## ✨ Why This Project Matters
Traditional HR policy PDFs are lengthy, static, and frustrating to navigate.  
**The Employee Policy Assistant revolutionizes this experience** by embedding a chatbot widget into any webpage, giving employees **instant, natural-language access** to company policies and HR processes.  

This project is more than just a chatbot it’s a **full-stack, open-source solution** that shows how AI + automation can reimagine workplace tools.  

---

## 🚀 Key Features
- **Conversational Q&A**: Ask natural questions like *“What’s the dress code?”* and get concise, policy-backed answers.
- **Personalized Assistance**: Identify employees via ID and provide tailored info (e.g., leave balances).
- **Automated Leave Application**:  
  - Guided, step-by-step leave requests  
  - Smart calendar with holiday/weekend detection  
  - Email notification to HR with all details  
- **Expense Claims**: Submit expense type, amount, date, and upload receipts directly in chat.  
- **Instant FAQs**: Handle common IT/HR queries instantly (e.g., *“How do I raise an IT ticket?”*).  

---

## 🏗️ Technical Architecture

### Backend (Python + FastAPI)
- **Core logic**: `ChatbotCore` orchestrates skills (policy Q&A, leave requests, expenses).  
- **Policy Q&A**: Retrieval-Augmented Generation (RAG) pipeline using **LangChain**, **Sentence-Transformers**, and **FAISS** vector database.  
- **LLM**: `mistralai/Mistral-7B-Instruct-v0.2`.  
- **Document Parsing**: PyMuPDF for PDF processing.  
- **Tooling**: Executes real-world actions (e.g., sending HR/Finance emails).  

### Frontend (Web Widget)
- Built with **HTML5, CSS3, and vanilla JavaScript**.  
- Lightweight, embeddable chat widget with dynamic UI:  
  - Message bubbles  
  - Interactive buttons  
  - Calendar (Flatpickr.js)  
  - File uploads  
- Async communication with backend via REST API (`/chat` endpoint).  

---

## ⚙️ Technology Stack
**Backend**: Python, FastAPI, Uvicorn, LangChain, FAISS, Sentence-Transformers, PyMuPDF, Torch  
**Frontend**: HTML, CSS, JavaScript (ES6+), Flatpickr.js  
**Environment & Tools**: venv, Git & GitHub  

---

## 📂 Project Files
- `Employees.json` → mock employee database  
- `Faqs.json` → list of trained FAQs and answers  
- `Holidays.json` → predefined holidays for leave management  
- `uploads/` → stores employee-uploaded proofs/receipts  
- `MPC Policy book.pdf` → HR policy reference  
- `backend terminal` → displays all simulated/generated emails  

---

## 🧑‍💻 User Guide – Running the Project

### Prerequisites
- Python **3.8+**  
- VS Code (recommended)  
- TogetherAI account (for API key)  

### Steps
1. **Clone the repository**  
   ```bash
   git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git
   cd YOUR-REPO
   
2. **Setup Backend**
   python -m venv venv
   .\venv\Scripts\activate
   pip install fastapi uvicorn langchain langchain-community langchain-core openai faiss-cpu    sentence-transformers pymupdf torch python-dotenv

3. **Environment Setup**
   Create a .env file
   Add your TogetherAI API key:
   TOGETHERAI_API_KEY=your_api_key_here

4. **Run Backend**
   uvicorn app.main:app --port 5000

5. **Run Frontend**
   python -m http.server 8000

Optional: Real Email Integration

To send real emails via Gmail instead of simulation:
Generate a 16-digit Google App Password.
Update .env:
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-16-digit-app-password
Update core.py with the new send_email function

You can Update the Policy Book with any document/s of your choice and add the path to core.py file and the faiss folder. The Model will re-evaluate the document and work just fine for the new documents as well.

**🤝 Contributing**

This project is open-source — contributions, issues, and feature requests are welcome!
Fork the repo
Create your feature branch (git checkout -b feature/AmazingFeature)
Commit changes (git commit -m 'Add some Feature')
Push to the branch (git push origin feature/AmazingFeature)
Open a Pull Request

**📜 License**

This project is released as open-source under the MIT License.
You are free to use, modify, and distribute it in both commercial and personal projects.
