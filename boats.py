from flask import Blueprint, request
from google.cloud import datastore
import json
import constants

client = datastore.Client()

bp = Blueprint('boats', __name__, url_prefix='/boats')

@bp.route('', methods=['POST','GET'])
def boats_get_post():
    if request.method == 'POST':
        try:
            content = request.get_json()
            new_boats = datastore.entity.Entity(key=client.key(constants.boats))
            new_boats.update({'name': content['name'], 'type': content['type'], 'loads': None, 'length': content['length']})
            client.put(new_boats)
            return (str(new_boats.key.id),201)
        except:
            return ('Missing attributes when creating the boat!', 400)
    elif request.method == 'GET':
        query = client.query(kind=constants.boats)
        q_limit = int(request.args.get('limit', '3'))
        q_offset = int(request.args.get('offset', '0'))
        l_iterator = query.fetch(limit= q_limit, offset=q_offset)
        pages = l_iterator.pages
        results = list(next(pages))
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None
        for e in results:
            e["id"] = e.key.id
            e["self"] = request.base_url + '/' + str(e.key.id)
        output = {"boats": results}
        if next_url:
            output["next"] = next_url
        return json.dumps(output)
    else:
        return 'Method not recogonized'

@bp.route('/<id>', methods=['GET','PUT','DELETE'])
def boats_get_put_delete(id):
    if request.method == 'GET':
        boats_key = client.key(constants.boats, int(id))
        boats = client.get(key=boats_key)
        if boats != None:
            boats['self'] = request.base_url
            return json.dumps(boats)
        else:
            return ('This boat does not exist!', 404)
    elif request.method == 'PUT':
        content = request.get_json()
        boats_key = client.key(constants.boats, int(id))
        boats = client.get(key=boats_key)
        boats.update({'name': content['name'], 'type': content['type'], 'length': content['length']})
        client.put(boats)
        return ('Boat has been successfully updated!',201)
    elif request.method == 'DELETE':
        boats_key = client.key(constants.boats, int(id))
        boats = client.get(key=boats_key)
        if boats != None:
            if boats['loads'] == None:
                client.delete(boats_key)
                return ("This boat was successfully deleted!", 200)
            else:
                for i in boats['loads']:
                    loads_key = client.key(constants.loads, i)
                    loads = client.get(key=loads_key)
                    loads['carrier'] = None
                    boats['loads'] = None
                    client.put(boats)
                    client.put(loads)
                    client.delete(boats_key)
                    return ("Load was removed successfully and the boat has been deleted!", 200)
        else:
            return ('This boat does not exist!', 404)
    else:
        return 'Method not recogonized'

@bp.route('/<bid>/loads/<lid>', methods=['PUT','DELETE'])
def add_delete_boatLoads(bid,lid):
    if request.method == 'PUT':
        boats_key = client.key(constants.boats, int(bid))
        boats = client.get(key=boats_key)
        loads_key = client.key(constants.loads, int(lid))
        loads = client.get(key=loads_key)
        if loads == None and loads == None:
            return ('Both load and boat do not exist!', 404)
        elif boats == None:
            return ('Boat does not exist!', 404)
        elif loads == None:
            return ('Load does not exist!', 404)
        elif loads['carrier'] != None:
            return ('Load already assigned to another boat!', 403)
        elif loads != None and boats != None:
            if boats['loads'] != None:
                boats['loads'].append(loads.id)
                loads['carrier'] = [boats.id]
                client.put(boats)
                client.put(loads)
                return('Load successfully appended to boat!', 201)
            else:
                boats['loads'] = [loads.id]
                loads['carrier'] = [boats.id]
                client.put(boats)
                client.put(loads)
                return('Load successfully assigned to boat!', 201)
        else:
            return ("Something went horribly wrong!", 500)
    if request.method == 'DELETE':
        boats_key = client.key(constants.boats, int(bid))
        boats = client.get(key=boats_key)
        if boats != None:
            if 'loads' in boats.keys():
                boats['loads'].remove(int(lid))
                client.put(boats)
                return('Load successfully removed from Boat', 200)
            else:
                return ('Load does not exist!', 404)
        else:
            return ("Boat does not exist!", 404)


@bp.route('/<id>/loads', methods=['GET'])
def get_boatLoads(id):
    boats_key = client.key(constants.boats, int(id))
    boats = client.get(key=boats_key)
    loads_list  = []
    if boats != None:
        if 'loads' in boats.keys():
            for lid in boats['loads']:
                loads_key = client.key(constants.loads, int(lid))
                loads_list.append(loads_key)
            return json.dumps(client.get_multi(loads_list))
        else:
            return json.dumps([])
    else:
        return ('Boat does not exist!', 404)