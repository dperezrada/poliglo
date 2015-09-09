import requests
import json
from random import randint

def main():
    poliglo_server = "http://localhost:9015"

    script_id = 'random_numbers_find_even'

    all_data = {
        'name': 'Random numbers' + str(randint(0, 10000000)),
        'data': {
            "how_many_to_create": 200,
            "numbers_range": [0, 10000]
        }
    }
    url = '%s/workflows/%s/workflow_instances' %(poliglo_server, script_id)
    print url
    print requests.post(
        url,
        data=json.dumps(all_data),
        headers={'content-type':'application/json'}
    )

main()
