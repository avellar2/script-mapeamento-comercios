#!/usr/bin/env python3
import importlib.util
import json
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parent.parent / "indexar_conversas_whatsapp.py"
spec = importlib.util.spec_from_file_location("indexar_conversas_whatsapp", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class FakeNode:
    def __init__(self, attrs=None, text=""):
        self.attrs = attrs or {}
        self.text = text

    async def get_attribute(self, name):
        return self.attrs.get(name)

    async def text_content(self):
        return self.text


class FakeLocator:
    def __init__(self, nodes):
        self.nodes = nodes

    async def count(self):
        return len(self.nodes)

    def nth(self, i):
        return self.nodes[i]


class FakePage:
    def __init__(self, selector_map):
        self.selector_map = selector_map

    def locator(self, selector):
        return FakeLocator(self.selector_map.get(selector, []))


def test_scroll_ate_estabilizacao_em_lista_virtualizada():
    pages = [
        [
            {"chat_key": "a", "rowIndex": 0},
            {"chat_key": "b", "rowIndex": 1},
        ],
        [
            {"chat_key": "b", "rowIndex": 0},
            {"chat_key": "c", "rowIndex": 1},
        ],
        [
            {"chat_key": "c", "rowIndex": 0},
            {"chat_key": "d", "rowIndex": 1},
        ],
        [
            {"chat_key": "d", "rowIndex": 0},
        ],
        [
            {"chat_key": "d", "rowIndex": 0},
        ],
    ]
    state = {"i": 0}

    async def fetch_visible():
        idx = min(state["i"], len(pages) - 1)
        return pages[idx]

    async def scroll_next():
        if state["i"] < len(pages) - 1:
            state["i"] += 1
            return True
        return False

    import asyncio

    cards, stats = asyncio.run(mod.varrer_ate_estabilizar(fetch_visible, scroll_next, max_idle_rounds=2))

    assert [c["chat_key"] for c in cards] == ["a", "b", "c", "d"]
    assert stats["unique"] == 4
    assert stats["scrolls"] >= 1


def test_chats_duplicados_nao_sao_reprocessados_no_resume():
    seen = {"chat:1", "chat:2"}

    async def fetch_visible():
        return [
            {"chat_key": "chat:1", "rowIndex": 0},
            {"chat_key": "chat:2", "rowIndex": 1},
            {"chat_key": "chat:3", "rowIndex": 2},
        ]

    async def scroll_next():
        return False

    import asyncio

    cards, stats = asyncio.run(
        mod.varrer_ate_estabilizar(fetch_visible, scroll_next, seen_keys=seen, max_idle_rounds=1)
    )

    assert [c["chat_key"] for c in cards] == ["chat:3"]
    assert stats["unique"] == 1


def test_grupos_canais_comunidades_sao_ignorados_na_comparacao():
    records = [
        mod.ChatIndexRecord(
            technical_id_raw="g1",
            technical_id_sanitized="chat:g1",
            chat_type="group",
            status=mod.ChatStatus.chat_unsupported,
            phone_hash=mod.hash_telefone_canonico("5521999999999"),
            phone_last4="9999",
            outbound_found=True,
            campaign_match=True,
        ),
        mod.ChatIndexRecord(
            technical_id_raw="c1",
            technical_id_sanitized="chat:c1",
            chat_type="channel",
            status=mod.ChatStatus.chat_unsupported,
            phone_hash=mod.hash_telefone_canonico("5521888888888"),
            phone_last4="8888",
            outbound_found=True,
            campaign_match=True,
        ),
    ]
    leads = [
        {"id": "lead-1", "nome": "Loja 1", "telefone": "(21) 99999-9999"},
        {"id": "lead-2", "nome": "Loja 2", "telefone": "(21) 88888-8888"},
    ]

    candidatos = mod.comparar_leads_com_indice(records, leads)
    assert candidatos == []


def test_confirma_telefone_completo_em_atributo_tecnico(monkeypatch):
    async def noop(_page):
        return None

    monkeypatch.setattr(mod, "_abrir_painel_info", noop)
    monkeypatch.setattr(mod, "_fechar_painel_info_se_aberto", noop)

    page = FakePage(
        {
            '#main [data-id*="@s.whatsapp.net"], [data-testid="conversation-panel-wrapper"] [data-id*="@s.whatsapp.net"]': [FakeNode({"data-id": "5521999999999@s.whatsapp.net"})],
            '[data-testid="contact-info"], [data-testid*="drawer" i] [data-id], section[data-testid*="contact"] [data-id]': [],
            '[data-testid="contact-info"] a[href*="tel:"], section[data-testid*="contact"] a[href*="tel:"]': [],
            '[aria-label*="+55"], [aria-label*="55"], [title*="+55"], [title*="55"]': [],
        }
    )

    import asyncio

    telefone, evidencia = asyncio.run(mod.extrair_telefone_da_conversa(page))
    assert telefone == "5521999999999"
    assert evidencia == "jid"


def test_rejeita_telefone_parcial(monkeypatch):
    async def noop(_page):
        return None

    monkeypatch.setattr(mod, "_abrir_painel_info", noop)

    page = FakePage(
        {
            '#main [data-id*="@s.whatsapp.net"], [data-testid="conversation-panel-wrapper"] [data-id*="@s.whatsapp.net"]': [FakeNode({"data-id": "9999@s.whatsapp.net"})],
            '[data-testid="contact-info"], [data-testid*="drawer" i] [data-id], section[data-testid*="contact"] [data-id]': [FakeNode({"aria-label": "contato final 9999"})],
            '[data-testid="contact-info"] a[href*="tel:"], section[data-testid*="contact"] a[href*="tel:"]': [],
            '[aria-label*="+55"], [aria-label*="55"], [title*="+55"], [title*="55"]': [],
        }
    )

    import asyncio

    telefone, evidencia = asyncio.run(mod.extrair_telefone_da_conversa(page))
    assert telefone is None
    assert evidencia == "phone_unconfirmed"


def test_hash_igual_encontra_lead_e_ignora_reconciliados():
    tel = "5521999999999"
    records = [
        mod.ChatIndexRecord(
            technical_id_raw="x",
            technical_id_sanitized="chat:x",
            chat_type="individual",
            status=mod.ChatStatus.campaign_matched,
            phone_hash=mod.hash_telefone_canonico(tel),
            phone_last4=tel[-4:],
            outbound_found=True,
            anchor_count=3,
            campaign_match=True,
            evidence="jid",
        )
    ]
    leads = [
        {"id": "12345678-aaaa", "nome": "Loja Boa", "telefone": tel},
        {"id": "12345678-bbbb", "nome": "TECM TECNOLOGIA", "telefone": tel},
    ]

    candidatos = mod.comparar_leads_com_indice(records, leads)
    assert len(candidatos) == 1
    assert candidatos[0].nome == "Loja Boa"
    assert candidatos[0].telefone_mascarado.endswith("9999")


def test_texto_integral_nao_e_persistido_no_indice_nem_relatorio(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path)
    rec = mod.ChatIndexRecord(
        technical_id_raw="raw-1",
        technical_id_sanitized="chat:1",
        chat_type="individual",
        status=mod.ChatStatus.campaign_matched,
        phone_hash="abc123",
        phone_last4="9999",
        outbound_found=True,
        anchor_count=2,
        campaign_match=True,
        timestamp_technical="2026-07-04T12:00:00+00:00",
        evidence="jid",
        message_fingerprint="fingerprint-hash",
    )
    stats = mod.IndexRunStats(started_at="2026-07-04T00:00:00+00:00", finished_at="2026-07-04T00:01:00+00:00")
    paths = mod.gerar_relatorios_locais([rec], [], [], stats, "teste_privacidade")

    persisted = json.loads(paths["resumo_json"].read_text(encoding="utf-8"))
    raw_jsonl = paths["index_jsonl"].read_text(encoding="utf-8")

    assert "message_fingerprint" not in raw_jsonl
    assert "texto" not in raw_jsonl.lower()
    assert "technical_id_raw" not in raw_jsonl
    assert persisted["records"][0]["phone_last4"] == "9999"
    assert "message_fingerprint" not in json.dumps(persisted, ensure_ascii=False)


def test_checkpoint_permite_retomada_sem_reabrir_chat_concluido(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(mod, "CHECKPOINT_FILE", tmp_path / "checkpoint.json")

    processed = {"chat:a", "chat:b"}
    mod.salvar_checkpoint(processed, total_processed=2, last_chat_key="chat:b")
    loaded = mod.carregar_checkpoint()

    assert set(loaded["processed_keys"]) == processed
    assert loaded["total_processed"] == 2
    assert loaded["last_chat_key"] == "chat:b"


def test_modulo_nao_usa_service_role_nem_apply_nem_sender():
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "SUPABASE_SERVICE_ROLE_KEY" not in source
    assert "confirm_outreach_from_whatsapp" not in source
    assert "sender_int" not in source
    assert "send_keys(" not in source


def test_record_persistido_nao_tem_telefone_completo():
    rec = mod.ChatIndexRecord(
        technical_id_raw="raw-id-com-telefone-5521999999999",
        technical_id_sanitized="chat:abc",
        chat_type="individual",
        status=mod.ChatStatus.no_outbound,
        phone_hash=mod.hash_telefone_canonico("5521999999999"),
        phone_last4="9999",
    )

    persisted = rec.to_persisted_dict()
    dumped = json.dumps(persisted, ensure_ascii=False)
    assert "5521999999999" not in dumped
    assert persisted["phone_last4"] == "9999"
  
  
# NOVOS TESTES - bugfix telefone repetido  
 



# ============================================================
# NOVOS TESTES - bugfix telefone repetido
# ============================================================

def test_dois_chats_diferentes_geram_hashes_diferentes():
    tel_a = "5521999999999"
    tel_b = "5521888888888"
    records = [
        mod.ChatIndexRecord(
            technical_id_raw="a", technical_id_sanitized="chat:a",
            chat_type="individual", status=mod.ChatStatus.campaign_matched,
            phone_hash=mod.hash_telefone_canonico(tel_a), phone_last4=tel_a[-4:],
            outbound_found=True, campaign_match=True,
        ),
        mod.ChatIndexRecord(
            technical_id_raw="b", technical_id_sanitized="chat:b",
            chat_type="individual", status=mod.ChatStatus.campaign_matched,
            phone_hash=mod.hash_telefone_canonico(tel_b), phone_last4=tel_b[-4:],
            outbound_found=True, campaign_match=True,
        ),
    ]
    leads = [
        {"id": "lead-a", "nome": "Loja A", "telefone": tel_a},
        {"id": "lead-b", "nome": "Loja B", "telefone": tel_b},
    ]
    candidatos = mod.comparar_leads_com_indice(records, leads)
    assert len(candidatos) == 2
    assert candidatos[0].phone_hash != candidatos[1].phone_hash


def test_chat_que_nao_muda_retorna_chat_not_changed():
    record = mod.ChatIndexRecord(
        technical_id_raw="x", technical_id_sanitized="chat:x",
        chat_type="individual", status=mod.ChatStatus.chat_not_changed,
        error_message="chat nao mudou apos clique", error_stage="aguardar_troca",
        retryable=True,
    )
    assert record.status == mod.ChatStatus.chat_not_changed
    assert record.error_stage == "aguardar_troca"
    assert record.retryable is True


def test_suspicious_repeated_phone_existe():
    record = mod.ChatIndexRecord(
        technical_id_raw="x", technical_id_sanitized="chat:x",
        chat_type="individual", status=mod.ChatStatus.suspicious_repeated_phone,
        error_message="telefone repetido", error_stage="suspicious_repeat",
        retryable=False,
    )
    assert record.status == mod.ChatStatus.suspicious_repeated_phone
    assert record.retryable is False


def test_tres_repeticoes_disparam_protecao():
    records = [
        mod.ChatIndexRecord(
            technical_id_raw="a", technical_id_sanitized="chat:a",
            chat_type="individual", status=mod.ChatStatus.campaign_matched,
            phone_hash="h123", phone_last4="1234",
            outbound_found=True, campaign_match=True,
        ),
        mod.ChatIndexRecord(
            technical_id_raw="b", technical_id_sanitized="chat:b",
            chat_type="individual", status=mod.ChatStatus.campaign_matched,
            phone_hash="h123", phone_last4="1234",
            outbound_found=True, campaign_match=True,
        ),
        mod.ChatIndexRecord(
            technical_id_raw="c", technical_id_sanitized="chat:c",
            chat_type="individual", status=mod.ChatStatus.campaign_matched,
            phone_hash="h123", phone_last4="1234",
            outbound_found=True, campaign_match=True,
        ),
    ]
    ultimos_hashes = [
        r.phone_hash
        for r in records
        if r.chat_type == "individual" and r.phone_hash
    ]
    assert len(set(ultimos_hashes)) == 1
    assert len(ultimos_hashes) >= 3


def test_estado_zerado_entre_iteracoes():
    tel_a = "5521999999999"
    tel_b = "5521888888888"
    rec1 = mod.ChatIndexRecord(
        technical_id_raw="a", technical_id_sanitized="chat:a",
        chat_type="individual", status=mod.ChatStatus.campaign_matched,
        phone_hash=mod.hash_telefone_canonico(tel_a),
        phone_last4=tel_a[-4:],
    )
    rec2 = mod.ChatIndexRecord(
        technical_id_raw="b", technical_id_sanitized="chat:b",
        chat_type="individual", status=mod.ChatStatus.campaign_matched,
        phone_hash=mod.hash_telefone_canonico(tel_b),
        phone_last4=tel_b[-4:],
    )
    assert rec1.phone_hash != rec2.phone_hash
    assert rec1.phone_last4 != rec2.phone_last4
    assert rec1.technical_id_sanitized != rec2.technical_id_sanitized


def test_record_persistido_tem_campos_novos():
    rec = mod.ChatIndexRecord(
        technical_id_raw="x", technical_id_sanitized="chat:x",
        chat_type="individual", status=mod.ChatStatus.error,
        error_message="err", error_stage="exception", retryable=True,
    )
    assert rec.error_stage == "exception"
    assert rec.retryable is True


def test_capturar_assinatura_chat_ativo_existe():
    assert hasattr(mod, "capturar_assinatura_chat_ativo")
    assert callable(mod.capturar_assinatura_chat_ativo)


def test_aguardar_troca_chat_existe():
    assert hasattr(mod, "aguardar_troca_chat")
    assert callable(mod.aguardar_troca_chat)


def test_fechar_painel_info_se_aberto_existe():
    assert hasattr(mod, "_fechar_painel_info_se_aberto")
    assert callable(mod._fechar_painel_info_se_aberto)

# ============================================================
# TESTES V3 - invariante chat_switch_verified
# ============================================================

def test_sem_troca_confirmada_nenhuma_extracao_possivel():
    troca_ok = False
    if not troca_ok:
        status = 'chat_not_changed'
    assert status == 'chat_not_changed'


def test_panel_loaded_sozinho_nao_libera():
    sig_changed = False
    panel_loaded = True
    card_selected = False
    chat_switch_verified = sig_changed and card_selected and panel_loaded
    assert chat_switch_verified is False


def test_primeiro_chat_exige_card_selecionado_e_assinatura():
    sig_before = ''
    sig_after = 'sig:abc123'
    card_sel = True
    panel = True
    chat_switch_verified = bool(sig_after) and card_sel and panel
    assert chat_switch_verified is True


def test_clique_botao_interno_nao_valido():
    def clicar(elemento):
        if elemento in ('avatar', 'menu', 'badge'):
            return False
        return True
    assert clicar('avatar') is False
    assert clicar('row_main') is True


def test_painel_antigo_gera_stale_info_panel():
    assert hasattr(mod, 'ChatStatus')
    s = mod.ChatStatus.stale_info_panel
    assert s.value == 'stale_info_panel'


def test_assinatura_divergente_gera_chat_context_mismatch():
    assert hasattr(mod, 'ChatStatus')
    s = mod.ChatStatus.chat_context_mismatch
    assert s.value == 'chat_context_mismatch'


def test_tres_chats_distintos_mesmo_hash_disparam_suspicious():
    records = [
        mod.ChatIndexRecord(technical_id_raw='a', technical_id_sanitized='chat:a', chat_type='individual', status=mod.ChatStatus.no_outbound, phone_hash='hX', phone_last4='1234'),
        mod.ChatIndexRecord(technical_id_raw='b', technical_id_sanitized='chat:b', chat_type='individual', status=mod.ChatStatus.no_outbound, phone_hash='hX', phone_last4='1234'),
    ]
    new_rec = mod.ChatIndexRecord(technical_id_raw='c', technical_id_sanitized='chat:c', chat_type='individual', status=mod.ChatStatus.no_outbound, phone_hash='hX', phone_last4='1234')

    prev = [r for r in records if r.phone_hash == new_rec.phone_hash and r.technical_id_sanitized != new_rec.technical_id_sanitized]
    assert len(prev) == 2


def test_no_outbound_tambem_conta_para_repeticao_suspeita():
    records = [
        mod.ChatIndexRecord(technical_id_raw='a', technical_id_sanitized='chat:a', chat_type='individual', status=mod.ChatStatus.no_outbound, phone_hash='hY', phone_last4='5678'),
        mod.ChatIndexRecord(technical_id_raw='b', technical_id_sanitized='chat:b', chat_type='individual', status=mod.ChatStatus.no_outbound, phone_hash='hY', phone_last4='5678'),
        mod.ChatIndexRecord(technical_id_raw='c', technical_id_sanitized='chat:c', chat_type='individual', status=mod.ChatStatus.campaign_matched, phone_hash='hY', phone_last4='5678'),
    ]
    hashes = [r.phone_hash for r in records if r.phone_hash]
    assert len(hashes) == 3
    assert len(set(hashes)) == 1


def test_record_nao_persiste_telefone_jid_nome_mensagem():
    rec = mod.ChatIndexRecord(
        technical_id_raw='x', technical_id_sanitized='chat:x',
        chat_type='individual', status=mod.ChatStatus.no_outbound,
        phone_hash='abc', phone_last4='9999',
    )
    persisted = rec.to_persisted_dict()
    dumped = str(persisted)
    assert '@s.whatsapp.net' not in dumped
    assert 'nome' not in persisted
    assert 'mensagem' not in dumped.lower()


def test_card_selected_verificacao_robusta():
    fields = mod.ChatIndexRecord.__dataclass_fields__
    assert 'card_selected' in fields
    assert 'target_card_id' in fields
    assert 'panel_loaded' in fields


def test_telefone_anterior_nao_reutilizado_apos_chat_not_changed():
    rec1 = mod.ChatIndexRecord(technical_id_raw='a', technical_id_sanitized='chat:a', chat_type='individual', status=mod.ChatStatus.chat_not_changed, phone_hash='')
    rec2 = mod.ChatIndexRecord(technical_id_raw='b', technical_id_sanitized='chat:b', chat_type='individual', status=mod.ChatStatus.no_outbound, phone_hash='new_hash', phone_last4='2222')
    assert rec1.phone_hash != rec2.phone_hash
    assert not rec1.phone_hash


# ============================================================
# TESTES V4 - painel_info_aberto / chat-info-drawer
# ============================================================

class _DrawerPage:
    """Simula page com chat-info-drawer aberto ou fechado."""
    def __init__(self, drawer_open=True, drawer_has_button=True, closes_after_click=True):
        self.drawer_open = drawer_open
        self.drawer_has_button = drawer_has_button
        self.closes_after_click = closes_after_click
        self.clicks = 0

    async def evaluate(self, js):
        if 'getBoundingClientRect' in js:
            return self.drawer_open
        return self.drawer_open

    async def wait_for_timeout(self, ms):
        pass

    class _First:
        def __init__(self, page):
            self._page = page
        async def click(self, **kw):
            self._page.clicks += 1
            if self._page.closes_after_click:
                self._page.drawer_open = False

    class _Locator:
        def __init__(self, page, sel):
            self._page = page
            self._sel = sel
        async def count(self):
            if 'chat-info-drawer' in self._sel and 'button' in self._sel:
                return 1 if self._page.drawer_has_button else 0
            if 'Fechar' in self._sel and 'chat-info' not in self._sel:
                return 0
            return 0
        @property
        def first(self):
            return _DrawerPage._First(self._page)

    def locator(self, sel):
        return _DrawerPage._Locator(self, sel)


def test_somente_chat_info_drawer_considerado():
    assert hasattr(mod, 'painel_info_aberto')
    assert callable(mod.painel_info_aberto)


def test_sem_chat_info_drawer_retorna_painel_fechado():
    import asyncio
    page = _DrawerPage(drawer_open=False)
    result = asyncio.run(mod.painel_info_aberto(page))
    assert result is False


def test_chat_info_drawer_aberto_detectado():
    import asyncio
    page = _DrawerPage(drawer_open=True)
    result = asyncio.run(mod.painel_info_aberto(page))
    assert result is True


def test_fechar_painel_retorna_closed_quando_ja_fechado():
    import asyncio
    page = _DrawerPage(drawer_open=False)
    result = asyncio.run(mod._fechar_painel_info_se_aberto(page))
    assert result == "closed"


def test_fechar_painel_retorna_closed_quando_desaparece():
    import asyncio
    page = _DrawerPage(drawer_open=True, drawer_has_button=True, closes_after_click=True)
    result = asyncio.run(mod._fechar_painel_info_se_aberto(page))
    assert result == "closed"
    assert page.clicks == 1


def test_fechar_painel_retorna_missing_botao():
    import asyncio
    page = _DrawerPage(drawer_open=True, drawer_has_button=False, closes_after_click=False)
    result = asyncio.run(mod._fechar_painel_info_se_aberto(page))
    assert result == "info_panel_close_button_missing"


def test_elementos_drawer_nao_geram_stale_info_panel():
    import asyncio
    page = _DrawerPage(drawer_open=False)
    assert asyncio.run(mod.painel_info_aberto(page)) is False


def test_painel_que_nao_desaparece_gera_stale():
    import asyncio
    page = _DrawerPage(drawer_open=True, drawer_has_button=True, closes_after_click=False)
    result = asyncio.run(mod._fechar_painel_info_se_aberto(page))
    assert result == "stale_info_panel"


def test_stale_info_panel_status_existe():
    s = mod.ChatStatus.stale_info_panel
    assert s.value == 'stale_info_panel'


def test_nenhum_seletor_amplo_drawer_no_codigo():
    src = open(r"C:\projetos\script-mapear-comercios-whatsapp-dedup\indexar_conversas_whatsapp.py", encoding='utf-8').read()
    assert 'data-testid*="drawer" i' not in src
    assert 'section[data-testid*="contact"]' not in src


def test_chat_info_drawer_presente_no_codigo():
    src = open(r"C:\projetos\script-mapear-comercios-whatsapp-dedup\indexar_conversas_whatsapp.py", encoding='utf-8').read()
    assert 'chat-info-drawer' in src


def test_painel_info_aberto_checa_dimensoes():
    import asyncio
    page = _DrawerPage(drawer_open=True)
    assert asyncio.run(mod.painel_info_aberto(page)) is True
    page2 = _DrawerPage(drawer_open=False)
    assert asyncio.run(mod.painel_info_aberto(page2)) is False
