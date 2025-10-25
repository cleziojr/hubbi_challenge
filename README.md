# Desafio Técnico - Hubbi

Este projeto implementa uma **pipeline automatizada de ETL** que extrai dados de produtos de um site de testes, processa e armazena em um **banco PostgreSQL**.  

A solução é **100% containerizada**, utilizando **Docker Compose** para orquestrar:  

- A aplicação Python (`app`)  
- O navegador para web scraping (`selenium/firefox`)  
- O banco de dados (`PostgreSQL`)  

---

## 🛠️ Pré-requisitos

Para rodar o projeto, você precisa ter instalado:  

1. **Git** – para clonar o repositório.  
2. **Docker e Docker Compose v2** – essencial para executar toda a pipeline.  
3. **Python 3.8+** (opcional) – apenas se desejar consultar o notebook localmente.  

---

### Guia de instalação dos pré-requisitos

**Windows e macOS:**  

- Instale o Docker Desktop. O Docker Compose v2 já vem incluído.  

**Linux (Ubuntu/Debian):**  

```bash
sudo apt-get update
sudo apt-get install docker.io docker-compose-plugin
````

> ⚠️ Recomendado: siga os passos pós-instalação do Docker para usar sem privilégios de root.

```bash
docker --version
docker compose version
```

---

## 💻 Observações sobre Docker em diferentes sistemas operacionais

### Windows e macOS

* O **Docker Desktop** já inclui Docker Engine e Docker Compose v2.
* Comandos são exatamente os mesmos que os listados abaixo.

### Linux (Ubuntu/Debian)

* Pode ser necessário usar `sudo` para os comandos Docker:

```bash
sudo docker compose up -d --build
sudo docker compose logs -f app
sudo docker compose down
```

* Para não precisar usar `sudo` sempre, adicione seu usuário ao grupo docker:

```bash
sudo usermod -aG docker $USER
```

Depois faça logout/login para aplicar.

### Observações gerais

* Todos os comandos devem ser executados **dentro do diretório do projeto**, onde está o `docker-compose.yml`.
* Use sempre `docker compose` (v2) e não o antigo `docker-compose`.
* Em PowerShell/Windows, caminhos relativos podem usar `.\` em vez de `./`.

---

## 🔄 Restaurando o banco a partir do `.dump`

E caso você queira restaurar os dados a partir do arquivo `.dump` (por exemplo, para iniciar a pipeline com os dados já carregados), siga o passo a passo abaixo. **Importante:** reflita antes de subir o container se você deseja restaurar ou não, para evitar inconsistências.

O backup binário está localizado em `./data/hubbi_dw_backup.dump`.

### 1️⃣ Restaurar antes de subir o container (recomendado)

1. Certifique-se de que nenhum container do PostgreSQL está rodando:

```bash
docker compose down
```

2. Suba apenas o serviço do banco (opcional, mas útil para controle):

```bash
docker compose up -d db
```

3. Acesse o shell do container:

```bash
docker compose exec db bash
```

4. Crie o banco vazio:

```bash
createdb -U hubbi hubbi_dw
```

5. Restaure o dump dentro do container:

```bash
pg_restore -U hubbi -d hubbi_dw /data/hubbi_dw_backup.dump
```

6. Saia do container (`exit`) e então suba os demais serviços normalmente:

```bash
docker compose up -d --build
docker compose logs -f app
```

---

### 2️⃣ Restaurar com o container já em execução

Se você já subiu o container `db` com a aplicação:

1. Acesse o container:

```bash
docker compose exec db bash
```

2. Crie um banco novo (ou drope o existente, se quiser sobrescrever):

```bash
dropdb -U hubbi hubbi_dw
createdb -U hubbi hubbi_dw
```

3. Restaure o dump:

```bash
pg_restore -U hubbi -d hubbi_dw /data/hubbi_dw_backup.dump
```

4. Reinicie o container da aplicação (`app`) para garantir que ela se conecte ao banco atualizado:

```bash
docker compose restart app
```

---

### 💡 Observações importantes

* Restaurar o dump **antes de subir o container** é mais seguro e evita inconsistências.
* Se optar por restaurar com o container já rodando, lembre-se de dropar/recriar o banco ou usar um banco alternativo.
* O `.dump` é binário (`pg_dump -Fc`), garantindo que **tabelas, índices e dados** sejam restaurados exatamente como estavam.

---

## Executando a pipeline

### 1. Clone o repositório

```bash
git clone https://github.com/cleziojr/hubbi_challenge.git
cd hubbi_challenge
```

### 2. Suba os containers

```bash
docker compose up -d --build
```

O comando cria as imagens e inicia os serviços `app`, `db` e `selenium-firefox`. O script `main.py` será executado automaticamente dentro do container `app`.

### 3. Acompanhe os logs de execução

```bash
docker compose logs -f app
```

> Pressione `Ctrl+C` para sair dos logs (isso **não serve para os containers**).

### 4. Consulte a análise exploratória (EDA)

O projeto inclui um **notebook `eda_hubbi.ipynb`** com análises exploratórias e gráficos sobre os dados coletados.
Ele pode ser **consultado diretamente como arquivo `.ipynb`**, sem necessidade de execução, permitindo revisar gráficos, tabelas e insights obtidos.

### 5. Desligue a pipeline

```bash
docker compose down
docker compose down -v
```

---

## 💡 Decisões de design e arquitetura

### Estratégia de ETL

* **Carga de dados:** a carga no banco de dados é efetuada a cada página de produtos iterada. Esta decisão foi um *trade-off* consciente para alcançar um equilíbrio entre performance e persistência:

  * É mais seguro do que efetuar a carga apenas ao final da execução (o que elevaria a performance, mas diminuiria a garantia de persistência em caso de falha).

  * É muito mais performático do que efetuar a carga a cada produto (o que diminuiria drasticamente a performance, mas garantiria ao máximo a persistência).

* **Integridade dos dados:** antes de inserir os dados de um produto no banco, o algoritmo sempre verifica se aquele produto já foi inserido anteriormente. Desta forma, garante-se a integridade e apenas os dados novos sobem para o banco, permitindo que a pipeline seja executada repetidas vezes sem gerar duplicidade.

* **Ferramenta de extração:** optei pelo selenium para a extração dos dados. Embora eu já tenha criado pipelines utilizando requests e beautifulsoup para parsear e extrair o conteúdo, o selenium foi escolhido neste projeto por eu achar mais fácil de lidar, o que permitiu um desenvolvimento mais ágil.

### Infraestrutura

* **Containerização:** Docker garante ambiente consistente e portável.
* **Orquestração:** `docker-compose` gerencia `app`, `db` e `selenium-firefox`.

### Segurança e credenciais

* As credenciais do banco de dados (usuário, senha, host) estão armazenadas em variáveis de ambiente, lidas a partir de um arquivo .env. Esta é uma prática de segurança fundamental para proteger dados sensíveis.

* **Disclaimer para avaliação:** tenho ciência de que, em um ambiente de produção, o arquivo .env **nunca** é "commitado" no repositório. Para facilitar a execução e correção deste desafio, o arquivo .env foi excepcionalmente incluído.

---

## Análise exploratória dos dados (EDA)

* **Foco na ruptura de estoque:** durante a análise, foi observado (conforme detalhado no notebook eda_hubbi.py) uma grande similaridade no comportamento estatístico de diversas variáveis (como preço, peso e dimensões).

* Dada a baixa variação estatística em atributos como preço e dimensões, a análise foi direcionada ao insight de maior relevância para a empresa: a falta de estoque (ruptura). Aplicando o princípo de pareto (80/20), pude identificar que o problema está altamente concentrado. Isso permite que, ao invés de uma solução genérica, seja possível priorizar categorias e marcas específicas que trarão o maior impacto na redução de perdas por ruptura.

