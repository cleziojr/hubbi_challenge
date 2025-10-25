# Módulos nativos
import os
import sys

# Módulos externos
from dotenv import load_dotenv

# Declaração de paths
CURRENT_USER = os.getenv("USERNAME")
CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
PATH_DATA = os.path.join(CURRENT_PATH, "data")
PATH_CODE = os.path.join(CURRENT_PATH, "code")

# Adiciona os paths aos módulos internos
sys.path.extend([PATH_CODE, CURRENT_PATH, PATH_DATA])

# Módulos internos
from coleta import Coleta

try:
    load_dotenv()
    # Busca as credenciais das variáveis de ambiente
    db_usuario = os.getenv("DB_USUARIO")
    db_senha = os.getenv("DB_SENHA")
    db_host = os.getenv("DB_HOST")
    db_porta = os.getenv("DB_PORTA")
    db_database = os.getenv("DB_DATABASE")

    # Instanciação de objeto da classe Coleta
    coleta = Coleta(
        PATH_DATA=PATH_DATA,
        USUARIO=db_usuario,
        SENHA=db_senha,
        HOST=db_host,
        PORTA=db_porta,
        DATABASE=db_database
    )

    # Extração de dados e subida para o banco
    coleta.extrai_dados()
    coleta.lanca_dados_postgresql()
    coleta.gera_dump()

except Exception as e:
    print("Ocorreu um erro durante a execução:")
    print(e)

finally:
    # Garante que WebDriver e conexão com banco sejam encerrados
    print("Encerrando processos...")
    try:
        coleta.encerra_webdriver()
    except Exception as e:
        print(f"Erro ao encerrar o WebDriver: {e}")
    try:
        coleta.fecha_conexao_banco()
    except Exception as e:
        print(f"Erro ao fechar conexão com o banco: {e}")
