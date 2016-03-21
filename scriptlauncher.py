#!/usr/bin/env python
from flask import Flask, request, Response, render_template, redirect, abort, flash, request,jsonify, session
from yamlns import namespace as ns
from ooop import OOOP
from collections import OrderedDict
import functools
import subprocess
import deansi
import shlex
import json
import os
from datetime import datetime
from werkzeug import secure_filename

app = Flask(__name__)
app.config.from_object(__name__)

filename=''
debug = True
import configdb


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
    configdb.ooop['user'] = username
    configdb.ooop['pwd'] = password
    try:
        O = OOOP(**configdb.ooop)
        return True
    except:
        print "Unable to connect to ERP"
        return False

def flash_errors(form):
    for field, errors in form.errors.items():
        flash(u"Error in the %s field - %s" % (
            field.label.text,
            errors
        ))

def config():
    if config.data is None or debug is True:
        config.data = ns.load('scripts.yaml')
    return config.data
config.data = None

def configScripts():
    scripts = ns()
    for key, category in config().items():
        scripts.update(category.scripts)
    return scripts

@app.route('/', methods=('GET', 'POST'))
@requires_auth
def index():
    scripts = config()
    forms={}
    w=file("/var/connectivity").read().strip()
    return render_template('index_template.html',
        items=scripts.items(),
        gdrive=w)

@app.route('/upload', methods=('GET','POST'))
@requires_auth
def upload():
    if request.method == 'POST':
        file = request.files['file']
        parmname=request.form['filename']
        session[parmname]=secure_filename(file.filename)    
        if file:
            filename_path = os.path.join(configdb.upload_folder, session[parmname])
            file.save(filename_path)
            return jsonify({"success":True})

@app.route('/runner/<cmd>')
@requires_auth
def runner(cmd):
    scripts = configScripts()
    script=scripts[cmd]
    script.islist = type(script.script) is list
    return render_template(
        'runner_template.html',
        name=cmd,
        style=deansi.styleSheet(),
        **script
        )

def execute(scriptname):
    import os
    scripts = configScripts()
    parameters = ns(request.form.items())
    params_list = []
    if 'parameters' in scripts[scriptname]:
        for parm_name,parm_data in scripts[scriptname]['parameters'].items():
            if parm_data.get('type', None) ==  'FILE':
                filename=os.path.join(configdb.upload_folder,session[parm_name])
                parameters[parm_name] = filename
            if not parameters.get(parm_name, None) and scripts[scriptname]['parameters'][parm_name].get('default',None):
                parameters[parm_name] = scripts[scriptname]['parameters'][parm_name]['default']
    script = scripts[scriptname].script
    if type(script) is not list:
        script = shlex.split(script)
    commandline = [
        piece.format(**parameters)
        for piece in script
        ]
    commandline = [cmd.replace('SOME_SRC',configdb.prefix) for cmd in commandline]
    print commandline
    return_code=0

    try:
        output=subprocess.check_output(commandline,stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        output=e.output
        return_code=e.returncode
    try:
        output_decoded=output.decode('utf-8')
    except UnicodeDecodeError:
        output_decoded=output.decode('latin-1')
    return json.dumps(dict(
        return_code=return_code,
        response=deansi.deansi(output_decoded),
        commandline=commandline,
        ))


@app.route('/run/<scriptname>', methods=['POST','GET'])
@requires_auth
def script_without_parms(scriptname):
    return execute(scriptname)


@app.errorhandler(400)
def badRequest(e):
    return render_template('400.html')


app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?Rd'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', processes=8)

