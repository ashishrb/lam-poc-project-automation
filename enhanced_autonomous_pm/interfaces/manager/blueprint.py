from flask import Blueprint, render_template

manager_bp = Blueprint('manager_bp', __name__, url_prefix='/manager')


@manager_bp.get('/')
def manager_home():
    return render_template('dashboards/manager.html')


@manager_bp.get('/portfolio')
def portfolio_view():
    return render_template('dashboards/portfolio.html')
