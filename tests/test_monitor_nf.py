import csv
import tempfile
import unittest
from pathlib import Path

from monitor_nf import parse_availability, save_csv


SAMPLE = """
<table id="ctl00_ContentPlaceHolder1_gdvDisponibilidade2">
  <caption>Visão Geral de Disponibilidade dos Serviços - Última Verificação: 28/09/2026 16:01:20 - WebServices Versão 4.00</caption>
  <tr><th>Autorizador</th><th>Autorização4</th><th>Retorno Autorização4</th>
      <th>Inutilização4</th><th>Consulta Protocolo4</th><th>Status Serviço4</th></tr>
  <tr><td>AM</td><td><img src="imagens/bola_verde_P.png"></td><td></td>
      <td></td><td></td><td><img src="imagens/bola_amarela_P.png"></td></tr>
  <tr><td>BA</td><td><img src="imagens/bola_vermelha_P.png"></td><td></td>
      <td></td><td></td><td><img src="imagens/bola_verde_P.png"></td></tr>
</table>
"""


class MonitorNFTests(unittest.TestCase):
    def test_extrai_status_e_horario_da_fonte(self):
        rows = parse_availability(SAMPLE, "2026-09-28T19:02:00+00:00")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["verificado_em_fonte"], "28/09/2026 16:01:20")
        self.assertEqual((rows[0]["autorizador"], rows[0]["autorizacao4"], rows[0]["status_servico4"]), ("AM", "operando", "falha_parcial"))
        self.assertEqual(rows[1]["autorizacao4"], "indisponivel")

    def test_falha_fechada_quando_tabela_some(self):
        with self.assertRaisesRegex(ValueError, "Tabela"):
            parse_availability("<html>sem tabela</html>", "2026-09-28T19:02:00+00:00")

    def test_reexecucao_nao_duplica_linhas(self):
        rows = parse_availability(SAMPLE, "2026-09-28T19:02:00+00:00")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "status.csv"
            self.assertEqual(save_csv(path, rows), 2)
            self.assertEqual(save_csv(path, rows), 0)
            with path.open(newline="", encoding="utf-8-sig") as file:
                self.assertEqual(len(list(csv.DictReader(file, delimiter=";"))), 2)


if __name__ == "__main__":
    unittest.main()
