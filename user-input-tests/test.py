from flask import Flask
import os
import platformtool

app = Flask(__name__)
@app.route("/")
def display_message():
    return platformtool.main()
    # os.system('#!/bin/sh python3 ../platformtool.py')
    # return "<p> Testing flask </p>"

if __name__ == "__main__":
    app.run()