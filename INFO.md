
Home Assistant OpenAI GPT4 with Pinecone Index
==============================================

This Home Assistant custom component creates a **Pinecone index** containing all your Home Assistant entity details. This allows you to make queries or ask questions using the `input_boolean.openassist_prompt`, such as "turn my kitchen light off" or "what's the current state of my kitchen light". 

This query is sent to the Pinecone index to find the closest matching entity, which is then sent to the **ChatGPT4** model, returning the necessary data to perform the corresponding service call action.

Prerequisites
-------------

You need to have the following accounts and their corresponding keys:

-   **[Pinecone:](https://app.pinecone.io/)** You need a **Pinecone account** with an **API key**, along with the **Environment ID** (example: *northamerica-northeast1-gcp*).
-   **[OpenAI:](https://platform.openai.com/playground/)** You need an **OpenAI API key**, used for embedding.
-   **[MindsDB](https://mindsdb.com/):** You'll need a **MindsDB account**, a **session cookie**, and the name of your **MindsDB model**.




Creating the AI model in MindsDB
--------------------------------

1.  Create a free account on MindsDB and login. You can do so [HERE](https://cloud.mindsdb.com/login).

2.  Navigate to the MindsDB editor. You can find it [HERE](https://cloud.mindsdb.com/editor).

3.  Create your AI model. In this example, we're creating an OpenAI GPT4 model named `gpt4-hass`. 
You can replace `gpt4-hass` with your preferred model name. Execute the following SQL query to create your model:

```sql
CREATE  MODEL mindsdb.gpt4-hass
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

Configuration
-------------

Example layout of the `configuration.yaml`:

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
  pinecone_env: "northamerica-northeast1-gcp" #YOUR_PINECONE_ENVIRONMENT ID

sensor:
  - platform: openassist
    your_name: "YOUR_NAME" #Optional if you want ChatGPT to know your name.
    mindsdb_model: "gpt4-hass" #MINDSDB MODEL NAME.
    mindsdb_cookie: ".eJw9i8sKgCAUBf_...." #MINDSDB SESSION COOKIE
    notify_device: "alexa_media_office_echo" #Optional, this sends each ChatGPT response to your notify entity.
    #Can be any of your Notify entities. (Phone, Amazon Echo etc)

# If you need to debug any issues.
logger:
  default: info
  logs:
    custom_components.openassist: debug
 ```
