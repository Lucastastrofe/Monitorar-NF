# Monitorar-NF

Consulta a [disponibilidade dos serviços da NF-e](https://www.nfe.fazenda.gov.br/portal/disponibilidade.aspx?versao=0.00&tipoConteudo=P2c98tUpxrI=) e grava uma linha por autorizador em CSV. O arquivo registra o horário da consulta em UTC, o horário informado pela página e os estados de Autorização4 e Status Serviço4.

## Executar

Requer Python 3.11 ou mais recente. Não precisa instalar pacotes.

```sh
python monitor_nf.py --output status_servicos.csv
```

Cada execução consulta a página uma vez. Para manter histórico, agende o comando no sistema operacional. Se a fonte repetir o mesmo horário de verificação, as linhas já registradas não são duplicadas.

O comando termina com código 1 e uma mensagem de erro quando a fonte falha, a tabela muda ou o CSV existente tem outro formato. Nessas situações, não grava status falsos.

Para conferir uma cópia HTML da página sem acessar a rede:

```sh
python monitor_nf.py --html-file pagina.html --output status_servicos.csv
```

## Dados

`operando`, `falha_parcial` e `indisponivel` seguem as imagens exibidas pelo portal. Uma imagem não reconhecida recebe `desconhecido`, sem interpretação automática. O horário `verificado_em_fonte` é apresentado pelo portal e não indica o momento exato em que cada serviço mudou de estado.

Este projeto registra o que o portal público mostra. Não substitui uma verificação direta do serviço de emissão de NF-e.
