"""Consulta a disponibilidade pública da NF-e e registra uma coleta em CSV."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


SOURCE_URL = (
    "https://www.nfe.fazenda.gov.br/portal/disponibilidade.aspx"
    "?versao=0.00&tipoConteudo=P2c98tUpxrI="
)
TABLE_ID = "ctl00_ContentPlaceHolder1_gdvDisponibilidade2"
FIELDS = (
    "consultado_em_utc",
    "verificado_em_fonte",
    "autorizador",
    "autorizacao4",
    "status_servico4",
)


class AvailabilityTable(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_table = False
        self.in_caption = False
        self.in_cell = False
        self.caption = ""
        self.rows: list[list[tuple[str, str]]] = []
        self.row: list[tuple[str, str]] | None = None
        self.cell_text = ""
        self.cell_image = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "table" and attributes.get("id") == TABLE_ID:
            self.in_table = True
        elif self.in_table and tag == "caption":
            self.in_caption = True
        elif self.in_table and tag == "tr":
            self.row = []
        elif self.row is not None and tag in ("td", "th"):
            self.in_cell = True
            self.cell_text = ""
            self.cell_image = ""
        elif self.in_cell and tag == "img":
            self.cell_image = attributes.get("src") or ""

    def handle_data(self, data: str) -> None:
        if self.in_caption:
            self.caption += data
        if self.in_cell:
            self.cell_text += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "caption":
            self.in_caption = False
        elif tag in ("td", "th") and self.in_cell and self.row is not None:
            self.row.append((" ".join(self.cell_text.split()), self.cell_image))
            self.in_cell = False
        elif tag == "tr" and self.row is not None:
            if self.row:
                self.rows.append(self.row)
            self.row = None
        elif tag == "table" and self.in_table:
            self.in_table = False


def image_status(source: str) -> str:
    name = source.lower()
    for color, status in (
        ("bola_verde", "operando"),
        ("bola_amarela", "falha_parcial"),
        ("bola_vermelha", "indisponivel"),
    ):
        if color in name:
            return status
    return "desconhecido"


def parse_availability(html: str, collected_at: str) -> list[dict[str, str]]:
    table = AvailabilityTable()
    table.feed(html)
    if len(table.rows) < 2:
        raise ValueError("Tabela de disponibilidade ausente ou vazia")

    headers = [cell[0].casefold().replace(" ", "") for cell in table.rows[0]]
    try:
        name_col = headers.index("autorizador")
        auth_col = headers.index("autorização4")
        service_col = headers.index("statusserviço4")
    except ValueError as error:
        raise ValueError("Colunas esperadas não encontradas na tabela") from error

    match = re.search(r"Última Verificação:\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})", table.caption)
    if not match:
        raise ValueError("Data de verificação da fonte não encontrada")
    source_time = match.group(1)

    records = []
    for row in table.rows[1:]:
        if len(row) <= max(name_col, auth_col, service_col):
            raise ValueError("Linha incompleta na tabela de disponibilidade")
        authorizer = row[name_col][0]
        if not authorizer:
            raise ValueError("Autorizador vazio na tabela de disponibilidade")
        records.append(
            {
                "consultado_em_utc": collected_at,
                "verificado_em_fonte": source_time,
                "autorizador": authorizer,
                "autorizacao4": image_status(row[auth_col][1]),
                "status_servico4": image_status(row[service_col][1]),
            }
        )
    if not records or all(
        record["autorizacao4"] == record["status_servico4"] == "desconhecido"
        for record in records
    ):
        raise ValueError("Nenhum status reconhecido na tabela de disponibilidade")
    return records


def save_csv(path: Path, records: list[dict[str, str]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: set[tuple[str, str]] = set()
    if path.exists():
        with path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file, delimiter=";")
            if tuple(reader.fieldnames or ()) != FIELDS:
                raise ValueError("O CSV existente possui colunas diferentes das esperadas")
            existing = {
                (row["verificado_em_fonte"], row["autorizador"]) for row in reader
            }
    new_records = [
        record
        for record in records
        if (record["verificado_em_fonte"], record["autorizador"]) not in existing
    ]
    if new_records:
        with path.open("a", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDS, delimiter=";")
            if not existing and path.stat().st_size == 0:
                writer.writeheader()
            writer.writerows(new_records)
    return len(new_records)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("status_servicos.csv"))
    parser.add_argument("--html-file", type=Path, help="Usa uma cópia local da página para conferência")
    args = parser.parse_args()
    try:
        if args.html_file:
            html = args.html_file.read_text(encoding="utf-8-sig")
        else:
            request = Request(SOURCE_URL, headers={"User-Agent": "Monitorar-NF/1.0"})
            with urlopen(request, timeout=25) as response:
                html = response.read().decode("utf-8-sig", errors="replace")
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        records = parse_availability(html, now)
        added = save_csv(args.output, records)
    except (OSError, ValueError, UnicodeError) as error:
        print(f"Falha na coleta: {error}", file=sys.stderr)
        return 1
    print(f"Fonte: {records[0]['verificado_em_fonte']} | autorizadores: {len(records)} | linhas novas: {added} | CSV: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
