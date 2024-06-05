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


remover = regex.MarkdownRemover()

if current_version < required_version:
  raise ValueError(
      f"Error: OpenAI version {openai.__version__} is less than the required version 1.1.1"
  )
else:
  print("OpenAI version is compatible.")

app = Flask(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

# Load assistant ID from file or create new one
assistant_id = functions.create_assistant(client)
print("Assistant created with ID:", assistant_id)


# Create thread
@app.route('/start', methods=['GET'])
def start_conversation():
  thread = client.beta.threads.create()
  print("New conversation started with thread ID:", thread.id)
  return jsonify({"thread_id": thread.id})


# Start run
@app.route('/chat', methods=['POST'])
def chat():
  data = request.json
  thread_id = data.get('thread_id')
  user_input = data['message']
  if not thread_id:
    print("Error: Missing thread_id in /chat")
    return jsonify({"error": "Missing thread_id"}), 400
  print("Received message for thread ID:", thread_id, "Message:", user_input)

  client.beta.threads.messages.create(thread_id=thread_id,
                                      role="user",
                                      content=user_input )
  run = client.beta.threads.runs.create(thread_id=thread_id,
                                        assistant_id=assistant_id)
  print("Run started with ID:", run.id)


  return jsonify({"run_id": run.id})


# Check status of run
@app.route('/check', methods=['POST'])
def check_run_status():
  data = request.json
  thread_id = data.get('thread_id')
  run_id = data.get('run_id')
  if not thread_id or not run_id:
    print("Error: Missing thread_id or run_id in /check")
    return jsonify({"response": "error"})

  # Start timer ensuring no more than 9 seconds, ManyChat timeout is 10s
  start_time = time.time()
  while time.time() - start_time < 30:
    run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
    print("Checking run status:", run_status.status)
    if run_status.status == 'requires_action':
      print("Action in progress...")
      # Handle the function call
      for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
        if tool_call.function.name == "get_dentist_info":
          # Process lead creation
          print("get_dentist_info")
          arguments = json.loads(tool_call.function.arguments)
          output = db_helper.get_dentist_info(arguments)
          client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id,
                                                       run_id=run_id,
                                                       tool_outputs=[{
                                                           "tool_call_id":
                                                           tool_call.id,
                                                           "output":
                                                           json.dumps(output)
                                                       }])
        elif tool_call.function.name == "get_specialist":
          print("get_specialist")
          output = db_helper.get_specialist()
          client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id,
                                                       run_id=run_id,
                                                       tool_outputs=[{
                                                           "tool_call_id":
                                                           tool_call.id,
                                                           "output":
                                                           json.dumps(output)
                                                       }]) 
        elif tool_call.function.name == "get_procedures":
          print("get_procedures")
          arguments = json.loads(tool_call.function.arguments)
          output = db_helper.get_procedures(arguments)
          client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id,
                                                       run_id=run_id,
                                                       tool_outputs=[{
                                                           "tool_call_id":
                                                           tool_call.id,
                                                           "output":
                                                           json.dumps(output)
                                                       }])
        
   
    if run_status.status == 'completed':

      messages = client.beta.threads.messages.list(thread_id=thread_id)
      print(messages.data[0].content[0].text)
      message_content = messages.data[0].content[0].text
      # Remove annotations
      annotations = message_content.annotations

      for annotation in annotations:
        message_content.value = message_content.value.replace(
            annotation.text, '')

      # print(message_content.value)
      array = []
      # Expressão regular para encontrar e substituir o Markdown pelo link puro
      mensagem_modificada = re.sub(r'\[.*?\]\((.*?)\)', r'\1', message_content.value)

      
      info = re.findall('{clinic.name}', mensagem_modificada)
      
      if info != None:
        mensagem_modificada = re.sub('{clinic.name}',  'Dentz', mensagem_modificada)  
      
      print("Mensagem modificada:", mensagem_modificada)
      # for mensagem in message_content.value.splitlines():
      for mensagem in mensagem_modificada.splitlines():
        # if mensagem.startswith("-"):
        array.append(remover.remove_markdown(mensagem))
          
      # array.append(mensagem_modificada)
      print("Run completed, returning response")
      return jsonify({
          "response": array,
          "status": "completed"
      })
    
    time.sleep(1)

  print("Run timed out")
  return jsonify({"response": "timeout"})

if __name__ == '__main__':
  # print(get_answer("Gostaria de agendar uma consulta com o João"))
  app.run(host='0.0.0.0', port=8080)
