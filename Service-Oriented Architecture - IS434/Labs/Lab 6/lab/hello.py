from flask import Flask, request, render_template_string

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/about")
def about():
    return "<p>About page</p>"


form_html = """
    <form method="POST">
        Enter your name: <input type="text" name="name">
        <input type="submit" value="Submit">
    </form>
"""


@app.route("/greet", methods=["GET", "POST"])
def greet():
    if request.method == "POST":
        user_name = request.form.get("name")
        return f"<h1>Hello, {user_name}!</h1>"
    return render_template_string(form_html)


if __name__ == "__main__":
    app.run(debug=True)

# Why __name__?
# __name__ is a special Python variable that holds the name of the current module.
# Flask uses this to:
# Know where to look for resources (like templates and static files).
# Configure paths correctly when the app runs.
# So if your main file is app.py, Flask uses __name__ to find the correct folder structure relative to it.
