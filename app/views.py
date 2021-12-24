from flask import request, redirect, url_for, render_template, send_from_directory, session,flash
import app.pingcastle.utils as utils
from flask_login import login_required
from app import app
import os
from app import auth



@app.route('/', methods=['GET','POST'])
@login_required
def index():
    url_for('static', filename='main.css')
    reports = utils.gen_reportlist()
    return render_template("report.html", reports=reports)

@app.route('/login', methods=['GET','POST'])
def login():
    url_for('static', filename='login.css')
    form = auth.LoginForm()
    if form.validate_on_submit():
        user = auth.User(username = form.username.data,
                         password = form.password.data)

        if user.check_username() is not None:
            if user.check_password() is not None:
                auth.login_user(user)
                return redirect(url_for('.index'))
        flash("User or password invalid")
    return render_template("authenticate.html", form = form, register="/login")

@app.route('/reports/<path:filename>')
@login_required
def show_report(filename):
    return send_from_directory(app.config['REPORT_FOLDER'],filename, as_attachment=False)

@app.route('/register', methods=['GET','POST'])
# Create a user and remove the commented line below
# vvv This one
#@login_required
def register():
    url_for('static', filename='main.css')
    url_for('static', filename='login.css')
    form = auth.LoginForm()
    if form.validate_on_submit():
        user = auth.User(username = form.username.data,
                         password = form.password.data)
        if user.register() is not None:
            flash("New user registered!")
    return render_template("register.html", form = form, register="/register")
    

@app.route('/api/Agent/Login', methods=['POST'])
def api_login():
    if request.is_json:
        json_request = request.get_json()
        api_key = json_request['apikey']
        ip = request.environ.get('HTTP_X_REAL_IP')
        if (_ := utils.check_api_login(api_key)) is not None:
            utils.temporarily_save_api(ip,api_key)
            return "Login successful"
        else:
            return redirect(url_for('.index'), code=401)
            
@app.route('/api/Agent/SendReport', methods=['POST'])
def api_upload():
    if request.is_json:
        json_request = request.get_json()
        # Combine path with reported filename
        # remove not allowed chars from it
        filename = utils.clean_path(json_request['filename'])
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        ip = request.environ.get('HTTP_X_REAL_IP')
        if (api := utils.get_api_key_from_ip(ip)) is not None:
            try:
                with open(f"{full_path}.xml","w+") as f:
                        f.write(json_request['xmlReport'])
                if not utils.xml_to_html(f"{full_path}.xml", api):
                    return redirect(url_for('.index'), code=500)
                else:
                    return redirect(url_for('.index'))
            except Exception as e:
                print(e)
                return redirect(url_for('.index'), code=500)
        else:
            return redirect(url_for('.index'), code=401)
    return redirect(url_for('.index'), code=500)

@app.route('/upload', methods=['GET','POST'])
@login_required
def upload():
    from pprint import pprint
    if request.method == 'POST':
        file = request.files['file']

        if file.filename == '':
            return redirect(url_for('.index'), code=500)
        filename = utils.clean_path(file.filename,method='cmd')
        file.save(os.path.join(app.config['REPORT_FOLDER'], filename))
        return redirect(url_for('.index'), code=200)
    
    return render_template("upload.html")




    url_for('static', filename='generate.css')
    return render_template('generate.html',domain=app.config['DOMAIN_NAME'])

@app.route('/generate', methods=['GET'])
@login_required
def generate_show():
    url_for('static', filename='generate.css')
    return render_template('generate.html',domain=app.config['DOMAIN_NAME'])

@app.route('/generate', methods=['POST'])
@login_required
def generate_new():
    if (name := request.form.get('acquisition')) is not None:
        switches = request.form.get('switches')
        api = utils.generate_keys(name)

        if utils.create_package(name, switches, api):
            link = utils.generate_download_link(f"{name}.zip",api)
            zip_hash = utils.calculate_hash(f"{name}.zip")
            flash([f"{app.config['DOMAIN_NAME']}/download/{link}",f"Hash: {zip_hash}"])
            return render_template('generate.html',domain=app.config['DOMAIN_NAME'])
        else:
            return redirect(url_for('.index'), code=500)
    else:
        return redirect(url_for('.index'), code=500)

@app.route('/download/<filekey>')
def download_package(filekey):
    if( download_file := utils.get_download_package(filekey)):
        return send_from_directory(directory=app.config['OUTPUT_FOLDER'], path=download_file, as_attachment=True)
    else:
        return redirect(url_for('.index'), code=404)
        
@app.route('/logout', methods=['GET'])
def logout():
    auth.logout()
    return redirect(url_for('.index'))
