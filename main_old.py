import json
import os
import time
from flask import Flask, request, jsonify
import openai
from openai import OpenAI
import functions
import regex
import db_helper
from packaging import version
import re
from dotenv import load_dotenv

required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
# OPENAI_API_KEY = 'sk-proj-dMlRhRxrJfBrIEfZFlUMT3BlbkFJOi234S2kwqtcnPNcof2V'
# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Acessar a chave da API armazenada em variáveis de ambiente
OPENAI_API_KEY = os.getenv('API_KEY')

if not OPENAI_API_KEY:
    raise ValueError("Error: Missing API_KEY in environment variables")

remover = regex.MarkdownRemover()

if current_version < required_version:
    raise ValueError(f"Error: OpenAI version {openai.__version__} is less than the required version 1.1.1")
else:
    print("OpenAI version is compatible.")

app = Flask(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

try:
    assistant_id = functions.create_assistant(client)
    print("Assistant created with ID:", assistant_id)
except Exception as e:
    print(f"Error creating assistant: {e}")
    assistant_id = None

@app.route('/start', methods=['GET'])
def start_conversation():
    try:
        thread = client.beta.threads.create()
        print("New conversation started with thread ID:", thread.id)
        return jsonify({"thread_id": thread.id})
    except Exception as e:
        print(f"Error starting conversation: {e}")
        return jsonify({"error": "Failed to start conversation"}), 500

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    thread_id = data.get('thread_id')
    user_input = data.get('message')

    if not thread_id or not user_input:
        print("Error: Missing thread_id or message in /chat")
        return jsonify({"error": "Missing thread_id or message"}), 400

    try:
        client.beta.threads.messages.create(thread_id=thread_id, role="user", content=user_input)
        run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)
        print("Run started with ID:", run.id)
        return jsonify({"run_id": run.id})
    except Exception as e:
        print(f"Error in /chat: {e}")
        return jsonify({"error": "Failed to create chat or run"}), 500

@app.route('/check', methods=['POST'])
def check_run_status():
    data = request.json
    thread_id = data.get('thread_id')
    run_id = data.get('run_id')

    if not thread_id or not run_id:
        print("Error: Missing thread_id or run_id in /check")
        return jsonify({"error": "Missing thread_id or run_id"}), 400

    try:
        start_time = time.time()
        while time.time() - start_time < 30:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            print("Checking run status:", run_status.status)

            if run_status.status == 'requires_action':
                for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
                    try:
                        if tool_call.function.name == "get_dentist_info":
                            arguments = json.loads(tool_call.function.arguments)
                            output = db_helper.get_dentist_info(arguments)
                        elif tool_call.function.name == "get_specialist":
                            output = db_helper.get_specialist()
                        elif tool_call.function.name == "get_all_dentist":
                            output = db_helper.get_all_dentist()
                        elif tool_call.function.name == "get_procedures":
                            arguments = json.loads(tool_call.function.arguments)
                            output = db_helper.get_procedures(arguments)
                        elif tool_call.function.name == "get_emergency":
                            output = "Atendente necessária"
                        else:
                            output = None

                        if output is not None:
                            client.beta.threads.runs.submit_tool_outputs(
                                thread_id=thread_id,
                                run_id=run_id,
                                tool_outputs=[{"tool_call_id": tool_call.id, "output": json.dumps(output)}]
                            )
                    except Exception as e:
                        print(f"Error processing tool call {tool_call.function.name}: {e}")

            if run_status.status == 'completed':
                try:
                    messages = client.beta.threads.messages.list(thread_id=thread_id)
                    message_content = messages.data[0].content[0].text
                    annotations = message_content.annotations

                    for annotation in annotations:
                        message_content.value = message_content.value.replace(annotation.text, '')

                    array = []
                    mensagem_modificada = re.sub(r'\[.*?\]\((.*?)\)', r'\1', message_content.value)
                    info = re.findall('{clinica}', mensagem_modificada)
                    
                    
                    if info:
                        mensagem_modificada = re.sub('{clinica}', 'Odontocamp', mensagem_modificada)

                    if re.findall('{user.name}', mensagem_modificada):
                        mensagem_modificada = re.sub('{user.name}', '', mensagem_modificada)

                    
                    for mensagem in mensagem_modificada.splitlines():
                        array.append(remover.remove_markdown(mensagem))

                    print("Run completed, returning response")
                    return jsonify({"response": array, "status": "completed"})
                except Exception as e:
                    print(f"Error processing completed run: {e}")
                    return jsonify({"error": "Failed to process completed run"}), 500

            time.sleep(1)

        print("Run timed out")
        return jsonify({"response": "timeout"}), 504
    except Exception as e:
        print(f"Error checking run status: {e}")
        return jsonify({"error": "Failed to check run status"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
