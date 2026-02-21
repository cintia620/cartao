from dataclasses import dataclass

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Organizador Financeiro", page_icon="📊", layout="wide")


@dataclass
class NormalizedColumns:
    date: str
    description: str
    amount: str
    source: str


def load_excel(file) -> pd.DataFrame:
    if file is None:
        return pd.DataFrame()

    xls = pd.ExcelFile(file)
    frames = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        if not df.empty:
            df["origem_planilha"] = sheet
            frames.append(df)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def normalize_dataframe(df: pd.DataFrame, cols: NormalizedColumns, source_name: str) -> pd.DataFrame:
    if df.empty:
        return df

    normalized = pd.DataFrame(
        {
            "data": pd.to_datetime(df[cols.date], errors="coerce"),
            "descricao": df[cols.description].astype(str),
            "valor": pd.to_numeric(df[cols.amount], errors="coerce"),
            "fonte": source_name,
        }
    )
    normalized["tipo"] = np.where(normalized["valor"] >= 0, "entrada", "despesa")
    normalized["valor_abs"] = normalized["valor"].abs()
    return normalized.dropna(subset=["data", "valor"])


def suggest_category(description: str) -> str:
    text = description.lower()
    rules = {
        "Alimentação": ["mercado", "super", "ifood", "restaurante", "padaria"],
        "Transporte": ["uber", "99", "combust", "posto", "ônibus", "metro"],
        "Moradia": ["aluguel", "condominio", "energia", "água", "internet", "gás"],
        "Saúde": ["farmacia", "hospital", "clinica", "plano"],
        "Educação": ["escola", "curso", "faculdade", "livraria"],
        "Lazer": ["cinema", "show", "streaming", "bar", "viagem"],
    }
    for category, keywords in rules.items():
        if any(word in text for word in keywords):
            return category
    return "Outros"


def generate_recommendations(df: pd.DataFrame) -> list[str]:
    expenses = df[df["tipo"] == "despesa"].copy()
    if expenses.empty:
        return ["Sem despesas registradas para recomendar otimizações."]

    monthly = (
        expenses.assign(mes=expenses["data"].dt.to_period("M").astype(str))
        .groupby("mes")["valor_abs"]
        .sum()
        .sort_index()
    )

    suggestions = []
    if len(monthly) >= 2 and monthly.iloc[-1] > monthly.mean() * 1.15:
        suggestions.append("Seu último mês ficou acima da média. Defina um teto semanal para reduzir picos.")

    by_category = expenses.groupby("categoria")["valor_abs"].sum().sort_values(ascending=False)
    total = by_category.sum()
    for category, amount in by_category.head(3).items():
        share = amount / total
        if share > 0.25:
            suggestions.append(
                f"A categoria '{category}' representa {share:.0%} das despesas. Meta: reduzir 10% e enviar para poupança."
            )

    discretionary = expenses[expenses["categoria"].isin(["Lazer", "Outros"])]
    if not discretionary.empty:
        possible_saving = discretionary["valor_abs"].sum() * 0.12
        suggestions.append(
            f"Reduzir gastos discricionários (Lazer/Outros) pode liberar ~R$ {possible_saving:,.2f} para reserva."
        )

    return suggestions or ["Seus dados parecem equilibrados. Continue acompanhando mensalmente."]


def projected_expenses(df: pd.DataFrame) -> pd.DataFrame:
    expenses = df[df["tipo"] == "despesa"].copy()
    if expenses.empty:
        return pd.DataFrame()

    monthly = (
        expenses.assign(mes=expenses["data"].dt.to_period("M").dt.to_timestamp())
        .groupby("mes")["valor_abs"]
        .sum()
        .reset_index()
        .sort_values("mes")
    )

    if len(monthly) < 2:
        return pd.DataFrame()

    x = np.arange(len(monthly))
    y = monthly["valor_abs"].values
    coef = np.polyfit(x, y, 1)

    future_idx = np.arange(len(monthly), len(monthly) + 3)
    future_dates = pd.date_range(monthly["mes"].max() + pd.offsets.MonthBegin(1), periods=3, freq="MS")
    future_vals = coef[0] * future_idx + coef[1]

    forecast = pd.DataFrame({"mes": future_dates, "valor_abs": np.maximum(future_vals, 0), "tipo": "projeção"})
    history = monthly.assign(tipo="histórico")
    return pd.concat([history, forecast], ignore_index=True)


st.title("📊 Organizador Financeiro")
st.write("Envie seus arquivos Excel de banco e cartão para organizar despesas da família.")

col1, col2 = st.columns(2)
with col1:
    bank_file = st.file_uploader("Arquivo Excel da conta bancária", type=["xls", "xlsx"], key="bank")
with col2:
    card_file = st.file_uploader("Arquivo Excel dos cartões", type=["xls", "xlsx"], key="card")

bank_df = load_excel(bank_file)
card_df = load_excel(card_file)

if bank_df.empty and card_df.empty:
    st.info("Faça upload de pelo menos um arquivo para começar.")
    st.stop()

st.subheader("1) Mapeie as colunas")


def mapping_ui(df: pd.DataFrame, prefix: str) -> NormalizedColumns | None:
    if df.empty:
        return None

    options = list(df.columns)
    c1, c2, c3 = st.columns(3)
    with c1:
        date_col = st.selectbox(f"{prefix}: coluna de data", options=options, key=f"{prefix}-date")
    with c2:
        desc_col = st.selectbox(f"{prefix}: descrição", options=options, key=f"{prefix}-desc")
    with c3:
        amount_col = st.selectbox(f"{prefix}: valor", options=options, key=f"{prefix}-amount")
    return NormalizedColumns(date=date_col, description=desc_col, amount=amount_col, source=prefix)


bank_map = mapping_ui(bank_df, "Banco")
card_map = mapping_ui(card_df, "Cartão")

normalized_frames = []
if bank_map:
    normalized_frames.append(normalize_dataframe(bank_df, bank_map, "Banco"))
if card_map:
    normalized_frames.append(normalize_dataframe(card_df, card_map, "Cartão"))

if not normalized_frames:
    st.warning("Não foi possível normalizar os dados enviados.")
    st.stop()

all_data = pd.concat(normalized_frames, ignore_index=True)
all_data["categoria"] = all_data["descricao"].apply(suggest_category)

st.subheader("2) Revise e ajuste categorias")
edited = st.data_editor(
    all_data[["data", "descricao", "valor", "valor_abs", "tipo", "fonte", "categoria"]],
    num_rows="dynamic",
    use_container_width=True,
    disabled=["valor_abs", "tipo", "fonte"],
    column_config={
        "categoria": st.column_config.SelectboxColumn(
            "categoria",
            options=["Alimentação", "Transporte", "Moradia", "Saúde", "Educação", "Lazer", "Outros"],
        )
    },
)

edited["valor_abs"] = edited["valor"].abs()
edited["tipo"] = np.where(edited["valor"] >= 0, "entrada", "despesa")

st.subheader("3) Painel de indicadores")
expenses = edited[edited["tipo"] == "despesa"]
income = edited[edited["tipo"] == "entrada"]

k1, k2, k3 = st.columns(3)
k1.metric("Entradas", f"R$ {income['valor_abs'].sum():,.2f}")
k2.metric("Despesas", f"R$ {expenses['valor_abs'].sum():,.2f}")
k3.metric("Saldo", f"R$ {edited['valor'].sum():,.2f}")

if not expenses.empty:
    fig_cat = px.pie(
        expenses,
        names="categoria",
        values="valor_abs",
        title="Distribuição de despesas por categoria",
    )
    st.plotly_chart(fig_cat, use_container_width=True)

    monthly = (
        edited.assign(mes=edited["data"].dt.to_period("M").astype(str))
        .groupby(["mes", "tipo"])["valor_abs"]
        .sum()
        .reset_index()
    )
    fig_month = px.bar(monthly, x="mes", y="valor_abs", color="tipo", barmode="group", title="Entradas x Despesas por mês")
    st.plotly_chart(fig_month, use_container_width=True)

forecast = projected_expenses(edited)
if not forecast.empty:
    fig_forecast = px.line(
        forecast,
        x="mes",
        y="valor_abs",
        color="tipo",
        markers=True,
        title="Projeção de despesas (3 meses)",
    )
    st.plotly_chart(fig_forecast, use_container_width=True)

st.subheader("4) Recomendações")
for rec in generate_recommendations(edited):
    st.write(f"- {rec}")

csv_data = edited.to_csv(index=False).encode("utf-8")
st.download_button("Baixar despesas categorizadas (CSV)", data=csv_data, file_name="despesas_categorizadas.csv")
