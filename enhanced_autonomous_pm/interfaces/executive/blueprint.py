from flask import Blueprint, render_template

executive_bp = Blueprint('executive_bp', __name__, url_prefix='/executive')


@executive_bp.get('/')
def executive_home():
    return render_template('dashboards/executive.html')

