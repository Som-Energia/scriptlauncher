#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import (
    Flask,
    request,
    Response,
    render_template,
    flash,
    jsonify,
    session,
    send_file,
)
from yamlns import namespace as ns
from ooop import OOOP
import functools
import subprocess
import deansi
import shlex
import json
import os
import sys
from datetime import datetime
import tempfile

app = Flask(__name__)
app.config.from_object(__name__)

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
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
        )

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    if configdb.scriptlauncher.get('ignoreauth',False):
        return True
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
        config.data = ns()
        for configfile in sys.argv[1:] or ['scripts.yaml']:
            config.data.update(ns.load(configfile))
    return config.data

config.data = None

def configScripts():
    scripts = ns()
    for key, category in config().items():
        scripts.update(category.scripts)
    return scripts

def parseDownloadFileParm(paramName,script):
    filename=paramName+"."+script.parameters[paramName].extension
    if not script.islist:
        script.script=script.script.replace(paramName,filename)
        return script
    script.script = [
        argument if paramName not in argument
        else argument.replace(paramName, filename)
        for argument in script.script
    ]
    return script


@app.route('/', methods=('GET', 'POST'))
@requires_auth
def index():
    scripts = config()
    return render_template('index_template.html',
        items=scripts.items(),
        )


@app.route('/upload', methods=('POST',))
@requires_auth
def upload():
    afile = request.files['file']
    parmname = request.form['filename']
    extension = os.path.splitext(afile.filename)[1]
    tmpfile = tempfile.NamedTemporaryFile(suffix=extension, delete=False)
    session[parmname]=tmpfile.name
    if not afile:
        return #jsonify({"success":False})

    afile.save(tmpfile.name)
    return jsonify({"success":True})

@app.route('/download/<scriptname>/<param_name>/<filename>')
def download(scriptname, param_name, filename=None):
    scripts = configScripts()
    parameter = scripts[scriptname].parameters[param_name]
    filename = filename or (
        param_name + '.' + parameter.get('extension', 'bin'))
    try:
        return send_file(
            session[param_name],
            attachment_filename=filename,
            as_attachment=True,
            cache_timeout=-1,
            )
    except IOError:
        return render_template('not_available_file.html',script=scriptname,filename=filename)


@app.route('/runner/<cmd>')
@requires_auth
def runner(cmd):
    scripts = configScripts()
    script=scripts[cmd]
    script.islist = type(script.script) is list
    if 'parameters' in script:
        for paramname, param in script.parameters.items():
            if param.get('type', None) == 'FILEDOWN':
                script=parseDownloadFileParm(
                    paramname,script)
    return render_template(
        'runner_template.html',
        name=cmd,
        style=deansi.styleSheet(),
        **script
        )


def execute(scriptname):
    scripts = configScripts()
    parameters = ns(request.form.items())
    params_list = []
    output_file = False
    entry = scripts[scriptname]
    for name, definition in entry.get('parameters',ns()).items():
        ptype = definition.get('type',None)
        if ptype ==  'FILE':
            parameters[name] = session[name]
        elif ptype == 'FILEDOWN':
            extension = definition.get('extension','bin')
            tmpfile = tempfile.NamedTemporaryFile(suffix='.'+extension, delete=False)
            session[name]=tmpfile.name
            parameters[name] = session[name]
            output_file = definition.get('filename',name).format(**parameters)
            output_param = name
        if not parameters.get(name, None) and definition.get('default',None):
            parameters[name] = definition.default

    command = entry.script
    if type(command) is not list:
        command = [
            piece.decode('utf8')
            for piece in shlex.split(command.encode('utf8'))
            ]
    command = [
        piece.decode('utf8').format(**parameters).encode('utf8')
        for piece in command
        ]
    command = [
        piece.replace('SOME_SRC',configdb.scriptlauncher['prefix'])
        for piece in command
        ]
    return_code=0

    try:
        output=subprocess.check_output(command,stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        output=e.output
        return_code=e.returncode
    except Exception as e:
        import traceback
        traceback.print_exc()
        output='\033[31;1m'+traceback.format_exc()
        return_code=-1
    try:
        output_decoded=output.decode('utf-8')
    except UnicodeDecodeError:
        output_decoded=output.decode('latin-1')
    import pipes
    output_decoded = 'Running:' + ' '.join([
        pipes.quote(arg) for arg in command]) + '\n' + output_decoded

    if 'send' in entry:
        subst = ns(
            title = entry.title,
            today = datetime.today(),
            OKKO = '' if return_code == 0 else "ERROR",
            **parameters
            )

        if 'subject' in entry.send:
            subject = entry.send.subject
        else:
            subject = u"[Web Script] {OKKO} {title} {today:%Y-%m-%d}"
        subject = subject.format(**subst)

        to= [
            mail.format(**subst)
            for mail in entry.send.to
            if mail.format(**subst).strip()
        ]

        if to:
            import emili
            emili.sendMail(
                sender=configdb.smtp['user'],
                to=to,
                subject=subject,
                ansi=output_decoded,
                config='configdb.py', # TODO: pass the object instead
                stylesheets = [],
                verbose=True
            )

    return json.dumps(dict(
        script_name=scriptname,
        output_file=output_file,
        output_param=output_param,
        return_code=return_code,
        response=deansi.deansi(output_decoded),
        commandline=command,
        ))


@app.route('/run/<scriptname>', methods=['POST','GET'])
@requires_auth
def script_without_parms(scriptname):
    return execute(scriptname)


@app.errorhandler(400)
def badRequest(e):
    return render_template('400.html')

# TODO: Move this to configuration!!!
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?Rd'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', processes=8, threaded=False)



# vim: et sw=4 ts=4
