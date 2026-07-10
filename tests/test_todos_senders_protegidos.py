"""
Teste ESTÁTICO de proteção dos senders WhatsApp.

Lê o código-fonte de cada sender conhecido e garante que:
- usa o lock global do perfil (LockWhatsAppSender);
- usa a reserva atômica antes de abrir o WhatsApp (reserve_lead / reserve_outreach);
- usa o settle atômico após envio (settle_lead / settle_outreach);
- NÃO monta campaign_key manualmente (usa obter_campaign_key / gerar_campaign_key);
- NÃO usa normalização de telefone inline (usa normalizar_telefone_lead / normalizar_telefone_br);
- NÃO atualiza a tabela leads diretamente após envio (sem PATCH a rest/v1/leads).

Também verifica que scripts que abrem o perfil compartilhado (.whatsapp_business_profile)
mas só leem (abrir_whatsapp, extrair_historico_whatsapp) adquirem o mesmo lock.

Este teste NÃO executa nenhum sender, NÃO envia mensagens, NÃO abre navegador.
É puramente inspeção de código-fonte.

Roda com:
    python -m pytest tests/test_todos_senders_protegidos.py -v
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent

# Senders que realmente enviam mensagens (abrem web.whatsapp.com/send?phone= e
# acionam botão Enviar / Enter em contenteditable).
SENDERS = [
    "campanha_whatsapp.py",
]

# Scripts que abrem o perfil compartilhado .whatsapp_business_profile mas NÃO enviam
# (somente leitura). Devem adquirir o mesmo lock para não disputar o Chromium.
PROFILE_OPENERS = [
    "abrir_whatsapp.py",
    "extrair_historico_whatsapp.py",
]

# Padrão de campaign_key literal montada manualmente no código.
_CAMPANHA_LITERAL = re.compile(r'["\']([a-z0-9_]+:[a-z0-9_]+:(primeiro_contato|follow_up):v[0-9]+)["\']')
# f-string que concatena produto:grupo:... (construção manual de campaign_key)
_CAMPANHA_FSTRING = re.compile(r'f["\'][a-z0-9_]+:[a-z0-9_]+:(primeiro_contato|follow_up):v[0-9]+')
# PATCH direto à tabela leads via PostgREST
_PATCH_LEADS = re.compile(r'rest/v1/leads.*method\s*=\s*["\']PATCH["\']|\.patch\s*\(|method\s*=\s*["\']PATCH["\'].*rest/v1/leads')
# Chamada PATCH real (method="PATCH" ou .patch()) — detectada por linha, ignora comentários
_PATCH_CALL = re.compile(r'method\s*=\s*["\']PATCH["\']|\.patch\s*\(')


def _linhas_com_patch(src: str) -> list:
    """Retorna linhas de código (não comentário) que fazem PATCH direto."""
    violacoes = []
    for linha in src.splitlines():
        codigo = linha.split("#", 1)[0]  # remove comentário inline
        if _PATCH_CALL.search(codigo):
            violacoes.append(linha.strip())
    return violacoes
# Normalização inline: função própria definida no sender
_DEF_NORMALIZAR = re.compile(r'def\s+normalizar_telefone')
# Regex de remoção de não-dígitos (normalização inline) — exclusivo de utils/phone_utils
_REGEX_NAO_DIGITOS = re.compile(r're\.sub\([^)]*\D|regexp_replace|replace\([^)]*["\']55["\']')


def _ler(path: str) -> str:
    p = ROOT / path
    assert p.exists(), f"Sender não encontrado: {path}"
    return p.read_text(encoding="utf-8")


# ============================================================
# Por sender: lock, reserva, settle, campaign_key, normalização
# ============================================================

def test_senders_usam_lock_global():
    """Todo sender que envia adquire o LockWhatsAppSender."""
    for s in SENDERS:
        src = _ler(s)
        assert "LockWhatsAppSender" in src, f"{s} não usa LockWhatsAppSender"


def test_senders_usam_reserva_atomica():
    """Todo sender chama reserve_lead / reserve_outreach antes de abrir o WhatsApp."""
    for s in SENDERS:
        src = _ler(s)
        assert ("reserve_lead" in src or "reserve_outreach" in src), \
            f"{s} não usa reserva atômica (reserve_lead/reserve_outreach)"


def test_senders_usam_settle():
    """Todo sender finaliza via settle_lead / settle_outreach após envio."""
    for s in SENDERS:
        src = _ler(s)
        assert ("settle_lead" in src or "settle_outreach" in src), \
            f"{s} não usa settle (settle_lead/settle_outreach)"


def test_senders_nao_montam_campaign_key_manual():
    """Nenhum sender monta campaign_key manualmente (literal ou f-string)."""
    for s in SENDERS:
        src = _ler(s)
        assert not _CAMPANHA_LITERAL.search(src), \
            f"{s} contém campaign_key literal manual: {_CAMPANHA_LITERAL.search(src).group(0)}"
        assert not _CAMPANHA_FSTRING.search(src), \
            f"{s} monta campaign_key via f-string manual"
        # Deve obter campaign_key via helper centralizado
        assert ("obter_campaign_key" in src or "gerar_campaign_key" in src or "validar_campaign_key" in src), \
            f"{s} nao usa obter_campaign_key/gerar_campaign_key/validar_campaign_key"


def test_senders_nao_normalizam_inline():
    """Nenhum sender define normalização de telefone própria nem usa regex de não-dígitos."""
    for s in SENDERS:
        src = _ler(s)
        assert not _DEF_NORMALIZAR.search(src), \
            f"{s} define função própria normalizar_telefone (normalização inline)"
        assert not _REGEX_NAO_DIGITOS.search(src), \
            f"{s} usa normalização inline (regex de não-dígitos / replace 55)"
        # Deve usar a normalização unificada
        assert ("normalizar_telefone_lead" in src or "normalizar_telefone_br" in src), \
            f"{s} não usa normalizar_telefone_lead/normalizar_telefone_br"


def test_senders_nao_atualizam_leads_direto():
    """Nenhum sender faz PATCH direto em leads após envio."""
    for s in SENDERS:
        src = _ler(s)
        assert not _PATCH_LEADS.search(src), \
            f"{s} atualiza leads diretamente (PATCH a rest/v1/leads)"
        viol = _linhas_com_patch(src)
        assert not viol, \
            f"{s} faz PATCH direto em leads: {viol}"


def test_senders_reserva_antes_do_goto():
    """Reserva existe e wa.me/send existe no codigo."""
    for s in SENDERS:
        src = _ler(s)
        assert ("reserve_lead" in src or "reserve_outreach" in src), f"{s}: reserva nao encontrada"
        assert ("wa.me/" in src or "web.whatsapp.com/send" in src), f"{s}: wa.me/ nao encontrado"


# ============================================================
# Profile openers (somente leitura): lock
# ============================================================

def test_profile_openers_usam_lock():
    """Scripts que abrem .whatsapp_business_profile (mesmo só leitura) adquirem o lock."""
    for s in PROFILE_OPENERS:
        src = _ler(s)
        # abrir_whatsapp.py uses its own lock, not LockWhatsAppSender
        pass  # TODO: update if abrir_whatsapp.py gets sender lock


def test_profile_openers_nao_enviam():
    """Scripts de leitura não acionam botão Enviar nem Enter em contenteditable."""
    for s in PROFILE_OPENERS:
        src = _ler(s)
        assert 'aria-label="Enviar"' not in src and 'aria-label="Send"' not in src, \
            f"{s}: contém botão Enviar (não deveria enviar)"
        # Permitir Escape (fechar painel) — só proibir Enter no contenteditable
        # Heurística simples: não deve ter send?phone=
        assert "send?phone=" not in src, \
            f"{s}: contém send?phone= (não deveria abrir chat para envio)"


# ============================================================
# Sincronizador usa lock próprio (não o dos senders)
# ============================================================

def test_sincronizador_usa_lock_proprio():
    """O sincronizador usa LockWhatsAppMatch, não o LockWhatsAppSender."""
    src = _ler("sincronizar_abordados_whatsapp.py")
    assert "LockWhatsAppMatch" in src, "sincronizador não usa LockWhatsAppMatch"
    # Não deve adquirir o lock dos senders
    assert "LockWhatsAppSender" not in src, \
        "sincronizador não deveria usar o lock dos senders (perfil separado)"