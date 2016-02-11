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
import bitstring
import os
from datetime import datetime

app = Flask(__name__)
app.config.from_object(__name__)


filename=''
scripts = ns.load('scripts.yaml')
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

@app.route('/', methods=('GET', 'POST'))
@requires_auth
def index():
    global scripts
    scripts = ns.load('scripts.yaml')
    forms={}
    tags = set()
    for script in scripts.itervalues():
        for tag in script.tags:
            tags.add(tag)
    return render_template('index_template.html',
        items=scripts.items(),tags=tags)
@app.route('/upload', methods=('GET','POST'))
@requires_auth
def upload():
    filename=session['filename']
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename_path = os.path.join(configdb.upload_folder, filename)
            file.save(filename_path)
            return jsonify({"success":True})

@app.route('/runner/<cmd>')
@requires_auth
def runner(cmd):
    global scripts
    scripts = ns.load('scripts.yaml')
    script=scripts[cmd]
    if 'fileparameter' in script:
        session['filename']=scripts[cmd]['fileparameter']['name']
    return render_template(
        'runner_template.html',
        name=cmd,
        style=deansi.styleSheet(),
        **script
        )

def execute(scriptname):
    import os
    os.environ['SOME_SRC']=configdb.prefix
    parameters = ns(request.form.items())
    commandline = scripts[scriptname].script.format(**parameters)
    params_list = []
    if 'fileparameter' in scripts[scriptname]:
        if scripts[scriptname]['fileparameter']['code']:
            params_list.append(scripts[scriptname]['fileparameter']['code'])
        params_list.append(os.path.join(configdb.upload_folder,session['filename']))
    if 'parameters' in scripts[scriptname]:
        for parm in parameters:
            if scripts[scriptname]['parameters'][parm]['code']:
                params_list.append(scripts[scriptname]['parameters'][parm]['code'])
            params_list.append(' '.join(list(shlex.shlex(parameters[parm],posix=True))))

    commandline = scripts[scriptname].script.replace('$SOME_SRC',configdb.prefix)
    return_code=0
    try:
        output=subprocess.check_output([commandline]+params_list,stderr=subprocess.STDOUT).decode('utf-8')
    except subprocess.CalledProcessError as e:
        output=e.output
        return_code=bitstring.Bits(uint=e.returncode, length=8).unpack('int')[0]
    return '{"return_code":'+json.dumps(return_code)+', "response": '+json.dumps(deansi.deansi(output))+'}'


@app.route('/run/<scriptname>', methods=['POST','GET'])
@requires_auth
def script_without_parms(scriptname):
    global scripts
    scripts = ns.load('scripts.yaml')
    return execute(scriptname)


@app.errorhandler(400)
def badRequest(e):
    return render_template('400.html')


app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?Rd'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', processes=8)

