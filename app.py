import streamlit as st
import re
import unicodedata
from datetime import datetime


# MEDICAMENTOS CONTROLADOS
medicacoes_controladas = {
    "AMITRIPTILINA",
    "BIPERIDENO",
    "CARBAMAZEPINA",
    "CARBONATO",
    "CLONAZEPAM",
    "CLORPROMAZINA",
    "DIAZEPAM",
    "FENITOINA",
    "FENOBARBITAL",
    "FLUOXETINA",
    "HALOPERIDOL",
    "IMIPRAMINA",
    "LEVOMEPROMAZINA",
    "METILFENIDATO",
    "MORFINA",
    "RISPERIDONA",
    "SERTRALINA"
}


# MEDICAMENTOS DE USO AGUDO (IGNORAR NO CÁLCULO)
medicacoes_agudas = {
    "DIPIRONA",
    "PARACETAMOL",
    "IBUPROFENO",
    "AMOXICILINA",
    "AZITROMICINA",
    "MIKANIA"
}


def normalizar_nome(nome):

    nome = nome.upper()
    nome = unicodedata.normalize("NFD", nome)
    nome = nome.encode("ascii", "ignore").decode("utf-8")

    return nome


def limpar_quantidade(valor):

    valor = valor.replace(".", "").replace(",", ".")
    return int(float(valor))


def extrair_dados(texto):

    dados = {
        "paciente": "Não identificado",
        "profissional": "Não identificado",
        "data_prescricao": "Não identificada",
        "medicamentos": []
    }

    paciente = re.search(r'Paciente\s*\n?\(\d+\)\s*([A-ZÁ-Ú\s]+)', texto)
    if paciente:
        dados["paciente"] = paciente.group(1).strip()

    profissional = re.search(r'Profissional\s*\n?([A-ZÁ-Ú\s]+)×', texto)
    if profissional:
        dados["profissional"] = profissional.group(1).strip()

    prescricao = re.search(r'Data da Prescrição\s*\n(\d{2}/\d{2}/\d{4})', texto)
    if prescricao:
        dados["data_prescricao"] = prescricao.group(1)

    blocos = re.split(r'\n\s*\(\s*\d+\s*\)\s*', texto)

    for bloco in blocos[1:]:

        linhas = [l.strip() for l in bloco.split("\n") if l.strip()]

        if len(linhas) < 7:
            continue

        nome_original = linhas[0]
        unidade = linhas[1]

        try:
            quantidade = limpar_quantidade(linhas[6])
        except:
            continue

        retorno = linhas[7] if len(linhas) > 7 else ""

        nome_normalizado = normalizar_nome(nome_original)
        principio = nome_normalizado.split()[0]

        dados["medicamentos"].append({
            "nome_original": nome_original,
            "principio": principio,
            "texto": f"{quantidade} {unidade} {nome_original}",
            "retorno": retorno
        })

    return dados


def gerar_evolucao(dados):

    if not dados["medicamentos"]:
        return "Nenhum medicamento identificado."

    # LISTA EM FORMATO DE LINHAS
    lista_meds = "\n".join([f"- {m['texto']}" for m in dados["medicamentos"]])

    controlados = []
    continuos = []

    for med in dados["medicamentos"]:

        principio = med["principio"]
        retorno = med["retorno"]

        if not re.match(r'\d{2}/\d{2}/\d{4}', retorno):
            continue

        if principio in medicacoes_controladas:
            controlados.append(retorno)

        elif principio not in medicacoes_agudas:
            continuos.append(retorno)

    texto_retorno_controlado = ""
    texto_retorno_continuo = ""

    if controlados:

        datas = [datetime.strptime(d, "%d/%m/%Y") for d in controlados]
        menor = min(datas).strftime("%d/%m/%Y")

        texto_retorno_controlado = (
            f"\nUso controlado: nova dispensação mediante receita médica a partir de {menor}."
        )

    if continuos:

        datas = [datetime.strptime(d, "%d/%m/%Y") for d in continuos]
        menor = min(datas).strftime("%d/%m/%Y")

        texto_retorno_continuo = (
            f"\nUso contínuo: nova dispensação prevista a partir de {menor}."
        )

    texto = (
        "Paciente comparece à farmácia para retirada de medicamentos.\n\n"
        "Dispensação realizada:\n"
        f"{lista_meds}\n\n"
        f"Receita prescrita por {dados['profissional']} em {dados['data_prescricao']}.\n\n"
        "Paciente orientado quanto ao uso correto das medicações."
        f"{texto_retorno_controlado}"
        f"{texto_retorno_continuo}"
    )

    return texto


st.set_page_config(page_title="Gerador de Evolução", layout="centered")

st.title("Gerador de Evolução de Dispensação")

st.write("1. Ctrl+A na tela da dispensação")
st.write("2. Ctrl+C")
st.write("3. Cole abaixo")

texto = st.text_area("Cole aqui o conteúdo copiado:", height=300)

if st.button("Gerar evolução"):

    dados = extrair_dados(texto)

    evolucao = gerar_evolucao(dados)

    st.subheader("Texto gerado")
    st.text_area("Evolução", evolucao, height=200)

    st.subheader("Medicamentos identificados")

    for med in dados["medicamentos"]:
        st.write("-", med["texto"])
