# 🐺 Fankaar Digital AI Agency

Welcome to your very own AI Digital Marketing Agency! This is like having 23 super-smart friends (like in Game of Thrones!) who work together to help you. You even have a special "Jarvis" screen to talk to them with your voice!

## 🚀 How to Start (The 5-Year-Old Version)

Follow these easy steps to wake up your agency:

### 1. Get your tools ready
Open your terminal (the black box where you type commands) and type:
```bash
pip install -r requirements.txt
```
*This is like making sure you have all the LEGO bricks before you start building.*

### 2. Tell the computer where the agency is
Type this command so the computer knows where to look:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
```

### 3. Wake up Jon Snow and the team
Type this to start the agency:
```bash
python backend/app/main.py
```
*Wait for the screen to say "App startup complete". This means Jon Snow is at his desk!*

### 4. Open your Jarvis screen
Open your web browser (like Chrome) and go to:
**http://localhost:8000**

### 5. Start talking!
1. Click the **Microphone** button.
2. Say something like: *"Jon, how is the team doing today?"*
3. Jon Snow will hear you and talk back to you!

---

## 🛠️ For the Grown-ups (Technical Details)

- **Backend**: FastAPI (Python 3.11)
- **Database**: SQLite with SQLAlchemy (using `extra_metadata` to avoid conflicts)
- **Voice**: Web Speech API (SpeechRecognition + Synthesis)
- **Agents**: 23 autonomous agents with independent memory.
- **Port**: Runs on port 8000 by default.

### Running with Uvicorn (Recommended)
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Starting the Worker
The agents start working automatically in the background. You can check their status at `http://localhost:8000/api/runtime/status`.
