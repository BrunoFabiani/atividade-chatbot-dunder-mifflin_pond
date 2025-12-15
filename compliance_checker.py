# compliance_checker.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd


# -----------------------------
# Data model
# -----------------------------

@dataclass
class Finding:
    d_transacao: str
    status: str              # "OK" | "SUSPEITA" | "VIOLACAO"
    regras_acionadas: List[str]
    explicacao_curta: str
    evidencias: Dict[str, Any]



# Formatção 

def _norm(s: Any) -> str: #normalizar
    return str(s or "").strip().lower()

def _to_float(v: Any) -> float:
    """Converts values like 123.45 or '1.234,56' safely to float."""
    try:
        return float(v)
    except Exception:
        s = str(v or "").strip()
        # handle pt-BR formats
        s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except Exception:
            return 0.0

def _get_tx_id(row: pd.Series, fallback_idx: int) -> str:
    # Your CSV uses d_transacao
    if "d_transacao" in row and pd.notna(row["d_transacao"]):
        return str(row["d_transacao"]).strip()
    return f"TX_IDX_{fallback_idx}"


# -----------------------------
# Rule configuration
# -----------------------------

TI_TERMS = [
    "servidor", "server", "aws", "licenca", "licença", "software",
    "tablet", "gadget", "cloud", "hosting", "ti"
]

KEYWORD_VIOLATIONS: List[Tuple[str, List[str]]] = [
    ("ENTRETENIMENTO_HOOTERS", ["hooters"]),
    ("HOTEL_NAO_REEMBOLSAVEL", ["frigobar", "mini bar", "minibar", "pay-per-view", "pay per view", "ppv", "spa"]),
    ("CARRO_CONVERSIVEL", ["conversivel", "conversível", "sebring", "chrysler sebring", "convertible"]),
    ("LISTA_NEGRA_MAGICA", ["kit de magica", "kit de mágica", "magica", "mágica", "algemas", "correntes", "fumaça", "fumaca",
                            "pombos", "baralhos marcados", "stripper", "strippers"]),
    ("LISTA_NEGRA_ARMAMENTO", ["arma", "armamento", "airsoft", "katana", "espada", "nunchaku",
                               "estrela ninja", "spray de pimenta", "camuflagem"]),
    ("RYAN_JAN_NEGOCIO_PESSOAL", ["wuphf", "dunder infinity", "startup", "start-up", "investimento", "rede social", "portal"]),
]



def check_row(row: pd.Series, idx: int) -> Finding:
    """
    Applies rules R1-R4 to a single transaction row.
    Returns a Finding with status OK/SUSPEITA/VIOLACAO.
    """
    tx_id = _get_tx_id(row, idx)
    descricao = _norm(row.get("descricao"))
    categoria = _norm(row.get("categoria"))
    valor = _to_float(row.get("valor"))

    regras: List[str] = []
    status = "OK"

    # R1: Categoria genérica > 5
    if categoria in {"outros", "diversos"} and valor > 5:
        regras.append("CATEGORIA_GENERICA_ACIMA_5")

    # R2: Alçadas por valor
    if 50.01 <= valor <= 500.0:
        regras.append("CATEGORIA_B_REQUER_APROVACAO")
    if valor > 500.0:
        regras.append("CATEGORIA_A_REQUER_PO")

    # R3: TI/tecnologia > 100 + termos
    if valor > 100.0 and any(t in descricao for t in TI_TERMS):
        regras.append("TI_ACIMA_100_REQUER_RH")

    # R4: Violações diretas por keywords
    for rule_key, terms in KEYWORD_VIOLATIONS:
        if any(t in descricao for t in terms):
            regras.append(rule_key)


    direct_violation_rules = set([rk for rk, _ in KEYWORD_VIOLATIONS] + ["CATEGORIA_GENERICA_ACIMA_5"])

    if any(r in direct_violation_rules for r in regras):
        status = "VIOLACAO"
    elif regras:
        status = "SUSPEITA"
    else:
        status = "OK"

    if status == "OK":
        explanation = "Nenhuma regra acionada."
    else:
        explanation = "Regras acionadas: " + ", ".join(regras)

    evidencias = {
        "d_transacao": tx_id,
        "data": row.get("data"),
        "funcionario": row.get("funcionario"),
        "cargo": row.get("cargo"),
        "descricao": row.get("descricao"),
        "valor": valor,
        "categoria": row.get("categoria"),
        "departamento": row.get("departamento"),
    }

    return Finding(
        d_transacao=tx_id,
        status=status,
        regras_acionadas=regras,
        explicacao_curta=explanation,
        evidencias=evidencias,
    )


def scan_csv(csv_path: str) -> List[Finding]:
    """Checks the entire CSV and returns a list of Finding objects."""
    df = pd.read_csv(csv_path)
    findings: List[Finding] = []
    for idx, row in df.iterrows():
        findings.append(check_row(row, idx))
    return findings


def filter_findings(findings: List[Finding], only_not_ok: bool = True) -> List[Finding]:
    """Convenience filter: keep only SUSPEITA/VIOLACAO by default."""
    if not only_not_ok:
        return findings
    return [f for f in findings if f.status != "OK"]


def to_jsonable(findings: List[Finding]) -> Dict[str, Any]:
    """Returns a JSON-ready dict."""
    return {"resultados": [asdict(f) for f in findings]}


def summarize(findings: List[Finding], limit: int = 30) -> str:
    """Human readable summary."""
    # sort: VIOLACAO first, then SUSPEITA, then OK; within that, higher value first
    order = {"VIOLACAO": 0, "SUSPEITA": 1, "OK": 2}

    def key(f: Finding):
        val = float(f.evidencias.get("valor") or 0.0)
        return (order.get(f.status, 99), -val)

    out = sorted(findings, key=key)[:limit]
    lines = []
    for f in out:
        e = f.evidencias
        lines.append(
            f"- [{f.status}] {f.d_transacao} | {e.get('data')} | {e.get('funcionario')} | "
            f"${e.get('valor')} | {e.get('descricao')} | regras={f.regras_acionadas}"
        )
    return "\n".join(lines)

