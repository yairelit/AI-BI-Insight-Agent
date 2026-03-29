# 🤖 BI Insight Agent

An AI-powered Business Intelligence tool that transforms natural language questions into SQL queries, executes them against a local SQLite database, and provides concise business insights.

Built with **Cursor** using **Streamlit** and the **Google Gemini 3.1 Flash Lite** model.

---

## 🌟 Overview

The **BI Insight Agent** bridges the gap between non-technical users and data. Instead of writing complex SQL, users can simply ask questions in plain English. The agent handles the schema mapping, query generation, data retrieval, and even summarizes the findings into actionable business insights.

## 🚀 Features

* **Natural Language → SQL:** Generates optimized SQLite queries from user prompts.
* **Automated Execution:** Runs queries and displays results instantly via Streamlit.
* **Smart Insights:** Uses Gemini 3.1 Flash Lite to interpret raw data into human-readable summaries.
* **Security-Centric:** Includes logic to ensure only `SELECT` (read-only) statements are executed.
* **Custom Data Support:** Easily import your own CSV files into the system.

## 🛠️ Tech Stack

* **LLM:** [Google Gemini 3.1 Flash Lite Preview](https://aistudio.google.com/)
* **Frontend:** [Streamlit](https://streamlit.io/)
* **Data Engine:** Python, Pandas, and SQLite
* **Development:** Built & optimized using **Cursor AI**

---

## 📋 Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/bi-insight-agent.git](https://github.com/your-username/bi-insight-agent.git)
cd bi-insight-agent
```

### 2. Install Dependencies
Make sure you have Python 3.9+ installed.
```bash
pip install -r requirements.txt
```
### 3. Environment Configuration
Create a .env file in the root directory and add your Google API key:
```Code snippet
GOOGLE_API_KEY=your_gemini_api_key_here
GOOGLE_MODEL=gemini-3.1-flash-lite-preview
```
### 4. Prepare Your Data
The agent reads from a SQLite database generated from your CSV files.
1.  Place all your `.csv` files into the `data/` directory.
2.  Run the setup script to initialize the database:
    ```bash
    python scripts/setup_data.py
    ```

---

## 🖥️ Running the App

Launch the Streamlit dashboard:
```bash
streamlit run app.py
```
Once the app is running:
Enter your question (e.g., "What were the top 5 selling products?").
View the generated SQL code.
Analyze the Data Results table.
Read the AI-generated Insight for a quick summary.

## 📂 Project Structure

* `app.py`: The Streamlit frontend and main entry point.
* `scripts/setup_data.py`: Utility script to convert raw CSVs into a structured SQLite database.
* `data/`: Directory for your raw input CSV files.
* `src/`:
    * `__init__.py`: Makes the directory a Python package.
    * `agent.py`: The core BI Agent logic (SQL generation & summarization).
    * `database.py`: Manages SQLite connections and schema retrieval.
    * `prompts.py`: Contains the system instructions and few-shot examples for the LLM.
    * `utils.py`: Helper functions for SQL cleaning and security checks.

## 🛡️ Security & Safety
The agent is designed for **read-only** operations. It checks generated SQL for keywords like `DROP`, `DELETE`, or `UPDATE` to prevent accidental data loss. Always review the generated SQL before using it in a production environment.

---

**Developed by Yair Elitzur** *Turning data into dialogue.*
