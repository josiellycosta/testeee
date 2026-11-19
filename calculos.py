"""Regras de negócio: média ponderada, nota necessária e situação da disciplina."""


def resumo_disciplina(media_minima, avaliacoes):
    """avaliacoes: lista de (peso, nota) — nota é None quando ainda não lançada.

    Considera que todas as atividades cadastradas formam o total de pesos da disciplina.
    """
    peso_total = sum(p for p, _ in avaliacoes)
    avaliadas = [(p, n) for p, n in avaliacoes if n is not None]
    peso_avaliado = sum(p for p, _ in avaliadas)
    pontos = sum(p * n for p, n in avaliadas)
    peso_restante = peso_total - peso_avaliado

    media_parcial = pontos / peso_avaliado if peso_avaliado else None
    necessaria = None
    if peso_restante > 0:
        necessaria = max(0.0, (media_minima * peso_total - pontos) / peso_restante)

    if not avaliadas:
        situacao = "Sem notas"
    elif pontos >= media_minima * peso_total - 1e-9:
        situacao = "Aprovado"
    elif peso_restante <= 0:
        situacao = "Reprovado"
    elif necessaria > 10:
        situacao = "Em risco"
    elif necessaria > 8 or media_parcial < media_minima:
        situacao = "Atenção"
    else:
        situacao = "No caminho"

    return {"media_parcial": media_parcial, "necessaria": necessaria, "situacao": situacao}
