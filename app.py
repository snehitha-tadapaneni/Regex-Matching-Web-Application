from flask import Flask, render_template, request
from markupsafe import Markup, escape
import regex as re  # 'regex' supports timeouts and nicer features than 're'

app = Flask(__name__)

# Small helper to compile flags from the form
def build_flags(form):
    flags = 0
    if form.get('IGNORECASE'):
        flags |= re.IGNORECASE
    if form.get('MULTILINE'):
        flags |= re.MULTILINE
    if form.get('DOTALL'):
        flags |= re.DOTALL
    if form.get('VERBOSE'):
        flags |= re.VERBOSE
    return flags

# Highlight matches by wrapping them in <mark>
def highlight_matches(text, matches):
    if not matches:
        return escape(text)

    parts = []
    last = 0
    for m in matches:
        s, e = m.span()
        parts.append(escape(text[last:s]))
        parts.append(Markup('<mark>') + escape(text[s:e]) + Markup('</mark>'))
        last = e
    parts.append(escape(text[last:]))
    return Markup('').join(parts)

@app.route('/', methods=['GET', 'POST'])
def index():
    context = {
        "message": "",
        "pattern": "",
        "test_string": "",
        "flag_values": {"IGNORECASE": False, "MULTILINE": False, "DOTALL": False, "VERBOSE": False},
        "highlighted": None,
        "matches": [],
        "groups_header": [],
    }

    if request.method == 'POST':
        test_string = request.form.get('test_string', '')
        pattern = request.form.get('regex', '')
        context["pattern"] = pattern
        context["test_string"] = test_string
        context["flag_values"] = {
            "IGNORECASE": bool(request.form.get('IGNORECASE')),
            "MULTILINE": bool(request.form.get('MULTILINE')),
            "DOTALL": bool(request.form.get('DOTALL')),
            "VERBOSE": bool(request.form.get('VERBOSE')),
        }

        try:
            flags = build_flags(request.form)
            # timeout prevents catastrophic backtracking (ms). Adjust if needed.
            compiled = re.compile(pattern, flags=flags, timeout=200)
            matches = list(compiled.finditer(test_string, timeout=200))

            context["highlighted"] = highlight_matches(test_string, matches)
            context["matches"] = [
                {
                    "i": i + 1,
                    "span": f"{m.start()}–{m.end()}",
                    "text": m.group(0),
                    "groups": m.groups(),
                    "named": {k: v for k, v in m.groupdict().items()}
                }
                for i, m in enumerate(matches)
            ]

            # Build dynamic group headers: numbered and named
            max_positional = max((len(m["groups"]) for m in context["matches"]), default=0)
            named_keys = set()
            for m in context["matches"]:
                named_keys.update(m["named"].keys())
            context["groups_header"] = [f"g{i}" for i in range(1, max_positional + 1)] + (sorted(named_keys) if named_keys else [])

            if matches:
                context["message"] = f"✅ {len(matches)} match(es) found."
            else:
                context["message"] = "❌ No matches."

        except re.TimeoutError:
            context["message"] = "⏱️ Regex evaluation timed out (possible catastrophic backtracking). Try a simpler pattern."
        except re.error as err:
            context["message"] = f"🚫 Invalid pattern: {escape(str(err))}"

    return render_template('index.html', **context)

if __name__ == '__main__':
    # host='0.0.0.0' useful for Render/Railway previews
    app.run(host='0.0.0.0', port=5000, debug=True)
