import json
import requests
import os
from openai import OpenAI
from prompts import assistant_instructions

OPENAI_API_KEY = os.getenv('API_KEY')

# Init OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)

# Create or load assistant
def create_assistant(client):
  assistant_file_path = 'assistant.json'

  # If there is an assistant.json file already, then load that assistant
  if os.path.exists(assistant_file_path):
    with open(assistant_file_path, 'r') as file:
      assistant_data = json.load(file)
      assistant_id = assistant_data['assistant_id']
      print("Loaded existing assistant ID.")
  else:
    # If no assistant.json is present, create a new assistant using the below specifications

    # To change the knowledge document, modify the file name below to match your document
    # If you want to add multiple files, paste this function into ChatGPT and ask for it to add support for multiple files
    # file = client.files.create(file=open("knowledge.docx", "rb"),
    #                            purpose='assistants')
    assistant = client.beta.assistants.create(
                  instructions=assistant_instructions,
                  model="gpt-3.5-turbo-0125",
                  tools=[
                    #   {
                    #       "type": "file_search"
                    #   },
                      {
                          "type": "function",
                          "function": {
                              "name": "get_dentist_info",
                              "description": """Retorna dados com LINK para consulta para agendar uma consulta com o dentista de acordo com o nome e/ou a especialidade fornecida e/ou procedimento fornecido e se a função retornar 'No  records found' significa que não foi encontrado nenhum dado no banco de dados""",
                              "parameters": {
                                  "type": "object",
                                  "properties": {
                                      "name": {
                                          "type": "string",
                                          "description": "Nome do dentista. Dr. Marcelo Matos",
                                      },
                                      "specialist": {
                                          "type": "string",
                                          "description": "Especialidade do dentista. Odontologia",
                                      },
                                      "procedure": {
                                          "type": "string",
                                          "description": "Procedimento de uma especialidade odontológica. Limpeza Dental",
                                      },
                                  },
                                  "required": ["name"],
                              }
                          }
                      },
                      {
                          "type": "function",
                          "function": {
                              "name": "get_specialist",
                              "description": """Retorna todos as especialidades cadastradas do banco de dados"""
                          }
                      },
                      {
                          "type": "function",
                          "function": {
                              "name": "get_procedures",
                              "description": """Retorna todos os procedimentos cadastrados do banco de dados""",
                              "parameters": {
                                  "type": "object",
                                  "properties": {
                                      "specialist": {
                                          "type": "string",
                                          "description": "Specialist of the dentist. Odontologia",
                                      },
                                  },
                              }
                          }
                      }
                  ]
              )

    
    # # Create a vector store caled "Financial Statements"
    # vector_store = client.beta.vector_stores.create(name="Financial Statements")
    
    # # Ready the files for upload to OpenAI
    # file_paths = ["knowledge.docx"]
    # file_streams = [open(path, "rb") for path in file_paths]
    
    # # Use the upload and poll SDK helper to upload the files, add them to the vector store,
    # # and poll the status of the file batch for completion.
    # client.beta.vector_stores.file_batches.upload_and_poll(
    #   vector_store_id=vector_store.id, files=file_streams
    # )
        

    # Create a new assistant.json file to load on future runs
    with open(assistant_file_path, 'w') as file:
      json.dump({'assistant_id': assistant.id}, file)
      print("Created a new assistant and saved the ID.")

    assistant_id = assistant.id

  return assistant_id
