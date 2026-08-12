import sqlite3
import os
import hashlib

DB_PATH = "interview_platform.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Admin table
    c.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )""")

    # Candidate users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            status TEXT DEFAULT 'active',
            sql_count INTEGER DEFAULT NULL,
            python_count INTEGER DEFAULT NULL,
            pyspark_count INTEGER DEFAULT NULL
        )""")
    # Migration: add columns to existing DBs
    for col, default in [("status","'active'"), ("sql_count","NULL"),
                          ("python_count","NULL"), ("pyspark_count","NULL")]:
        try:
            c.execute(f"ALTER TABLE candidates ADD COLUMN {col} {'TEXT' if col=='status' else 'INTEGER'} DEFAULT {default}")
            conn.commit()
        except Exception:
            pass

    # Questions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,  -- 'SQL', 'Python', 'PySpark'
            difficulty TEXT NOT NULL, -- 'Easy', 'Medium', 'Hard'
            expected_output TEXT NOT NULL,
            solution_code TEXT,
            test_input TEXT,
            is_active INTEGER DEFAULT 1
        )""")

    # Submissions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER,
            question_id INTEGER,
            code TEXT NOT NULL,
            is_correct INTEGER DEFAULT 0,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )""")

    # Interview sessions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER,
            question_ids TEXT,  -- JSON list of question IDs
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        )""")

    # Interview config table
    c.execute("""
        CREATE TABLE IF NOT EXISTS interview_config (
            id INTEGER PRIMARY KEY DEFAULT 1,
            sql_count INTEGER DEFAULT 5,
            python_count INTEGER DEFAULT 5,
            pyspark_count INTEGER DEFAULT 0
        )""")
    c.execute("INSERT OR IGNORE INTO interview_config (id,sql_count,python_count,pyspark_count) VALUES (1,5,5,0)")

    # Templates table
    c.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )""")

    # Template questions (junction table)
    c.execute("""
        CREATE TABLE IF NOT EXISTS template_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            position INTEGER DEFAULT 0,
            FOREIGN KEY (template_id) REFERENCES templates(id),
            FOREIGN KEY (question_id) REFERENCES questions(id),
            UNIQUE(template_id, question_id)
        )""")

    # Migrations for existing DBs
    for col_def in [
        ("status",        "TEXT",    "'active'"),
        ("sql_count",     "INTEGER", "NULL"),
        ("python_count",  "INTEGER", "NULL"),
        ("pyspark_count", "INTEGER", "NULL"),
        ("template_id",   "INTEGER", "NULL"),
    ]:
        try:
            c.execute(f"ALTER TABLE candidates ADD COLUMN {col_def[0]} {col_def[1]} DEFAULT {col_def[2]}")
        except Exception:
            pass

    conn.commit()

    # Create default admin if not exists
    admin_pass = hashlib.sha256("admin123".encode()).hexdigest()
    try:
        c.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)", ("admin", admin_pass))
        conn.commit()
    except sqlite3.IntegrityError:
        pass

    conn.close()
    _seed_questions()
    _migrate_strip_interviewer_content()
    _migrate_add_templates()
    _migrate_fix_candidate_status()



def _migrate_fix_candidate_status():
    """Fix any candidates with NULL or empty status — set to 'active'."""
    conn = get_conn()
    conn.execute(
        "UPDATE candidates SET status='active' WHERE is_active=1 AND (status IS NULL OR TRIM(status)='')"
    )
    conn.commit()
    conn.close()


def _migrate_add_templates():
    """Migration: add templates tables and template_id column to existing DBs."""
    conn = get_conn()
    c = conn.cursor()
    # Templates table
    c.execute("""CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL,
        description TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1)""")
    # Template questions
    c.execute("""CREATE TABLE IF NOT EXISTS template_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, template_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL, position INTEGER DEFAULT 0,
        FOREIGN KEY (template_id) REFERENCES templates(id),
        FOREIGN KEY (question_id) REFERENCES questions(id),
        UNIQUE(template_id, question_id))""")
    # Add template_id to candidates
    try:
        c.execute("ALTER TABLE candidates ADD COLUMN template_id INTEGER DEFAULT NULL")
    except Exception:
        pass
    conn.commit()
    conn.close()

def _migrate_strip_interviewer_content():
    """Auto-migration: remove Rubric and Optional follow-up sections from all questions."""
    import re
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, description FROM questions WHERE description LIKE '%Rubric%' OR description LIKE '%Optional follow%'"
    ).fetchall()
    for qid, desc in rows:
        cleaned = re.sub(r'\n\n?\*\*Rubric:\*\*\n.*', '', desc, flags=re.DOTALL)
        cleaned = re.sub(r'\n\n?\*\*Optional follow[\w\s\-]*?:\*\*.*', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = cleaned.rstrip()
        if cleaned != desc:
            conn.execute("UPDATE questions SET description=? WHERE id=?", (cleaned, qid))
    conn.commit()
    conn.close()


def _seed_questions():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM questions")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    sql_questions = [
        {
            "title": "Find Duplicate Emails",
            "description": """**Problem:** Write a SQL query to find all duplicate email addresses from a table called `Person`.

**Table: Person**
| Column | Type |
|--------|------|
| id | int |
| email | varchar |

**Example:**
```
Person table:
+----+------------------+
| id | email            |
+----+------------------+
| 1  | a@b.com          |
| 2  | c@d.com          |
| 3  | a@b.com          |
+----+------------------+
```
**Expected Output:** `a@b.com`

Write your query using the pre-created `Person` table.""",
            "category": "SQL",
            "difficulty": "Easy",
            "expected_output": "a@b.com",
            "test_input": "CREATE TABLE IF NOT EXISTS Person (id INT, email VARCHAR(100)); INSERT OR IGNORE INTO Person VALUES (1,'a@b.com'),(2,'c@d.com'),(3,'a@b.com');",
            "solution_code": "SELECT email FROM Person GROUP BY email HAVING COUNT(*) > 1;"
        },
        {
            "title": "Second Highest Salary",
            "description": """**Problem:** Write a SQL query to get the second highest salary from the `Employee` table. Return `NULL` if there is no second highest salary.

**Table: Employee**
| Column | Type |
|--------|------|
| id | int |
| salary | int |

**Example Input:**
```
+----+--------+
| id | salary |
+----+--------+
| 1  | 100    |
| 2  | 200    |
| 3  | 300    |
+----+--------+
```
**Expected Output:** `200`""",
            "category": "SQL",
            "difficulty": "Medium",
            "expected_output": "200",
            "test_input": "CREATE TABLE IF NOT EXISTS Employee (id INT, salary INT); INSERT OR IGNORE INTO Employee VALUES (1,100),(2,200),(3,300);",
            "solution_code": "SELECT MAX(salary) AS SecondHighestSalary FROM Employee WHERE salary < (SELECT MAX(salary) FROM Employee);"
        },
        {
            "title": "Customers Who Never Order",
            "description": """**Problem:** Write a SQL query to find all customers who never placed an order.

**Tables:**
- `Customers(id, name)`
- `Orders(id, customerId)`

**Example:**
```
Customers:        Orders:
+----+-------+   +----+------------+
| id | name  |   | id | customerId |
+----+-------+   +----+------------+
| 1  | Joe   |   | 1  | 3          |
| 2  | Henry |   +----+------------+
| 3  | Sam   |
| 4  | Max   |
+----+-------+
```
**Expected Output:** `Henry, Max`""",
            "category": "SQL",
            "difficulty": "Easy",
            "expected_output": "Henry\nJoe\nMax",
            "test_input": "CREATE TABLE IF NOT EXISTS Customers (id INT, name VARCHAR(50)); CREATE TABLE IF NOT EXISTS Orders (id INT, customerId INT); INSERT OR IGNORE INTO Customers VALUES (1,'Joe'),(2,'Henry'),(3,'Sam'),(4,'Max'); INSERT OR IGNORE INTO Orders VALUES (1,3);",
            "solution_code": "SELECT name FROM Customers WHERE id NOT IN (SELECT customerId FROM Orders) ORDER BY name;"
        },
        {
            "title": "Department Highest Salary",
            "description": """**Problem:** Write a SQL query to find employees who have the highest salary in each department.

**Tables:**
- `Employee(id, name, salary, departmentId)`
- `Department(id, name)`

**Expected Output format:** `Department | Employee | Salary`

**Example Output:**
```
IT | Max | 90000
Sales | Henry | 80000
```""",
            "category": "SQL",
            "difficulty": "Medium",
            "expected_output": "IT|Max|90000\nSales|Henry|80000",
            "test_input": "CREATE TABLE IF NOT EXISTS Department (id INT, name VARCHAR(50)); CREATE TABLE IF NOT EXISTS Employee (id INT, name VARCHAR(50), salary INT, departmentId INT); INSERT OR IGNORE INTO Department VALUES (1,'IT'),(2,'Sales'); INSERT OR IGNORE INTO Employee VALUES (1,'Joe',70000,1),(2,'Henry',80000,2),(3,'Sam',60000,2),(4,'Max',90000,1);",
            "solution_code": "SELECT d.name, e.name, e.salary FROM Employee e JOIN Department d ON e.departmentId = d.id WHERE e.salary = (SELECT MAX(salary) FROM Employee WHERE departmentId = e.departmentId) ORDER BY d.name;"
        },
        {
            "title": "Rank Scores",
            "description": """**Problem:** Write a SQL query to rank scores. Ties get the same rank, and the next rank skips no numbers (dense rank).

**Table: Scores**
| Column | Type |
|--------|------|
| id | int |
| score | decimal |

**Example Input:**
```
+----+-------+
| id | score |
+----+-------+
| 1  | 3.50  |
| 2  | 3.65  |
| 3  | 4.00  |
| 4  | 3.85  |
| 5  | 4.00  |
| 6  | 3.65  |
+----+-------+
```
**Expected Output:** Scores in descending order with dense rank. Top score `4.00` should have rank `1`.""",
            "category": "SQL",
            "difficulty": "Medium",
            "expected_output": "4\n4\n3.85\n3.65\n3.65\n3.5",
            "test_input": "CREATE TABLE IF NOT EXISTS Scores (id INT, score DECIMAL(4,2)); INSERT OR IGNORE INTO Scores VALUES (1,3.50),(2,3.65),(3,4.00),(4,3.85),(5,4.00),(6,3.65);",
            "solution_code": "SELECT score, DENSE_RANK() OVER (ORDER BY score DESC) as rank FROM Scores ORDER BY score DESC;"
        },
        {
            "title": "Consecutive Numbers",
            "description": """**Problem:** Write a SQL query to find all numbers that appear at least three times consecutively.

**Table: Logs**
| Column | Type |
|--------|------|
| id | int (auto-increment) |
| num | int |

**Example:**
```
+----+-----+
| id | num |
+----+-----+
| 1  | 1   |
| 2  | 1   |
| 3  | 1   |
| 4  | 2   |
| 5  | 1   |
| 6  | 2   |
| 7  | 2   |
+----+-----+
```
**Expected Output:** `1` (appears 3 times consecutively)""",
            "category": "SQL",
            "difficulty": "Medium",
            "expected_output": "1",
            "test_input": "CREATE TABLE IF NOT EXISTS Logs (id INT, num INT); INSERT OR IGNORE INTO Logs VALUES (1,1),(2,1),(3,1),(4,2),(5,1),(6,2),(7,2);",
            "solution_code": "SELECT DISTINCT l1.num FROM Logs l1 JOIN Logs l2 ON l1.id = l2.id - 1 JOIN Logs l3 ON l1.id = l3.id - 2 WHERE l1.num = l2.num AND l2.num = l3.num;"
        },
        {
            "title": "Rising Temperature",
            "description": """**Problem:** Write a SQL query to find all dates where the temperature was higher than the previous day.

**Table: Weather**
| Column | Type |
|--------|------|
| id | int |
| recordDate | date |
| temperature | int |

**Example:**
```
+----+------------+-------------+
| id | recordDate | temperature |
+----+------------+-------------+
| 1  | 2015-01-01 | 10          |
| 2  | 2015-01-02 | 25          |
| 3  | 2015-01-03 | 20          |
| 4  | 2015-01-04 | 30          |
+----+------------+-------------+
```
**Expected Output:** IDs `2` and `4`""",
            "category": "SQL",
            "difficulty": "Easy",
            "expected_output": "2\n4",
            "test_input": "CREATE TABLE IF NOT EXISTS Weather (id INT, recordDate DATE, temperature INT); INSERT OR IGNORE INTO Weather VALUES (1,'2015-01-01',10),(2,'2015-01-02',25),(3,'2015-01-03',20),(4,'2015-01-04',30);",
            "solution_code": "SELECT w1.id FROM Weather w1 JOIN Weather w2 ON DATE(w1.recordDate) = DATE(w2.recordDate, '+1 day') WHERE w1.temperature > w2.temperature ORDER BY w1.id;"
        },
        {
            "title": "Employee Bonus",
            "description": """**Problem:** Select the name and bonus of each employee whose bonus is less than 1000, or who has no bonus record at all.

**Tables:**
- `Employee(empId, name, supervisor, salary)`
- `Bonus(empId, bonus)`

**Example Data:**
```
Employee:                          Bonus:
+-------+--------+------------+   +-------+-------+
| empId | name   | salary     |   | empId | bonus |
+-------+--------+------------+   +-------+-------+
| 3     | Brad   | 4000       |   | 2     | 500   |
| 1     | John   | 1000       |   | 4     | 2000  |
| 2     | Dan    | 2000       |   +-------+-------+
| 4     | Thomas | 4000       |
+-------+--------+------------+
```

**Expected Output:**
```
+------+-------+
| name | bonus |
+------+-------+
| John | null  |
| Dan  | 500   |
| Brad | null  |
+------+-------+
```
*(Thomas has bonus 2000 ≥ 1000, so excluded)*""",
            "category": "SQL",
            "difficulty": "Easy",
            "expected_output": "John\nDan|500\nBrad",
            "test_input": "CREATE TABLE IF NOT EXISTS Employee (empId INT, name VARCHAR(50), supervisor INT, salary INT); CREATE TABLE IF NOT EXISTS Bonus (empId INT, bonus INT); INSERT OR IGNORE INTO Employee VALUES (3,'Brad',NULL,4000),(1,'John',3,1000),(2,'Dan',3,2000),(4,'Thomas',3,4000); INSERT OR IGNORE INTO Bonus VALUES (2,500),(4,2000);",
            "solution_code": "SELECT e.name, b.bonus FROM Employee e LEFT JOIN Bonus b ON e.empId = b.empId WHERE b.bonus < 1000 OR b.bonus IS NULL ORDER BY e.name DESC;"
        },
    ]

    python_questions = [
        {
            "title": "Two Sum",
            "description": """**Problem:** Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.

**Function signature:**
```python
def two_sum(nums, target):
    # your code here
```

**Example:**
```
Input: nums = [2, 7, 11, 15], target = 9
Output: [0, 1]  # nums[0] + nums[1] = 2 + 7 = 9
```

**Test cases your code will run against:**
- `two_sum([2,7,11,15], 9)` → `[0, 1]`
- `two_sum([3,2,4], 6)` → `[1, 2]`""",
            "category": "Python",
            "difficulty": "Easy",
            "expected_output": "[0, 1]",
            "test_input": "nums=[2,7,11,15]; target=9",
            "solution_code": "def two_sum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target-n], i]\n        seen[n] = i"
        },
        {
            "title": "Valid Palindrome",
            "description": """**Problem:** A phrase is a palindrome if it reads the same forward and backward after converting uppercase to lowercase and removing non-alphanumeric characters.

**Function signature:**
```python
def is_palindrome(s):
    # your code here
```

**Examples:**
```
Input: "A man, a plan, a canal: Panama"
Output: True

Input: "race a car"
Output: False
```""",
            "category": "Python",
            "difficulty": "Easy",
            "expected_output": "True",
            "test_input": "s='A man, a plan, a canal: Panama'",
            "solution_code": "def is_palindrome(s):\n    cleaned = ''.join(c.lower() for c in s if c.isalnum())\n    return cleaned == cleaned[::-1]"
        },
        {
            "title": "FizzBuzz",
            "description": """**Problem:** Write a function that returns a list of strings for numbers 1 to n:
- `"FizzBuzz"` for multiples of both 3 and 5
- `"Fizz"` for multiples of 3
- `"Buzz"` for multiples of 5
- The number itself otherwise

**Function signature:**
```python
def fizz_buzz(n):
    # your code here
```

**Example:**
```
Input: n = 5
Output: ["1", "2", "Fizz", "4", "Buzz"]
```""",
            "category": "Python",
            "difficulty": "Easy",
            "expected_output": "['1', '2', 'Fizz', '4', 'Buzz']",
            "test_input": "n=5",
            "solution_code": "def fizz_buzz(n):\n    res = []\n    for i in range(1, n+1):\n        if i % 15 == 0: res.append('FizzBuzz')\n        elif i % 3 == 0: res.append('Fizz')\n        elif i % 5 == 0: res.append('Buzz')\n        else: res.append(str(i))\n    return res"
        },
        {
            "title": "Merge Two Sorted Lists",
            "description": """**Problem:** Given two sorted lists, merge them into one sorted list.

**Function signature:**
```python
def merge_sorted(list1, list2):
    # your code here
```

**Example:**
```
Input: list1 = [1, 2, 4], list2 = [1, 3, 4]
Output: [1, 1, 2, 3, 4, 4]
```""",
            "category": "Python",
            "difficulty": "Easy",
            "expected_output": "[1, 1, 2, 3, 4, 4]",
            "test_input": "list1=[1,2,4]; list2=[1,3,4]",
            "solution_code": "def merge_sorted(list1, list2):\n    result = []\n    i = j = 0\n    while i < len(list1) and j < len(list2):\n        if list1[i] <= list2[j]:\n            result.append(list1[i]); i += 1\n        else:\n            result.append(list2[j]); j += 1\n    return result + list1[i:] + list2[j:]"
        },
        {
            "title": "Maximum Subarray",
            "description": """**Problem:** Given an integer array `nums`, find the contiguous subarray with the largest sum and return its sum.

**Function signature:**
```python
def max_subarray(nums):
    # your code here
```

**Example:**
```
Input: nums = [-2, 1, -3, 4, -1, 2, 1, -5, 4]
Output: 6  # [4, -1, 2, 1] has the largest sum = 6
```""",
            "category": "Python",
            "difficulty": "Medium",
            "expected_output": "6",
            "test_input": "nums=[-2,1,-3,4,-1,2,1,-5,4]",
            "solution_code": "def max_subarray(nums):\n    max_sum = cur = nums[0]\n    for n in nums[1:]:\n        cur = max(n, cur + n)\n        max_sum = max(max_sum, cur)\n    return max_sum"
        },
        {
            "title": "Climbing Stairs",
            "description": """**Problem:** You are climbing a staircase with `n` steps. Each time you can climb 1 or 2 steps. Return the number of distinct ways to reach the top.

**Function signature:**
```python
def climb_stairs(n):
    # your code here
```

**Example:**
```
Input: n = 5
Output: 8
```""",
            "category": "Python",
            "difficulty": "Easy",
            "expected_output": "8",
            "test_input": "n=5",
            "solution_code": "def climb_stairs(n):\n    if n <= 2: return n\n    a, b = 1, 2\n    for _ in range(3, n+1):\n        a, b = b, a + b\n    return b"
        },
        {
            "title": "Group Anagrams",
            "description": """**Problem:** Given an array of strings, group the anagrams together.

**Function signature:**
```python
def group_anagrams(strs):
    # your code here
```

**Example:**
```
Input: strs = ["eat","tea","tan","ate","nat","bat"]
Output: [["bat"],["nat","tan"],["ate","eat","tea"]]
(order within groups and between groups doesn't matter)
```

Your output will be checked by comparing sorted inner lists.""",
            "category": "Python",
            "difficulty": "Medium",
            "expected_output": "[['eat', 'tea', 'ate'], ['tan', 'nat'], ['bat']]",
            "test_input": "strs=['eat','tea','tan','ate','nat','bat']",
            "solution_code": "def group_anagrams(strs):\n    from collections import defaultdict\n    d = defaultdict(list)\n    for s in strs:\n        d[tuple(sorted(s))].append(s)\n    return list(d.values())"
        },
        {
            "title": "Flatten Nested List",
            "description": """**Problem:** Write a function to flatten a nested list (arbitrary depth) into a single flat list.

**Function signature:**
```python
def flatten(nested):
    # your code here
```

**Example:**
```
Input: [1, [2, [3, 4], 5], 6, [7, 8]]
Output: [1, 2, 3, 4, 5, 6, 7, 8]
```""",
            "category": "Python",
            "difficulty": "Medium",
            "expected_output": "[1, 2, 3, 4, 5, 6, 7, 8]",
            "test_input": "nested=[1,[2,[3,4],5],6,[7,8]]",
            "solution_code": "def flatten(nested):\n    result = []\n    for item in nested:\n        if isinstance(item, list):\n            result.extend(flatten(item))\n        else:\n            result.append(item)\n    return result"
        },
    ]

    all_questions = sql_questions + python_questions
    for q in all_questions:
        c.execute("""
            INSERT INTO questions (title, description, category, difficulty, expected_output, solution_code, test_input, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)""", (q["title"], q["description"], q["category"], q["difficulty"],
              q["expected_output"], q["solution_code"], q["test_input"]))


    # ── Questions from team PDF (mid-to-senior data engineering) ──────────────
    advanced_questions = [

        # ── Python 1: Build latest customer state from CDC events ─────────────
        {
            "title": " Build latest customer state from CDC events",
            "description": """**Difficulty:** Hard · **Time:** 20 min

**Problem:** You are given a list of dicts representing change events from a vendor CDC feed.

```python
events = [
  {"customer_id":"c1","event_ts":"2026-05-01T10:00:00","seq":1,"op":"UPSERT","email":"a@x.com","status":"active"},
  {"customer_id":"c1","event_ts":"2026-05-01T10:00:00","seq":1,"op":"UPSERT","email":"a@x.com","status":"active"},  # exact duplicate
  {"customer_id":"c1","event_ts":"2026-05-01T10:05:00","seq":2,"op":"UPSERT","email":None,"status":"inactive"},
  {"customer_id":"c2","event_ts":"2026-05-01T09:00:00","seq":5,"op":"DELETE"},
  {"customer_id":"c2","event_ts":"2026-05-01T08:00:00","seq":4,"op":"UPSERT","email":"b@x.com","status":"active"},
  {"customer_id":"c3","event_ts":"2026-05-01T11:00:00","seq":1,"op":"UPSERT","email":"c_old@x.com","status":"active"},
  {"customer_id":"c3","event_ts":"2026-05-01T11:00:00","seq":2,"op":"UPSERT","email":"c_new@x.com","status":None},
]
```

**Write:**
```python
def build_latest_customer_state(events) -> list[dict]:
    ...
```

**Requirements:**
- Remove **exact duplicate** events (all fields identical)
- Order by `(event_ts, seq)` — latest wins
- Preserve **latest non-null value per field** across history (null in latest row → fall back to most recent non-null)
- `DELETE` op removes the customer from final output
- Output sorted by `customer_id`

**Expected output** (2 customers — c2 is deleted):
```
[{'customer_id': 'c1', 'email': 'a@x.com', 'status': 'inactive'},
 {'customer_id': 'c3', 'email': 'c_new@x.com', 'status': 'active'}]
```""",
            "category": "Python",
            "difficulty": "Hard",
            "test_input": """events=[{"customer_id":"c1","event_ts":"2026-05-01T10:00:00","seq":1,"op":"UPSERT","email":"a@x.com","status":"active"},{"customer_id":"c1","event_ts":"2026-05-01T10:00:00","seq":1,"op":"UPSERT","email":"a@x.com","status":"active"},{"customer_id":"c1","event_ts":"2026-05-01T10:05:00","seq":2,"op":"UPSERT","email":None,"status":"inactive"},{"customer_id":"c2","event_ts":"2026-05-01T09:00:00","seq":5,"op":"DELETE"},{"customer_id":"c2","event_ts":"2026-05-01T08:00:00","seq":4,"op":"UPSERT","email":"b@x.com","status":"active"},{"customer_id":"c3","event_ts":"2026-05-01T11:00:00","seq":1,"op":"UPSERT","email":"c_old@x.com","status":"active"},{"customer_id":"c3","event_ts":"2026-05-01T11:00:00","seq":2,"op":"UPSERT","email":"c_new@x.com","status":None}]""",
            "expected_output": "c1|c3",
            "solution_code": """def build_latest_customer_state(events):
    from copy import deepcopy
    # 1. Deduplicate exact duplicates using frozenset of items
    seen = set()
    unique = []
    for e in events:
        key = tuple(sorted((k, str(v)) for k, v in e.items()))
        if key not in seen:
            seen.add(key)
            unique.append(e)
    # 2. Sort by (event_ts, seq)
    unique.sort(key=lambda e: (e["event_ts"], e.get("seq", 0)))
    # 3. Build per-customer state with null fallback
    state = {}
    for e in unique:
        cid = e["customer_id"]
        if e["op"] == "DELETE":
            state[cid] = None  # mark deleted
            continue
        if cid not in state or state[cid] is None:
            state[cid] = {}
        for k, v in e.items():
            if k in ("customer_id", "op", "event_ts", "seq"):
                continue
            if v is not None:
                state[cid][k] = v
            elif k not in state[cid]:
                state[cid][k] = v
    # 4. Remove deleted, sort by customer_id
    result = []
    for cid in sorted(state):
        if state[cid] is not None:
            row = {"customer_id": cid}
            row.update(state[cid])
            result.append(row)
    return result"""
        },

        # ── Python 2: Canonicalize multi-source entity records ────────────────
        {
            "title": "Canonicalize Multi-Source Entity Records",
            "description": """**Difficulty:** Hard · **Time:** 20 min

**Problem:** You receive daily records for the same business entity from multiple upstream systems. Records can be duplicated, partially populated, or arrive out of order.

```python
records = [
  {"entity_id":"e1","source":"crm","updated_at":"2026-05-01T10:00:00","name":"Acme Inc","status":"active","risk_score":None},
  {"entity_id":"e1","source":"vendor_api","updated_at":"2026-05-01T10:05:00","name":"Acme Incorporated","status":None,"risk_score":72},
  {"entity_id":"e1","source":"crm","updated_at":"2026-05-01T10:00:00","name":"Acme Inc","status":"active","risk_score":None},  # duplicate
  {"entity_id":"e2","source":"vendor_api","updated_at":"2026-05-01T09:00:00","name":None,"status":"blocked","risk_score":91},
  {"entity_id":"e2","source":"crm","updated_at":"2026-05-01T11:00:00","name":"Beta LLC","status":"active","risk_score":None},
]
```

**Write:**
```python
def canonicalize_entities(records: list[dict]) -> list[dict]:
    ...
```

**Return one row per `entity_id` with:**
- Exact duplicates removed
- Latest `updated_at` wins as default
- If latest value for a field is `null`, fall back to most recent non-null for that field
- `source_count` = number of **distinct** sources seen
- Output sorted by `entity_id`

**Expected output:**
```
[{ 'entity_id': 'e1' 'name':'Acme Incorporated', 'status':'active', 'risk_score':72, 'source_count'=2},
{'entity_id':e2 'name':'Beta LLC', 'status':'active', 'risk_score':91, 'source_count':2},]
```""",
            "category": "Python",
            "difficulty": "Hard",
            "test_input": """records=[{"entity_id":"e1","source":"crm","updated_at":"2026-05-01T10:00:00","name":"Acme Inc","status":"active","risk_score":None},{"entity_id":"e1","source":"vendor_api","updated_at":"2026-05-01T10:05:00","name":"Acme Incorporated","status":None,"risk_score":72},{"entity_id":"e1","source":"crm","updated_at":"2026-05-01T10:00:00","name":"Acme Inc","status":"active","risk_score":None},{"entity_id":"e2","source":"vendor_api","updated_at":"2026-05-01T09:00:00","name":None,"status":"blocked","risk_score":91},{"entity_id":"e2","source":"crm","updated_at":"2026-05-01T11:00:00","name":"Beta LLC","status":"active","risk_score":None}]""",
            "expected_output": "e1|e2",
            "solution_code": """def canonicalize_entities(records):
    # 1. Dedupe exact duplicates
    seen = set()
    unique = []
    for r in records:
        key = tuple(sorted((k, str(v)) for k, v in r.items()))
        if key not in seen:
            seen.add(key)
            unique.append(r)
    # 2. Sort ascending by updated_at so latest overwrites
    unique.sort(key=lambda r: r["updated_at"])
    # 3. Build canonical state with null fallback
    state = {}
    sources = {}
    skip_keys = {"entity_id", "source", "updated_at"}
    for r in unique:
        eid = r["entity_id"]
        if eid not in state:
            state[eid] = {"updated_at": r["updated_at"]}
            sources[eid] = set()
        sources[eid].add(r["source"])
        if r["updated_at"] >= state[eid]["updated_at"]:
            state[eid]["updated_at"] = r["updated_at"]
        for k, v in r.items():
            if k in skip_keys:
                continue
            if v is not None:
                state[eid][k] = v
            elif k not in state[eid]:
                state[eid][k] = None
    # 4. Build output
    result = []
    for eid in sorted(state):
        row = {"entity_id": eid}
        row.update(state[eid])
        row["source_count"] = len(sources[eid])
        result.append(row)
    return result"""
        },

        # ── Python 3: Build canonical vendor file load plan ───────────────────
        {
            "title": "Build a canonical vendor file load plan",
            "description": """**Difficulty:** Hard · **Time:** 15 min

**Problem:** You are given file delivery records from a vendor. Files can be redelivered, duplicated, or conflict.

```python
files = [
  {"vendor_file_id":"f1","arrived_ts":"2026-05-01T08:00:00","partition_date":"2026-04-30","checksum":"aaa","size_bytes":100},
  {"vendor_file_id":"f1","arrived_ts":"2026-05-01T08:05:00","partition_date":"2026-04-30","checksum":"aaa","size_bytes":100},  
  {"vendor_file_id":"f2","arrived_ts":"2026-05-01T08:10:00","partition_date":"2026-04-30","checksum":"bbb","size_bytes":200},
  {"vendor_file_id":"f2","arrived_ts":"2026-05-01T08:20:00","partition_date":"2026-04-30","checksum":"ccc","size_bytes":210},  
  {"vendor_file_id":"f3","arrived_ts":"2026-05-01T09:00:00","partition_date":"2026-05-01","checksum":"ddd","size_bytes":150},
]
```

**Write:**
```python
def build_load_plan(files: list[dict]) -> dict:
    ...
```

**Return a dict with:**
- `files_to_load` — one row per `vendor_file_id`, keeping **latest** `arrived_ts`
- `conflicts` — list of `vendor_file_id`s that appear with **different checksums**
- `bytes_by_partition` — total `size_bytes` of canonical files grouped by `partition_date`

**Expected output structure:**
```python
{'files_to_load': [{'vendor_file_id': 'f1',
   'arrived_ts': '2026-05-01T08:05:00',
   'partition_date': '2026-04-30',
   'checksum': 'aaa',
   'size_bytes': 100},
  {'vendor_file_id': 'f2',
   'arrived_ts': '2026-05-01T08:20:00',
   'partition_date': '2026-04-30',
   'checksum': 'ccc',
   'size_bytes': 210},
  {'vendor_file_id': 'f3',
   'arrived_ts': '2026-05-01T09:00:00',
   'partition_date': '2026-05-01',
   'checksum': 'ddd',
   'size_bytes': 150}],
 'conflicts': ['f2'],
 'bytes_by_partition': {'2026-04-30': 310, '2026-05-01': 150}}
```""",
            "category": "Python",
            "difficulty": "Hard",
            "test_input": """files=[{"vendor_file_id":"f1","arrived_ts":"2026-05-01T08:00:00","partition_date":"2026-04-30","checksum":"aaa","size_bytes":100},{"vendor_file_id":"f1","arrived_ts":"2026-05-01T08:05:00","partition_date":"2026-04-30","checksum":"aaa","size_bytes":100},{"vendor_file_id":"f2","arrived_ts":"2026-05-01T08:10:00","partition_date":"2026-04-30","checksum":"bbb","size_bytes":200},{"vendor_file_id":"f2","arrived_ts":"2026-05-01T08:20:00","partition_date":"2026-04-30","checksum":"ccc","size_bytes":210},{"vendor_file_id":"f3","arrived_ts":"2026-05-01T09:00:00","partition_date":"2026-05-01","checksum":"ddd","size_bytes":150}]""",
            "expected_output": "f2|2026-04-30|2026-05-01",
            "solution_code": """def build_load_plan(files):
    from collections import defaultdict
    # Group by vendor_file_id
    grouped = defaultdict(list)
    for f in files:
        grouped[f["vendor_file_id"]].append(f)
    files_to_load = []
    conflicts = []
    for fid, records in sorted(grouped.items()):
        records.sort(key=lambda r: r["arrived_ts"])
        latest = records[-1]
        files_to_load.append(latest)
        checksums = {r["checksum"] for r in records}
        if len(checksums) > 1:
            conflicts.append(fid)
    # bytes_by_partition using canonical (latest) files
    bytes_by_partition = defaultdict(int)
    for f in files_to_load:
        bytes_by_partition[f["partition_date"]] += f["size_bytes"]
    return {
        "files_to_load": files_to_load,
        "conflicts": sorted(conflicts),
        "bytes_by_partition": dict(sorted(bytes_by_partition.items()))
    }"""
        },

        # ── SQL 1: Current subscription state from append-only events ─────────
        {
            "title": "Current subscription state from append-only events",
            "description": """**Difficulty:** Hard · **Time:** 15 min

**Problem:** You have an append-only events table:
```sql
subscription_events(
  account_id  STRING,
  plan_id     STRING,
  event_ts    TIMESTAMP,
  ingest_ts   TIMESTAMP,
  event_type  STRING,   -- START, CHANGE, CANCEL
  amount      NUMERIC
)
```

**Write SQL that returns one row per `account_id` with:**
- `account_id`
- `current_plan_id`
- `current_amount`
- `is_active` (0 if CANCEL, 1 otherwise)
- `state_last_updated_ts`

**Rules:**
- Remove exact duplicates first
- Order by `event_ts`, break ties with `ingest_ts`
- Latest event determines current state
- `CANCEL` → `is_active = 0`
- Exactly **one row per account_id**

**Example Data:**
```
account_id | plan_id     | event_ts            | event_type | amount
-----------+-------------+---------------------+------------+-------
a1         | plan_basic  | 2026-01-01T10:00:00 | START      | 9.99
a1         | plan_basic  | 2026-01-01T10:00:00 | START      | 9.99   
a1         | plan_pro    | 2026-02-01T10:00:00 | CHANGE     | 19.99
a2         | plan_basic  | 2026-01-15T08:00:00 | START      | 9.99
a2         | plan_basic  | 2026-03-01T09:00:00 | CANCEL     | 9.99
a3         | plan_pro    | 2026-02-10T12:00:00 | START      | 19.99
```

**Expected Output:**
```
account_id | current_plan_id | current_amount | is_active | state_last_updated_ts
-----------+-----------------+----------------+-----------+----------------------
a1         | plan_pro        | 19.99          | 1         | 2026-02-01T10:00:00
a2         | plan_basic      | 9.99           | 0         | 2026-03-01T09:00:00
a3         | plan_pro        | 19.99          | 1         | 2026-02-10T12:00:00
```""",
            "category": "SQL",
            "difficulty": "Hard",
            "test_input": """CREATE TABLE IF NOT EXISTS subscription_events (account_id TEXT, plan_id TEXT, event_ts TEXT, ingest_ts TEXT, event_type TEXT, amount REAL);
INSERT OR IGNORE INTO subscription_events VALUES
('a1','plan_basic','2026-01-01T10:00:00','2026-01-01T10:01:00','START',9.99),
('a1','plan_basic','2026-01-01T10:00:00','2026-01-01T10:01:00','START',9.99),
('a1','plan_pro','2026-02-01T10:00:00','2026-02-01T10:01:00','CHANGE',19.99),
('a2','plan_basic','2026-01-15T08:00:00','2026-01-15T08:01:00','START',9.99),
('a2','plan_basic','2026-03-01T09:00:00','2026-03-01T09:01:00','CANCEL',9.99),
('a3','plan_pro','2026-02-10T12:00:00','2026-02-10T12:01:00','START',19.99);""",
            "expected_output": "a1|plan_pro|19.99|2026-02-01T10:00:00\na2|plan_basic|9.99|2026-03-01T09:00:00\na3|plan_pro|19.99|2026-02-10T12:00:00",
            "solution_code": """WITH deduped AS (
  SELECT DISTINCT account_id, plan_id, event_ts, ingest_ts, event_type, amount
  FROM subscription_events
),
ranked AS (
  SELECT *,
    ROW_NUMBER() OVER (
      PARTITION BY account_id
      ORDER BY event_ts DESC, ingest_ts DESC
    ) AS rn
  FROM deduped
)
SELECT
  account_id,
  plan_id            AS current_plan_id,
  amount             AS current_amount,
  CASE WHEN event_type = 'CANCEL' THEN 0 ELSE 1 END AS is_active,
  event_ts           AS state_last_updated_ts
FROM ranked
WHERE rn = 1
ORDER BY account_id;"""
        },

        # ── SQL 2: Latest KYC decision per user ───────────────────────────────
        {
            "title": "Latest KYC Decision Per User",
            "description": """**Difficulty:** Hard · **Time:** 15 min

**Problem:** You have two tables:
```sql
kyc_decisions(
  user_id      STRING,
  decision_ts  TIMESTAMP,
  ingest_ts    TIMESTAMP,
  decision     STRING,   -- approved, denied, manual_review
  reviewer_id  STRING
)
kyc_documents(
  user_id      STRING,
  document_id  STRING,
  doc_type     STRING,
  uploaded_ts  TIMESTAMP
)
```

**Return one row per `user_id` with:**
- `latest_decision`
- `decision_ts`
- `reviewer_id`
- `doc_count` — number of uploaded documents
- `latest_doc_ts`

**Requirements:**
- Break ties in decisions using `ingest_ts`
- Do **not** double-count documents
- Exactly one row per user

**Example Data:**
```
kyc_decisions:                                      kyc_documents:
user_id | decision_ts         | decision       | reviewer_id   user_id | document_id | doc_type
--------+---------------------+----------------+------------   --------+-------------+---------
u1      | 2026-03-01T10:00:00 | approved       | rev1          u1      | doc1        | passport
u1      | 2026-03-01T10:00:00 | denied         | rev2          u1      | doc2        | utility_bill
u2      | 2026-03-02T09:00:00 | manual_review  | rev3          u2      | doc3        | passport
u3      | 2026-03-03T11:00:00 | approved       | rev4          u3      | doc4        | passport
                                                               u3      | doc5        | bank_statement
```
*(u1 tie broken by ingest_ts → denied wins)*

**Expected Output:**
```
user_id | latest_decision | decision_ts         | reviewer_id | doc_count | latest_doc_ts
--------+-----------------+---------------------+-------------+-----------+--------------
u1      | denied          | 2026-03-01T10:00:00 | rev2        | 2         | 2026-02-05
u2      | manual_review   | 2026-03-02T09:00:00 | rev3        | 1         | 2026-02-10
u3      | approved        | 2026-03-03T11:00:00 | rev4        | 2         | 2026-02-20
```""",
            "category": "SQL",
            "difficulty": "Hard",
            "test_input": """CREATE TABLE IF NOT EXISTS kyc_decisions (user_id TEXT, decision_ts TEXT, ingest_ts TEXT, decision TEXT, reviewer_id TEXT);
CREATE TABLE IF NOT EXISTS kyc_documents (user_id TEXT, document_id TEXT, doc_type TEXT, uploaded_ts TEXT);
INSERT OR IGNORE INTO kyc_decisions VALUES
('u1','2026-03-01T10:00:00','2026-03-01T10:01:00','approved','rev1'),
('u1','2026-03-01T10:00:00','2026-03-01T10:02:00','denied','rev2'),
('u2','2026-03-02T09:00:00','2026-03-02T09:01:00','manual_review','rev3'),
('u3','2026-03-03T11:00:00','2026-03-03T11:01:00','approved','rev4');
INSERT OR IGNORE INTO kyc_documents VALUES
('u1','doc1','passport','2026-02-01T08:00:00'),
('u1','doc2','utility_bill','2026-02-05T09:00:00'),
('u2','doc3','passport','2026-02-10T10:00:00'),
('u3','doc4','passport','2026-02-15T11:00:00'),
('u3','doc5','bank_statement','2026-02-20T12:00:00');""",
            "expected_output": "u1|denied|2026-03-01T10:00:00|rev2\nu2|manual_review|2026-03-02T09:00:00|rev3\nu3|approved|2026-03-03T11:00:00|rev4",
            "solution_code": """WITH latest_decision AS (
  SELECT *,
    ROW_NUMBER() OVER (
      PARTITION BY user_id
      ORDER BY decision_ts DESC, ingest_ts DESC
    ) AS rn
  FROM kyc_decisions
),
doc_agg AS (
  SELECT user_id,
    COUNT(document_id) AS doc_count,
    MAX(uploaded_ts)   AS latest_doc_ts
  FROM kyc_documents
  GROUP BY user_id
)
SELECT
  ld.user_id,
  ld.decision     AS latest_decision,
  ld.decision_ts,
  ld.reviewer_id,
  COALESCE(da.doc_count, 0)   AS doc_count,
  da.latest_doc_ts
FROM latest_decision ld
LEFT JOIN doc_agg da ON ld.user_id = da.user_id
WHERE ld.rn = 1
ORDER BY ld.user_id;"""
        },

        # ── SQL 3: Rolling failed-payment rate by processor ───────────────────
        {
            "title": "Rolling 7-Day Failed Payment Rate",
            "description": """**Difficulty:** Hard · **Time:** 15 min

**Problem:**
```sql
payments(
  payment_id  STRING,
  processor   STRING,
  payment_ts  TIMESTAMP,
  status      STRING,   -- success, failed
  amount      NUMERIC
)
```

**Return one row per `(processor, payment_date)` with:**
- `payment_date`, `processor`
- `daily_total_payments`, `daily_failed_payments`, `daily_failed_rate`
- `rolling_7d_failed_rate`

**Requirements:**
- Use a window function for the rolling 7-day metric
- Rolling rate = **total failed ÷ total payments** in the 7-day window (not average of daily rates)

**Example Data:**
```
payment_id | processor | payment_ts          | status
-----------+-----------+---------------------+--------
p1         | stripe    | 2026-01-01T10:00:00 | success
p2         | stripe    | 2026-01-01T11:00:00 | failed
p3         | stripe    | 2026-01-02T10:00:00 | success
p4         | stripe    | 2026-01-02T11:00:00 | failed
p5         | stripe    | 2026-01-02T12:00:00 | failed
p6         | paypal    | 2026-01-01T09:00:00 | success
p7         | paypal    | 2026-01-01T10:00:00 | failed
```

**Expected Output (sample rows):**
```
payment_date | processor | daily_total | daily_failed | daily_rate | rolling_7d_rate
-------------+-----------+-------------+--------------+------------+----------------
2026-01-01   | paypal    | 2           | 1            | 0.5        | 0.5
2026-01-01   | stripe    | 2           | 1            | 0.5        | 0.5
2026-01-02   | stripe    | 3           | 2            | 0.6667     | 0.6
```""",
            "category": "SQL",
            "difficulty": "Hard",
            "test_input": """CREATE TABLE IF NOT EXISTS payments (payment_id TEXT, processor TEXT, payment_ts TEXT, status TEXT, amount REAL);
INSERT OR IGNORE INTO payments VALUES
('p1','stripe','2026-01-01T10:00:00','success',100),
('p2','stripe','2026-01-01T11:00:00','failed',50),
('p3','stripe','2026-01-02T10:00:00','success',200),
('p4','stripe','2026-01-02T11:00:00','failed',75),
('p5','stripe','2026-01-02T12:00:00','failed',30),
('p6','paypal','2026-01-01T09:00:00','success',120),
('p7','paypal','2026-01-01T10:00:00','failed',60),
('p8','paypal','2026-01-03T08:00:00','success',90),
('p9','stripe','2026-01-03T09:00:00','success',110);""",
            "expected_output": "2026-01-01|paypal|2|0.5\n2026-01-03|paypal|0.0|0.3333\n2026-01-01|stripe|2|0.5\n2026-01-02|stripe|3|2\n2026-01-03|stripe|0.0|0.5",
            "solution_code": """WITH daily AS (
  SELECT
    DATE(payment_ts) AS payment_date,
    processor,
    COUNT(*)                                        AS daily_total_payments,
    SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS daily_failed_payments,
    ROUND(
      1.0 * SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) / COUNT(*), 4
    )                                               AS daily_failed_rate
  FROM payments
  GROUP BY DATE(payment_ts), processor
)
SELECT
  payment_date,
  processor,
  daily_total_payments,
  daily_failed_payments,
  daily_failed_rate,
  ROUND(
    1.0 * SUM(daily_failed_payments) OVER w / SUM(daily_total_payments) OVER w,
    4
  ) AS rolling_7d_failed_rate
FROM daily
WINDOW w AS (
  PARTITION BY processor
  ORDER BY payment_date
  ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
)
ORDER BY processor, payment_date;"""
        },

        # ── SQL Debug 1: Fix broken daily orders model ────────────────────────
        {
            "title": "Debug: Fix Broken Daily Orders Model",
            "description": """**Difficulty:** Medium · **Time:** 12 min

**You are given:**
```sql
orders(order_id, customer_id, order_ts, status, total_amount)
-- status values: placed, shipped, cancelled

order_items(order_id, sku, quantity, unit_price)
```

**A teammate wrote this query:**
```sql
SELECT
  DATE(o.order_ts)                 AS order_date,
  o.customer_id,
  COUNT(*)                         AS orders_count,
  SUM(oi.quantity * oi.unit_price) AS gross_revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status != 'cancelled'
GROUP BY 1, 2;
```

**Tasks:**
1. Explain what is wrong with this query
2. Write a corrected CTE-based query returning:
   - `order_date`, `customer_id`, `orders_count`, `gross_revenue`, `avg_order_value`, `latest_order_ts`

**Requirements:** exclude cancelled, no double-counting, item-level revenue, CTE-based.

**Example Data:**
```
orders:                                    order_items:
order_id | customer_id | status   | ...   order_id | sku   | qty | price
---------+-------------+----------+----   ---------+-------+-----+------
o1       | cust1       | placed   |       o1       | sku_a | 2   | 50.0
o2       | cust1       | shipped  |       o1       | sku_b | 1   | 50.0
o3       | cust2       | placed   |       o2       | sku_c | 4   | 20.0
o4       | cust2       | cancelled|       o3       | sku_d | 2   | 100.0
```
*(o1 has 2 items → COUNT(*) would count it twice! That's the bug.)*

**Expected Output:**
```
order_date  | customer_id | orders_count | gross_revenue | avg_order_value | latest_order_ts
------------+-------------+--------------+---------------+-----------------+----------------
2026-03-01  | cust1       | 2            | 230.0         | 115.0           | 2026-03-01T14:00
2026-03-01  | cust2       | 1            | 200.0         | 200.0           | 2026-03-01T09:00
```""",
            "category": "SQL",
            "difficulty": "Medium",
            "test_input": """CREATE TABLE IF NOT EXISTS orders_tbl (order_id TEXT, customer_id TEXT, order_ts TEXT, status TEXT, total_amount REAL);
CREATE TABLE IF NOT EXISTS order_items (order_id TEXT, sku TEXT, quantity INT, unit_price REAL);
INSERT OR IGNORE INTO orders_tbl VALUES
('o1','cust1','2026-03-01T10:00:00','placed',150),
('o2','cust1','2026-03-01T14:00:00','shipped',80),
('o3','cust2','2026-03-01T09:00:00','placed',200),
('o4','cust2','2026-03-01T11:00:00','cancelled',50);
INSERT OR IGNORE INTO order_items VALUES
('o1','sku_a',2,50.0),('o1','sku_b',1,50.0),
('o2','sku_c',4,20.0),
('o3','sku_d',2,100.0),
('o4','sku_e',1,50.0);""",
            "expected_output": "2026-03-01|cust1|2|230.0\n2026-03-01|cust2|200.0|200.0",
            "solution_code": """WITH item_revenue AS (
  SELECT order_id,
    SUM(quantity * unit_price) AS order_revenue
  FROM order_items
  GROUP BY order_id
),
order_base AS (
  SELECT o.order_id, o.customer_id, o.order_ts,
    ir.order_revenue
  FROM orders_tbl o
  JOIN item_revenue ir ON o.order_id = ir.order_id
  WHERE o.status != 'cancelled'
)
SELECT
  DATE(order_ts)          AS order_date,
  customer_id,
  COUNT(order_id)         AS orders_count,
  SUM(order_revenue)      AS gross_revenue,
  AVG(order_revenue)      AS avg_order_value,
  MAX(order_ts)           AS latest_order_ts
FROM order_base
GROUP BY DATE(order_ts), customer_id
ORDER BY customer_id;"""
        },

        # ── SQL Debug 2: Fix broken latest-status query ───────────────────────
        {
            "title": "Debug: Fix Broken Latest Status Query",
            "description": """**Difficulty:** Medium · **Time:** 10 min

**You have:**
```sql
user_status_events(user_id, event_ts, ingest_ts, status)
```

**A teammate wrote:**
```sql
SELECT e.user_id, e.status, e.event_ts
FROM user_status_events e
JOIN (
  SELECT user_id, MAX(event_ts) AS max_ts
  FROM user_status_events
  GROUP BY user_id
) m ON e.user_id = m.user_id
   AND e.event_ts = m.max_ts;
```

**The query produces duplicate users and sometimes returns the wrong latest row.**

**Tasks:**
1. Explain why this happens
2. Rewrite to return exactly **one** latest row per user, breaking ties with `ingest_ts`

**Example Data:**
```
user_id | event_ts            | ingest_ts           | status
--------+---------------------+---------------------+-----------
u1      | 2026-03-01T10:00:00 | 2026-03-01T10:01:00 | active
u1      | 2026-03-01T10:00:00 | 2026-03-01T10:02:00 | suspended  ← same ts, later ingest
u2      | 2026-03-02T09:00:00 | 2026-03-02T09:01:00 | active
u2      | 2026-03-03T11:00:00 | 2026-03-03T11:01:00 | inactive
u3      | 2026-03-01T08:00:00 | 2026-03-01T08:01:00 | active
```
*(u1 has two rows with the same event_ts — the broken query returns BOTH)*

**Expected Output:**
```
user_id | status    | event_ts
--------+-----------+---------------------
u1      | suspended | 2026-03-01T10:00:00
u2      | inactive  | 2026-03-03T11:00:00
u3      | active    | 2026-03-01T08:00:00
```""",
            "category": "SQL",
            "difficulty": "Medium",
            "test_input": """CREATE TABLE IF NOT EXISTS user_status_events (user_id TEXT, event_ts TEXT, ingest_ts TEXT, status TEXT);
INSERT OR IGNORE INTO user_status_events VALUES
('u1','2026-03-01T10:00:00','2026-03-01T10:01:00','active'),
('u1','2026-03-01T10:00:00','2026-03-01T10:02:00','suspended'),
('u2','2026-03-02T09:00:00','2026-03-02T09:01:00','active'),
('u2','2026-03-03T11:00:00','2026-03-03T11:01:00','inactive'),
('u3','2026-03-01T08:00:00','2026-03-01T08:01:00','active');""",
            "expected_output": "u1|suspended|2026-03-01T10:00:00\nu2|inactive|2026-03-03T11:00:00\nu3|active|2026-03-01T08:00:00",
            "solution_code": """WITH ranked AS (
  SELECT *,
    ROW_NUMBER() OVER (
      PARTITION BY user_id
      ORDER BY event_ts DESC, ingest_ts DESC
    ) AS rn
  FROM user_status_events
)
SELECT user_id, status, event_ts
FROM ranked
WHERE rn = 1
ORDER BY user_id;"""
        },
    ]

    for q in advanced_questions:
        c.execute("""
            INSERT INTO questions (title, description, category, difficulty, expected_output, solution_code, test_input, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)""", (q["title"], q["description"], q["category"], q["difficulty"],
              q["expected_output"], q["solution_code"], q["test_input"]))

    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def verify_admin(username, password):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM admins WHERE username=? AND password_hash=?",
              (username, hash_password(password)))
    result = c.fetchone()
    conn.close()
    return result is not None


def get_candidate_question_config(candidate_id):
    """Return per-candidate question counts, falling back to global config."""
    conn = get_conn()
    cand = conn.execute(
        "SELECT sql_count, python_count, pyspark_count FROM candidates WHERE id=?",
        (candidate_id,)
    ).fetchone()
    conn.close()
    if cand and any(v is not None for v in [cand["sql_count"], cand["python_count"], cand["pyspark_count"]]):
        global_cfg = get_interview_config()
        return {
            "sql_count":     cand["sql_count"]     if cand["sql_count"]     is not None else global_cfg["sql_count"],
            "python_count":  cand["python_count"]  if cand["python_count"]  is not None else global_cfg["python_count"],
            "pyspark_count": cand["pyspark_count"] if cand["pyspark_count"] is not None else global_cfg["pyspark_count"],
        }
    return get_interview_config()


def verify_candidate(username, password):
    conn = get_conn()
    c = conn.cursor()
    # Use NULLIF to treat empty string same as NULL, then COALESCE
    c.execute(
        "SELECT * FROM candidates "
        "WHERE username=? AND password_hash=? AND is_active=1 "
        "AND COALESCE(NULLIF(status,''),'active')='active'",
        (username, hash_password(password))
    )
    result = c.fetchone()
    conn.close()
    return dict(result) if result else None


def change_admin_password(username, new_password):
    conn = get_conn()
    conn.execute(
        "UPDATE admins SET password_hash=? WHERE username=?",
        (hash_password(new_password), username)
    )
    conn.commit()
    conn.close()


def create_candidate(username, password, sql_count=None, python_count=None, pyspark_count=None):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO candidates (username, password_hash, is_active, status, sql_count, python_count, pyspark_count) "
            "VALUES (?,?,1,'active',?,?,?)",
            (username, hash_password(password), sql_count, python_count, pyspark_count)
        )
        conn.commit()
        conn.close()
        return True, "Candidate created successfully"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username already exists"


def reset_candidate_password(username, new_password):
    """Admin resets a candidate's password."""
    conn = get_conn()
    affected = conn.execute(
        "UPDATE candidates SET password_hash=? WHERE username=?",
        (hash_password(new_password), username)
    ).rowcount
    conn.commit()
    conn.close()
    return affected > 0


def deactivate_candidate(username):
    """Block login but keep all history."""
    conn = get_conn()
    conn.execute(
        "UPDATE candidates SET status='deactivated' WHERE username=?", (username,)
    )
    conn.commit()
    conn.close()


def reactivate_candidate(username):
    """Re-enable a deactivated candidate."""
    conn = get_conn()
    conn.execute(
        "UPDATE candidates SET status='active', is_active=1 WHERE username=?", (username,)
    )
    conn.commit()
    conn.close()


def delete_candidate(username):
    """Legacy — kept for compatibility. Calls deactivate."""
    return deactivate_candidate(username)


def get_all_candidates(include_deactivated=False):
    conn = get_conn()
    c = conn.cursor()
    if include_deactivated:
        c.execute(
            "SELECT id, username, created_at, COALESCE(status,'active') as status "
            "FROM candidates ORDER BY created_at DESC"
        )
    else:
        c.execute(
            "SELECT id, username, created_at, COALESCE(status,'active') as status "
            "FROM candidates WHERE is_active=1 AND COALESCE(status,'active')='active' "
            "ORDER BY created_at DESC"
        )
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows



# ── Template management ───────────────────────────────────────────────────────

def create_template(name, description=""):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO templates (name, description) VALUES (?,?)",
            (name.strip(), description.strip())
        )
        conn.commit()
        tid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return True, tid, "Template created"
    except sqlite3.IntegrityError:
        conn.close()
        return False, None, "Template name already exists"


def update_template(template_id, name=None, description=None):
    conn = get_conn()
    if name is not None:
        conn.execute("UPDATE templates SET name=? WHERE id=?", (name.strip(), template_id))
    if description is not None:
        conn.execute("UPDATE templates SET description=? WHERE id=?", (description.strip(), template_id))
    conn.commit()
    conn.close()


def delete_template(template_id):
    conn = get_conn()
    # Unassign from candidates first
    conn.execute("UPDATE candidates SET template_id=NULL WHERE template_id=?", (template_id,))
    conn.execute("DELETE FROM template_questions WHERE template_id=?", (template_id,))
    conn.execute("DELETE FROM templates WHERE id=?", (template_id,))
    conn.commit()
    conn.close()


def toggle_template(template_id, active):
    conn = get_conn()
    conn.execute("UPDATE templates SET is_active=? WHERE id=?", (1 if active else 0, template_id))
    conn.commit()
    conn.close()


def get_all_templates(active_only=False):
    conn = get_conn()
    if active_only:
        rows = conn.execute(
            "SELECT t.*, COUNT(tq.question_id) as q_count "
            "FROM templates t LEFT JOIN template_questions tq ON t.id=tq.template_id "
            "WHERE t.is_active=1 GROUP BY t.id ORDER BY t.name"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT t.*, COUNT(tq.question_id) as q_count "
            "FROM templates t LEFT JOIN template_questions tq ON t.id=tq.template_id "
            "GROUP BY t.id ORDER BY t.name"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_template(template_id):
    conn = get_conn()
    t = conn.execute("SELECT * FROM templates WHERE id=?", (template_id,)).fetchone()
    conn.close()
    return dict(t) if t else None


def get_template_questions(template_id):
    """Return full question dicts for a template, ordered by position."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT q.*, tq.position
        FROM template_questions tq
        JOIN questions q ON tq.question_id = q.id
        WHERE tq.template_id = ?
        ORDER BY tq.position, q.category, q.difficulty
    """, (template_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_question_to_template(template_id, question_id):
    conn = get_conn()
    try:
        pos = conn.execute(
            "SELECT COALESCE(MAX(position),0)+1 FROM template_questions WHERE template_id=?",
            (template_id,)
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO template_questions (template_id, question_id, position) VALUES (?,?,?)",
            (template_id, question_id, pos)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False  # Already added


def remove_question_from_template(template_id, question_id):
    conn = get_conn()
    conn.execute(
        "DELETE FROM template_questions WHERE template_id=? AND question_id=?",
        (template_id, question_id)
    )
    conn.commit()
    conn.close()


def assign_template_to_candidate(candidate_id, template_id):
    """Assign a template (or None to clear) to a candidate."""
    conn = get_conn()
    conn.execute(
        "UPDATE candidates SET template_id=? WHERE id=?",
        (template_id, candidate_id)
    )
    conn.commit()
    conn.close()


def get_candidate_template(candidate_id):
    """Return the template assigned to a candidate, or None."""
    conn = get_conn()
    row = conn.execute(
        "SELECT t.* FROM candidates c JOIN templates t ON c.template_id=t.id WHERE c.id=?",
        (candidate_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_questions_for_candidate(candidate_id):
    """
    Return the question list for a candidate.
    - If candidate has a template → return template questions
    - Else → return random questions based on candidate/global config
    """
    # Check for template
    tmpl = get_candidate_template(candidate_id)
    if tmpl:
        qs = get_template_questions(tmpl["id"])
        if qs:
            return qs, tmpl["name"]

    # Fall back to random
    cfg = get_candidate_question_config(candidate_id)
    qs = get_random_questions(
        sql_count=cfg["sql_count"],
        python_count=cfg["python_count"],
        pyspark_count=cfg.get("pyspark_count", 0)
    )
    return qs, None  # None = random mode

def get_interview_config():
    """Get the global default question count configuration."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM interview_config WHERE id=1").fetchone()
    conn.close()
    if row:
        return {"sql_count": row["sql_count"], "python_count": row["python_count"],
                "pyspark_count": row["pyspark_count"]}
    return {"sql_count": 5, "python_count": 5, "pyspark_count": 0}


def set_interview_config(sql_count, python_count, pyspark_count=0):
    """Update the global default question count configuration."""
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO interview_config (id, sql_count, python_count, pyspark_count) VALUES (1,?,?,?)",
        (max(0, int(sql_count)), max(0, int(python_count)), max(0, int(pyspark_count)))
    )
    conn.commit()
    conn.close()


def get_available_question_counts():
    """Return how many active questions exist per category."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM questions WHERE is_active=1 GROUP BY category"
    ).fetchall()
    conn.close()
    return {r["category"]: r["cnt"] for r in rows}


def get_random_questions(sql_count=5, python_count=5, pyspark_count=0):
    conn = get_conn()
    c = conn.cursor()
    result = []
    if sql_count > 0:
        c.execute("SELECT * FROM questions WHERE category='SQL' AND is_active=1 ORDER BY RANDOM() LIMIT ?", (sql_count,))
        result += [dict(r) for r in c.fetchall()]
    if python_count > 0:
        c.execute("SELECT * FROM questions WHERE category='Python' AND is_active=1 ORDER BY RANDOM() LIMIT ?", (python_count,))
        result += [dict(r) for r in c.fetchall()]
    if pyspark_count > 0:
        c.execute("SELECT * FROM questions WHERE category='PySpark' AND is_active=1 ORDER BY RANDOM() LIMIT ?", (pyspark_count,))
        result += [dict(r) for r in c.fetchall()]
    conn.close()
    return result


def get_candidate_detail(candidate_id, all_question_ids=None):
    """Return submission stats for a candidate including attempted/not-attempted."""
    conn = get_conn()
    # All submissions for this candidate (latest per question)
    subs = conn.execute("""
        SELECT s.question_id, q.title, q.category, q.difficulty,
               MAX(s.is_correct) as best_correct,
               COUNT(s.id) as attempts,
               MAX(s.submitted_at) as last_attempt
        FROM submissions s
        JOIN questions q ON s.question_id = q.id
        WHERE s.candidate_id = ?
        GROUP BY s.question_id
    """, (candidate_id,)).fetchall()
    subs = [dict(r) for r in subs]

    # Session info
    session = conn.execute(
        "SELECT question_ids, started_at FROM interview_sessions WHERE candidate_id=? ORDER BY started_at DESC LIMIT 1",
        (candidate_id,)
    ).fetchone()
    conn.close()

    attempted_ids = {s["question_id"] for s in subs}
    assigned_ids = []
    if session and session["question_ids"]:
        import json as _j
        try:
            assigned_ids = _j.loads(session["question_ids"])
        except Exception:
            pass

    not_attempted = []
    if assigned_ids:
        conn2 = get_conn()
        for qid in assigned_ids:
            if qid not in attempted_ids:
                q = conn2.execute("SELECT title, category, difficulty FROM questions WHERE id=?", (qid,)).fetchone()
                if q:
                    not_attempted.append({"question_id": qid, "title": q["title"],
                                          "category": q["category"], "difficulty": q["difficulty"]})
        conn2.close()

    return {
        "attempted": subs,
        "not_attempted": not_attempted,
        "assigned_count": len(assigned_ids),
        "attempted_count": len(subs),
        "correct_count": sum(1 for s in subs if s["best_correct"]),
        "session_started": session["started_at"] if session else None,
    }


def get_candidate_detail_full(candidate_id):
    """Extended detail — includes last submitted code per question for PDF report."""
    conn = get_conn()

    # Latest code + result per question (pick last submission by time)
    subs = conn.execute("""
        SELECT s.question_id, q.title, q.category, q.difficulty,
               MAX(s.is_correct) as best_correct,
               COUNT(s.id)       as attempts,
               MAX(s.submitted_at) as last_attempt
        FROM submissions s
        JOIN questions q ON s.question_id = q.id
        WHERE s.candidate_id = ?
        GROUP BY s.question_id
    """, (candidate_id,)).fetchall()
    subs = [dict(r) for r in subs]

    # Fetch the actual code from the most recent submission per question
    for sub in subs:
        row = conn.execute("""
            SELECT code FROM submissions
            WHERE candidate_id=? AND question_id=?
            ORDER BY submitted_at DESC LIMIT 1
        """, (candidate_id, sub["question_id"])).fetchone()
        sub["last_code"] = row["code"] if row else ""

    # Session info
    session = conn.execute(
        "SELECT question_ids, started_at FROM interview_sessions "
        "WHERE candidate_id=? ORDER BY started_at DESC LIMIT 1",
        (candidate_id,)
    ).fetchone()
    conn.close()

    attempted_ids = {s["question_id"] for s in subs}
    assigned_ids  = []
    if session and session["question_ids"]:
        import json as _j
        try:
            assigned_ids = _j.loads(session["question_ids"])
        except Exception:
            pass

    not_attempted = []
    if assigned_ids:
        conn2 = get_conn()
        for qid in assigned_ids:
            if qid not in attempted_ids:
                q = conn2.execute(
                    "SELECT title, category, difficulty FROM questions WHERE id=?", (qid,)
                ).fetchone()
                if q:
                    not_attempted.append({
                        "question_id": qid, "title": q["title"],
                        "category": q["category"], "difficulty": q["difficulty"]
                    })
        conn2.close()

    return {
        "attempted":       subs,
        "not_attempted":   not_attempted,
        "assigned_count":  len(assigned_ids),
        "attempted_count": len(subs),
        "correct_count":   sum(1 for s in subs if s["best_correct"]),
        "session_started": session["started_at"] if session else None,
    }


def save_submission(candidate_id, question_id, code, is_correct):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO submissions (candidate_id, question_id, code, is_correct) VALUES (?,?,?,?)",
              (candidate_id, question_id, code, 1 if is_correct else 0))
    conn.commit()
    conn.close()


def get_candidate_submissions(candidate_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT s.*, q.title, q.category
        FROM submissions s
        JOIN questions q ON s.question_id = q.id
        WHERE s.candidate_id = ?
        ORDER BY s.submitted_at DESC""", (candidate_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_active_session(candidate_id):
    """
    Return the most recent interview session for a candidate.
    Returns dict with session_id, question_ids (list), started_at.
    Returns None if no session exists.
    """
    import json
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM interview_sessions WHERE candidate_id=? ORDER BY started_at DESC LIMIT 1",
        (candidate_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    try:
        qids = json.loads(row["question_ids"]) if row["question_ids"] else []
    except Exception:
        qids = []
    return {"session_id": row["id"], "question_ids": qids, "started_at": row["started_at"]}


def get_session_questions(question_ids: list) -> list:
    """Fetch full question dicts for a list of IDs, preserving order."""
    if not question_ids:
        return []
    conn = get_conn()
    result = []
    for qid in question_ids:
        row = conn.execute("SELECT * FROM questions WHERE id=?", (qid,)).fetchone()
        if row:
            result.append(dict(row))
    conn.close()
    return result


def restore_session_answers(candidate_id: int, question_ids: list) -> dict:
    """
    Rebuild the answers dict from the submissions table.
    Returns {qid_key: {"code": last_code, "is_correct": best_correct, "result": {...}}}
    so the UI shows previous results on re-login.
    """
    if not question_ids:
        return {}
    conn = get_conn()
    answers = {}
    for qid in question_ids:
        # Get the latest submission for this question
        row = conn.execute("""
            SELECT code, is_correct, submitted_at FROM submissions
            WHERE candidate_id=? AND question_id=?
            ORDER BY submitted_at DESC LIMIT 1
        """, (candidate_id, qid)).fetchone()
        if row:
            answers[str(qid)] = {
                "code":       row["code"] or "",
                "is_correct": bool(row["is_correct"]),
                "result":     {
                    "is_correct": bool(row["is_correct"]),
                    "output":     "",
                    "error":      "",
                    "df_data":    None,
                },
            }
    conn.close()
    return answers


def start_interview_session(candidate_id, question_ids):
    import json
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO interview_sessions (candidate_id, question_ids) VALUES (?,?)",
              (candidate_id, json.dumps(question_ids)))
    conn.commit()
    session_id = c.lastrowid
    conn.close()
    return session_id


def get_all_questions():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM questions ORDER BY category, difficulty")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def add_question(title, description, category, difficulty, expected_output, solution_code, test_input):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO questions (title, description, category, difficulty, expected_output, solution_code, test_input)
                 VALUES (?,?,?,?,?,?,?)""",
              (title, description, category, difficulty, expected_output, solution_code, test_input))
    conn.commit()
    conn.close()


def toggle_question(question_id, active):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE questions SET is_active=? WHERE id=?", (1 if active else 0, question_id))
    conn.commit()
    conn.close()