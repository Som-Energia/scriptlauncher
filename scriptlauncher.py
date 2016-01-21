from flask import Flask
from yamlns import namespace as ns

app = Flask(__name__)

scripts = ns.load('scripts.yaml')

header = """\
<html>
<head>
<title>Lista de scripts</title>
</head>
<body>
<ul> 
"""
footer="</ul></body></html>"

@app.route('/')
def index():
    items = [
        '<li><a href="/script/{0}">{1}</a></li>'.format(scriptname,script.description)
        for scriptname,script in scripts.iteritems()
        ]

    return '\n'.join([header]+items+[footer])
    return script_index

@app.route('/script/<scriptname>')
def script(scriptname):
    execfile(scripts[scriptname].script)
    return 'OK'

if __name__ == '__main__':
    print '09'
    app.run(debug=1)
