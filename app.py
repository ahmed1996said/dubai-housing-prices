import os
from flask import Flask, flash, jsonify, redirect, render_template, request, session,redirect, jsonify
import requests
import json
import time
import numpy as np
from static.property_types import PROPERTY_TYPES
from static.locations import LOCATIONS

app = Flask(__name__)


@app.route("/")
def index():
	return render_template("index.html",message="",locations=LOCATIONS,property_types=PROPERTY_TYPES)

@app.route("/predict", methods=["POST"])
def predict():
    print(jsonify(request.form).json)
    return render_template("index.html",
                            message=f"Predicted price is AED {np.random.randint(100000):,} / year",
                            locations=LOCATIONS,
                            property_types=PROPERTY_TYPES
                            )

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html',error_code='404',message='Opps! Are you lost?',link_to_home=True)

# return render_template("error.html",message="Error message here!")


if __name__ == '__main__':
	app.debug=True
	app.run(debug=True)
