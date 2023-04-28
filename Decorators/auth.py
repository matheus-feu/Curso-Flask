from functools import wraps

import jwt
from app import app
from app.models.BD.User import User
from flask import request


def token_required(Admin=False, Tech=False, Analist=False, All=False):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):

            token = None

            if not "token" in request.headers:
                return "Token is missing!", 400
            token = request.headers['token']

            try:
                data = jwt.decode(token, app.config['SECRET_KEY'])
            except jwt.ExpiredSignatureError:
                return "Session Expired", 401
            except:
                return "Invalid token!", 401

            current_user = User.query.get(data["id"])
            if not current_user.active:
                return "User inactive, please contact your admin!", 401
            if (current_user.access_type == "Admin" and not Admin) and not All:
                return "Access not allowed!", 401
            if (current_user.access_type == "Tech" and not Tech) and not All:
                return "Access not allowed!", 401
            if (current_user.access_type == "Analist" and not Analist) and not All:
                return "Access not allowed!", 401

            kwargs["current_user"] = current_user

            return function(*args, **kwargs)

        return wrapper

    return decorator


def required_keys(keys):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            if not request.is_json:
                raise "Request must be a JSON."

            data_request = request.get_json()

            for key_value in keys:
                if key_value not in data_request:
                    raise f"Key {key_value} not found in request."

            return func(*args, **kwargs)

        return wrapper

    return decorator
