from flask import Blueprint, render_template

employee_bp = Blueprint('employee_bp', __name__, url_prefix='/employee')


@employee_bp.get('/')
def employee_home():
    return render_template('forms/employee_portal.html')

