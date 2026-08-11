# 💻 Interview Coding Platform

A Streamlit-based coding assessment platform for SQL and Python interview rounds.

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
streamlit run app.py
```
The app opens at `http://localhost:8501`

---

## 🔐 Default Credentials

| Role     | Username | Password  |
|----------|----------|-----------|
| Admin    | admin    | admin123  |

---

## 📁 File Structure

```
coding_test/
├── app.py           # Main Streamlit app (UI + routing)
├── db.py            # SQLite database layer + seeded questions
├── executor.py      # Code execution engine (SQL + Python)
├── requirements.txt
└── README.md
```

---

## ✨ Features

### For Candidates
- 5 random SQL + 5 random Python questions per session
- Live code editor with **paste disabled** (typing only)
- ✅ Green / ❌ Red result feedback after running
- Real SQL execution against in-memory SQLite tables
- Python function execution with test inputs
- Question navigator sidebar
- Live session timer

### For Admins
- Create temporary candidate accounts for interviews
- Delete / deactivate candidates after interview ends
- Browse full question bank (SQL & Python)
- Toggle questions active/inactive
- Add custom questions with Markdown descriptions
- View all candidate submissions and accuracy stats

---

## 🗄️ Database

SQLite (`interview_platform.db`) is auto-created on first run with:
- 8 SQL questions (Easy–Medium difficulty)
- 8 Python questions (Easy–Medium difficulty)

Questions are randomly sampled (5 SQL + 5 Python) per interview session.

---

## 📝 Adding Questions

**Via Admin Panel → Add Question:**
- Fill Title, Category (SQL/Python/PySpark), Difficulty
- Write description in Markdown
- Set Test Setup (SQL: `CREATE TABLE`/`INSERT` statements; Python: variable assignments like `n=5`)
- Set Expected Output (used for correctness check)
- Optionally add reference solution

---

## 🔒 Anti-Cheat

- Paste is blocked in the code editor via JavaScript event interception
- Each candidate gets a different random subset of questions
- All submissions are logged with timestamps

---

## 🛠️ Customisation

- Edit `db.py` → `_seed_questions()` to change default questions
- Modify time limit: add a `MAX_DURATION_MINUTES` constant and check in `page_exam()`
- PySpark support: add PySpark questions in the DB with category `PySpark`
