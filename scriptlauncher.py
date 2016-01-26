#!/usr/bin/env python
from flask import Flask, request, Response, render_template, redirect, abort, flash, request
from wtforms import StringField,SubmitField,FieldList
from wtforms.validators import DataRequired
from flask_wtf import Form
from yamlns import namespace as ns
from ooop import OOOP
from collections import OrderedDict
import functools
import subprocess
import deansi
app = Flask(__name__)

scripts = ns.load('scripts.yaml')


class ParameterForm(Form):

    parms = FieldList(StringField('Parameter'))
    submit = SubmitField("Execute")

    def validate(self):
        validation=True
        for parm,(parmname,val) in zip(self.parms,self.validations.iteritems()):
            try:
                if not val(parm.data):
                    print "validate: "+parm
                    self.errors[parm]='Invalid parameter {} '.format(parmname)
                    validation=False
            except Exception:
                print(repr(parm))
                self.errors[parm]='Invalid parameter {} '.format(parmname)
                validation=False
        return validation

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

def flash_errors(form):
    for field, errors in form.errors.items():
        flash(u"Error in the %s field - %s" % (
            field.label.text,
            errors
        ))

@app.route('/', methods=('GET', 'POST'))
@requires_auth
def index():
    scripts = ns.load('scripts.yaml')
    forms={}
    return render_template('index_template.html',items=scripts.iteritems())


@app.route('/runner/<cmd>')
@requires_auth
def runner(cmd):
    script=scripts[cmd]
    return render_template(
        'runner_template.html',
        name=cmd,
        style=deansi.styleSheet(),
        **script
        )

def execute(scriptname,parms=""):
    output=subprocess.check_output(
        scripts[scriptname].script+parms,
        stderr=subprocess.STDOUT,
        shell=True).decode('utf-8')
    return deansi.deansi(output)
    return render_template('cmd_template.html',script_name=scriptname,script=scripts[scriptname].script,script_output=deansi.deansi(output),style=deansi.styleSheet())


@app.route('/run/<scriptname>')
@requires_auth
def script_without_parms(scriptname):
    if 'parameters' in scripts[scriptname]:
        abort(400)
    return execute(scriptname)


@app.route('/run/<scriptname>/<parameters>')
@requires_auth
def script_with_parms(scriptname,parameters):
    param_list=parameters.split('&')
    if ('parameters' in scripts[scriptname] and len(filter(bool,param_list)) != len(scripts[scriptname].parameters)) or 'parameters' not in scripts[scriptname]:
        abort(400)
    param_spaced=' '+parameters.replace('&',' ')
    return execute(scriptname,parms=param_spaced)


@app.errorhandler(400)
def badRequest(e):
    return render_template('400.html')


app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?Rd'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', processes=8)

