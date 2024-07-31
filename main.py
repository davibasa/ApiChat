from flask import Flask, request, jsonify
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from sqlalchemy import create_engine
import os
from urllib.parse import quote_plus
from sqlalchemy.exc import OperationalError
import datetime
from tools import tools
from prompt import assistant_instructions
import re
import regex
load_dotenv()
remove = regex.MarkdownRemover()

# Encode the password to handle special characters
password = quote_plus(os.getenv('MYSQL_PASSWORD'))
connection_string = f"mysql+mysqlconnector://{os.getenv('MYSQL_USERNAME')}:{password}@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DATABASE')}"
connection = create_engine(connection_string, pool_pre_ping=True)

app = Flask(__name__)

def CreateBot():
    model = ChatOpenAI(model="gpt-3.5-turbo")

    prompt = ChatPromptTemplate.from_messages(
            [
                ("system", assistant_instructions),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
                ("placeholder", "{tool_names}"),
                ("placeholder", "{tools}"),
                ("placeholder", "{clinica}"),
            ]
        )

    agent = create_tool_calling_agent(
        llm=model,
        tools=tools,  # Adicione suas ferramentas aqui
        prompt=prompt,
    )

    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,  # Adicione suas ferramentas aqui
        verbose=True,
        handle_parsing_errors=True
    )

    agent_with_chat_history = RunnableWithMessageHistory(
            agent_executor,
            get_session_history,
            input_messages_key="input",
            history_messages_key="history",
            agent_scratchpad_key="agent_scratchpad"
        )

    return agent_with_chat_history

def get_session_history(session_id):
    return SQLChatMessageHistory(session_id, connection_string)

def add_message_to_history(session_id, message, message_type="human"):
    history = get_session_history(session_id)
    if message_type == "human":
        history.add_user_message(message)
    elif message_type == "ai":
        history.add_ai_message(message)
    elif message_type == "system":
        history.add_message(SystemMessage(content=message))

agent_with_chat_history = CreateBot()


@app.route('/chat', methods=['POST'])
def chat():
    print("entrou")
    data = request.json
    query = data['query']
    numberFrom = data.get('numberFrom')
    numberTo = data.get('numberTo')
    clinic = data.get('clinic')
    primeira = data.get('primeira')
    session_id = f"session_id_{datetime.datetime.now().strftime('%d/%m/%Y')}_{numberFrom}_{numberTo}_{clinic}"
    
    if primeira:
        # Adiciona uma mensagem de contexto ao histórico como sistema
        add_message_to_history(session_id, "A clinica é Odontocamp", message_type="system")
        primeira = False
        
    try:
        response_in_lines = []
        response = agent_with_chat_history.invoke({"input": query}, config={"configurable": {"session_id": session_id}})
        response_modified = re.sub(r'\[.*?\]\((.*?)\)', r'\1',  response["output"])
        for msg in response_modified.splitlines():
            response_in_lines.append(remove.remove_markdown(msg))

        print(response_in_lines)
        return jsonify({"response": response_in_lines, "status": "completed"})
    except OperationalError:
        return jsonify({"error": "Database connection error"}), 500
    except Exception as e:
        return jsonify({"error": f"Erro ao processar a solicitação: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
