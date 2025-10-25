# Módulos nativos
import os
import subprocess
import platform

# Módulos externos
import pandas as pd
import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine, text
import sqlalchemy

class Banco:

    def __init__(self, USUARIO: str, SENHA: str, HOST: str, PORTA: str, DATABASE: str, PATH_DATA: str):

        super().__init__()
        self.USUARIO = USUARIO
        self.SENHA = SENHA
        self.HOST = HOST
        self.PORTA = PORTA
        self.DATABASE = DATABASE
        self.PATH_DATA = PATH_DATA
        self.PATH_PROJETO = os.path.dirname(self.PATH_DATA)
        
        try:
            self.engine = self.cria_conexao_postgresql()
            print("Conexão com o banco de dados (Docker) estabelecida.")
        except Exception as e:
            print("Falha ao conectar ao banco de dados.")
            print("Verifique se o container Docker está rodando ('docker-compose up -d')")
            raise e

    def cria_conexao_postgresql(self) -> sqlalchemy.engine.Engine:
        url = f"postgresql+psycopg2://{self.USUARIO}:{self.SENHA}@{self.HOST}:{self.PORTA}/{self.DATABASE}"
        engine = create_engine(url)
        return engine

    def consulta_dados_produtos(self) -> pd.DataFrame:
        query = text("""
            SELECT  name,
                    product_url,
                    part_number,
                    brand_name,
                    category,
                    price,
                    gross_weight,
                    width,
                    length,
                    warranty,
                    material,
                    photo_url,
                    stock_quantity
            FROM sch_precificacao.product
        """)
        df_produtos = pd.read_sql(query, self.engine)
        return df_produtos

    def sobe_dados_postgresql(self, df: pd.DataFrame) -> None:
        try:
            df_produtos = self.consulta_dados_produtos()
            df_mesclado = df.merge(df_produtos, how='left', on=["part_number", "product_url", "name", "category"], indicator=True)
            df_mesclado = df_mesclado[df_mesclado['_merge'] == 'left_only'].drop(columns=['_merge'])
            df_mesclado = df_mesclado.loc[:, ~df_mesclado.columns.str.endswith('_y')]
            df_mesclado.columns = df_mesclado.columns.str.replace('_x', '', regex=False)
            
            if not df_mesclado.empty:
                df_mesclado.to_sql('product', self.engine, schema='sch_precificacao', if_exists='append', index=False)
                print(f"LOG: {len(df_mesclado)} novos produtos inseridos no banco.")
            else:
                print("LOG: Nenhum produto novo para inserir.")
        except Exception as e:
            print(f"Erro ao subir dados para o PostgreSQL: {e}")

    def lanca_dados_postgresql(self) -> None:
        path_csv = os.path.join(self.PATH_DATA, 'products.csv')
        try:
            df = pd.read_sql("SELECT * FROM sch_precificacao.product", self.engine)
            df.to_csv(path_csv, index=False)
            print(f"LOG: Dados exportados para {path_csv}")
        except Exception as e:
            print(f"Erro ao gerar CSV: {e}")

    def gera_dump(self):
        
        nome_arquivo = f"{self.DATABASE}_backup.dump"
        path_arquivo = os.path.join(self.PATH_DATA, nome_arquivo)

        comando = [
            "pg_dump",
            "-U", self.USUARIO,
            "-h", self.HOST,
            "-p", str(self.PORTA),
            "-F", "c",
            "-b",
            "-v",
            self.DATABASE
        ]
        
        env_com_senha = os.environ.copy()
        env_com_senha["PGPASSWORD"] = self.SENHA

        try:
            with open(path_arquivo, 'wb') as f:
                processo = subprocess.run(
                    comando,
                    check=True,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env_com_senha
                )
            print(f"Dump gerado com sucesso em: {path_arquivo}")
        except subprocess.CalledProcessError as e:
            erro_stderr = e.stderr.decode().strip()
            print(f"Erro ao gerar dump (via pg_dump nativo): {erro_stderr}")
        except FileNotFoundError:
            print(f"ERRO: Comando 'pg_dump' não encontrado no contêiner 'app'.")

    def fecha_conexao_banco(self):
        if hasattr(self, 'engine'):
            self.engine.dispose()
            print("INFO: Conexão com o banco fechada.")
