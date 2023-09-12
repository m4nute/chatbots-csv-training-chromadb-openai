import openai
from os import environ as env

def ask_openai(system_prompt, user_prompt):
    
    sysprompt = [{"role": "system", "content": system_prompt}]
    messages = sysprompt + user_prompt

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        api_key=env['OPENAI_KEY'],
    )
    return response["choices"][0]["message"]["content"]
