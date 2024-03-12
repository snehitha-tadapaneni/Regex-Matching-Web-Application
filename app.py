from flask import Flask, render_template, request
import re

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        test_string = request.form['test_string']
        regex = request.form['regex']
        result = re.search(regex, test_string)
        if result:
            message = f"The regex '{regex}' was found in the test string '{test_string}'."
        else:
            message = f"The regex '{regex}' was not found in the test string '{test_string}'."
    else:
        message = ''
    return render_template('index.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)