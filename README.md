import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import schedule
import time
import logging
import csv

# Função para configurar o log
def configurar_logs(caminho_pasta):
    log_file = os.path.join(caminho_pasta, "monitor_nf.log")
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.info("Logs configurados com sucesso.")

# Função para obter o caminho da pasta onde os arquivos serão salvos
def obter_caminho_pasta():
    caminho_pasta = os.path.join(os.path.expanduser("~"), "Desktop", "Monitor_NF_Status")
    os.makedirs(caminho_pasta, exist_ok=True)
    return caminho_pasta

# Função para criar o arquivo CSV, caso ele não exista
def criar_arquivo_csv(caminho_pasta):
    caminho_csv = os.path.join(caminho_pasta, "status_servicos.csv")
    if not os.path.exists(caminho_csv):
        with open(caminho_csv, mode="w", newline="", encoding="utf-8-sig") as arquivo:
            escritor = csv.writer(arquivo, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL)
            # Coloca a legenda de status no topo com as cores associadas
            escritor.writerow(["Legenda de Status:"])
            escritor.writerow(["Verde", "Operando normalmente", "Serviço funcionando sem problemas."])
            escritor.writerow(["Amarelo", "Operando com falhas", "Problemas parciais no serviço."])
            escritor.writerow(["Vermelho", "Indisponível", "Serviço fora de operação."])
            escritor.writerow([])  # Linha em branco
            # Adiciona a linha de cabeçalho para os dados coletados
            escritor.writerow(["Data/Hora", "Autorizador", "Autorização4", "Status Serviço4"])
    return caminho_csv

# Função para buscar a página da web com o status dos serviços
def buscar_pagina_status(url):
    try:
        resposta = requests.get(url)
        resposta.raise_for_status()
        logging.info("Página acessada com sucesso.")
        return resposta.text
    except requests.HTTPError as e:
        logging.error(f"Erro HTTP ao acessar a página: {e}")
    except requests.RequestException as e:
        logging.error(f"Erro de requisição ao acessar a página: {e}")
    return None

# Função para analisar os dados da tabela de status
def analisar_tabela_status(html):
    try:
        soup = BeautifulSoup(html, "html.parser")
        tabela = soup.find("table", {"id": "ctl00_ContentPlaceHolder1_gdvDisponibilidade2"})
        if not tabela:
            logging.warning("Tabela não encontrada.")
            return []
        linhas = tabela.find_all("tr")[1:]  # Ignora a primeira linha (cabeçalho)
        dados = []
        for linha in linhas:
            colunas = linha.find_all("td")
            if len(colunas) < 6:
                logging.warning("Linha incompleta encontrada.")
                continue
            autorizador = colunas[0].get_text(strip=True)
            autorizacao4 = traduzir_status(colunas[1])
            status_servico4 = traduzir_status(colunas[5])
            dados.append([autorizador, autorizacao4, status_servico4])
        logging.info(f"{len(dados)} linhas extraídas da tabela.")
        return dados
    except Exception as e:
        logging.error(f"Erro ao analisar HTML: {e}")
        return []

# Função para traduzir o status com base na imagem
def traduzir_status(col):
    try:
        img = col.find("img")
        if img:
            src = img.get("src", "").lower()
            if "bola_verde" in src:
                return "Operando normalmente"
            elif "bola_amarela" in src:
                return "Operando com falhas"
            elif "bola_vermelha" in src:
                return "Indisponível"
    except Exception as e:
        logging.error(f"Erro ao traduzir status: {e}")
    return "Status desconhecido"

# Função para salvar os dados no CSV
def salvar_em_csv(dados, caminho_csv):
    try:
        with open(caminho_csv, mode="a", newline="", encoding="utf-8-sig") as arquivo:
            escritor = csv.writer(arquivo, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for linha in dados:
                escritor.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + linha)
    except Exception as e:
        logging.error(f"Erro ao salvar em CSV: {e}")

# Função que realiza o processo completo de monitoramento
def tarefa():
    url = "http://www.nfe.fazenda.gov.br/portal/disponibilidade.aspx?versao=0.00&tipoConteudo=P2c98tUpxrI="
    caminho_pasta = obter_caminho_pasta()
    caminho_csv = criar_arquivo_csv(caminho_pasta)
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Monitoramento em andamento...")
    html = buscar_pagina_status(url)
    if html:
        dados = analisar_tabela_status(html)
        if dados:
            salvar_em_csv(dados, caminho_csv)
            logging.info("Dados salvos no CSV com sucesso.")
        else:
            logging.warning("Nenhum dado extraído.")
    else:
        logging.error("Não foi possível acessar o HTML.")

# Função para agendar a execução da tarefa a cada 10 minutos
def agendar_tarefas():
    schedule.every(10).minutes.do(tarefa)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    caminho_pasta = obter_caminho_pasta()
    configurar_logs(caminho_pasta)
    print("Monitoramento iniciado. Verifique o log para detalhes.")
    tarefa()
    agendar_tarefas()
