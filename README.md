<p align="center">
  <img src="logo/logo-completa.png" alt="Notas & Atividades — Acompanhamento acadêmico" width="560">
</p>

<p align="center">
  Controle de disciplinas, atividades, prazos e notas em um só lugar, sem planilhas.
</p>

<p align="center">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-1d4ed8?logo=python&logoColor=white">
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-web-1d4ed8?logo=streamlit&logoColor=white">
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite-banco%20local-1d4ed8?logo=sqlite&logoColor=white">
  <img alt="Tkinter" src="https://img.shields.io/badge/Tkinter-desktop-1d4ed8">
</p>

---

## 📚 Sobre

O **Acompanhamento de Atividades e Notas** reúne tudo o que o estudante precisa para saber como está indo no semestre: disciplinas por período, atividades com prazo e peso, notas lançadas, a **média parcial** e quanto ainda é preciso tirar nas avaliações restantes para passar.

Existem duas interfaces que compartilham as mesmas regras de cálculo e o mesmo banco SQLite:

| Versão | Arquivo | Tecnologia |
|---|---|---|
| 🌐 Web | `streamlit_app.py` | Streamlit |
| 🖥️ Desktop | `main.py` + `ui.py` | Tkinter |

Desenvolvido com apoio do **GitHub Copilot** (veja `.github/copilot-instructions.md`).

## ✨ Funcionalidades

- **Disciplinas por período/semestre**, cada uma com média mínima configurável.
- **Atividades** com prazo, peso e status (pendente, em andamento ou concluída).
- **Notas** com média ponderada automática e **nota necessária** nas avaliações que faltam.
- **Painel de desempenho**: cartões por disciplina com barra de média parcial, situação por cor (Aprovado, No caminho, Atenção, Em risco, Reprovado) e próximos prazos.
- **Dashboard** com gráficos que seguem o tema: média parcial por disciplina, atividades por status e prazos por semana.
- **Sugestões de estudo** para todas as disciplinas, com destaque para atividades atrasadas e prazos da semana.
- **CRUD completo** de alunos, disciplinas, atividades e notas, persistido em SQLite.

## 🎨 Temas (versão web)

Escolha as cores e o modo direto na barra lateral:

- Paletas: **Azul** (padrão), Preto e branco, Verde, Roxo, Rosa e **Personalizada** (seletor de cor).
- Modo **claro** (☀) e **escuro** (☾) em todas as paletas.

## 🛠️ Tecnologias

Python 3.10+ · Streamlit · SQLite · Tkinter · Git & GitHub

## ▶️ Como executar

**No seu computador**

```bash
git clone https://github.com/josiellycosta/Acompanhamento.git
cd Acompanhamento
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Para a versão desktop, use `python main.py`. No Linux, se faltar o Tkinter: `sudo apt install python3-tk`.
O banco `academico.db` é criado automaticamente na primeira execução.

**Dentro do GitHub (Codespaces)** — Code → Codespaces → *Create codespace on main*. O ambiente instala tudo e abre o app sozinho (porta 8501).

**Publicar online (Streamlit Community Cloud)** — em [share.streamlit.io](https://share.streamlit.io), escolha este repositório e o arquivo `streamlit_app.py`.

> ⚠️ O GitHub Pages não executa Python. No Streamlit Community Cloud, o armazenamento local não é permanente: o arquivo `academico.db` pode ser perdido quando o ambiente for recriado. Para uso contínuo online, configure um banco externo persistente (por exemplo, PostgreSQL). Esta versão não possui autenticação: **não publique dados acadêmicos pessoais em um app público**. No computador e no Codespace, os dados ficam no arquivo local `academico.db`.

## 🧮 Regras de cálculo

- **Média parcial** = Σ(nota × peso) ÷ Σ(peso das atividades já avaliadas).
- **Nota necessária** = (média mínima × Σ peso total − Σ pontos obtidos) ÷ Σ peso das atividades sem nota.
- Os pesos de todas as atividades cadastradas formam o total da disciplina: cadastre todas as avaliações previstas para a projeção ficar correta.

| Situação | Quando |
|---|---|
| **Aprovado** | os pontos obtidos já garantem a média mínima |
| **No caminho** | a nota necessária é de até 8 e a média parcial está na meta |
| **Atenção** | a nota necessária passa de 8 ou a média parcial está abaixo da mínima |
| **Em risco** | a nota necessária passa de 10 |
| **Reprovado** | todas as avaliações foram feitas e a média ficou abaixo da mínima |

**Exemplo:** média mínima 7, três atividades com pesos 1, 1 e 2. Com notas 6 e 8 nas duas primeiras, a nota necessária na última é (7 × 4 − 14) ÷ 2 = **7,0**.

## ⚙️ Esquema do banco

| Tabela | Campos principais |
|---|---|
| `alunos` | id, nome, email |
| `disciplinas` | id, aluno_id → alunos, nome, periodo, media_minima |
| `atividades` | id, disciplina_id → disciplinas, titulo, descricao, prazo, peso, status |
| `notas` | id, atividade_id → atividades (única), valor (0–10) |

Todas as relações usam `ON DELETE CASCADE`.

## 📁 Estrutura

```
streamlit_app.py       interface web (Streamlit, temas claro/escuro)
main.py                ponto de entrada da versão desktop
ui.py                  interface desktop (Tkinter)
database.py            esquema e CRUD (SQLite)
calculos.py            médias, nota necessária e situação
logo/                  logo do projeto (SVG e PNG)
.streamlit/            tema base do Streamlit
.devcontainer/         ambiente do Codespaces
tests/                 testes unitários
.github/               CI (Actions) e instruções do Copilot
```

## 🧪 Testes

```bash
python -m unittest discover -s tests -t . -v
```

---

<p align="center">Feito por <a href="https://github.com/josiellycosta">Josielly</a> 💙</p>
