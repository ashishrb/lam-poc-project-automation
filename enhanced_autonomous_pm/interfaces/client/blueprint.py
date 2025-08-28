from flask import Blueprint, jsonify

client_bp = Blueprint('client_bp', __name__, url_prefix='/client')


@client_bp.get('/')
def client_home():
    return jsonify({"message": "Client interface coming soon"})

