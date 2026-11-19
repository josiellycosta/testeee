"""Camada de dados (SQLite) do Acompanhamento de Atividades e Notas."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("academico.db")

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS alunos (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    nome  TEXT NOT NULL,
    email TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS disciplinas (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id     INTEGER NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
    nome         TEXT NOT NULL,
    periodo      TEXT NOT NULL,
    media_minima REAL NOT NULL DEFAULT 7.0 CHECK (media_minima BETWEEN 0 AND 10)
);
CREATE TABLE IF NOT EXISTS atividades (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    disciplina_id INTEGER NOT NULL REFERENCES disciplinas(id) ON DELETE CASCADE,
    titulo        TEXT NOT NULL,
    descricao     TEXT NOT NULL DEFAULT '',
    prazo         TEXT,
    peso          REAL NOT NULL DEFAULT 1.0 CHECK (peso > 0),
    status        TEXT NOT NULL DEFAULT 'pendente'
                  CHECK (status IN ('pendente', 'em_andamento', 'concluida'))
);
CREATE TABLE IF NOT EXISTS notas (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    atividade_id INTEGER NOT NULL UNIQUE REFERENCES atividades(id) ON DELETE CASCADE,
    valor        REAL NOT NULL CHECK (valor BETWEEN 0 AND 10)
);
"""


class Banco:
    def __init__(self, caminho=DB_PATH):
        self.con = sqlite3.connect(str(caminho), check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        self.con.executescript(SCHEMA)

    def _exec(self, sql, params=()):
        with self.con:
            return self.con.execute(sql, params).lastrowid

    def _all(self, sql, params=()):
        return self.con.execute(sql, params).fetchall()

    # ---- alunos
    def add_aluno(self, nome, email=None):
        return self._exec("INSERT INTO alunos (nome, email) VALUES (?, ?)", (nome, email))

    def listar_alunos(self):
        return self._all("SELECT * FROM alunos ORDER BY nome")

    def excluir_aluno(self, id_):
        self._exec("DELETE FROM alunos WHERE id = ?", (id_,))

    # ---- disciplinas
    def add_disciplina(self, aluno_id, nome, periodo, media_minima=7.0):
        return self._exec(
            "INSERT INTO disciplinas (aluno_id, nome, periodo, media_minima) VALUES (?, ?, ?, ?)",
            (aluno_id, nome, periodo, media_minima))

    def listar_disciplinas(self, aluno_id):
        return self._all("SELECT * FROM disciplinas WHERE aluno_id = ? "
                         "ORDER BY periodo DESC, nome", (aluno_id,))

    def atualizar_disciplina(self, id_, nome, periodo, media_minima):
        self._exec("UPDATE disciplinas SET nome = ?, periodo = ?, media_minima = ? WHERE id = ?",
                   (nome, periodo, media_minima, id_))

    def excluir_disciplina(self, id_):
        self._exec("DELETE FROM disciplinas WHERE id = ?", (id_,))

    # ---- atividades
    def add_atividade(self, disciplina_id, titulo, descricao, prazo, peso, status="pendente"):
        return self._exec(
            "INSERT INTO atividades (disciplina_id, titulo, descricao, prazo, peso, status) "
            "VALUES (?, ?, ?, ?, ?, ?)", (disciplina_id, titulo, descricao, prazo, peso, status))

    def listar_atividades(self, disciplina_id):
        return self._all(
            "SELECT a.*, n.valor AS nota FROM atividades a "
            "LEFT JOIN notas n ON n.atividade_id = a.id WHERE a.disciplina_id = ? "
            "ORDER BY a.prazo IS NULL, a.prazo, a.id", (disciplina_id,))

    def atualizar_atividade(self, id_, titulo, descricao, prazo, peso, status):
        self._exec("UPDATE atividades SET titulo = ?, descricao = ?, prazo = ?, peso = ?, "
                   "status = ? WHERE id = ?", (titulo, descricao, prazo, peso, status, id_))

    def excluir_atividade(self, id_):
        self._exec("DELETE FROM atividades WHERE id = ?", (id_,))

    def proximos_prazos(self, aluno_id):
        return self._all(
            "SELECT a.titulo, a.prazo, d.id AS disciplina_id, d.nome AS disciplina "
            "FROM atividades a JOIN disciplinas d ON d.id = a.disciplina_id "
            "WHERE d.aluno_id = ? AND a.status != 'concluida' AND a.prazo IS NOT NULL "
            "ORDER BY a.prazo", (aluno_id,))

    # ---- notas
    def lancar_nota(self, atividade_id, valor):
        self._exec("INSERT INTO notas (atividade_id, valor) VALUES (?, ?) "
                   "ON CONFLICT(atividade_id) DO UPDATE SET valor = excluded.valor",
                   (atividade_id, valor))

    def remover_nota(self, atividade_id):
        self._exec("DELETE FROM notas WHERE atividade_id = ?", (atividade_id,))
