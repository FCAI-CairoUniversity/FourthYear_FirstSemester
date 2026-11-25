from flask import Flask, request, render_template_string

app = Flask(__name__)
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
