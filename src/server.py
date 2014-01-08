#!/usr/bin/env python

import os.path
from cStringIO import StringIO
from flask import Flask, render_template, make_response, redirect, request,\
    url_for
from werkzeug import secure_filename
from fixer import fix_sms


PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
OUTPUT_PATH = os.path.join(PROJECT_ROOT, '../output/')
app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/fix/', methods=['POST'])
def fix():
    filename = secure_filename(request.form.get('output-filename')) or 'output'
    files = request.files.getlist('input-files[]')
    contacts = request.form.get('contacts')
    if files[0].filename == '':
        error = "You need to upload some files."
        return render_template(
            'index.html', output=filename, contacts=contacts, error=error)
    try:
        address_book = dict([line.split(':') for line in contacts.split('\n')
                                             if ':' in line])
        with open(os.path.join(OUTPUT_PATH, filename + '.xml'), 'w') as output_file:
            _, missing = fix_sms(
                input=files, 
                output=output_file,
                logger=app.logger,
                address_book=address_book)
            print missing
    except:
        error = "An unknown error occurred."
        return render_template(
            'index.html', output=filename, contacts=contacts, error=error)
    return render_template(
        'index.html', 
        output=filename, 
        missing=missing,
        contacts=contacts,
        link=url_for('get_file', filename=filename))


@app.route('/fix/<filename>.xml')
def get_file(filename):
    filename = os.path.join(OUTPUT_PATH, secure_filename(filename) + '.xml')
    try:
        with open(filename, 'r') as output_file:
            content = output_file.read()
            return make_response(
                content, 200, {'Content-Type': 'application/xml'})
    except IOError:
        return "invalid filename", 404


@app.route('/fix/sms.xsl')
def xsl():
    return render_template('sms.xsl')


if __name__ == '__main__':
    app.run(debug=True)