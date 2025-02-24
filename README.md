Monitor NF Status

Olá, meu nome é Lucas da Silva Pereira e desenvolvi este projeto para monitorar a disponibilidade dos serviços de Nota Fiscal Eletrônica (NF-e) no site da Receita Federal. Meu objetivo foi criar uma solução automatizada que acessa periodicamente a página de status, extrai as informações relevantes e salva os dados em um arquivo CSV para análise posterior.

Funcionalidades

Acesso automático à página de disponibilidade da NF-e.

Extração dos dados de status dos autorizadores.

Salvamento dos dados extraídos em um arquivo CSV.

Registro de logs das execuções para acompanhamento.

Verificação automática a cada 10 minutos.

Tecnologias Utilizadas

Python 3

Requests

BeautifulSoup (bs4)

Schedule

Logging

CSV

Estrutura do Projeto

Monitor_NF_Status
├── monitor_nf.py  # Script principal
├── status_servicos.csv  # Arquivo CSV com os status coletados
└── monitor_nf.log  # Arquivo de log das execuções

Instalação e Uso

1. Clone o repositório:

git clone https://github.com/lucasdasilvapereira/monitor-nf-status.git
cd monitor-nf-status

2. Instale as dependências:

pip install -r requirements.txt

3. Execute o script:

python monitor_nf.py

Assim que o script for iniciado, ele começará a monitorar os serviços e atualizar os dados automaticamente a cada 10 minutos.

Como Funciona

O script acessa a página de disponibilidade da NF-e.

Extrai os dados da tabela de status.

Traduz os ícones de status em texto legível.

Salva os dados extraídos em um arquivo CSV.

Registra logs para rastrear erros e execuções.

Mantém o monitoramento ativo, executando a verificação a cada 10 minutos.

Possíveis Melhorias

Criar uma interface gráfica para visualização dos dados.

Implementar alertas por e-mail ou Telegram quando um serviço estiver indisponível.

Criar um dashboard para análise dos históricos de disponibilidade.

Licença

Este projeto está sob a licença MIT. Fique à vontade para usá-lo e melhorá-lo!

Desenvolvido por Lucas da Silva Pereira
