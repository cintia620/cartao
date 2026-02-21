import pandas as pd
import streamlit as st

st.set_page_config(page_title="Organizador Financeiro Familiar", page_icon="💸", layout="wide")

st.title("💸 Organizador Financeiro Familiar")
st.subheader("Página inicial do app web")

st.markdown(
    """
Bem-vindo! Esta é a página principal para iniciar seu organizador financeiro.

### Como usar
1. No menu lateral, clique em **Organizador Financeiro**.
2. Envie os arquivos Excel do banco e dos cartões.
3. Mapeie colunas de data, descrição e valor.
4. Revise categorias, acompanhe gráficos e veja projeções.
5. Baixe o resultado categorizado em CSV.
"""
)

st.info("Dica: para melhor resultado, mantenha datas válidas e valores numéricos no Excel.")

sample = pd.DataFrame(
    {
        "data": ["2026-01-05", "2026-01-06", "2026-01-10"],
        "descricao": ["Salário", "Supermercado", "Uber"],
        "valor": [4500.00, -320.40, -38.90],
    }
)

st.download_button(
    "Baixar modelo de planilha (CSV)",
    data=sample.to_csv(index=False).encode("utf-8"),
    file_name="modelo_financeiro.csv",
    mime="text/csv",
)

st.success("Pronto! Agora acesse a página **Organizador Financeiro** no menu lateral para rodar o app.")
