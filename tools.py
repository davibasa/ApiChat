from langchain_core.tools import Tool, StructuredTool 
from langchain.pydantic_v1 import BaseModel, Field
from db_tools import get_procedures, get_all_dentist, get_specialist, get_dentist_info

class DentistInfo(BaseModel):
    name: str = Field(default="", description="Capture o nome do dentista informado")
    specialist: str = Field(default="", description="Capture a especialidade do dentista")
    procedure: str = Field(default="", description="Captura o tipo de procedimento de uma especialidade odontológica que deseja")


class ProcedureInfo(BaseModel):
    specialist: str = Field(description="Capture a especialidade odontológica")

tools=[
    StructuredTool(
        name="GetDentistInfo",
        func=get_dentist_info,
        description="Retorna dados com LINK para consulta para agendar uma consulta com o dentista de acordo com o nome e/ou a especialidade fornecida e/ou procedimento fornecido e se a função retornar 'No  records found' significa que não foi encontrado nenhum dado no banco de dados. Caso a mensagem tenha marcação de tempo como 'hoje', 'semana que vem', entre outros, retornar link para consulta ",
        args_schema=DentistInfo,
    ),
    Tool(
        name="GetAllSpecialist",
        func=get_specialist,
        description="Retorna todos as especialidades odontológicas cadastradas do banco de dados",
    ),
    Tool(
        name="GetAllDentist",
        func=get_all_dentist,
        description="Retorna todos os dentistas da clinica com as especialidades de cada um cadastradas do banco de dados",
    ),
    StructuredTool(
        name="GetProcedures",
        func=get_procedures,
        description="Retorna todos os procedimentos cadastrados do banco de dados",
        args_schema=ProcedureInfo,
    ),
]
