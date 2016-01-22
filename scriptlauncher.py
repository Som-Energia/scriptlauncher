#!/usr/bin/env python
from flask import Flask, request, Response, render_template
from yamlns import namespace as ns
from ooop import OOOP
import functools
import subprocess
import deansi
app = Flask(__name__)

scripts = ns.load('scripts.yaml')

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
    #return username == 'admin' and password == 'secret'

    from config import Config
    cfg = Config(file('openerp.cfg'))
    cfg.user = username
    cfg.pwd = password
    try:
        O = OOOP(**cfg)
        return True
    except:
        print "Unable to connect to ERP"
        return False


@app.route('/')
@requires_auth
def index():

    return render_template('index_template.html',items=scripts.iteritems())

@app.route('/run/<scriptname>')
@requires_auth
def script(scriptname):
    output=subprocess.check_output(
        scripts[scriptname].script,
        stderr=subprocess.STDOUT,
        shell=True).decode('utf-8')
    return render_template('cmd_template.html',script_name=scriptname,script=scripts[scriptname].script,script_output=deansi.deansi(output),style=deansi.styleSheet())

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?Rd'
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', processes=8)
