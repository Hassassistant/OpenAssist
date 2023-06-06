<a href="https://www.buymeacoffee.com/hassassistant" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a><br>
Home Assistant OpenAI GPT4 with Pinecone Index - Beta
==============================================
<br>

***Hey there! Just wanted to let you know that this project is still in the beta stage. Sure, it's functional, but it's got a couple of quirks (like not always finding the right entities after a query).***

***This is a one-man show and I'm knee-deep in the development process. I'm open to any ideas from the community. Your suggestions could really help in shaping this into something spectacular. So, dive in!***
<br><br><br>

This Home Assistant custom component creates a **Pinecone index** containing all your Home Assistant entity details. This allows you to make queries or ask questions using the `input_boolean.openassist_prompt`, such as "turn my kitchen light off" or "what's the current state of my kitchen light". 

This query is sent to the Pinecone index to find the closest matching entity, which is then sent to the **ChatGPT4** model, returning the necessary data to perform the corresponding service call action.

Integration Install
-------------
1. **(Manual)** Copy the **OpenMindsAI** folder to your Home Assistant's custom_components directory. If you don't have a **custom_components** directory, create one in the same directory as your **configuration.yaml** file.

**(HACS)** Add this repository as a HACS Integration: https://github.com/Hassassistant/openassist

2. Restart Home Assistant.

3. Add the following lines to your Home Assistant **configuration.yaml** file:
***(See below for prerequisites)***

```yaml
input_text:
  openassist_prompt:
    initial: ""
    max: 255

  pinecone_index:
    initial: ""
    max: 255

openassist:
  openai_key: "sk-...s1jz" #YOUR_OPENAI_KEY  
  pinecone_key: "b9a09c6a-...db2" #YOUR_PINECONE_ENVIRONMENT ID
  pinecone_env: "us-west1-gcp-free" #YOUR_PINECONE_ENVIRONMENT ID

sensor:
  - platform: openassist
    your_name: "YOUR_NAME" #Optional if you want ChatGPT to know your name.
    mindsdb_model: "gpt4hass" #MINDSDB MODEL NAME.
    mindsdb_cookie: ".eJw9i8sKgCAUBf_...." #MINDSDB SESSION COOKIE
    notify_device: "alexa_media_office_echo" #Optional, this sends each ChatGPT response to your notify entity.
    #Can be any of your Notify entities. (Phone, Amazon Echo etc)

# If you need to debug any issues.
logger:
  default: info
  logs:
    custom_components.openassist: debug
 ```


4. Restart Home Assistant.

Example Lovelace Card
-------------
![enter image description here](https://github.com/Hassassistant/OpenAssist/blob/main/misc/card_example.PNG?raw=true)

```yaml
square: false
columns: 1
type: grid
cards:
  - type: entities
    entities:
      - entity: input_text.openassist_prompt
        name: OpenAssist
      - entity: input_text.pinecone_index
        name: Index Creation (Please type your ENV ID and hit enter)
  - type: markdown
    content: '{{ state_attr(''sensor.openassist_response'', ''message'') }}'
    title: OpenAssist Response 
 ```
How to use
-------------
1. Type in your Pinecone Environment ID in the Pinecone Index input_boolean.
2. Hit enter.
3. Your Pinecone index will be created, this will then upload all your Home Assistant entity data to the index.
Please allow 10 - 15 minutes for the proccess to complete, dependant on how many entites you have.<br><br>
**Be aware: There is a known issue in Pinecone free tier, creation of new indexes getting stuck in a loop. This is out of my control, on one occasion I abandoned the index creation, and started this whole proccess again with a new Pinecone account.**<br><br>
![enter image description here](https://github.com/Hassassistant/OpenAssist/blob/main/misc/index%20creation.PNG?raw=true)<br><br>
4. Notifications on the Index creation will be send to the OpenAssist Response entity.<br>
![enter image description here](https://github.com/Hassassistant/OpenAssist/blob/main/misc/1.PNG?raw=true)<br>
![enter image description here](https://github.com/Hassassistant/OpenAssist/blob/main/misc/2.PNG?raw=true)<br>
5. Send a question or query.<br>
**Example 1**<br>
![enter image description here](https://github.com/Hassassistant/OpenAssist/blob/main/misc/query%201.PNG?raw=true)<br>
**Example 2**<br>
![enter image description here](https://github.com/Hassassistant/OpenAssist/blob/main/misc/query%202.PNG?raw=true)<br>
**Example 3**<br>
![enter image description here](https://github.com/Hassassistant/OpenAssist/blob/main/misc/query%203.PNG?raw=true)<br>
**Example 4**<br>
![enter image description here](https://github.com/Hassassistant/OpenAssist/blob/main/misc/query%204.PNG?raw=true)

Prerequisites
-------------

You need to have the following accounts and their corresponding keys:

-   **[Pinecone:](https://app.pinecone.io/)** You need a **Pinecone account** with an **API key**, along with the **Environment ID** (example: *us-west1-gcp-free*).
-   **[OpenAI:](https://platform.openai.com/playground/)** You need an **OpenAI API key**, used for embedding.
-   **[MindsDB](https://mindsdb.com/):** You'll need a **MindsDB account**, a **session cookie**, and the name of your **MindsDB model**.




Creating the AI model in MindsDB
--------------------------------

1.  Create a free account on MindsDB and login. You can do so [HERE](https://cloud.mindsdb.com/login).

2.  Navigate to the MindsDB editor. You can find it [HERE](https://cloud.mindsdb.com/editor).

3.  Create your AI model. In this example, we're creating an OpenAI GPT4 model named `gpt4hass`. 
You can replace `gpt4hass` with your preferred model name. Execute the following SQL query to create your model:

```sql
CREATE  MODEL mindsdb.gpt4hass
PREDICT response
USING
  engine  =  'openai',
  max_tokens =  2000,
  model_name =  'gpt-4',
  prompt_template =  '{{text}}';
```

   Click **"Run"** to execute the query and create your model.

4.  Obtain your MindsDB Session Cookie for authentication within Home Assistant. Here's how:

    -   Log into MindsDB and open your web browser's Inspect Element tool.
    -   Navigate to the Network tab and refresh the webpage (F5).
    -   Look for the **Editor** or **Home** element.
    -   Go to the Cookies tab and copy the Session Cookie.
        It should look something like this ***".eJw9i8sKgCAUBf_lrl2UlUY...iTsfiAsSdp0Y0yWuDsBE3vdtII"***<br>
        
![enter image description here](https://github.com/Hassassistant/OpenMindsAI/blob/main/misc/cookie.png?raw=true)

Pinecone API Key and Environment ID
-------------
1.  Create a free account on Pinecone and login. You can do so [HERE](https://app.pinecone.io/).
2.  Wait for **"Project Initializing"** to finish.
3.  Navigate to the Pinecone API Key page and take note of the API Key (Value) and Environment ID. <br>

![enter image description here](https://github.com/Hassassistant/OpenAssist/blob/main/misc/pinecone.PNG?raw=true)

OpenAI API Key
-------------
1.  Create a free account on Openai Playground and login. You can do so [HERE](https://platform.openai.com/playground/).
2.  Navigate to the OpenAI API Keys page. You can do so [HERE](https://platform.openai.com/account/api-keys).<br>
3.  Create a new secret key, and take note of the API Key.

![enter image description here](https://github.com/Hassassistant/OpenAssist/blob/main/misc/openai.PNG?raw=true)
