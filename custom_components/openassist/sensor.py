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
    vol.Required('mindsdb_model'): cv.string,
    vol.Required('mindsdb_cookie'): cv.string,
    vol.Optional('notify_device'): cv.string,
    vol.Optional('your_name'): cv.string,
})

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the OpenAssist sensor."""
    _LOGGER.debug("Setting up OpenAssistSensor")

    name = config.get(CONF_NAME, DEFAULT_NAME)
    mindsdb_model = config['mindsdb_model']
    mindsdb_cookie = config['mindsdb_cookie']
    notify_device = config.get('notify_device', 'alexa_media_kitchen_echo')
    your_name = config.get('your_name', '')
    
    add_entities([OpenAssistSensor(name, mindsdb_model, mindsdb_cookie, notify_device, your_name)])
    _LOGGER.debug("OpenAssistSensor added to entities")




class OpenAssistSensor(Entity):
    """Representation of an OpenAssist Sensor."""

    async def ask_mindsdb(self, prompt):
        _LOGGER.debug("Asking MindsDB")
        url = f"https://cloud.mindsdb.com/api/projects/mindsdb/models/{self._mindsdb_model}/predict"
        cookies = {"session": self._mindsdb_cookie}
        data = {"data": [{"text": prompt}]}
        headers = {"Content-Type": "application/json"}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, cookies=cookies, headers=headers) as resp:
                response_json = await resp.json()
        try:
            response_message = response_json[0]["response"]
        except KeyError:
            response_message = None
        return response_message



    def __init__(self, name, mindsdb_model, mindsdb_cookie, notify_device, your_name):
        """Initialize the sensor."""
        self._state = None
        self._name = name
        self._response = None  
        self._message = None  
        self._mindsdb_model = mindsdb_model
        self._mindsdb_cookie = mindsdb_cookie
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
            "If the query is a generic question, respond with:\n\n"
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
            service_dict = json.loads(response)
        except json.JSONDecodeError:
            _LOGGER.error("Could not decode response as JSON")
            return
        domain = service_dict.get('domain')
        service = service_dict.get('service')
        entity_id = service_dict.get('entity_id')
        data = service_dict.get('data', {})  
        if not all([domain, service, entity_id]):
            _LOGGER.error("Response missing required fields")
            return
        if 'entity_id' not in data:
            data['entity_id'] = entity_id
        await hass.services.async_call(domain, service, data)


    async def send_notification(self, message):
        if not message:
            _LOGGER.error("No message to send")
            return
        await self.hass.services.async_call("notify", self._notify_device, {"message": message})
