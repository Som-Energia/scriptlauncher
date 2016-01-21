#!/usr/bin/env python

from flask import Flask, request, Response
from yamlns import namespace as ns
import functools
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

def requires_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwd):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwd)
    return decorated

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    "No ha estat possible validar l'usuari.\n", 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'secret'

    import config
    config.ooop.update(
        user = username,
        pwd = password,
        )
    try:
        O = OOOP(**config.ooop)
        return True
    except:
        error("Unable to connect to ERP")
        return False


@app.route('/')
@requires_auth
def index():
    items = [
        '<h1>Scripts</h1>',
        ] + [
        '<li><a href="/run/{0}">{1}</a></li>'.format(scriptname,script.description)
        for scriptname,script in scripts.iteritems()
        ]

    return '\n'.join([header.format(style=''),'<lu>']+items+['</lu>',footer])



@app.route('/run/<scriptname>')
@requires_auth
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

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?Rd'
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', processes=8)



