from flask import Flask, render_template, request, jsonify
import ast
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("GEMINI_API_KEY", "")

# ---------- ROUTES ----------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/review", methods=["POST"])
def api_review():
    data = request.get_json()
    code = data.get("code", "").strip()
    mode = data.get("mode", "Lightning Scan")
    action = data.get("action", "review")

    if not code:
        return jsonify({"error": "No code provided."}), 400

    if not API_KEY:
        return jsonify({"error": "No API key configured. Set GEMINI_API_KEY in your .env file."}), 500

    # AST check (for review action)
    ast_result = None
    if action == "review":
        try:
            ast.parse(code)
            ast_result = "✅ AST Parsing: Structural integrity verified."
        except SyntaxError as e:
            ast_result = f"❌ AST Fracture Detected: {e}"

    # Build prompt based on action
    if action == "review":
        mode_context = "quick, high-level" if "Lightning" in mode else "deep, exhaustive"
        prompt = f"Please do a {mode_context} diagnostic review of the following Python code. Identify any syntax anomalies, logical bottlenecks, security vulnerabilities, and runtime inefficiencies. Format your response elegantly in Markdown, and provide a clear 'Code Quality Score' out of 10 at the top.\n\nCode:\n{code}"
    elif action == "fix":
        prompt = f"Refactor and fix all syntax errors, logical bugs, and bad practices in the following Python code. Return strictly ONLY the completely fixed code without any conversational explanation, wrapped in a python code block.\n\nCode:\n{code}"
    elif action == "explain":
        prompt = f"Analyze the following Python code systematically. Explain the absolute root cause of any bugs, syntax errors, or convoluted logical flows in detail. Offer a step-by-step resolution strategy for how the developer can resolve these specific issues themselves.\n\nCode:\n{code}"
    else:
        return jsonify({"error": "Invalid action."}), 400

    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        result_text = response.text

        # For fix action, extract code block
        fixed_code = None
        if action == "fix":
            fixed_code = result_text
            if "```python" in fixed_code:
                fixed_code = fixed_code.split("```python")[1].split("```")[0].strip()
            elif "```" in fixed_code:
                fixed_code = fixed_code.split("```")[1].split("```")[0].strip()

        return jsonify({
            "result": result_text,
            "ast_result": ast_result,
            "fixed_code": fixed_code
        })
    except Exception as e:
        return jsonify({"error": f"Gemini API Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)