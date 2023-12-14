import config
import json
from requests import post

STATUS_ENTITY_API_URL = "api/states/sensor."


def publish_status(io_status):
    entity_id = "hompi_{}_status".format(config.HOMPI_ID.lower())
    entity_friendly_name = "Hompi {} status".format(config.HOMPI_ID)
    url = config.HASS_SERVER + STATUS_ENTITY_API_URL + entity_id
    json_str = io_status.get_output()
    json_attr = json.loads(json_str)
    json_attr["friendly_name"] = entity_friendly_name
    json_attr["icon"] = "mdi:home-automation"
    data = {"state": io_status.last_update,
            "attributes": json_attr}

    headers = {"Authorization": "Bearer " + config.HASS_TOKEN, "content-type": "application/json"}
    response = post(url, headers=headers, json=data, verify=False)
    print('HASS PUBLISH ({}): {}'.format(entity_id, json_str.replace('\n', ' ')))
    print(response.text)
