"""Interface gráfica (Tkinter/ttk) do Acompanhamento de Atividades e Notas."""
import sqlite3
import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox, simpledialog, ttk

from calculos import resumo_disciplina
from database import Banco

COR = {"menu": "#1e293b", "hover": "#334155", "ativo": "#6366f1", "fundo": "#f1f5f9",
       "card": "#ffffff", "texto": "#0f172a", "suave": "#64748b", "borda": "#e2e8f0"}
SITUACAO = {"Aprovado": "#dcfce7", "No caminho": "#e0f2fe", "Atenção": "#fef9c3",
            "Em risco": "#fee2e2", "Reprovado": "#fee2e2", "Sem notas": "#f1f5f9"}
STATUS = {"pendente": "Pendente", "em_andamento": "Em andamento", "concluida": "Concluída"}
STATUS_REV = {v: k for k, v in STATUS.items()}
MENU = [("painel", "Painel"), ("disciplinas", "Disciplinas"), ("atividades", "Atividades e notas")]
TITULOS = {"painel": "Painel geral", "disciplinas": "Disciplinas", "atividades": "Atividades e notas"}
FONTE = "Segoe UI"


def fmt(v, casas=1):
    return "—" if v is None else f"{v:.{casas}f}".replace(".", ",")


def num(texto, nome, minimo=None, maximo=None):
    try:
        v = float(texto.strip().replace(",", "."))
    except ValueError:
        raise ValueError(f"{nome} deve ser um número.")
    if (minimo is not None and v < minimo) or (maximo is not None and v > maximo):
        raise ValueError(f"{nome} fora do intervalo permitido.")
    return v


def data_iso(txt):
    txt = txt.strip()
    if not txt or txt == "—":
        return None
    try:
        return datetime.strptime(txt, "%d/%m/%Y").date().isoformat()
    except ValueError:
        raise ValueError("Prazo inválido. Use DD/MM/AAAA.")


def data_br(iso):
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y") if iso else "—"


def estilo(raiz):
    s = ttk.Style(raiz)
    s.theme_use("clam")
    s.configure(".", font=(FONTE, 10), background=COR["fundo"], foreground=COR["texto"])
    s.configure("Card.TFrame", background=COR["card"])
    s.configure("Card.TLabel", background=COR["card"])
    s.configure("Suave.TLabel", background=COR["card"], foreground=COR["suave"], font=(FONTE, 9))
    s.configure("Sub.TLabel", background=COR["card"], font=(FONTE, 11, "bold"))
    s.configure("Titulo.TLabel", font=(FONTE, 20, "bold"))
    s.configure("Treeview", rowheight=32, background="#fff", fieldbackground="#fff", borderwidth=0)
    s.configure("Treeview.Heading", background="#f8fafc", foreground=COR["suave"],
                font=(FONTE, 9, "bold"), relief="flat", padding=6)
    s.map("Treeview", background=[("selected", "#c7d2fe")], foreground=[("selected", COR["texto"])])
    for nome, bg, fg, ativo in [("TButton", "#e2e8f0", COR["texto"], "#cbd5e1"),
                                ("Primario.TButton", COR["ativo"], "#fff", "#4f46e5"),
                                ("Perigo.TButton", "#fee2e2", "#b91c1c", "#fecaca")]:
        s.configure(nome, background=bg, foreground=fg, padding=(14, 8), borderwidth=0, focusthickness=0)
        s.map(nome, background=[("active", ativo)])
    s.configure("TEntry", padding=6, fieldbackground="#fff")
    s.configure("TCombobox", padding=5, fieldbackground="#fff")


def card(pai):
    """Cartão branco com borda fina; devolve (externo, interno)."""
    ext = tk.Frame(pai, bg=COR["card"], highlightbackground=COR["borda"], highlightthickness=1)
    inte = ttk.Frame(ext, style="Card.TFrame", padding=16)
    inte.pack(fill="both", expand=True)
    return ext, inte


def estatistica(pai, titulo, cor):
    ext = tk.Frame(pai, bg=COR["card"], highlightbackground=COR["borda"], highlightthickness=1)
    tk.Frame(ext, bg=cor, width=5).pack(side="left", fill="y")
    corpo = ttk.Frame(ext, style="Card.TFrame", padding=14)
    corpo.pack(side="left", fill="both", expand=True)
    ttk.Label(corpo, text=titulo, style="Suave.TLabel").pack(anchor="w")
    var = tk.StringVar(value="—")
    ttk.Label(corpo, textvariable=var, style="Card.TLabel", font=(FONTE, 20, "bold")).pack(anchor="w")
    return ext, var


def tabela(pai, colunas, altura=8):
    caixa = ttk.Frame(pai, style="Card.TFrame")
    tv = ttk.Treeview(caixa, columns=[c[0] for c in colunas], show="headings",
                      height=altura, selectmode="browse")
    for chave, titulo, largura in colunas:
        tv.heading(chave, text=titulo, anchor="w")
        tv.column(chave, width=largura, anchor="w")
    sb = ttk.Scrollbar(caixa, command=tv.yview)
    tv.configure(yscrollcommand=sb.set)
    tv.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    tv.tag_configure("par", background="#ffffff")
    tv.tag_configure("impar", background="#f8fafc")
    tv.tag_configure("atraso", background="#fee2e2")
    tv.dados = {}
    return caixa, tv


def zebra(tv):
    return "par" if len(tv.get_children()) % 2 == 0 else "impar"


def limpar(tv):
    tv.delete(*tv.get_children())
    tv.dados = {}


def inserir(tv, id_, dados):
    tv.insert("", "end", iid=str(id_), values=[dados[c] for c in tv["columns"]], tags=(zebra(tv),))
    tv.dados[str(id_)] = dados


def selecionado(tv):
    s = tv.selection()
    return int(s[0]) if s else None


def formulario(pai, defs):
    vs = {}
    for i, (chave, rotulo, larg, *opcoes) in enumerate(defs):
        ttk.Label(pai, text=rotulo, style="Suave.TLabel").grid(row=0, column=i, sticky="w", padx=4)
        vs[chave] = tk.StringVar()
        if opcoes:
            w = ttk.Combobox(pai, textvariable=vs[chave], values=opcoes[0], state="readonly", width=larg)
        else:
            w = ttk.Entry(pai, textvariable=vs[chave], width=larg)
        w.grid(row=1, column=i, padx=4, pady=(2, 0))
    return vs


def botoes(pai, acoes):
    f = ttk.Frame(pai, style="Card.TFrame")
    for texto, comando, *est in acoes:
        ttk.Button(f, text=texto, command=comando, style=est[0] if est else "TButton").pack(side="left", padx=(0, 8))
    return f


class App(tk.Tk):
    def __init__(self, banco=None):
        super().__init__()
        self.title("Notas & Atividades")
        self.geometry("1140x740")
        self.minsize(1000, 660)
        self.configure(bg=COR["fundo"])
        estilo(self)
        self.db = banco or Banco()
        self.alunos, self.disciplinas, self.media_min = {}, {}, {}
        self.var_aluno, self.var_disc = tk.StringVar(), tk.StringVar()
        self.var_titulo, self.var_aviso, self.var_resumo = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self._menu()
        self._area()
        self.paginas = {"painel": self._pg_painel(), "disciplinas": self._pg_disciplinas(),
                        "atividades": self._pg_atividades()}
        self.recarregar_alunos()
        self.mostrar("painel")

    # ---------- estrutura
    def _menu(self):
        m = tk.Frame(self, bg=COR["menu"], width=240)
        m.pack(side="left", fill="y")
        m.pack_propagate(False)
        tk.Label(m, text="Notas & Atividades", bg=COR["menu"], fg="white",
                 font=(FONTE, 15, "bold")).pack(anchor="w", padx=20, pady=(26, 2))
        tk.Label(m, text="Controle acadêmico", bg=COR["menu"], fg="#94a3b8",
                 font=(FONTE, 9)).pack(anchor="w", padx=20, pady=(0, 26))
        self.botoes_menu = {}
        for nome, texto in MENU:
            b = tk.Button(m, text=texto, anchor="w", relief="flat", bd=0, padx=20, pady=11, cursor="hand2",
                          font=(FONTE, 10, "bold"), activebackground=COR["hover"], activeforeground="white",
                          command=lambda n=nome: self.mostrar(n))
            b.pack(fill="x", padx=10, pady=2)
            self.botoes_menu[nome] = b
        rod = tk.Frame(m, bg=COR["menu"])
        rod.pack(side="bottom", fill="x", padx=16, pady=22)
        tk.Label(rod, text="ALUNO", bg=COR["menu"], fg="#94a3b8", font=(FONTE, 8, "bold")).pack(anchor="w")
        self.cb_aluno = ttk.Combobox(rod, textvariable=self.var_aluno, state="readonly")
        self.cb_aluno.pack(fill="x", pady=8)
        self.cb_aluno.bind("<<ComboboxSelected>>", lambda e: self.atualizar_tudo())
        linha = tk.Frame(rod, bg=COR["menu"])
        linha.pack(fill="x")
        ttk.Button(linha, text="Novo", style="Primario.TButton", command=self.cmd(self.novo_aluno)
                   ).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ttk.Button(linha, text="Excluir", style="Perigo.TButton", command=self.cmd(self.excluir_aluno)
                   ).pack(side="left", expand=True, fill="x", padx=(4, 0))

    def _area(self):
        area = tk.Frame(self, bg=COR["fundo"])
        area.pack(side="left", fill="both", expand=True, padx=26, pady=22)
        cab = tk.Frame(area, bg=COR["fundo"])
        cab.pack(fill="x", pady=(0, 16))
        ttk.Label(cab, textvariable=self.var_titulo, style="Titulo.TLabel").pack(side="left")
        ttk.Label(cab, textvariable=self.var_aviso, foreground="#15803d",
                  font=(FONTE, 10, "bold")).pack(side="right")
        self.conteudo = tk.Frame(area, bg=COR["fundo"])
        self.conteudo.pack(fill="both", expand=True)

    def mostrar(self, nome):
        for n, f in self.paginas.items():
            f.pack_forget()
            self.botoes_menu[n].configure(bg=COR["menu"], fg="#cbd5e1")
        self.paginas[nome].pack(fill="both", expand=True)
        self.botoes_menu[nome].configure(bg=COR["ativo"], fg="white")
        self.var_titulo.set(TITULOS[nome])
        self.atualizar_tudo()

    # ---------- utilidades
    def cmd(self, fn, *args):
        def run():
            try:
                fn(*args)
            except (ValueError, sqlite3.Error) as e:
                messagebox.showerror("Verifique os dados", str(e), parent=self)
        return run

    def aviso(self, texto):
        self.var_aviso.set("✔ " + texto)
        self.after(3500, lambda: self.var_aviso.set(""))

    @property
    def aluno_id(self):
        return self.alunos.get(self.var_aluno.get())

    def _aluno(self):
        if self.aluno_id is None:
            raise ValueError("Cadastre ou selecione um aluno primeiro (menu à esquerda).")
        return self.aluno_id

    def _preencher(self, tv, form):
        s = tv.selection()
        if s:
            for k, v in tv.dados[s[0]].items():
                if k in form:
                    form[k].set("" if v == "—" else v)

    def atualizar_tudo(self):
        self._carregar_disc()
        self._carregar_ativ()
        self._desempenho()

    # ---------- alunos
    def recarregar_alunos(self):
        self.alunos = {f"{a['nome']} (#{a['id']})": a["id"] for a in self.db.listar_alunos()}
        self.cb_aluno["values"] = list(self.alunos)
        if self.var_aluno.get() not in self.alunos:
            self.var_aluno.set(next(iter(self.alunos), ""))
        self.atualizar_tudo()

    def novo_aluno(self):
        nome = simpledialog.askstring("Novo aluno", "Nome do aluno:", parent=self)
        if not nome or not nome.strip():
            return
        email = simpledialog.askstring("Novo aluno", "E-mail (opcional):", parent=self)
        novo = self.db.add_aluno(nome.strip(), (email or "").strip() or None)
        self.recarregar_alunos()
        for rotulo, id_ in self.alunos.items():
            if id_ == novo:
                self.var_aluno.set(rotulo)
        self.atualizar_tudo()
        self.aviso("Aluno cadastrado")

    def excluir_aluno(self):
        id_ = self._aluno()
        if messagebox.askyesno("Excluir", "Excluir o aluno e todos os seus dados?", parent=self):
            self.db.excluir_aluno(id_)
            self.var_aluno.set("")
            self.recarregar_alunos()
            self.aviso("Aluno excluído")

    # ---------- painel
    def _pg_painel(self):
        f = tk.Frame(self.conteudo, bg=COR["fundo"])
        f.columnconfigure((0, 1, 2, 3), weight=1, uniform="e")
        f.rowconfigure(2, weight=1)
        self.est = {}
        for i, (chave, titulo, cor) in enumerate([
                ("disc", "Disciplinas", "#6366f1"), ("pend", "Atividades em aberto", "#f59e0b"),
                ("prazo", "Próximo prazo", "#0ea5e9"), ("alerta", "Disciplinas em alerta", "#ef4444")]):
            w, self.est[chave] = estatistica(f, titulo, cor)
            w.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 7, 0 if i == 3 else 7))
        ext, c = card(f)
        ext.grid(row=1, column=0, columnspan=4, sticky="ew", pady=14)
        ttk.Label(c, text="Desempenho por disciplina", style="Sub.TLabel").pack(anchor="w", pady=(0, 8))
        cx, self.tv_desemp = tabela(c, [("nome", "Disciplina", 300), ("periodo", "Período", 90),
                                        ("media", "Média parcial", 110), ("minima", "Média mínima", 110),
                                        ("nec", "Nota necessária", 120), ("sit", "Situação", 120)], 6)
        cx.pack(fill="x")
        for sit, cor in SITUACAO.items():
            self.tv_desemp.tag_configure(sit.replace(" ", "_"), background=cor)
        ext, c = card(f)
        ext.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=(0, 7))
        ttk.Label(c, text="Próximos prazos", style="Sub.TLabel").pack(anchor="w", pady=(0, 8))
        cx, self.tv_prazos = tabela(c, [("disc", "Disciplina", 150), ("ativ", "Atividade", 170),
                                        ("prazo", "Prazo", 85), ("quando", "Quando", 95)], 6)
        cx.pack(fill="both", expand=True)
        ext, c = card(f)
        ext.grid(row=2, column=2, columnspan=2, sticky="nsew", padx=(7, 0))
        ttk.Label(c, text="Sugestões de estudo", style="Sub.TLabel").pack(anchor="w", pady=(0, 8))
        self.var_sug = tk.StringVar()
        ttk.Label(c, textvariable=self.var_sug, style="Card.TLabel", wraplength=400,
                  justify="left").pack(anchor="nw")
        return f

    def _desempenho(self):
        limpar(self.tv_desemp)
        limpar(self.tv_prazos)
        self.var_sug.set("Selecione ou cadastre um aluno para começar.")
        for v in self.est.values():
            v.set("—")
        if not self.aluno_id:
            return
        hoje, proxima, prazos = date.today(), {}, self.db.proximos_prazos(self.aluno_id)
        for p in prazos:
            dias = (date.fromisoformat(p["prazo"]) - hoje).days
            quando = f"atrasada {-dias} d" if dias < 0 else "hoje" if dias == 0 else f"em {dias} d"
            proxima.setdefault(p["disciplina_id"], (p["titulo"], quando))
            self.tv_prazos.insert("", "end", values=(p["disciplina"], p["titulo"], data_br(p["prazo"]), quando),
                                  tags=("atraso",) if dias < 0 else (zebra(self.tv_prazos),))
        alertas, disciplinas, abertas = [], self.db.listar_disciplinas(self.aluno_id), 0
        for d in disciplinas:
            ativs = self.db.listar_atividades(d["id"])
            abertas += sum(a["status"] != "concluida" for a in ativs)
            r = resumo_disciplina(d["media_minima"], [(a["peso"], a["nota"]) for a in ativs])
            self.tv_desemp.insert("", "end", tags=(r["situacao"].replace(" ", "_"),), values=(
                d["nome"], d["periodo"], fmt(r["media_parcial"]), fmt(d["media_minima"]),
                fmt(r["necessaria"]), r["situacao"]))
            if r["situacao"] == "Em risco":
                msg = (f"• {d['nome']}: atingir {fmt(d['media_minima'])} exigiria mais que 10 nas "
                       "avaliações restantes. Busque reforço e converse com o professor.")
            elif r["situacao"] == "Atenção":
                msg = f"• {d['nome']}: é preciso média {fmt(r['necessaria'])} nas avaliações restantes."
            else:
                continue
            if d["id"] in proxima:
                titulo, quando = proxima[d["id"]]
                msg += f" Priorize “{titulo}” ({quando})."
            alertas.append(msg)
        self.est["disc"].set(str(len(disciplinas)))
        self.est["pend"].set(str(abertas))
        self.est["prazo"].set(proxima and prazos and
                              (lambda p: f"{data_br(p['prazo'])[:5]} · {p['titulo'][:14]}")(prazos[0]) or "—")
        self.est["alerta"].set(str(len(alertas)))
        self.var_sug.set("\n\n".join(alertas) or "Nenhum alerta no momento. Tudo sob controle.")

    # ---------- disciplinas
    def _pg_disciplinas(self):
        f = tk.Frame(self.conteudo, bg=COR["fundo"])
        ext, c = card(f)
        ext.pack(fill="x")
        ttk.Label(c, text="Cadastro", style="Sub.TLabel").pack(anchor="w", pady=(0, 8))
        linha = ttk.Frame(c, style="Card.TFrame")
        linha.pack(fill="x")
        self.f_disc = formulario(linha, [("nome", "Disciplina", 38), ("periodo", "Período (ex.: 2026.1)", 20),
                                         ("media", "Média mínima", 12)])
        self.f_disc["media"].set("7")
        botoes(c, [("Adicionar", self.cmd(self._salvar_disc, True), "Primario.TButton"),
                   ("Salvar alterações", self.cmd(self._salvar_disc, False)),
                   ("Excluir", self.cmd(self._excluir_disc), "Perigo.TButton"),
                   ("Limpar", self._limpar_disc)]).pack(anchor="w", pady=(14, 0))
        ext, c = card(f)
        ext.pack(fill="both", expand=True, pady=(14, 0))
        cx, self.tv_disc = tabela(c, [("nome", "Disciplina", 420), ("periodo", "Período", 130),
                                      ("media", "Média mínima", 130)], 12)
        cx.pack(fill="both", expand=True)
        self.tv_disc.bind("<<TreeviewSelect>>", lambda e: self._preencher(self.tv_disc, self.f_disc))
        return f

    def _limpar_disc(self):
        for v in self.f_disc.values():
            v.set("")
        self.f_disc["media"].set("7")

    def _carregar_disc(self):
        limpar(self.tv_disc)
        self.disciplinas, self.media_min = {}, {}
        if self.aluno_id:
            for d in self.db.listar_disciplinas(self.aluno_id):
                inserir(self.tv_disc, d["id"], {"nome": d["nome"], "periodo": d["periodo"],
                                                "media": fmt(d["media_minima"])})
                self.disciplinas[f"{d['nome']} ({d['periodo']})"] = d["id"]
                self.media_min[d["id"]] = d["media_minima"]
        self.cb_disc["values"] = list(self.disciplinas)
        if self.var_disc.get() not in self.disciplinas:
            self.var_disc.set(next(iter(self.disciplinas), ""))

    def _salvar_disc(self, novo):
        aluno = self._aluno()
        f = self.f_disc
        nome, periodo = f["nome"].get().strip(), f["periodo"].get().strip()
        if not nome or not periodo:
            raise ValueError("Informe a disciplina e o período.")
        media = num(f["media"].get() or "7", "Média mínima", 0, 10)
        if novo:
            self.db.add_disciplina(aluno, nome, periodo, media)
        else:
            id_ = selecionado(self.tv_disc)
            if id_ is None:
                raise ValueError("Selecione uma disciplina na lista.")
            self.db.atualizar_disciplina(id_, nome, periodo, media)
        self._limpar_disc()
        self.atualizar_tudo()
        self.aviso("Disciplina salva")

    def _excluir_disc(self):
        id_ = selecionado(self.tv_disc)
        if id_ is None:
            raise ValueError("Selecione uma disciplina na lista.")
        if messagebox.askyesno("Excluir", "Excluir a disciplina, suas atividades e notas?", parent=self):
            self.db.excluir_disciplina(id_)
            self.atualizar_tudo()
            self.aviso("Disciplina excluída")

    # ---------- atividades e notas
    def _pg_atividades(self):
        f = tk.Frame(self.conteudo, bg=COR["fundo"])
        ext, c = card(f)
        ext.pack(fill="x")
        topo = ttk.Frame(c, style="Card.TFrame")
        topo.pack(fill="x", pady=(0, 12))
        ttk.Label(topo, text="Disciplina", style="Sub.TLabel").pack(side="left")
        self.cb_disc = ttk.Combobox(topo, textvariable=self.var_disc, state="readonly", width=40)
        self.cb_disc.pack(side="left", padx=10)
        self.cb_disc.bind("<<ComboboxSelected>>", lambda e: self._carregar_ativ())
        ttk.Label(topo, textvariable=self.var_resumo, style="Suave.TLabel").pack(side="left", padx=8)
        linha = ttk.Frame(c, style="Card.TFrame")
        linha.pack(fill="x")
        self.f_ativ = formulario(linha, [
            ("titulo", "Título", 22), ("descricao", "Descrição", 22), ("prazo", "Prazo (DD/MM/AAAA)", 16),
            ("peso", "Peso", 6), ("status", "Status", 13, list(STATUS.values())), ("nota", "Nota (0–10)", 9)])
        self._limpar_ativ()
        botoes(c, [("Adicionar", self.cmd(self._salvar_ativ, True), "Primario.TButton"),
                   ("Salvar alterações", self.cmd(self._salvar_ativ, False)),
                   ("Marcar concluída", self.cmd(self._concluir)),
                   ("Excluir", self.cmd(self._excluir_ativ), "Perigo.TButton"),
                   ("Limpar", self._limpar_ativ)]).pack(anchor="w", pady=(14, 0))
        ext, c = card(f)
        ext.pack(fill="both", expand=True, pady=(14, 0))
        cx, self.tv_ativ = tabela(c, [("titulo", "Atividade", 210), ("descricao", "Descrição", 230),
                                      ("prazo", "Prazo", 90), ("peso", "Peso", 60),
                                      ("status", "Status", 110), ("nota", "Nota", 60)], 9)
        cx.pack(fill="both", expand=True)
        self.tv_ativ.bind("<<TreeviewSelect>>", lambda e: self._preencher(self.tv_ativ, self.f_ativ))
        return f

    def _limpar_ativ(self):
        for v in self.f_ativ.values():
            v.set("")
        self.f_ativ["peso"].set("1")
        self.f_ativ["status"].set(STATUS["pendente"])

    def _carregar_ativ(self):
        limpar(self.tv_ativ)
        self.var_resumo.set("")
        did = self.disciplinas.get(self.var_disc.get())
        if did is None:
            return
        ativs = self.db.listar_atividades(did)
        for a in ativs:
            inserir(self.tv_ativ, a["id"], {
                "titulo": a["titulo"], "descricao": a["descricao"], "prazo": data_br(a["prazo"]),
                "peso": fmt(a["peso"], 2), "status": STATUS[a["status"]], "nota": fmt(a["nota"])})
        r = resumo_disciplina(self.media_min[did], [(a["peso"], a["nota"]) for a in ativs])
        self.var_resumo.set(f"Média parcial {fmt(r['media_parcial'])}  ·  Nota necessária "
                            f"{fmt(r['necessaria'])}  ·  {r['situacao']}")

    def _salvar_ativ(self, novo):
        did = self.disciplinas.get(self.var_disc.get())
        if did is None:
            raise ValueError("Cadastre/selecione uma disciplina primeiro.")
        f = self.f_ativ
        titulo = f["titulo"].get().strip()
        if not titulo:
            raise ValueError("Informe o título da atividade.")
        desc, prazo = f["descricao"].get().strip(), data_iso(f["prazo"].get())
        peso = num(f["peso"].get() or "1", "Peso", 0.01)
        nota_txt = f["nota"].get().strip()
        nota = num(nota_txt, "Nota", 0, 10) if nota_txt else None
        status = "concluida" if nota is not None else STATUS_REV.get(f["status"].get(), "pendente")
        if novo:
            id_ = self.db.add_atividade(did, titulo, desc, prazo, peso, status)
        else:
            id_ = selecionado(self.tv_ativ)
            if id_ is None:
                raise ValueError("Selecione uma atividade na lista.")
            self.db.atualizar_atividade(id_, titulo, desc, prazo, peso, status)
        if nota is None:
            self.db.remover_nota(id_)
        else:
            self.db.lancar_nota(id_, nota)
        self._limpar_ativ()
        self.atualizar_tudo()
        self.aviso("Atividade salva")

    def _concluir(self):
        id_ = selecionado(self.tv_ativ)
        if id_ is None:
            raise ValueError("Selecione uma atividade na lista.")
        d = self.tv_ativ.dados[str(id_)]
        self.db.atualizar_atividade(id_, d["titulo"], d["descricao"], data_iso(d["prazo"]),
                                    num(d["peso"], "Peso"), "concluida")
        self.atualizar_tudo()
        self.aviso("Atividade concluída")

    def _excluir_ativ(self):
        id_ = selecionado(self.tv_ativ)
        if id_ is None:
            raise ValueError("Selecione uma atividade na lista.")
        self.db.excluir_atividade(id_)
        self.atualizar_tudo()
        self.aviso("Atividade excluída")
