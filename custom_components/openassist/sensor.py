import logging
import aiohttp
import voluptuous as vol
import json
import yaml

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv

from . import DOMAIN, EVENT_OPENASSIST_UPDATE

DEFAULT_NAME = "OpenAssist Response"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
#    vol.Required('mindsdb_cookie'): cv.string,
    vol.Required('mindsdb_model'): cv.string,
    vol.Required('mindsdb_email'): cv.string,
    vol.Required('mindsdb_password'): cv.string,
    vol.Optional('notify_device'): cv.string,
    vol.Optional('your_name'): cv.string,
})


_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the OpenAssist sensor."""
    _LOGGER.debug("Setting up OpenAssistSensor")

    name = config.get(CONF_NAME, DEFAULT_NAME)
    mindsdb_model = config['mindsdb_model']
    mindsdb_email = config['mindsdb_email']
    mindsdb_password = config['mindsdb_password']
    notify_device = config.get('notify_device', '')
    your_name = config.get('your_name', '')

    add_entities([OpenAssistSensor(name, mindsdb_model, mindsdb_email, mindsdb_password, notify_device, your_name)])
    _LOGGER.debug("OpenAssistSensor added to entities")




class OpenAssistSensor(Entity):
    """Representation of an OpenAssist Sensor."""




    async def ask_mindsdb(self, prompt):
        _LOGGER.debug("Asking MindsDB")

        # Check if the prompt starts and ends with double quotes, if not, add them.
        if not prompt.startswith('"'):
            prompt = '"' + prompt
        if not prompt.endswith('"'):
            prompt = prompt + '"'

        # Replace all double quotes except for the ones at the start and end
        sanitized_prompt = '"' + prompt[1:-1].replace('"', '') + '"'

        # Create a ClientSession that will be used for both authentication and querying
        async with aiohttp.ClientSession() as session:

            # Login
            login_url = "https://cloud.mindsdb.com/cloud/login"
            login_data = {
                'email': self._mindsdb_email,
                'password': self._mindsdb_password
            }
            login_response = await session.post(login_url, json=login_data)
            
            if login_response.status != 200:
                _LOGGER.error(f"Login request failed with status {login_response.status}: {login_response.reason}")
                return None

            # Query MindsDB
            query_url = 'https://cloud.mindsdb.com/api/sql/query'
            query_data = {
                'query': f"SELECT response from mindsdb.{self._mindsdb_model} WHERE text={sanitized_prompt};"
            }
            query_response = await session.post(query_url, json=query_data)
            
            if query_response.status != 200:
                _LOGGER.error(f"Query request failed with status {query_response.status}: {query_response.reason}")
                return None

            response_json = await query_response.json()

        _LOGGER.info(f"MindsDB response: {response_json}")
        
        try:
            response_message = response_json['data'][0][0]
        except (KeyError, IndexError):
            _LOGGER.error(f"Unexpected response structure: {response_json}")
            response_message = None

        return response_message





    def __init__(self, name, mindsdb_model, mindsdb_email, mindsdb_password, notify_device, your_name):
        """Initialize the sensor."""
        self._state = None
        self._name = name
        self._response = None  
        self._message = None  
        self._mindsdb_model = mindsdb_model
        self._mindsdb_email = mindsdb_email
        self._mindsdb_password = mindsdb_password
        self._notify_device = notify_device
        self._your_name = your_name
        _LOGGER.info("OpenAssistSensor initialized")

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {"response": self._response, "message": self._message} 

    async def async_added_to_hass(self):
        """Run when entity about to be added to hass."""
        _LOGGER.info("OpenAssistSensor added to hass, connecting to OpenAssist update event")
        self.hass.bus.async_listen(EVENT_OPENASSIST_UPDATE, self._async_handle_update)
        _LOGGER.info("OpenAssistSensor connected to OpenAssist update event")


    async def _async_handle_update(self, event):
        """Handle the OpenAssist update event."""
        _LOGGER.info("OpenAssistSensor received update event")
        new_state = event.data.get("new_state", "")
        if not new_state:
            _LOGGER.info("Input text is empty. Skipping...")
            return
        metadata = event.data.get("metadata", "")
        _LOGGER.info(f"Event data: new_state={new_state}, metadata={metadata}")

        
        prompt = (
            "If the query is a generic question, respond with a valid JSON object:\n\n"
            "{\n"
            f"  \"message\": \"Generate a humane response (reference current user {self._your_name})\"\n"
            "}\n\n"

            "If the query is for the current state of an entity, For example, question: is the (device) on?\n\n"
            "{\n"
            "  \"message\": \"The current state of the (original_name) is {{ states() }}\"\n"
            "}\n\n"
            
            "device attributes is the following format, {{ state_attr('domain.entity', 'attribute') }}\n\n"

            "If the query requires a call service, please format your response as a valid JSON object in the following way:"
            "\n\n{\n"
            "  \"domain\": \"The domain of the service\",\n"
            "  \"service\": \"The service to be called\",\n"
            "  \"entity_id\": \"The entity id to be affected\",\n"
            "  \"data\": {\n"
            "    \"key1\": \"value1\",\n"
            "    \"key2\": \"value2\",\n"
            "    ... and so on ...\n"
            "  },\n"
            "  \"message\": \"Confirmation message\"\n"
            "}\n\n"
            "For example, if the question asks to play 'Planet Rock' on the Amazon Echo device named 'Loft Echo', "
            "you should respond with:\n\n"
            "{\n"
            "  \"domain\": \"media_player\",\n"
            "  \"service\": \"play_media\",\n"
            "  \"entity_id\": \"media_player.loft_echo\",\n"
            "  \"data\": {\n"
            "    \"media_content_id\": \"play Planet Rock\",\n"
            "    \"media_content_type\": \"custom\"\n"
            "  },\n"
            "  \"message\": \"(Generate a message confirming completion of task)\"\n"
            "}\n\n"
            "Remember, all the keys in the dictionary ('domain', 'service', 'entity_id', 'data', 'message') are required. "
            "The 'data' key should always have a dictionary as its value, and this dictionary can contain any number of keys "
            "and values, depending on what the service requires.\n"
            "If the questions refer to more than 1 actions, reply with the actions under the 'actions' key, and a single 'message' key to represent all actions."
            "Example:\n\n"
            "{\n"
            "  \"actions\": [\n"
            "    {\n"
            "      \"domain\": \"The domain of the first service\",\n"
            "      \"service\": \"The first service to be called\",\n"
            "      \"entity_id\": \"The entity id to be affected by the first service\",\n"
            "      \"data\": {\n"
            "        \"key1\": \"value1\",\n"
            "        \"key2\": \"value2\",\n"
            "        ... and so on ...\n"
            "      }\n"
            "    },\n"
            "    {\n"
            "      \"domain\": \"The domain of the second service\",\n"
            "      \"service\": \"The second service to be called\",\n"
            "      \"entity_id\": \"The entity id to be affected by the second service\",\n"
            "      \"data\": {\n"
            "        \"key1\": \"value1\",\n"
            "        \"key2\": \"value2\",\n"
            "        ... and so on ...\n"
            "      }\n"
            "    }\n"
            "  ],\n"
            "  \"message\": \"Confirmation message for both the first and second action\"\n"
            "}\n\n"
            f"Question: {new_state}\n\nData: {json.dumps(metadata, indent=4)}\n"
        )



        _LOGGER.info(f"Prepared prompt for GPT-4: {prompt}")


        _LOGGER.info("Getting GPT-4 response")
        response = await self.ask_mindsdb(prompt)
        self._response = response  
        _LOGGER.info(f'GPT Response: \n{response}')
        self._state = 'Response received'  
        _LOGGER.info("Executing service")
        await self.execute_service(self.hass, response)
        _LOGGER.info("Sending notification")
        message = json.loads(response).get('message') if response else None
        if message:  
            message = self.hass.helpers.template.Template(message, self.hass).async_render()
        self._message = message
        await self.send_notification(message)
        _LOGGER.info("Updating Home Assistant state")
        self.async_schedule_update_ha_state()
        _LOGGER.info("Home Assistant state updated")


    async def execute_service(self, hass, response):
        if not response:
            _LOGGER.error("No response to execute")
            return

        try:
            response_dict = json.loads(response)
        except json.JSONDecodeError:
            _LOGGER.error("Could not decode response as JSON")
            return

        # Log the full response
        _LOGGER.error(f"MindsDB response: {response_dict}")

        actions = response_dict.get('actions')
        if actions is None:  # if 'actions' key is not present, assume it's a single-action response
            actions = [response_dict]  # wrap it into a list to make it compatible with the loop below

        if not actions:
            _LOGGER.error("No actions in response")
            return

        for action in actions:
            domain = action.get('domain')
            service = action.get('service')
            entity_id = action.get('entity_id')
            data = action.get('data', {})  
            if not all([domain, service, entity_id]):
                _LOGGER.error("Action missing required fields")
                continue
            if 'entity_id' not in data:
                data['entity_id'] = entity_id
            await hass.services.async_call(domain, service, data)



    async def send_notification(self, message):
        if not message:
            _LOGGER.error("No message to send")
            return
        await self.hass.services.async_call("notify", self._notify_device, {"message": message})
