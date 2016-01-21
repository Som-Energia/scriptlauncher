from flask import Flask
from yamlns import namespace as ns
import subprocess
import deansi
app = Flask(__name__)

scripts = ns.load('scripts.yaml')

header = """\
<html>
<head>
<title>Lista de scripts</title>
<style>
{style}
</style>
</head>
<body>
"""
footer="</body></html>"

import json
print json.dumps(scripts)

@app.route('/')
def index():
    items = [
        '<li><a href="/script/{0}">{1}</a></li>'.format(scriptname,script.description)
        for scriptname,script in scripts.iteritems()
        ]

    return '\n'.join([header.format(style=''),'<lu>']+items+['</lu>',footer])
    return script_index

@app.route('/script/<scriptname>')
def script(scriptname):
    output=subprocess.check_output(
        scripts[scriptname].script,
        stderr=subprocess.STDOUT,
        shell=True)
    return '\n'.join([
        header.format(style=deansi.styleSheet()),
        '<div class="ansi_terminal">',
        deansi.deansi(output),
        '</div>',
        footer,
        ])
    return deansi.deansi(output)

if __name__ == '__main__':
    print '09'
    app.run(debug=1)
