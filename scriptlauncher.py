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
    send_from_directory,
)
from yamlns import namespace as ns
from erppeek import Client
import functools
import subprocess
import deansi
import shlex
import json
import os
import sys
try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path
from datetime import datetime
import tempfile

app = Flask(__name__)
app.config.from_object(__name__)

debug = True
import configdb


def requires_auth(f):
    if os.environ.get('DISABLE_AUTH'):
        return f
    @functools.wraps(f)
    def decorated(*args, **kwd):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authentication_error()
        return f(*args, **kwd)
    return decorated

def authentication_error():
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
    configdb.erppeek['user'] = username
    configdb.erppeek['password'] = password
    try:
        O = Client(**configdb.erppeek)
        return True
    except:
        print("Unable to connect to ERP")
        return False

def flash_errors(form):
    for field, errors in form.errors.items():
        flash(u"Error in the %s field - %s" % (
            field.label.text,
            errors
        ))

def workingDirForScripts(scripts, workingdir, legacy=False):
    for script in scripts.values():
        thislegacy = legacy or script.get
        script.workingdir = (
            None if legacy and 'workingdir' not in script else
            None if script.get('workingdir',None) == 'LEGACY' else
            workingdir if 'workingdir' not in script else
            workingdir / script.workingdir
        )

def workingDirForCategories(categories, workingdir, legacy=False):
    for category in categories.values():
        workingDirForScripts(
            category.scripts,
            workingdir if 'workingdir' not in category else
            workingdir if category.workingdir == "LEGACY" else
            workingdir / category.workingdir
            ,
            legacy = (
                (legacy and 'workingdir' not in category)
                or category.get('workingdir') == 'LEGACY'
            ),
        )

def config():
    if config.data is None or debug is True:
        config.data = ns()
        for configfile in sys.argv[1:] or ['scripts.yaml']:
            workingdir = Path(configfile).parent.resolve(strict=True)
            categories = ns.load(configfile)
            workingDirForCategories(
                categories,
                workingdir,
                legacy=configdb.scriptlauncher.get('legacyWorkingDir',False),
            )
            config.data.update(categories)
    return config.data

config.data = None

def configScripts():
    scripts = ns()
    for key, category in config().items():
        scripts.update(category.scripts)
    return scripts

def parseDownloadFileParm(paramName, script):
    parameter = script.parameters[paramName]
    filename=paramName+"."+parameter.extension
    if not script.islist:
        script.script = script.script.replace('{'+paramName+'}','{'+filename+'}')
        return
    script.script = [
        argument.replace('{'+paramName+'}','{'+filename+'}')
        for argument in script.script
    ]
    return


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
    import uuid
    fileid=str(uuid.uuid4())
    session[fileid]=tmpfile.name
    if not afile:
        return #jsonify({"success":False})

    afile.save(tmpfile.name)
    return jsonify({"fileid": fileid, "success":True})

@app.route('/download/<scriptname>/<param_name>/<filename>')
def download(scriptname, param_name, filename=None):
    def fileNotAvailable():
        return render_template(
            'not_available_file.html',
            script=scriptname,
            filename=param_name)

    scripts = configScripts()

    if param_name not in scripts[scriptname]['parameters']:
        return fileNotAvailable()

    parameter = scripts[scriptname].parameters[param_name]
    filename = filename or (
        param_name + '.' + parameter.get('extension', 'bin'))
    dir=configdb.scriptlauncher.get('download_folder','/tmp')

    try:
        return send_from_directory(
            dir,
            session[param_name],
            download_name=filename,
            as_attachment=True,
            max_age=None,
            )
    except IOError:
        return fileNotAvailable()


@app.route('/runner/<cmd>')
@requires_auth
def runner(cmd):
    scripts = configScripts()
    script=scripts[cmd]
    script.islist = type(script.script) is list
    if 'parameters' in script:
        for paramname, param in script.parameters.items():
            if param.get('type', None) == 'FILEDOWN':
                parseDownloadFileParm(paramname,script)
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
    output_param = ''
    entry = scripts[scriptname]
    for name, definition in entry.get('parameters',ns()).items():
        ptype = definition.get('type',None)
        if ptype ==  'FILE':
            fileid = parameters.get(name+"-fileid", None)
            if fileid and fileid in session:
                parameters[name] = session[fileid]
            else:
                parameters[name] = definition.get('default', '/dev/null')

        elif ptype == 'FILEDOWN':
            extension = definition.get('extension','bin')
            tmpfile = tempfile.NamedTemporaryFile(
                suffix='.'+extension,
                delete=False,
                dir=configdb.scriptlauncher.get('download_folder','/tmp'),
                )
            parameters[name] = tmpfile.name # use the tmp file in the command
            session[name] = os.path.basename(tmpfile.name) # store the basefilename as cockie
            output_param = name # write down the output param name
            output_file = definition.get('filename',name).format(**parameters) # build the attachment file name
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

    workingdir = (
        os.getcwd()
        if entry.workingdir is None else
        entry.workingdir
    )
    try:
        output=subprocess.check_output(
            command,
            stderr=subprocess.STDOUT,
            cwd= str(workingdir),
        )
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

        to = [
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
