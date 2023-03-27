from flask import Blueprint

example_blueprint = Blueprint('example_blueprint', __name__)


@example_blueprint.route('/')
def index():
    return "Isso é um exemplo de Blueprint"

