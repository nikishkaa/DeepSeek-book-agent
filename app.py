import json
import os
import gradio as gr
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com",
)


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_books",
            "description": "Get a list of books from an online library in a form of JSON with basic information about each book.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A string of one or more query words, for example, 'cooking+recipies' or 'harry+potter'. "
                            "This string should be construsted based on the user's enquiry. If user's message is not in English, "
                            "you must translate the query into English first. If more than one word, the words must be "
                            "separated by '+'.",
                    }
                },
                "required": ["query"]
            },
        }
    },
]


def get_book(query):
    url = f'https://openlibrary.org/search.json?q={query}&fields=title,author_name,editions,language,first_publish_year'
    print(url)
    resp = requests.get(url)
    return resp.json()['docs']


def send_messages(message, history):
    messages = history + [{'role': 'user', 'metadata': None, 'content': message, 'options': None}]
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools
    )
    if response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        result = get_book(args["query"])

        messages.append(response.choices[0].message)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": str(result)
        })

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=tools,
        )
    return response.choices[0].message.content

demo = gr.ChatInterface(
    fn=send_messages,
    type="messages"
)

demo.launch(server_name='0.0.0.0')