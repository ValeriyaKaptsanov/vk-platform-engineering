from flask import Flask, render_template
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
# import os
import platformtool

app = Flask(__name__)
app.secret_key = 'aa'
bootstrap = Bootstrap5(app)
csrf = CSRFProtect(app)

class ResourceForm(FlaskForm):
    name = StringField('What resource do you want to use?', validators=[DataRequired()])
    submit = SubmitField('Submit')
    
@app.route("/", methods=['GET', 'POST'])
def display_message():
    resources = 'ec2'
    form = ResourceForm()
    message = ""
    if form.validate_on_submit():
        name = form.name.data
        if name.lower() == resources:
            form.name.data = ""
            message = "okay"
        else:
            message = "Fail"
    return render_template('index.html', resources=resources, form=form, message=message)

    
    
    # return platformtool.main()
    # os.system('#!/bin/sh python3 ../platformtool.py')
    # return "<p> Testing flask </p>"

if __name__ == "__main__":
    app.run()