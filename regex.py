import re

class MarkdownRemover:
    def __init__(self):
        # Compilação da expressão regular para capturar elementos comuns de Markdown e quebras de linha
        self.pattern = re.compile(
            r'(\*\*|__)(.*?)\1'              # Negrito
            r'|(\*|_)(.*?)\3'                # Itálico
            r'|\[(.*?)\]\(.*?\)'             # Links
            r'|(`)(.*?)\6'                   # Códigos inline
            r'|(```)(.*?)\8'                 # Blocos de código
            r'|(\~\~)(.*?)\10'               # Tachado
            , re.MULTILINE | re.DOTALL)      # Flags para multilinhas e captura de qualquer caractere

    def remove_markdown(self, text):
        # Substitui as ocorrências de Markdown no texto
        text = self.pattern.sub(r'\2\4\5\7\9\11', text)
        # Substitui quebras de linha por "%0A"
        text = text.replace('\n', '<br>')
        return text
