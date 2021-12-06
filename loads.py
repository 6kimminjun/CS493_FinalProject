from flask import Blueprint, request
from google.cloud import datastore
import json
from json2html import *
import constants

client = datastore.Client()

bp = Blueprint('loads', __name__, url_prefix='/loads')

@bp.route('', methods=['POST','GET'])
def loads_get_post():
    if request.method == 'POST':
        try:
            content = request.get_json()
            new_loads = datastore.entity.Entity(key=client.key(constants.loads))
            new_loads.update({"volume": content["volume"], "items": content["items"], "carrier": None})
            client.put(new_loads)
            return (str(new_loads.key.id), 201)
        except:
            return ('Load is missing some attributes!', 400)
    elif request.method == 'GET':
        query = client.query(kind=constants.loads)
        q_limit = int(request.args.get('limit', '3'))
        q_offset = int(request.args.get('offset', '0'))
        g_iterator = query.fetch(limit= q_limit, offset=q_offset)
        pages = g_iterator.pages
        results = list(next(pages))
        if g_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None
        for e in results:
            e["id"] = e.key.id
            e["self"] = request.base_url + '/' + str(e.key.id)
        output = {"loads": results}
        if next_url:
            output["next"] = next_url
        return json.dumps(output)


@bp.route('/<id>', methods=['GET','PUT','DELETE'])
def loads_get_put_delete(id):
    if request.method == 'GET':
        loads_key = client.key(constants.loads, int(id))
        loads = client.get(key=loads_key)
        if loads != None:
            loads['self'] = request.base_url
            return json.dumps(loads)
        else:
            return ('This load does not exist!', 404)
    elif request.method == 'PUT':
        content = request.get_json()
        loads_key = client.key(constants.loads, int(id))
        loads = client.get(key=loads_key)
        loads.update({"volume": content["volume"], "items": content["items"]})
        client.put(loads)
        return ('Load has been successfully updated!',200)
    elif request.method == 'DELETE':
        loads_key = client.key(constants.loads, int(id))
        loads = client.get(key=loads_key)
        if loads != None:
            if loads['carrier'] == None:
                client.delete(loads_key)
                return ("This load was successfully deleted!", 200)
            else:
                for i in loads['carrier']:
                    boats_key = client.key(constants.boats, i)
                    boats = client.get(key=boats_key)
                    loads['carrier'] = None
                    boats['loads'] = None
                    client.put(boats)
                    client.put(loads)
                    client.delete(loads_key)
                    return ("Load was unassigned successfully and the load has been deleted!", 200)
        else:
            return ('This load does not exist!', 404)
    else:
        return 'Method not recogonized'