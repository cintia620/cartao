# Organizador Financeiro Familiar

Aplicativo web para organizar finanças da família com extratos de banco e cartões em Excel.

## Arquivos no repositório

Os arquivos principais do app **estão versionados** neste repositório:

- `app.py` (página inicial)
- `pages/1_Organizador_Financeiro.py` (página principal do organizador)
- `requirements.txt` (dependências)
- `README.md` (documentação)

Para conferir localmente:

```bash
git ls-files
```

## Estrutura de páginas

- **Home (`app.py`)**: página inicial para iniciar o app, com instruções e modelo de arquivo.
- **Organizador Financeiro (`pages/1_Organizador_Financeiro.py`)**: página principal com upload, categorização, gráficos, projeções e recomendações.

## Como executar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Abra no navegador: `http://localhost:8501`

## Fluxo de uso

1. Acesse a página **Organizador Financeiro** no menu lateral.
2. Envie Excel do banco e/ou cartões.
3. Faça o mapeamento das colunas (data, descrição, valor).
4. Revise categorias sugeridas e ajuste manualmente.
5. Analise métricas, gráficos e projeções.
6. Baixe o arquivo final em CSV.
