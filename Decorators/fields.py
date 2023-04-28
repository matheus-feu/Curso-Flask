from datetime import datetime as dt
from functools import wraps

from flask import request


class DtField():
    def __init__(self, format):
        self.format = format

    def convert(self, value):
        try:
            dt.strptime(value, self.format)
            return dt.strptime(value, self.format)
        except ValueError:
            return None


def fields_get(methods="*", out="fields"):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            xstr = lambda s: s or ""
            contentJson = "json" in xstr(request.headers.get("Content-Type"))

            if methods == "*" or request.method in methods:
                if request.method == "GET":
                    fields = request.args.to_dict()
                elif request.method in ["POST", "PUT", "DELETE", "DEL", "CREDIT"]:
                    data = request.get_json(force=True) or request.get_json() or request.form.to_dict()
                    fields = request.json if contentJson else data

                kwargs[out] = fields
                result = function(*args, **kwargs)
                return result
            else:
                kwargs[out] = []
                return function(*args, **kwargs)

        return wrapper

    return decorator


def fields_type(dic):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):

            fields = kwargs["fields"]

            for k, v in dic.items():
                if not k in fields:
                    continue

                if v == float and isinstance(fields[k], int):
                    fields[k] = float(fields[k])

                if not isinstance(fields[k], v):
                    tipo = str(v).split("'")[1]
                    return {"error": f"the field '{k}' does not correspond to the type ({tipo})"}, 400

            return function(*args, **kwargs)

        return wrapper

    return decorator


def fields_required(lista):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):

            fields = kwargs["fields"]

            lista2 = lista if isinstance(lista, list) else list(lista.keys())
            notfound = [x for x in lista2 if not x in fields]
            if notfound:
                return {"error": f"the fields {notfound} are required"}, 400

            if isinstance(lista, dict):
                for k, v in lista.items():
                    if fields[k] == None:
                        continue

                    if isinstance(v, DtField):
                        ndt = v.convert(fields[k])
                        if not ndt: return {"error": f"the field '{k}' date format invalid!"}, 400
                        fields[k] = ndt
                        continue

                    if v == float and isinstance(fields[k], int):
                        fields[k] = float(fields[k])

                    if not isinstance(fields[k], v):
                        tipo = str(v).split("'")[1]
                        return {"error": f"the field '{k}' does not correspond to the type ({tipo})"}, 400

            result = function(*args, **kwargs)
            return result

        return wrapper

    return decorator


# fields_notEmpty(['key1','key2'])        => string|list
def fields_not_empty(lista):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):

            fields = kwargs["fields"]

            for field in lista:
                if not field in fields:
                    return {"error": f"Field '{field}' not found!"}, 404

            for k, v in fields.items():
                if k in lista:
                    if v is None:
                        return {"error": f"Required field '{k}' must not be empty!"}, 400

                    if isinstance(v, dt):
                        continue

                    if isinstance(v, int) or isinstance(v, float):
                        if v is None:
                            return {"error": f"Required field '{k}' must not be empty!"}, 400
                        continue

                    if isinstance(v, list):
                        if not len(v):
                            return {"error": f"Required field '{k}' must not be empty!"}, 400
                    else:
                        if v.strip() == "":
                            return {"error": f"Required field '{k}' must not be empty!"}, 400

            return function(*args, **kwargs)

        return wrapper

    return decorator


# fields_dateValid(['key1','key2'],'%Y-%m-%d')
def fields_date_valid(lista, format):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):

            fields = kwargs["fields"]

            for field in lista:
                if not field in fields:
                    return {"error": f"Field '{field}' not found!"}, 404

            for k, v in fields.items():
                if k in lista:
                    try:
                        dt.strptime(v, format)
                        kwargs["fields"][k] = dt.strptime(v, format)
                    except ValueError:
                        return {"error": f"Field '{k}' date format invalid!"}, 400

            return function(*args, **kwargs)

        return wrapper

    return decorator


# lista => {'field1',['blue','red']}
def fields_values_allowed(lista):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):

            fields = kwargs["fields"]

            for k, v in lista.items():
                if not k in fields:
                    return {"error": f"Field '{k}' not found!"}, 404

            for k, v in lista.items():
                if not fields[k] in v:
                    return {"error": f"Field '{k}' value not allowed!"}, 400

            return function(*args, **kwargs)

        return wrapper

    return decorator


# fields_Allowed(['key1','key2'])
def fields_allowed(lista, removeFields=False):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):

            fields = kwargs["fields"]

            if removeFields:
                fields = {k: v for k, v in fields.items() if k in lista}
                kwargs["fields"] = fields
                return function(*args, **kwargs)

            for field in fields:
                if not field in lista:
                    return {"error": f"Field '{field}' not allowed!"}, 400

            return function(*args, **kwargs)

        return wrapper

    return decorator


# fields_ValidateList('key1',{'k1':str,'k2':int}) => [{k1:'my value',k2:1},{k1:'my value2',k2:2}]
# fields_ValidateList('key1',int)                 => [1,2,3,4]
# fields_ValidateList('key1',str)                 => ['A','B','C','D']
# fields_ValidateList('key1',dict)                => [{}.{},{}]
def fields_validate_list(key, obj):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):

            field = kwargs["fields"][key]

            tipo = str(obj).split("'")[1]

            if not isinstance(field, list):
                return {"error": f"Field '{key}' must be a list!"}, 400

            if isinstance(obj, dict):
                newVal = []
                for val in field:
                    lista2 = list(obj.keys())
                    notfound = [x for x in lista2 if not x in val.keys()]
                    if notfound:
                        return {"error": f"Some record at {key} does not have keys:\n\t" + '\n\t'.join(notfound)}, 400

                    for k, v in obj.items():
                        if val[k] == None:
                            continue

                        if isinstance(v, DtField):
                            ndt = v.convert(val[k])
                            if not ndt: return {
                                "error": f"The field '{k}' at field '{key}' not corresponds to date format '{v.format}"}, 400
                            val[k] = ndt
                            continue

                        if v == float and isinstance(val[k], int):
                            val[k] = float(val[k])

                        if not isinstance(val[k], v):
                            tipo = str(v).split("'")[1]
                            return {"error": f"the field '{k}' at field '{key}' does not correspond to the type ({tipo})"}, 400

                    newVal.append(val)
                kwargs["fields"][key] = newVal
            else:
                for v in field:
                    if not isinstance(v, obj): return {"error": f"the field '{key}' does not correspond to the type ({tipo})"}, 400

            result = function(*args, **kwargs)
            return result

        return wrapper

    return decorator


# lista => {'field1',Func}
def fields_validate_argument_object(field, func, new_name=None, replace_field=False, condition=True):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):

            fields = kwargs["fields"]

            v = func(fields[field])

            sts = v if isinstance(v, bool) else v[0]

            if sts != condition:
                msg = f"Invalid value for field {field}" if isinstance(v, bool) else v[1]
                code = 404 if isinstance(v, bool) else (404 if len(v) < 3 else v[2])
                return msg if msg else msg, code

            if new_name and replace_field:
                fields[new_name] = v
                del fields[field]

            if new_name and not replace_field:
                fields[new_name] = v

            if not new_name and replace_field:
                fields[field] = v

            return function(*args, **kwargs)

        return wrapper

    return decorator


# lista => {'field1',Func}
def fields_validate_object(lista):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):

            fields = kwargs["fields"]

            for k, v in lista.items():
                if not k in fields:
                    return {"message": f"Field '{k}' not found!"}, 404
            for k, v in lista.items():
                if not fields[k] in v:
                    return {"message": f"value '{fields[k]}' not allowed in field '{k}'"}, 404

            return function(*args, **kwargs)

        return wrapper

    return decorator
