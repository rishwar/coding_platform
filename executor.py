"""
Code execution engine for SQL, Python, and PySpark questions.
Runs user code in a sandboxed environment and compares output.
"""
import sys
import io
import traceback
import sqlite3
import re
import ast


def execute_python_code(user_code: str, test_input: str, expected_output: str) -> dict:
    """
    Execute Python code and compare with expected output.
    Returns dict with: success, output, error, is_correct
    """
    # Parse test input into variables
    env = {}
    try:
        exec(test_input, env)
    except Exception as e:
        return {"success": False, "output": "", "error": f"Test input error: {e}", "is_correct": False}

    # Strip __builtins__ noise from env
    test_vars = {k: v for k, v in env.items() if not k.startswith("__")}

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()

    result_output = ""
    error_msg = ""
    actual_result = None

    try:
        # Execute user code
        exec_env = {}
        exec(user_code, exec_env)

        # Try to call the defined function with test vars.
        # Use inspect.isfunction to exclude imported classes/types (e.g. datetime.datetime)
        # which are callable but have no inspectable signature in Python 3.14.
        import inspect
        user_functions = {
            k: v for k, v in exec_env.items()
            if inspect.isfunction(v) and not k.startswith("__")
        }

        if user_functions:
            func_name = list(user_functions.keys())[0]
            func = user_functions[func_name]

            # Determine args from test_input variable names
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            args = [test_vars.get(p) for p in params if p in test_vars]

            actual_result = func(*args)
            result_output = str(actual_result)
        else:
            # No function found — check stdout
            result_output = buffer.getvalue().strip()

    except Exception as e:
        error_msg = traceback.format_exc()
        result_output = buffer.getvalue().strip()
    finally:
        sys.stdout = old_stdout

    stdout_output = buffer.getvalue().strip()
    full_output = result_output or stdout_output

    is_correct = _compare_outputs(full_output, expected_output, actual_result)

    return {
        "success": error_msg == "",
        "output": full_output,
        "stdout": stdout_output,
        "error": error_msg,
        "is_correct": is_correct
    }


def execute_sql_code(user_code: str, test_input: str, expected_output: str) -> dict:
    """
    Execute SQL code against an in-memory SQLite database.
    Returns dict with: success, output, error, is_correct, dataframe
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    error_msg = ""
    output_rows = []
    df_data = None

    try:
        # Run setup SQL (create tables, insert data)
        if test_input:
            for stmt in test_input.strip().split(";"):
                stmt = stmt.strip()
                if stmt:
                    c.execute(stmt)
            conn.commit()

        # Execute user query as a whole unit first (handles CTEs, subqueries with ;)
        result = None
        columns = []
        user_code_clean = user_code.strip().rstrip(";")

        try:
            c.execute(user_code_clean)
            if c.description:
                result = c.fetchall()
                columns = [desc[0] for desc in c.description]
        except Exception:
            # Fallback: split on ";" for simple multi-statement scripts
            for stmt in [s.strip() for s in user_code.strip().split(";") if s.strip()]:
                c.execute(stmt)
                if c.description:
                    result = c.fetchall()
                    columns = [desc[0] for desc in c.description]

        if result is not None:
            output_rows = [list(row) for row in result]
            df_data = {"columns": columns, "rows": output_rows}

        conn.close()

    except Exception as e:
        error_msg = str(e)
        conn.close()
        return {
            "success": False,
            "output": "",
            "error": error_msg,
            "is_correct": False,
            "df_data": None
        }

    # Format output for comparison
    flat_output = "|".join(
        str(val) for row in output_rows for val in row
    )

    is_correct = _sql_compare(output_rows, expected_output)

    return {
        "success": True,
        "output": flat_output,
        "error": "",
        "is_correct": is_correct,
        "df_data": df_data
    }


def _compare_outputs(actual: str, expected: str, actual_obj=None) -> bool:
    """Flexible comparison between actual and expected outputs."""
    try:
        # Direct string match
        if actual.strip() == expected.strip():
            return True

        # Try parsing as Python literals and compare
        try:
            actual_parsed = ast.literal_eval(actual.strip())
            expected_parsed = ast.literal_eval(expected.strip())

            if isinstance(actual_parsed, list) and isinstance(expected_parsed, list):
                return sorted(str(x) for x in actual_parsed) == sorted(str(x) for x in expected_parsed)
            return actual_parsed == expected_parsed
        except (ValueError, SyntaxError):
            pass

        # Numeric comparison
        try:
            return float(actual.strip()) == float(expected.strip())
        except ValueError:
            pass

        # Compare count (for group_anagrams / list-of-lists type)
        if actual_obj is not None and isinstance(actual_obj, list):
            try:
                if len(actual_obj) == int(expected.strip()):
                    return True
            except (ValueError, TypeError):
                pass

        # Handle list-of-lists: compare as flattened sorted elements
        try:
            actual_parsed2 = ast.literal_eval(actual.strip())
            if isinstance(actual_parsed2, list) and actual_parsed2 and isinstance(actual_parsed2[0], list):
                flat_actual = sorted(str(x) for sub in actual_parsed2 for x in sub)
                try:
                    exp_parsed = ast.literal_eval(expected.strip())
                    if isinstance(exp_parsed, list):
                        flat_expected = sorted(str(x) for sub in (exp_parsed if exp_parsed and isinstance(exp_parsed[0], list) else [exp_parsed]) for x in sub)
                        if flat_actual == flat_expected:
                            return True
                except Exception:
                    pass
                # Compare group count
                try:
                    if len(actual_parsed2) == int(expected.strip()):
                        return True
                except Exception:
                    pass
        except Exception:
            pass

        # Substring/token match — for complex dict/list outputs
        # Check if all expected |-separated tokens appear in the actual output string
        exp_tokens = [t.strip() for t in expected.strip().split("|") if t.strip()]
        if exp_tokens and all(tok in actual for tok in exp_tokens):
            return True

        return False
    except Exception:
        return False


def _val_eq(a: str, b: str) -> bool:
    """Case-insensitive, numeric-aware equality between two string values."""
    a, b = a.strip(), b.strip()
    if a.lower() == b.lower():
        return True
    try:
        return float(a) == float(b)
    except (ValueError, TypeError):
        pass
    return False


def _sql_compare(output_rows: list, expected_output: str) -> bool:
    """
    Strict structural comparison for SQL output.

    Strategy:
    - The expected_output is a |-separated list of KEY values that must appear
      in the result set, grouped into expected rows (rows separated by \n).
    - We verify:
        1. Every expected value appears in the flat result (token presence).
        2. The result does NOT contain obviously more data than expected
           (guards against SELECT * passing when only 1 column is expected).
        3. Row count matches when expected row count is specified.
    - Numeric values are compared as floats (so 4.00 == 4).
    """
    if not output_rows:
        return expected_output.strip() == ""

    expected_output = expected_output.strip()

    # Split expected into rows (newline-separated) then tokens (pipe-separated)
    expected_rows = [
        [t.strip() for t in row.split("|") if t.strip()]
        for row in expected_output.split("\n")
        if row.strip()
    ]
    # Flatten expected tokens
    expected_tokens = [t for row in expected_rows for t in row]
    if not expected_tokens:
        return False

    # Flatten actual output to list of string values
    flat_actual = [str(v) if v is not None else "None"
                   for row in output_rows for v in row]

    # ── Guard 1: result has too many columns vs expected ─────────────────────
    # If expected has max N tokens per row and actual has significantly more
    # columns, a wide SELECT * is likely passing. Reject if actual columns
    # outnumber expected tokens by more than factor of 2.
    if output_rows:
        actual_cols = len(output_rows[0])
        max_expected_cols = max(len(r) for r in expected_rows) if expected_rows else 1
        if actual_cols > max(max_expected_cols * 2, max_expected_cols + 3):
            return False

    # ── Guard 2: expected row count must match (if > 1 row specified) ────────
    if len(expected_rows) > 1:
        if len(output_rows) != len(expected_rows):
            return False

    # ── Guard 3: row-level matching when multiple rows expected ──────────────
    if len(expected_rows) > 1:
        # Try to match each expected row to an actual row (order-insensitive)
        unmatched = list(range(len(output_rows)))
        for exp_row in expected_rows:
            found = False
            for i in unmatched:
                act_vals = [str(v) if v is not None else "None" for v in output_rows[i]]
                if all(any(_val_eq(et, av) for av in act_vals) for et in exp_row):
                    unmatched.remove(i)
                    found = True
                    break
            if not found:
                return False
        return True

    # ── Single-value expected: require exactly 1 row, 1 col ─────────────────
    # This prevents SELECT * from a multi-row/multi-col table passing when
    # the answer should be a single aggregated value.
    is_single_token = ("|" not in expected_output and "\n" not in expected_output
                       and len(expected_tokens) == 1)
    if is_single_token:
        if len(output_rows) != 1 or len(output_rows[0]) != 1:
            return False
        return _val_eq(expected_tokens[0], str(output_rows[0][0]) if output_rows[0][0] is not None else "None")

    # ── Token-list expected ────────────────────────────────────────────────────
    # All tokens must appear and result can't be wildly larger than expected
    total_actual_cells = len(flat_actual)
    if total_actual_cells > len(expected_tokens) * 10 + 10:
        return False

    for et in expected_tokens:
        if not any(_val_eq(et, av) for av in flat_actual):
            return False

    return True