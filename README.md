# 🚀 Educational Project: Testing a FastAPI RAG Agent

Welcome to your practical testing sandbox! This project is a microservice built with **FastAPI** that wraps an AI Agent designed using the **RAG (Retrieval-Augmented Generation)** pattern.

The agent can search through uploaded company documents and answer user questions based *only* on that data. Our main goal for this mentorship is to learn how to write robust automated tests for this AI system.

---

## 🛠️ Tech Stack & Requirements

* **OS:** Windows 11
* **IDE:** PyCharm (Community or Professional)
* **Language:** Python 3.10+
* **Frameworks:** FastAPI, LangChain, Uvicorn, PyTest
* **Vector Database:** Chroma DB (runs locally in-memory)
---

## 📂 Project Structure in PyCharm

Ensure your project directory looks exactly like this:

```text
llm-agent-testing/
│
├── app/                  # Application source code
│   ├── __init__.py
│   ├── agent.py          # AI Agent core logic
│   └── main.py           # FastAPI application & endpoints
│
├── requirements.txt      # Project dependencies
└── README.md             # This instruction file

```

---

## ⚙️ Step 1: Project Setup in PyCharm (Windows 11)

1. **Open the Project:** Launch PyCharm, click **Open**, and select your `llm-agent-testing` folder.
2. **Create a Virtual Environment (venv):**
**Open the Terminal:** Find the **Terminal** tab in PyCharm's bottom panel. 
Windows:

```bash
python -m venv venv

```
Linux:
```bash
python3 -m venv venv

```

3. Activate your virtual environment

Windows:

```bash
venv\Scripts\activate

```
Linux:
```bash
source venv/bin/activate

```

## 📦 Step 2: Installing Dependencies

In the PyCharm terminal, run the following command to install all required libraries:

```bash
pip install -r requirements.txt
```

---

## 🐳 Step 3: Spinning up PostgreSQL via Docker
We use Docker Desktop to run a real PostgreSQL database for our integration tests. This keeps your local Windows system clean and guarantees identical testing environments.

1. Make sure Docker Desktop is running on your Windows machine.
2. Open your terminal in the root directory of the project (where docker-compose.yml is located).
3. Start the PostgreSQL database container in background mode:

```cmd
docker compose up -d
```
4. To verify that the database container has successfully started, run:

```cmd
docker ps
```
You should see a running container named integration_test_db mapped to port 5432.


## 🔑 Step 4: Setting Up the OpenAI API Key in Windows

Our agent requires an API key to communicate with the language model. We pass it via environment variables so we don't accidentally hardcode it.

### Option A: Quick setup via PyCharm Terminal

Every time before you start the server, run this command in your PyCharm terminal:

```cmd
set OPENAI_API_KEY=your-actual-openai-api-key

```

*(Note: If you close the terminal tab, you will need to re-run this command in the new terminal window).*

### Option B: Permanent setup via PyCharm Configurations (Recommended)

To avoid typing the key every time:

1. In the top right of PyCharm, click the drop-down menu next to the green **Run** button -> **Edit Configurations...**
2. (If there are no configurations yet, we will create one in Step 4, then return to this step).
3. Find the **Environment variables** field, click the folder icon, and add a new entry:
* Name: `OPENAI_API_KEY`
* Value: `your-actual-openai-api-key`


---

## 🏃 Step 5: Launching the FastAPI Server

You can start the application using the PyCharm Terminal. Run the following command from the root directory:

```bash
uvicorn app.main:app --reload

```

If everything is configured correctly, server logs will start streaming, and you will see:

```text
INFO: Uvicorn running on [http://127.0.0.1:8000](http://127.0.0.1:8000) (Press CTRL+C to quit)

```

---

## 🧪 Step 6: Manual Testing via Swagger UI (Smoke Test)

When the server runs, FastAPI automatically generates an interactive API documentation page.

1. Open your browser and navigate to: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
2. You will see the **Swagger UI** dashboard with our endpoint: `POST /query`.
3. Click on the endpoint, then click the **Try it out** button on the right.
4. In the **Request body** JSON box, type a question related to the mock corporate documents (the data is preloaded automatically on startup; you can check the exact sentences in `app/main.py`).

**Example Request:**

```json
{
  "question": "What is our primary tech stack?"
}

```

5. Click the big blue **Execute** button.
6. Scroll down to the **Responses** section. In the `Server response` body (Code 200), you should see the AI agent's answer:

```json
{
  "answer": "Our primary tech stack consists of Python, FastAPI, and React."
}

```

---

## 🛠️ Troubleshooting

* **Error: `ModuleNotFoundError**` -> You either forgot to activate your `venv` or didn't run `pip install -r requirements.txt`.
* **Error: `RuntimeError: OPENAI_API_KEY environment variable is not set!**` -> The application cannot find your key. Double-check Step 3 (the `set` command must be run in the *exact same* terminal window where you start the server).
* **Port Conflict Error** -> If port 8000 is already in use by another app on your PC, change the port using this command: `uvicorn app.main:app --reload --port 8080`.

---

**Next Learning Stage:** We will start writing automated tests using `pytest` and learn how to use **mocks** so we can test this exact endpoint automatically, instantly, and for free!

```

```