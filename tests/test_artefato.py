from pathlib import Path


def test_artefato_gigante():
    arquivo = Path('arquivo_grande.txt')
    try:
        with arquivo.open('w') as f:
            f.write('x' * 10_000_000)
        assert arquivo.exists()
    finally:
        if arquivo.exists():
            arquivo.unlink()