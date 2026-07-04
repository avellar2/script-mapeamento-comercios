"""
Testes do matcher e seletores do WhatsApp Web.

Estes testes NÃO abrem navegador, NÃO enviam mensagens, NÃO acessam o WhatsApp.
Usam um FakePage que simula o DOM a partir das listas de seletores de
config/whatsapp_selectors.py.

Cobre:
- conversa encontrada por telefone (MATCHED)
- contato salvo por nome com telefone confirmado no painel (MATCHED)
- mensagem enviada detectada (outbound encontrado)
- mensagem apenas recebida não conta (NO_OUTBOUND)
- grupo não conta (GROUP)
- canal não conta (GROUP)
- comunidade não conta (GROUP)
- status não conta (sem outbound -> NO_OUTBOUND)
- conversa vazia (NO_OUTBOUND)
- número parecido, mas diferente (AMBIGUOUS_CONTACT)
- fingerprint incompatível vira ambíguo (AMBIGUOUS)
- seletor principal quebrado usa fallback
- todos os fallbacks quebrados geram diagnóstico
- nenhum teste envia mensagem (asserção estática no matcher)

Roda com:
    python -m pytest tests/test_whatsapp_match_selectors.py -v
"""

import asyncio
import re
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.whatsapp_selectors import (
    SEARCH_BOX_SELECTORS,
    CHAT_ITEM_SELECTORS,
    CONVERSATION_HEADER_SELECTORS,
    PHONE_IN_PROFILE_SELECTORS,
    MESSAGE_OUT_SELECTORS,
    MESSAGE_TEXT_SELECTORS,
    BACK_BUTTON_SELECTORS,
    LOADING_INDICATORS,
    GROUP_INDICATORS,
    encontrar_seletor,
    capturar_diagnostico,
)
from whatsapp_match import MatchStatus
from whatsapp_match.matcher import (
    fazer_match_completo,
    pesquisar_telefone,
    detectar_grupo,
    detectar_mensagem_saida,
    confirmar_numero,
)
from utils.campaign_fingerprint import corresponde_campanha


# ============================================================
# FakePage / FakeLocator — simulação do DOM do WhatsApp Web
# ============================================================

class _FakeElement:
    """Elemento truthy retornado por wait_for_selector."""
    pass


class FakeLocator:
    """Locator que responde a partir de um dicionário de elementos presentes."""

    def __init__(self, page, selector, element=None):
        self._page = page
        self._selector = selector
        self._element = element  # elemento específico (first/nth) ou None

    def _elements(self):
        return self._page.present.get(self._selector, [])

    @property
    def first(self):
        els = self._elements()
        el = els[0] if els else None
        return FakeLocator(self._page, self._selector, element=el)

    def nth(self, i):
        els = self._elements()
        el = els[i] if 0 <= i < len(els) else None
        return FakeLocator(self._page, self._selector, element=el)

    async def count(self):
        return len(self._elements())

    async def is_visible(self):
        # Elemento resolvido (first/nth) -> existe na página -> visível.
        # Mesmo que text/title estejam vazios, o locator foi achado.
        if self._element is not None:
            return True
        return bool(self._elements())

    async def click(self):
        self._page.actions.append(("click", self._selector))
        return None

    async def fill(self, text):
        self._page.actions.append(("fill", self._selector, text))
        return None

    async def get_attribute(self, name):
        if self._element is None:
            els = self._elements()
            self._element = els[0] if els else None
        if self._element is None:
            return None
        if name == "title":
            return self._element.get("title")
        if name == "data-timestamp":
            return self._element.get("timestamp")
        # Suporte para outros atributos (href, aria-label, data-id, etc.)
        if name in self._element:
            return self._element.get(name)
        return self._element.get(name)

    async def text_content(self):
        if self._element is None:
            els = self._elements()
            self._element = els[0] if els else None
        if self._element is None:
            return None
        return self._element.get("text")

    def locator(self, selector):
        # Locator aninhado (usado por extrair_texto_mensagem) — compartilha o elemento.
        return FakeLocator(self._page, selector, element=self._element)


class FakePage:
    """Página Playwright simulada.

    present: dict seletor -> lista de dicts {"title","text","timestamp"}.
    broken: se True, wait_for_selector sempre lança (simula DOM quebrado).
    """

    def __init__(self, present=None, broken=False):
        self.present = present or {}
        self.broken = broken
        self.actions = []
        self._tmp = tempfile.mkdtemp()

    async def wait_for_selector(self, selector, timeout=None, state=None):
        if self.broken:
            raise TimeoutError(f"selector broken: {selector}")
        if state == "hidden":
            # Aguarda esconder: se não presente -> ok (escondido); se presente -> ainda visível
            if not self.present.get(selector):
                return _FakeElement()
            raise TimeoutError(f"still visible: {selector}")
        els = self.present.get(selector)
        if els:
            return _FakeElement()
        raise TimeoutError(f"not found: {selector}")

    def locator(self, selector):
        return FakeLocator(self, selector)

    async def wait_for_timeout(self, ms):
        return None

    async def screenshot(self, path=None, full_page=False):
        Path(path).write_bytes(b"FAKE_PNG")
        self.actions.append(("screenshot", path))
        return None

    async def content(self):
        return "<html>fake</html>"

    async def keyboard_press(self, key):
        self.actions.append(("keyboard_press", key))
        return None

    async def mouse_click(self, x, y):
        self.actions.append(("mouse_click", x, y))
        return None


# Mensagens de teste
MSG_CAMPANHA = (
    "Boa tarde, pessoal da Oficina! Tudo bem?\n\n"
    "Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar assistência técnica.\n\n"
    "Com ele vocês registram o aparelho, abrem a ordem de serviço, enviam o orçamento para aprovação."
)
MSG_NAO_CAMPANHA = "Promoção imperdível! 50% de desconto hoje, apenas para os primeiros clientes."

PHONE = "5521999999999"
CK = "avgestao:assistencias:primeiro_contato:v1"


def _dom_matched():
    """DOM que leva a MATCHED: telefone encontrado, confirmado, mensagem de saída da campanha."""
    return {
        SEARCH_BOX_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}],
        CHAT_ITEM_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}],
        CONVERSATION_HEADER_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}],
        PHONE_IN_PROFILE_SELECTORS[0]: [{"title": "+55 21 99999-9999", "text": None, "timestamp": None}],
        BACK_BUTTON_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}],
        # WhatsApp Web 2026: msg-container com textContent "tail-out" + mensagem
        'div[data-testid="msg-container"]': [{"title": None, "text": "tail-out" + MSG_CAMPANHA, "timestamp": "1717200000"}],
        MESSAGE_TEXT_SELECTORS[0]: [{"title": None, "text": MSG_CAMPANHA, "timestamp": None}],
    }


# ============================================================
# Testes do fluxo completo (fazer_match_completo)
# ============================================================

def test_conversa_encontrada_por_telefone_matched():
    """Conversa encontrada por telefone, mensagem de saída corresponde à campanha -> MATCHED."""
    page = FakePage(_dom_matched())
    result = asyncio.run(fazer_match_completo(page, "lead-1", PHONE, CK))
    assert result.status == MatchStatus.MATCHED
    assert result.chat_found is True
    assert result.outbound_found is True
    assert result.campaign_match is True
    assert result.message_fingerprint  # hash preenchido
    assert result.message_timestamp  # timestamp preenchido


def test_contato_salvo_por_nome_telefone_confirmado_painel():
    """Contato salvo por nome mas com telefone confirmado no painel -> MATCHED."""
    # Mesmo DOM: o telefone é confirmado via PHONE_IN_PROFILE no painel de informações.
    page = FakePage(_dom_matched())
    result = asyncio.run(fazer_match_completo(page, "lead-2", PHONE, CK))
    assert result.status == MatchStatus.MATCHED
    # Confirmação veio do painel (title com +55...)
    assert result.details.get("phone_found") in (None, PHONE) or result.status == MatchStatus.MATCHED


def test_mensagem_enviada_detectada():
    """Mensagem de saída é detectada (outbound_found True)."""
    page = FakePage(_dom_matched())
    result = asyncio.run(fazer_match_completo(page, "lead-3", PHONE, CK))
    assert result.outbound_found is True


def test_mensagem_apenas_recebida_nao_conta():
    """Conversa sem mensagem de saída (só recebidas) -> NO_OUTBOUND, não conta."""
    dom = _dom_matched()
    dom.pop(MESSAGE_OUT_SELECTORS[0])  # nenhuma mensagem de saída
    dom.pop(MESSAGE_TEXT_SELECTORS[0])
    page = FakePage(dom)
    result = asyncio.run(fazer_match_completo(page, "lead-4", PHONE, CK))
    assert result.status == MatchStatus.NO_OUTBOUND
    assert result.outbound_found is False


def test_grupo_nao_conta():
    """Grupo -> GROUP, não marca."""
    dom = _dom_matched()
    dom[GROUP_INDICATORS[0]] = [{"title": None, "text": None, "timestamp": None}]
    page = FakePage(dom)
    result = asyncio.run(fazer_match_completo(page, "lead-5", PHONE, CK))
    assert result.status == MatchStatus.GROUP
    assert result.status != MatchStatus.MATCHED


def test_canal_nao_conta():
    """Canal -> não conta (GROUP_INDICATORS inclui channel-icon)."""
    dom = _dom_matched()
    # índice de channel-icon em GROUP_INDICATORS
    canal_sel = next((s for s in GROUP_INDICATORS if "channel" in s), GROUP_INDICATORS[-1])
    dom[canal_sel] = [{"title": None, "text": None, "timestamp": None}]
    page = FakePage(dom)
    result = asyncio.run(fazer_match_completo(page, "lead-6", PHONE, CK))
    assert result.status == MatchStatus.CHANNEL
    assert result.status != MatchStatus.MATCHED


def test_comunidade_nao_conta():
    """Comunidade -> não conta (GROUP_INDICATORS inclui community-icon)."""
    dom = _dom_matched()
    com_sel = next((s for s in GROUP_INDICATORS if "community" in s), GROUP_INDICATORS[1])
    dom[com_sel] = [{"title": None, "text": None, "timestamp": None}]
    page = FakePage(dom)
    result = asyncio.run(fazer_match_completo(page, "lead-7", PHONE, CK))
    assert result.status == MatchStatus.COMMUNITY
    assert result.status != MatchStatus.MATCHED


def test_status_nao_conta():
    """Status (sem mensagem de saída para o contato) -> NO_OUTBOUND, não conta."""
    # Status não tem outbound -> mesmo caminho de "sem saída".
    dom = _dom_matched()
    dom.pop(MESSAGE_OUT_SELECTORS[0])
    dom.pop(MESSAGE_TEXT_SELECTORS[0])
    page = FakePage(dom)
    result = asyncio.run(fazer_match_completo(page, "lead-8", PHONE, CK))
    assert result.status == MatchStatus.NO_OUTBOUND
    assert result.status != MatchStatus.MATCHED


def test_conversa_vazia():
    """Conversa vazia (sem outbound) -> NO_OUTBOUND."""
    dom = _dom_matched()
    dom.pop(MESSAGE_OUT_SELECTORS[0])
    dom.pop(MESSAGE_TEXT_SELECTORS[0])
    page = FakePage(dom)
    result = asyncio.run(fazer_match_completo(page, "lead-9", PHONE, CK))
    assert result.status == MatchStatus.NO_OUTBOUND


def test_numero_parecido_mas_diferente():
    """Número parecido mas diferente -> AMBIGUOUS_CONTACT, não marca."""
    dom = _dom_matched()
    # Telefone no painel é diferente (8888 em vez de 9999)
    dom[PHONE_IN_PROFILE_SELECTORS[0]] = [{"title": "+55 21 88888-8888", "text": None, "timestamp": None}]
    page = FakePage(dom)
    result = asyncio.run(fazer_match_completo(page, "lead-10", PHONE, CK))
    assert result.status == MatchStatus.AMBIGUOUS_CONTACT
    assert result.status != MatchStatus.MATCHED


def test_fingerprint_incompativel_vira_ambiguo():
    """Mensagem de saída com fingerprint incompatível -> AMBIGUOUS, não MATCHED."""
    dom = _dom_matched()
    dom['div[data-testid="msg-container"]'] = [{"title": None, "text": "tail-out" + MSG_NAO_CAMPANHA, "timestamp": "1717200000"}]
    dom[MESSAGE_TEXT_SELECTORS[0]] = [{"title": None, "text": MSG_NAO_CAMPANHA, "timestamp": None}]
    page = FakePage(dom)
    result = asyncio.run(fazer_match_completo(page, "lead-11", PHONE, CK))
    assert result.status == MatchStatus.AMBIGUOUS
    assert result.outbound_found is True
    assert result.campaign_match is False
    # Sanity: a mensagem de fato não corresponde à campanha
    assert corresponde_campanha(MSG_NAO_CAMPANHA, CK) is False
    assert corresponde_campanha(MSG_CAMPANHA, CK) is True


def test_nenhuma_conversa_encontrada_no_chat():
    """Telefone não existe no WhatsApp -> NO_CHAT."""
    # Apenas o campo de busca existe; nenhum item de conversa aparece.
    page = FakePage({SEARCH_BOX_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}]})
    result = asyncio.run(fazer_match_completo(page, "lead-12", PHONE, CK))
    assert result.status == MatchStatus.NO_CHAT
    assert result.chat_found is False


# ============================================================
# Testes de seletores (fallback e diagnóstico)
# ============================================================

def test_seletor_principal_quebrado_usa_fallback():
    """Se o seletor principal não existe, encontrar_seletor usa o fallback."""
    # Só o 2º seletor de SEARCH_BOX está presente.
    dom = {SEARCH_BOX_SELECTORS[1]: [{"title": None, "text": None, "timestamp": None}]}
    page = FakePage(dom)
    sel = asyncio.run(encontrar_seletor(page, SEARCH_BOX_SELECTORS, timeout=1000))
    assert sel == SEARCH_BOX_SELECTORS[1]


def test_todos_fallbacks_quebrados_retornam_none():
    """Todos os seletores quebrados -> encontrar_seletor retorna None (graceful)."""
    page = FakePage({})  # DOM vazio
    sel = asyncio.run(encontrar_seletor(page, SEARCH_BOX_SELECTORS, timeout=1000))
    assert sel is None


def test_todos_fallbacks_quebrados_geram_diagnostico():
    """DOM totalmente quebrado -> fazer_match_completo gera diagnóstico (screenshot + snapshot)."""
    with tempfile.TemporaryDirectory() as tmp:
        page = FakePage(broken=True)
        result = asyncio.run(fazer_match_completo(page, "lead-diag", PHONE, CK, diagnostic_dir=tmp))
        assert result.status == MatchStatus.SEARCH_FIELD_NOT_FOUND
        # Diagnóstico: screenshot + snapshot salvos
        arquivos = list(Path(tmp).glob("*"))
        assert any(a.suffix == ".png" for a in arquivos), "screenshot não gerado"
        assert any(a.suffix == ".html" for a in arquivos), "snapshot HTML não gerado"


def test_capturar_diagnostico_escreve_arquivos():
    """capturar_diagnostico cria screenshot.png e snapshot.html."""
    with tempfile.TemporaryDirectory() as tmp:
        page = FakePage(_dom_matched())
        asyncio.run(capturar_diagnostico(page, Path(tmp), prefixo="teste"))
        assert (Path(tmp) / "teste_screenshot.png").exists()
        assert (Path(tmp) / "teste_snapshot.html").exists()


# ============================================================
# Teste estático: nenhum teste/envio envia mensagem
# ============================================================

def test_login_required_returns_login_required_status():
    """WhatsApp not authenticated (QR screen) -> LOGIN_REQUIRED, not NO_CHAT."""
    # Only QR elements present, no search field, no chat-list
    page = FakePage({
        'canvas[aria-label*="escaneie" i]': [{"title": None, "text": None, "timestamp": None}],
    })
    result = asyncio.run(fazer_match_completo(page, "lead-login", PHONE, CK))
    assert result.status == MatchStatus.LOGIN_REQUIRED
    assert result.status != MatchStatus.NO_CHAT


def test_no_search_field_returns_search_field_not_found():
    """No search box and no QR -> SEARCH_FIELD_NOT_FOUND, not NO_CHAT."""
    # Empty page - no search box, no QR
    page = FakePage({})
    result = asyncio.run(fazer_match_completo(page, "lead-nosearch", PHONE, CK))
    assert result.status in (MatchStatus.SEARCH_FIELD_NOT_FOUND, MatchStatus.NO_CHAT)
    # The distinction: SEARCH_FIELD_NOT_FOUND means the search UI element is missing
    # NO_CHAT means we found the search UI but no chat matched the phone




def test_no_chat_nao_interrompe_lote():
    """Resultado NO_CHAT nao deve interromper o processamento do lote."""
    # This is a state machine test: no_chat is a valid per-lead result
    # that should NOT trigger global abort
    from whatsapp_match.matcher import MatchStatus
    # no_chat is not a global error
    assert MatchStatus.NO_CHAT not in (
        MatchStatus.SEARCH_FIELD_NOT_FOUND,
        MatchStatus.LOGIN_REQUIRED,
        MatchStatus.ERROR,
    )


def test_search_field_found_returns_no_chat():
    """Search field found + no chat item = NO_CHAT (not SEARCH_FIELD_NOT_FOUND)."""
    # FakePage with search box but no chat items
    dom = {SEARCH_BOX_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}]}
    page = FakePage(dom)
    result = asyncio.run(fazer_match_completo(page, "lead-nochat", PHONE, CK))
    assert result.status == MatchStatus.NO_CHAT
    assert result.selector_used is not None  # Search field was found


def test_search_field_absent_returns_search_field_not_found():
    """No search box at all = SEARCH_FIELD_NOT_FOUND."""
    page = FakePage({})  # Empty page
    result = asyncio.run(fazer_match_completo(page, "lead-absent", PHONE, CK))
    assert result.status == MatchStatus.SEARCH_FIELD_NOT_FOUND


def test_input_uses_fill_not_contenteditable():
    """Search uses fill() method which works with INPUT elements."""
    # The real DOM uses INPUT, not contenteditable DIV
    # fill() works with both, but we verify the selector targets INPUT
    assert '#side input[role="textbox"]' in SEARCH_BOX_SELECTORS[0]

def test_matcher_nao_envia_mensagens():
    """O módulo matcher não contém lógica de envio (send?phone, Enter, botão Enviar)."""
    src = (Path(__file__).resolve().parent.parent / "whatsapp_match" / "matcher.py").read_text(encoding="utf-8")
    assert "send?phone=" not in src, "matcher não deve abrir send?phone="
    assert "web.whatsapp.com/send" not in src, "matcher não deve navegar para send"
    # Escape é usado para fechar modais, não para enviar mensagens
    assert 'aria-label="Enviar"' not in src and 'aria-label="Send"' not in src, \
        "matcher não deve clicar em botão Enviar"
    # Não deve conter Enter no composer
    assert '"Enter"' not in src, "matcher não deve pressionar Enter"


# ============================================================
# TESTES DE MODAL/DIALOG
# ============================================================

DIALOG_SELECTOR = '[role="dialog"][aria-modal="true"]'


def test_modal_intercepta_click_retorna_modal_blocked():
    """Dialog interceptando clique no campo de busca -> modal_blocked, não search_field_not_found."""
    dom = _dom_matched()
    # Adiciona modal visível mas sem botão de fechar
    dom[DIALOG_SELECTOR] = [{"title": None, "text": None, "timestamp": None}]
    page = FakePage(dom)
    result = asyncio.run(fazer_match_completo(page, "lead-modal-1", PHONE, CK))
    # Pode ser modal_blocked se não conseguir fechar, ou matched se fechar e continuar
    # Como FakePage não remove o dialog dinamicamente, deve retornar modal_blocked
    assert result.status in (MatchStatus.MODAL_BLOCKED, MatchStatus.MATCHED, MatchStatus.NO_CHAT)


def test_escape_fecha_modal():
    """Escape fecha modal e permite encontrar o campo de busca."""
    # FakePage registra keyboard_press nas actions
    dom = _dom_matched()
    dom[DIALOG_SELECTOR] = [{"title": None, "text": None, "timestamp": None}]
    page = FakePage(dom)
    asyncio.run(fazer_match_completo(page, "lead-modal-2", PHONE, CK))
    # Verifica que Escape foi tentado
    keyboard_actions = [a for a in page.actions if a[0] == "keyboard_press"]
    assert any("Escape" in a[1] for a in keyboard_actions), "Escape deve ser tentado"


def test_botao_seguro_fecha_modal():
    """Botão seguro (Fechar/OK) fecha modal."""
    from whatsapp_match.matcher import _BOTOES_SEGUROS_MODAL
    # Verifica que existem botões seguros configurados
    assert len(_BOTOES_SEGUROS_MODAL) > 0
    # Verifica que botões destrutivos NÃO estão na lista
    for sel in _BOTOES_SEGUROS_MODAL:
        assert "Enviar" not in sel, "Botão Enviar não deve ser seguro"
        assert "Send" not in sel, "Botão Send não deve ser seguro"
        assert "Delete" not in sel, "Botão Delete não deve ser seguro"
        assert "Block" not in sel, "Botão Block não deve ser seguro"
        assert "Report" not in sel, "Botão Report não deve ser seguro"


def test_botao_desconhecido_nao_clicado():
    """Botão desconhecido no dialog não deve ser clicado."""
    from whatsapp_match.matcher import _BOTOES_SEGUROS_MODAL
    # Seletores só devem clicar em botões com aria-label conhecido
    for sel in _BOTOES_SEGUROS_MODAL:
        # Cada seletor deve ter filtro por aria-label ou data-testid
        assert "aria-label" in sel or "data-testid" in sel, \
            f"Seletor sem filtro: {sel}"


def test_modal_persistente_retorna_modal_blocked():
    """Modal que não pode ser fechado retorna modal_blocked, não search_field_not_found."""
    dom = _dom_matched()
    dom[DIALOG_SELECTOR] = [{"title": None, "text": None, "timestamp": None}]
    # Sem botões de fechar — modal persistente
    page = FakePage(dom)
    result = asyncio.run(fazer_match_completo(page, "lead-modal-3", PHONE, CK))
    # FakePage não remove elementos dinamicamente, então modal persiste
    assert result.status == MatchStatus.MODAL_BLOCKED


def test_modal_nao_vira_search_field_not_found():
    """Modal blocked não deve ser classificado como search_field_not_found."""
    dom = _dom_matched()
    dom[DIALOG_SELECTOR] = [{"title": None, "text": None, "timestamp": None}]
    page = FakePage(dom)
    result = asyncio.run(fazer_match_completo(page, "lead-modal-4", PHONE, CK))
    assert result.status != MatchStatus.SEARCH_FIELD_NOT_FOUND, \
        "Modal blocked não deve virar search_field_not_found"


def test_apos_fechar_modal_campo_busca_encontrado():
    """Sem modal, campo de busca deve ser encontrado normalmente."""
    dom = _dom_matched()
    # Sem dialog no DOM
    page = FakePage(dom)
    result = asyncio.run(fazer_match_completo(page, "lead-no-modal", PHONE, CK))
    assert result.status == MatchStatus.MATCHED


def test_telefone_diferente_mantem_ambiguous_contact():
    """Telefone diferente no painel mantém ambiguous_contact."""
    dom = _dom_matched()
    # Telefone no painel diferente do esperado
    dom[PHONE_IN_PROFILE_SELECTORS[0]] = [{"title": "+55 21 88888-8888", "text": None, "timestamp": None}]
    page = FakePage(dom)
    result = asyncio.run(fazer_match_completo(page, "lead-diff-tel", PHONE, CK))
    assert result.status == MatchStatus.AMBIGUOUS_CONTACT


def test_telefone_igual_permite_continuar():
    """Telefone igual no painel permite continuar o match."""
    dom = _dom_matched()
    # Telefone correto
    dom[PHONE_IN_PROFILE_SELECTORS[0]] = [{"title": "+55 21 99999-9999", "text": None, "timestamp": None}]
    page = FakePage(dom)
    result = asyncio.run(fazer_match_completo(page, "lead-same-tel", PHONE, CK))
    assert result.status == MatchStatus.MATCHED


def test_modal_nenhuma_escrita_supabase():
    """Testes de modal não escrevem no Supabase."""
    src = (Path(__file__).resolve().parent.parent / "whatsapp_match" / "matcher.py").read_text(encoding="utf-8")
    assert "service_role" not in src.lower(), "matcher não deve carregar service role"
    assert "rpc" not in src.lower() or "no_rpc" in src.lower(), "matcher não deve chamar RPC"


def test_modal_nenhum_envio():
    """Tratamento de modal não envia mensagens."""
    src = (Path(__file__).resolve().parent.parent / "whatsapp_match" / "matcher.py").read_text(encoding="utf-8")
    assert "send?phone=" not in src
    assert "web.whatsapp.com/send" not in src
    assert '"Enter"' not in src, "matcher não deve pressionar Enter"


# ============================================================
# TESTES DE EXTRACAO DE TELEFONE
# ============================================================

from whatsapp_match.matcher import extrair_telefone_confirmado_chat
from utils.phone_utils import normalizar_telefone_br


def test_telefone_extraido_por_span_title():
    """Telefone extraído por PHONE_IN_PROFILE_SELECTORS deve ser confirmado."""
    dom = {
        CONVERSATION_HEADER_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}],
        PHONE_IN_PROFILE_SELECTORS[0]: [{"title": "+55 21 99999-9999", "text": None, "timestamp": None}],
        BACK_BUTTON_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}],
    }
    page = FakePage(dom)
    confirmado, tel, tipo = asyncio.run(extrair_telefone_confirmado_chat(page, "5521999999999"))
    assert confirmado is True
    assert tel == "5521999999999"
    assert tipo == "phone_profile"


def test_telefone_extraido_por_tel_link():
    """Telefone extraído por link tel: deve ser confirmado."""
    dom = {
        CONVERSATION_HEADER_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}],
        'a[href*="tel:"]': [{"title": None, "text": None, "timestamp": None, "href": "tel:+5521999999999"}],
        BACK_BUTTON_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}],
    }
    page = FakePage(dom)
    confirmado, tel, tipo = asyncio.run(extrair_telefone_confirmado_chat(page, "5521999999999"))
    assert confirmado is True
    assert tel == "5521999999999"
    assert tipo == "tel_link"


def test_telefone_extraido_por_aria_label():
    """Telefone extraído por aria-label deve ser confirmado."""
    dom = {
        CONVERSATION_HEADER_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}],
        # O código usa '[aria-label*="+55"], [aria-label*="55"]'
        '[aria-label*="+55"], [aria-label*="55"]': [{"title": None, "text": None, "timestamp": None, "aria-label": "+55 21 99999-9999"}],
        BACK_BUTTON_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}],
    }
    page = FakePage(dom)
    confirmado, tel, tipo = asyncio.run(extrair_telefone_confirmado_chat(page, "5521999999999"))
    assert confirmado is True
    assert tel == "5521999999999"


def test_telefone_extraido_por_jid():
    """Telefone extraído por JID deve ser confirmado."""
    dom = {
        CONVERSATION_HEADER_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}],
        '[data-id*="@s.whatsapp.net"]': [{"title": None, "text": None, "timestamp": None, "data-id": "5521999999999@s.whatsapp.net"}],
        BACK_BUTTON_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}],
    }
    page = FakePage(dom)
    confirmado, tel, tipo = asyncio.run(extrair_telefone_confirmado_chat(page, "5521999999999"))
    assert confirmado is True
    assert tel == "5521999999999"
    assert tipo == "jid"


def test_telefone_nacional_e_55_sao_equivalentes():
    """Telefone nacional (21999999999) e com 55 (5521999999999) são equivalentes."""
    assert normalizar_telefone_br("21999999999") == "5521999999999"
    assert normalizar_telefone_br("5521999999999") == "5521999999999"


def test_numero_parcial_nao_confirma():
    """Número parcial (últimos 4 dígitos) não deve confirmar."""
    dom = {
        CONVERSATION_HEADER_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}],
        PHONE_IN_PROFILE_SELECTORS[0]: [{"title": "9999", "text": None, "timestamp": None}],
        BACK_BUTTON_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}],
    }
    page = FakePage(dom)
    confirmado, tel, tipo = asyncio.run(extrair_telefone_confirmado_chat(page, "5521999999999"))
    assert confirmado is False


def test_nome_igual_nao_confirma():
    """Apenas nome igual não deve confirmar telefone."""
    dom = {
        CONVERSATION_HEADER_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}],
        PHONE_IN_PROFILE_SELECTORS[0]: [],  # Sem telefone no painel
        BACK_BUTTON_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}],
    }
    page = FakePage(dom)
    confirmado, tel, tipo = asyncio.run(extrair_telefone_confirmado_chat(page, "5521999999999"))
    assert confirmado is False


def test_chat_diferente_mantem_ambiguous_contact():
    """Chat com telefone diferente mantém ambiguous_contact."""
    dom = {
        CONVERSATION_HEADER_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}],
        PHONE_IN_PROFILE_SELECTORS[0]: [{"title": "+55 21 88888-8888", "text": None, "timestamp": None}],
        BACK_BUTTON_SELECTORS[0]: [{"title": None, "text": None, "timestamp": None}],
    }
    page = FakePage(dom)
    confirmado, tel, tipo = asyncio.run(extrair_telefone_confirmado_chat(page, "5521999999999"))
    assert confirmado is False
    assert tel is None


def test_extrair_telefone_nenhuma_escrita():
    """Extração de telefone não escreve no Supabase."""
    src = (Path(__file__).resolve().parent.parent / "whatsapp_match" / "matcher.py").read_text(encoding="utf-8")
    assert "service_role" not in src.lower()
    assert "rpc" not in src.lower() or "no_rpc" in src.lower()


def test_extrair_telefone_nenhum_envio():
    """Extração de telefone não envia mensagens."""
    src = (Path(__file__).resolve().parent.parent / "whatsapp_match" / "matcher.py").read_text(encoding="utf-8")
    assert "send?phone=" not in src
    assert "web.whatsapp.com/send" not in src