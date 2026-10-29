"""
Copia os backups (.dump) mais recentes da pasta de origem para a pasta de
destino, mantendo na pasta de destino apenas os N arquivos mais recentes.

Feito para rodar via Agendador de Tarefas do Windows: o script roda uma vez,
faz a verificação/cópia e termina (nada fica rodando em segundo plano).

Regra de nomes esperada: AAAAMMDDHH.dump (ex: 2026102501.dump), então a
ordenação alfabética dos nomes já corresponde à ordem cronológica.
"""

import logging
import shutil
from pathlib import Path

# ----------------------- CONFIGURAÇÃO -----------------------
SOURCE_DIR = Path(r"CAMINHO\DA\PASTA\ORIGEM")
DEST_DIR = Path(r"CAMINHO\DA\PASTA\DESTINO")

FILE_PATTERN = "*.dump"
KEEP_COUNT = 14

LOG_FILE = Path(__file__).with_name("backup_sync.log")
# --------------------------------------------------------------


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def list_dump_files(folder: Path) -> list[Path]:
    """Retorna os arquivos .dump da pasta, ordenados do mais antigo para o mais novo."""
    if not folder.is_dir():
        return []
    return sorted(folder.glob(FILE_PATTERN), key=lambda p: p.name)


def copy_missing_files(source_files: list[Path], dest_files: list[Path]) -> None:
    """Copia para o destino os arquivos da origem mais novos que o último já salvo."""
    last_dest_name = dest_files[-1].name if dest_files else ""

    if not dest_files:
        # Pasta destino vazia: evita copiar o histórico inteiro, pega só
        # os últimos KEEP_COUNT, que é o que vai sobrar de qualquer forma.
        to_copy = source_files[-KEEP_COUNT:]
    else:
        to_copy = [f for f in source_files if f.name > last_dest_name]

    if not to_copy:
        logging.info("Destino já está com o último arquivo da origem. Nada para copiar.")
        return

    for file in to_copy:
        destino = DEST_DIR / file.name
        shutil.copy2(file, destino)  # copy2 preserva data/hora; nunca move/exclui a origem
        logging.info("Copiado: %s", file.name)


def enforce_retention() -> None:
    """Mantém apenas os KEEP_COUNT arquivos mais recentes na pasta destino."""
    dest_files = list_dump_files(DEST_DIR)
    excedentes = dest_files[:-KEEP_COUNT] if len(dest_files) > KEEP_COUNT else []

    for file in excedentes:
        file.unlink()
        logging.info("Removido do destino (fora do limite de %d): %s", KEEP_COUNT, file.name)


def main():
    setup_logging()

    if not SOURCE_DIR.is_dir():
        logging.error("Pasta de origem não encontrada: %s", SOURCE_DIR)
        return

    DEST_DIR.mkdir(parents=True, exist_ok=True)

    source_files = list_dump_files(SOURCE_DIR)
    if not source_files:
        logging.warning("Nenhum arquivo %s encontrado na origem.", FILE_PATTERN)
        return

    dest_files = list_dump_files(DEST_DIR)

    copy_missing_files(source_files, dest_files)
    enforce_retention()

    logging.info("Verificação concluída.")


if __name__ == "__main__":
    main()
