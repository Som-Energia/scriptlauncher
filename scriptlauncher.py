#!/usr/bin/env python
from flask import Flask, request, Response, render_template, redirect, abort
from wtforms import StringField,SubmitField,FieldList
from wtforms.validators import DataRequired
from flask_wtf import Form
from yamlns import namespace as ns
from ooop import OOOP
import functools
import subprocess
import deansi
app = Flask(__name__)

scripts = ns.load('scripts.yaml')


class ParameterForm(Form):
    
    parms = FieldList(StringField('Parameter'))
    submit = SubmitField("Execute")
    def validate(self):
        return all(val(parm.data) for parm,val in zip(parms,validations))]

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


@app.route('/', methods=('GET', 'POST'))
@requires_auth
def index():
    scripts = ns.load('scripts.yaml')
    forms={}
    for key in scripts.iterkeys():
        forms[key]=ParameterForm(prefix=key)   
        forms[key].validations=[eval('lambda parm:'+val_func) for val_func in scripts[key].parameters.itervalues()]
        if forms[key].validate_on_submit() and forms[key].submit.data:
            parameters="&".join([a.data for a in forms[key].parms])
            return redirect('/run/'+key+'/'+parameters) if parameters else redirect('/run/'+key)
    return render_template('index_template.html',items=scripts.iteritems(),forms=forms)

def execute(scriptname,parms=""):
    output=subprocess.check_output(
        scripts[scriptname].script+parms,
        stderr=subprocess.STDOUT,
        shell=True).decode('utf-8')
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
