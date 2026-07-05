#!/usr/bin/env python3
"""
whatsapp_reverse_index.py — indexação reversa de conversas do WhatsApp Web.

Objetivo:
1) indexar conversas existentes uma única vez;
2) extrair telefone e mensagens de saída;
3) comparar com leads elegíveis do Supabase em memória;
4) gerar candidatos para apply;
5) não escrever no Supabase nesta etapa.

Regras de segurança:
- não usa service role;
- não envia mensagens;
- não executa apply;
- não persiste telefone completo nem texto integral das mensagens.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import logging
import os
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional

from config.lock_whatsapp_match import LockWhatsAppMatch
from config.whatsapp_selectors import (
    CONVERSATION_HEADER_SELECTORS,
    PHONE_IN_PROFILE_SELECTORS,
    TIMEOUT_RAPIDO,
    capturar_diagnostico,
    encontrar_seletor_rapido,
)
from utils.campaign_fingerprint import (
    chaves_estaveis_da_campanha,
    corresponde_campanha,
    fingerprint_mensagem,
    normalizar_texto,
)
from utils.campaign_key import PRIMEIRO_CONTATO_V1, validar_campaign_key
from utils.phone_utils import canonical_phone_hash, hash_telefone_canonico, normalizar_telefone_br
from whatsapp_match import _fechar_modal, limpar_campo_busca
from whatsapp_match.matcher import detectar_grupo

logger = logging.getLogger("whatsapp_reverse_index")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

PROFILE_DIR = Path("profiles/whatsapp_match")
OUTPUT_DIR = Path("output/avgestao/whatsapp_reverse_index")
CHECKPOINT_FILE = OUTPUT_DIR / "checkpoint.json"
DEFAULT_LIMIT = 20
MAX_IDLE_ROUNDS = 4
CHANGE_TIMEOUT_MS = 5000
SCROLL_STEP = 760
SCROLL_PAUSE_MS = 650
MAX_OUTBOUND_SCAN = 12
EXCLUDED_LEAD_NAMES = {
    "tecm tecnologia",
    "suporte smart nova iguaçu",
    "you cell conserto de celulares",
    "smart tech",
}

CHAT_LIST_SELECTORS = [
    'div[data-testid="chat-list"]',
    'div[aria-label*="lista de conversas" i]',
    'div[aria-label*="chat list" i]',
]

CHAT_ROW_SELECTOR = (
    'div[role="row"], '
    'div[data-testid="chat-list-item"], '
    'div[data-testid="cell-frame-container"], '
    'div[tabindex="-1"]'
)

ARCHIVE_BUTTON_SELECTORS = [
    'div[aria-label*="Arquivadas" i]',
    'div[aria-label*="Archived" i]',
    'button[aria-label*="Arquivadas" i]',
    'button[aria-label*="Archived" i]',
]

MESSAGE_CONTAINER_SELECTOR = 'div[data-testid="msg-container"]'


class ChatStatus(str, Enum):
    campaign_matched = "campaign_matched"
    outbound_other_campaign = "outbound_other_campaign"
    no_outbound = "no_outbound"
    phone_unconfirmed = "phone_unconfirmed"
    chat_unsupported = "chat_unsupported"
    chat_not_changed = "chat_not_changed"
    chat_click_failed = "chat_click_failed"
    suspicious_repeated_phone = "suspicious_repeated_phone"
    error = "error"


@dataclass
class ChatIndexRecord:
    technical_id_raw: str
    technical_id_sanitized: str
    chat_type: str
    status: ChatStatus
    phone_hash: str = ""
    phone_last4: str = ""
    outbound_found: bool = False
    anchor_count: int = 0
    campaign_match: bool = False
    timestamp_technical: str | None = None
    evidence: str = ""
    message_fingerprint: str = ""
    error_message: str = ""
    error_stage: str = ""
    retryable: bool = True
    signature_before: str = ""
    signature_after: str = ""
    card_selected: bool = False
    panel_loaded: bool = False

    def to_persisted_dict(self) -> dict[str, Any]:
        return {
            "phone_hash": self.phone_hash,
            "phone_last4": self.phone_last4,
            "chat_type": self.chat_type,
            "technical_id_sanitized": self.technical_id_sanitized,
            "outbound_found": self.outbound_found,
            "anchor_count": self.anchor_count,
            "campaign_match": self.campaign_match,
            "timestamp_technical": self.timestamp_technical,
        }


@dataclass
class CandidateRecord:
    lead_id_masked: str
    nome: str
    telefone_mascarado: str
    hash_parcial: str
    evidencia_telefone: str
    outbound: bool
    campaign_match: bool
    chat_type: str
    phone_hash: str


@dataclass
class IndexRunStats:
    started_at: str
    finished_at: str = ""
    total_chats_unique: int = 0
    total_rounds: int = 0
    total_scrolls: int = 0
    total_individual: int = 0
    total_groups_ignored: int = 0
    total_status_ignored: int = 0
    total_phone_confirmed: int = 0
    total_outbound: int = 0
    total_campaign_matched: int = 0
    total_candidates: int = 0
    total_errors: int = 0
    elapsed_seconds: float = 0.0
    avg_seconds_per_chat: float = 0.0
    estimated_total_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Utilidades de privacidade / hashing
# ---------------------------------------------------------------------------

def mascarar_telefone(telefone: str | None) -> str:
    if not telefone:
        return ""
    digits = "".join(ch for ch in str(telefone) if ch.isdigit())
    if len(digits) <= 6:
        return digits[:2] + "****" + digits[-2:]
    return digits[:4] + "****" + digits[-4:]


def sanitizar_identificador_tecnico(raw: str | None) -> str:
    if not raw:
        return ""
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"chat:{digest}"


def hash_parcial(valor_hex: str | None, chars: int = 12) -> str:
    if not valor_hex:
        return ""
    return valor_hex[:chars]


def _agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Checkpoint local
# ---------------------------------------------------------------------------

def carregar_checkpoint() -> dict[str, Any]:
    if not CHECKPOINT_FILE.exists():
        return {
            "processed_keys": [],
            "total_processed": 0,
            "last_chat_key": "",
            "updated_at": "",
        }
    try:
        data = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("checkpoint inválido")
        data.setdefault("processed_keys", [])
        data.setdefault("total_processed", 0)
        data.setdefault("last_chat_key", "")
        data.setdefault("updated_at", "")
        return data
    except Exception as exc:
        logger.warning("Erro ao carregar checkpoint: %s", exc)
        return {
            "processed_keys": [],
            "total_processed": 0,
            "last_chat_key": "",
            "updated_at": "",
        }


def salvar_checkpoint(processed_keys: set[str], total_processed: int, last_chat_key: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "processed_keys": sorted(processed_keys),
        "total_processed": total_processed,
        "last_chat_key": last_chat_key,
        "updated_at": _agora_iso(),
    }
    tmp = CHECKPOINT_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CHECKPOINT_FILE)


# ---------------------------------------------------------------------------
# Supabase leitura apenas
# ---------------------------------------------------------------------------

def _get_supabase_client():
    try:
        from supabase import create_client
    except ImportError:
        logger.error("Pacote 'supabase' não instalado")
        return None

    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        try:
            from dotenv import load_dotenv

            load_dotenv(env_path)
        except ImportError:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())

    url = os.environ.get("SUPABASE_URL", "")
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "")
    if not url or not anon_key:
        logger.error("SUPABASE_URL / SUPABASE_ANON_KEY ausentes")
        return None
    return create_client(url, anon_key)


def carregar_leads_eligiveis(limit: int | None = None) -> list[dict[str, Any]]:
    client = _get_supabase_client()
    if not client:
        return []

    query = (
        client.table("leads")
        .select("id,nome,telefone,whatsapp,telefone_normalizado,status")
        .in_("status", ["novo", "pronto_para_enviar"])
        .order("created_at")
    )
    if limit is not None:
        query = query.limit(limit)

    try:
        result = query.execute()
        return result.data if result.data else []
    except Exception as exc:
        logger.error("Erro ao carregar leads elegíveis: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Comparação índice ↔ leads
# ---------------------------------------------------------------------------

def lead_deve_ser_ignorado(nome: str | None) -> bool:
    if not nome:
        return False
    return nome.strip().lower() in EXCLUDED_LEAD_NAMES


def montar_indice_por_hash(records: list[ChatIndexRecord]) -> dict[str, ChatIndexRecord]:
    indice: dict[str, ChatIndexRecord] = {}
    for rec in records:
        if not rec.phone_hash:
            continue
        if rec.chat_type != "individual":
            continue
        if not rec.outbound_found or not rec.campaign_match:
            continue
        indice[rec.phone_hash] = rec
    return indice


def comparar_leads_com_indice(
    records: list[ChatIndexRecord],
    leads: list[dict[str, Any]],
) -> list[CandidateRecord]:
    indice = montar_indice_por_hash(records)
    candidatos: list[CandidateRecord] = []

    for lead in leads:
        nome = str(lead.get("nome", "") or "")
        if lead_deve_ser_ignorado(nome):
            continue

        tel_raw = lead.get("telefone_normalizado") or lead.get("whatsapp") or lead.get("telefone") or ""
        tel_norm = normalizar_telefone_br(str(tel_raw))
        if not tel_norm:
            continue

        tel_hash = canonical_phone_hash(tel_norm)
        rec = indice.get(tel_hash)
        if not rec:
            continue

        lead_id = str(lead.get("id", "") or "")
        candidatos.append(
            CandidateRecord(
                lead_id_masked=(lead_id[:8] + "...") if lead_id else "",
                nome=nome,
                telefone_mascarado=mascarar_telefone(tel_norm),
                hash_parcial=hash_parcial(tel_hash),
                evidencia_telefone=rec.evidence,
                outbound=rec.outbound_found,
                campaign_match=rec.campaign_match,
                chat_type=rec.chat_type,
                phone_hash=tel_hash,
            )
        )

    return candidatos


# ---------------------------------------------------------------------------
# Virtualização / scroll controlado
# ---------------------------------------------------------------------------

def _resolver_chave_card(raw: dict[str, Any]) -> str:
    raw_id = str(raw.get("rawTechnicalId") or "").strip()
    title = str(raw.get("title") or "").strip()
    aria = str(raw.get("ariaLabel") or "").strip()
    data_id = str(raw.get("dataId") or "").strip()
    data_testid = str(raw.get("dataTestid") or "").strip()
    base = " | ".join(x for x in [raw_id, data_id, data_testid, aria, title] if x)
    return sanitizar_identificador_tecnico(base or f"row:{raw.get('rowIndex', 0)}")


async def coletar_chats_visiveis(page) -> list[dict[str, Any]]:
    cards = await page.evaluate(
        """() => {
            const list = document.querySelector('div[data-testid="chat-list"], div[aria-label*="lista de conversas" i], div[aria-label*="chat list" i]');
            if (!list) return [];
            const rows = Array.from(list.querySelectorAll('div[role="row"], div[data-testid="chat-list-item"], div[data-testid="cell-frame-container"], div[tabindex="-1"]'));
            return rows.map((row, rowIndex) => {
                const titleEl = row.querySelector('span[title], div[title], a[title]');
                const title = titleEl ? (titleEl.getAttribute('title') || titleEl.textContent || '') : '';
                const ariaLabel = row.getAttribute('aria-label') || '';
                const dataId = row.getAttribute('data-id') || '';
                const dataTestid = row.getAttribute('data-testid') || '';
                const text = (row.textContent || '').slice(0, 280);
                const hasGroupIcon = !!row.querySelector('[data-testid="group-icon"], [data-testid="community-icon"], [data-testid="channel-icon"], [data-testid="icon-group"], [data-testid="icon-community"], [data-testid="icon-channel"]');
                const tech = [dataId, dataTestid, ariaLabel, title].filter(Boolean).join(' | ');
                const statusHint = /status/i.test([dataId, dataTestid].join(' '));
                return { rowIndex, rawTechnicalId: tech, title, ariaLabel, dataId, dataTestid, text, hasGroupIcon, statusHint };
            });
        }"""
    )
    out: list[dict[str, Any]] = []
    for raw in cards or []:
        item = dict(raw)
        item["chat_key"] = _resolver_chave_card(item)
        item["chat_type_hint"] = "status" if item.get("statusHint") else ("groupish" if item.get("hasGroupIcon") else "individual")
        out.append(item)
    return out


async def scroll_chat_list(page, step: int = SCROLL_STEP) -> bool:
    result = await page.evaluate(
        """(step) => {
            const list = document.querySelector('div[data-testid="chat-list"], div[aria-label*="lista de conversas" i], div[aria-label*="chat list" i]');
            if (!list) return { moved: false, top: null };
            const before = list.scrollTop;
            list.scrollTop = before + step;
            return { moved: list.scrollTop !== before, top: list.scrollTop };
        }""",
        step,
    )
    return bool(result and result.get("moved"))


def deduplicar_cards(cards: list[dict[str, Any]], seen_keys: set[str]) -> list[dict[str, Any]]:
    novos: list[dict[str, Any]] = []
    for card in cards:
        key = str(card.get("chat_key") or "")
        if not key or key in seen_keys:
            continue
        seen_keys.add(key)
        novos.append(card)
    return novos


async def varrer_ate_estabilizar(
    fetch_visible: Callable[[], Awaitable[list[dict[str, Any]]]],
    scroll_next: Callable[[], Awaitable[bool]],
    *,
    limit: int | None = None,
    seen_keys: set[str] | None = None,
    max_idle_rounds: int = MAX_IDLE_ROUNDS,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    seen = seen_keys or set()
    collected: list[dict[str, Any]] = []
    rounds = 0
    scrolls = 0
    idle_rounds = 0

    while True:
        rounds += 1
        visible = await fetch_visible()
        novos = deduplicar_cards(visible, seen)
        if novos:
            collected.extend(novos)
            idle_rounds = 0
        else:
            idle_rounds += 1

        if limit is not None and len(collected) >= limit:
            collected = collected[:limit]
            break

        if idle_rounds >= max_idle_rounds:
            break

        moved = await scroll_next()
        scrolls += 1 if moved else 0
        if not moved and idle_rounds > 0:
            break

    stats = {
        "rounds": rounds,
        "scrolls": scrolls,
        "unique": len(collected),
        "idle_rounds": idle_rounds,
    }
    return collected, stats


# ---------------------------------------------------------------------------
# Conversa aberta: classificação / telefone / campanha
# ---------------------------------------------------------------------------

async def capturar_assinatura_chat_ativo(page) -> str:
    """Gera assinatura SHA-256 do chat ativo usando sinais do #main."""
    try:
        sinais = await page.evaluate(
            """() => {
                const main = document.querySelector('#main');
                if (!main) return [];

                const signals = [];

                const headerInMain = main.querySelector('header');
                if (headerInMain) {
                    const hTitle = headerInMain.getAttribute('title') || '';
                    const hAria = headerInMain.getAttribute('aria-label') || '';
                    const hDataId = headerInMain.getAttribute('data-id') || '';
                    signals.push('h:' + [hAria, hTitle, hDataId].filter(Boolean).join('|'));
                }

                const msgs = main.querySelectorAll('[data-id]');
                const msgIds = [];
                for (const m of msgs) {
                    const d = m.getAttribute('data-id');
                    if (d && d.length > 4) msgIds.push(d);
                }
                if (msgIds.length > 0) {
                    signals.push('m1:' + msgIds[0]);
                    signals.push('mN:' + msgIds[msgIds.length - 1]);
                }

                const contactEls = main.querySelectorAll(
                    '[data-testid="conversation-header"], '
                    + '[data-testid="conversation-info-header"]'
                );
                for (const el of contactEls) {
                    const id = el.getAttribute('data-id') || '';
                    const aria = el.getAttribute('aria-label') || '';
                    if (id || aria) signals.push('c:' + (id || aria));
                }

                const selected = document.querySelector(
                    '[aria-selected="true"], '
                    + '[data-testid="chat-list-item"][aria-current], '
                    + 'div[role="row"][aria-selected="true"]'
                );
                if (selected) {
                    const sId = selected.getAttribute('data-id') || '';
                    const sAria = selected.getAttribute('aria-label') || '';
                    signals.push('sel:' + (sId || sAria));
                }

                return signals;
            }"""
        )

        if not sinais:
            return ""
        raw = "||".join(str(s) for s in sinais)
        return "sig:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    except Exception:
        return ""


async def aguardar_troca_chat(page, prev_signature: str, timeout_ms: int = CHANGE_TIMEOUT_MS) -> bool:
    """Aguarda assinatura do #main mudar após clique em novo chat."""
    import asyncio as _asyncio
    deadline = _asyncio.get_event_loop().time() + timeout_ms / 1000.0
    while _asyncio.get_event_loop().time() < deadline:
        current = await capturar_assinatura_chat_ativo(page)
        if not prev_signature and current:
            return True
        if current and current != prev_signature:
            return True
        await page.wait_for_timeout(250)
    return False


async def _fechar_painel_info_se_aberto(page) -> None:
    """Fecha painel de informações se estiver aberto (vestígio do chat anterior)."""
    try:
        close_btns = page.locator(
            'button[aria-label*="Fechar" i], '
            'button[aria-label*="Close" i], '
            'div[role="button"][aria-label*="close" i]'
        )
        count = await close_btns.count()
        for i in range(min(count, 3)):
            try:
                await close_btns.nth(i).click(timeout=2000)
                await page.wait_for_timeout(300)
            except Exception:
                pass
    except Exception:
        pass
    # fallback: Escape para fechar painéis
    try:
        keyboard = getattr(page, "keyboard", None)
        if keyboard and hasattr(keyboard, "press"):
            await keyboard.press("Escape")
            await page.wait_for_timeout(200)
    except Exception:
        pass


async def classificar_conversa_aberta(page) -> str:
    try:
        tipo_grupo = await detectar_grupo(page)
        if tipo_grupo:
            return tipo_grupo
    except Exception:
        pass

    try:
        url = str(getattr(page, "url", "") or "").lower()
        if "/status" in url:
            return "status"
    except Exception:
        pass

    return "individual"


async def _abrir_painel_info(page) -> None:
    header_selector = await encontrar_seletor_rapido(page, CONVERSATION_HEADER_SELECTORS, timeout=TIMEOUT_RAPIDO)
    if not header_selector:
        return
    try:
        await page.locator(header_selector).first.click(timeout=5000)
        await page.wait_for_timeout(500)
    except Exception:
        pass


async def extrair_telefone_da_conversa(page) -> tuple[Optional[str], str]:
    """Extrai telefone do chat ATUAL, com escopo restrito para evitar vestígios."""
    # Fecha painel antigo, abre o do chat atual
    await _fechar_painel_info_se_aberto(page)
    await _abrir_painel_info(page)

    # 1) JID no main/conversation panel - escopo restrito
    try:
        jid_elements = page.locator(
            '#main [data-id*="@s.whatsapp.net"], '
            '[data-testid="conversation-panel-wrapper"] [data-id*="@s.whatsapp.net"]'
        )
        count = await jid_elements.count()
        for i in range(count):
            el = jid_elements.nth(i)
            raw = None
            for attr in ("data-id",):
                try:
                    raw = await el.get_attribute(attr)
                except Exception:
                    pass
            telefone = normalizar_telefone_br(raw or "")
            if telefone:
                return telefone, "jid"
    except Exception:
        pass

    # 2) telefone no painel lateral (info drawer) apenas
    try:
        drawer_els = page.locator(
            '[data-testid="contact-info"], '
            '[data-testid*="drawer" i] [data-id], '
            'section[data-testid*="contact"] [data-id]'
        )
        count = await drawer_els.count()
        for i in range(count):
            el = drawer_els.nth(i)
            raw = None
            for attr in ("data-id", "aria-label", "title"):
                try:
                    raw = await el.get_attribute(attr)
                except Exception:
                    pass
            telefone = normalizar_telefone_br(raw or "")
            if telefone:
                return telefone, f"drawer:{attr}"
    except Exception:
        pass

    # 3) link tel: no painel lateral
    try:
        tel_links = page.locator(
            '[data-testid="contact-info"] a[href*="tel:"], '
            'section[data-testid*="contact"] a[href*="tel:"]'
        )
        count = await tel_links.count()
        for i in range(count):
            href = await tel_links.nth(i).get_attribute("href")
            telefone = normalizar_telefone_br((href or "").replace("tel:", ""))
            if telefone:
                return telefone, "tel_link"
    except Exception:
        pass

    # 4) painel de informações (seletores específicos)
    try:
        for selector in PHONE_IN_PROFILE_SELECTORS:
            try:
                count = await page.locator(selector).count()
            except Exception:
                count = 0
            for i in range(count):
                el = page.locator(selector).nth(i)
                raw = await el.get_attribute("title")
                if not raw:
                    raw = await el.text_content()
                telefone = normalizar_telefone_br(raw or "")
                if telefone:
                    return telefone, "info_panel"
    except Exception:
        pass

    return None, "phone_unconfirmed"


async def detectar_outbound_campanha(page, campaign_key: str) -> tuple[bool, str, Optional[str], str, int]:
    frases = chaves_estaveis_da_campanha(campaign_key)
    if not frases:
        frases = []

    try:
        locator = page.locator(MESSAGE_CONTAINER_SELECTOR)
        count = await locator.count()
    except Exception:
        return False, ChatStatus.no_outbound.value, None, "", 0

    outbound_seen = 0
    first_other_timestamp: Optional[str] = None
    first_other_fingerprint = ""
    first_other_anchor_count = 0

    for i in range(count - 1, -1, -1):
        if outbound_seen >= MAX_OUTBOUND_SCAN:
            break
        msg = locator.nth(i)
        try:
            texto = await msg.text_content()
        except Exception:
            continue
        if not texto or not texto.startswith("tail-out"):
            continue

        outbound_seen += 1
        corpo = texto[len("tail-out"):].strip()
        timestamp = None
        try:
            ts = await msg.get_attribute("data-timestamp")
            if ts:
                timestamp = datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
        except Exception:
            timestamp = None

        norma = normalizar_texto(corpo)
        anchor_count = sum(1 for frase in frases if frase in norma) if frases else 0
        fp = fingerprint_mensagem(corpo)
        match = corresponde_campanha(corpo, campaign_key)

        if match:
            return True, ChatStatus.campaign_matched.value, timestamp, fp, anchor_count

        if first_other_timestamp is None:
            first_other_timestamp = timestamp
            first_other_fingerprint = fp
            first_other_anchor_count = anchor_count

    if outbound_seen > 0:
        return True, ChatStatus.outbound_other_campaign.value, first_other_timestamp, first_other_fingerprint, first_other_anchor_count

    return False, ChatStatus.no_outbound.value, None, "", 0


async def _fechar_contexto_chat(page) -> None:
    try:
        await limpar_campo_busca(page)
    except Exception:
        pass
    try:
        keyboard = getattr(page, "keyboard", None)
        if keyboard and hasattr(keyboard, "press"):
            await keyboard.press("Escape")
        elif hasattr(page, "keyboard_press"):
            await page.keyboard_press("Escape")
    except Exception:
        pass


async def abrir_chat_por_indice(page, row_index: int) -> bool:
    """Clica no card da lista pelo indice visual e aguarda o painel #main comecar a carregar."""
    try:
        resultado = await page.evaluate(
            """(rowIndex) => {
                const list = document.querySelector(
                    'div[data-testid="chat-list"], '
                    + 'div[aria-label*="lista de conversas" i], '
                    + 'div[aria-label*="chat list" i]'
                );
                if (!list) return false;
                const rows = Array.from(list.querySelectorAll(
                    'div[role="row"], '
                    + 'div[data-testid="chat-list-item"], '
                    + 'div[data-testid="cell-frame-container"], '
                    + 'div[tabindex="-1"]'
                ));
                const row = rows[rowIndex];
                if (!row) return false;

                const clickTarget = row.querySelector(
                    '[role="button"], '
                    + '[data-testid="chat-list-item"] > div, '
                    + 'div[tabindex="0"]'
                ) || row;

                const ev = { bubbles: true, cancelable: true, view: window };
                clickTarget.dispatchEvent(new MouseEvent('mousedown', ev));
                clickTarget.dispatchEvent(new MouseEvent('mouseup', ev));
                clickTarget.dispatchEvent(new MouseEvent('click', ev));
                if (typeof clickTarget.click === 'function') clickTarget.click();
                return true;
            }""",
            row_index,
        )
        if resultado:
            await page.wait_for_timeout(800)
        return bool(resultado)
    except Exception:
        return False


async def processar_card(page, card: dict[str, Any], campaign_key: str, diagnostic_dir: Path) -> ChatIndexRecord:
    raw_tech = str(card.get("rawTechnicalId") or "")
    tech_sanitized = str(card.get("chat_key") or sanitizar_identificador_tecnico(raw_tech))
    row_index = int(card.get("rowIndex") or 0)
    chat_type_hint = str(card.get("chat_type_hint") or "individual")

    # --- ZERAR ESTADO entre iterações ---
    telefone_extraido: Optional[str] = None
    phone_hash_local: str = ""
    phone_last4_local: str = ""
    evidence_local: str = ""
    outbound_found_local: bool = False
    anchor_count_local: int = 0
    campaign_match_local: bool = False
    signature_before: str = ""
    signature_after: str = ""
    card_selected: bool = False
    panel_loaded: bool = False

    try:
        # 1) Fechar painel de informacoes antigo
        await _fechar_painel_info_se_aberto(page)

        # 2) Capturar assinatura do chat ATUAL antes de clicar
        signature_before = await capturar_assinatura_chat_ativo(page)

        # 3) Clicar no card alvo
        if not await abrir_chat_por_indice(page, row_index):
            return ChatIndexRecord(
                technical_id_raw=raw_tech,
                technical_id_sanitized=tech_sanitized,
                chat_type=chat_type_hint,
                status=ChatStatus.chat_click_failed,
                error_message="clique no card nao foi executado",
                error_stage="abrir_chat",
                retryable=True,
                signature_before=signature_before,
            )

        # 4) Aguardar troca real do chat
        if not await aguardar_troca_chat(page, signature_before):
            return ChatIndexRecord(
                technical_id_raw=raw_tech,
                technical_id_sanitized=tech_sanitized,
                chat_type=chat_type_hint,
                status=ChatStatus.chat_not_changed,
                error_message="assinatura do chat nao mudou apos clique",
                error_stage="aguardar_troca",
                retryable=True,
                signature_before=signature_before,
            )

        # 5) Capturar assinatura pos-clique e validar
        signature_after = await capturar_assinatura_chat_ativo(page)

        # Verificar estado do card
        try:
            card_sel = await page.evaluate(
                """() => {
                    const sel = document.querySelector('[aria-selected="true"], div[role="row"][aria-selected="true"]');
                    return !!sel;
                }"""
            )
            card_selected = bool(card_sel)
        except Exception:
            card_selected = False

        # Verificar se #main carregou conteudo
        try:
            pl = await page.evaluate(
                """() => {
                    const main = document.querySelector('#main');
                    if (!main) return false;
                    const msgs = main.querySelectorAll('[data-id]');
                    return msgs.length > 0;
                }"""
            )
            panel_loaded = bool(pl)
        except Exception:
            panel_loaded = False

        # Validar troca: primeiro chat ou assinatura diferente
        troca_ok = (not signature_before and signature_after) or (signature_after and signature_after != signature_before)
        if not troca_ok:
            return ChatIndexRecord(
                technical_id_raw=raw_tech,
                technical_id_sanitized=tech_sanitized,
                chat_type=chat_type_hint,
                status=ChatStatus.chat_not_changed,
                error_message="assinatura nao alterou; possivel clique em chat ja aberto",
                error_stage="validar_troca",
                retryable=True,
                signature_before=signature_before,
                signature_after=signature_after,
                card_selected=card_selected,
                panel_loaded=panel_loaded,
            )

        await _fechar_modal(page)
        chat_type = await classificar_conversa_aberta(page)
        if chat_type != "individual":
            return ChatIndexRecord(
                technical_id_raw=raw_tech,
                technical_id_sanitized=tech_sanitized,
                chat_type=chat_type,
                status=ChatStatus.chat_unsupported,
                signature_before=signature_before,
                signature_after=signature_after,
                card_selected=card_selected,
                panel_loaded=panel_loaded,
            )

        telefone, evidence_local = await extrair_telefone_da_conversa(page)
        if not telefone:
            return ChatIndexRecord(
                technical_id_raw=raw_tech,
                technical_id_sanitized=tech_sanitized,
                chat_type=chat_type,
                status=ChatStatus.phone_unconfirmed,
                evidence=evidence_local,
                signature_before=signature_before,
                signature_after=signature_after,
                card_selected=card_selected,
                panel_loaded=panel_loaded,
            )

        telefone_extraido = telefone
        phone_hash_local = hash_telefone_canonico(telefone)
        phone_last4_local = telefone[-4:]

        outbound_found_local, status, timestamp, fp, anchor_count_local = await detectar_outbound_campanha(page, campaign_key)
        campaign_match_local = (status == ChatStatus.campaign_matched.value)

        record = ChatIndexRecord(
            technical_id_raw=raw_tech,
            technical_id_sanitized=tech_sanitized,
            chat_type=chat_type,
            status=ChatStatus(status),
            phone_hash=phone_hash_local,
            phone_last4=phone_last4_local,
            outbound_found=outbound_found_local,
            anchor_count=anchor_count_local,
            campaign_match=campaign_match_local,
            timestamp_technical=timestamp,
            evidence=evidence_local,
            message_fingerprint=fp if fp else "",
            error_stage="ok",
            signature_before=signature_before,
            signature_after=signature_after,
            card_selected=card_selected,
            panel_loaded=panel_loaded,
        )

        return record

    except Exception as exc:
        exc_name = type(exc).__name__
        exc_msg = str(exc)[:240]
        try:
            await capturar_diagnostico(page, diagnostic_dir, prefixo=f"index_{tech_sanitized[:10]}")
        except Exception:
            pass
        return ChatIndexRecord(
            technical_id_raw=raw_tech,
            technical_id_sanitized=tech_sanitized,
            chat_type=chat_type_hint,
            status=ChatStatus.error,
            error_message=f"{exc_name}: {exc_msg}",
            error_stage="exception",
            retryable=True,
            signature_before=signature_before,
            signature_after=signature_after,
            card_selected=card_selected,
            panel_loaded=panel_loaded,
        )
    finally:
        try:
            await _fechar_contexto_chat(page)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Playwright / browser
# ---------------------------------------------------------------------------

async def abrir_contexto_whatsapp():
    from playwright.async_api import async_playwright

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    p = await async_playwright().start()
    context = await p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR.resolve()),
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )

    page = None
    for existing in context.pages:
        if "web.whatsapp.com" in getattr(existing, "url", ""):
            page = existing
            break
    if page is None:
        page = await context.new_page()
        await page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

    for existing in list(context.pages):
        if existing is not page and getattr(existing, "url", "") == "about:blank":
            try:
                await existing.close()
            except Exception:
                pass

    return p, context, page


async def aguardar_chat_list(page, timeout_ms: int = 180000) -> bool:
    for selector in CHAT_LIST_SELECTORS:
        try:
            await page.wait_for_selector(selector, timeout=timeout_ms)
            return True
        except Exception:
            continue
    return False


async def tentar_arquivadas(page) -> bool:
    for selector in ARCHIVE_BUTTON_SELECTORS:
        try:
            loc = page.locator(selector).first
            if await loc.count() > 0:
                await loc.click(timeout=5000)
                await page.wait_for_timeout(1000)
                return True
        except Exception:
            continue
    return False


def _acumular_stats(stats: IndexRunStats, result: ChatIndexRecord) -> None:
    if result.chat_type == "individual":
        stats.total_individual += 1
    elif result.chat_type in {"group", "channel", "community"}:
        stats.total_groups_ignored += 1
    elif result.chat_type == "status":
        stats.total_status_ignored += 1

    if result.status in (ChatStatus.phone_unconfirmed, ChatStatus.chat_not_changed, ChatStatus.chat_click_failed):
        stats.total_status_ignored += 1
    elif result.status == ChatStatus.error:
        stats.total_errors += 1

    if result.phone_hash:
        stats.total_phone_confirmed += 1
    if result.outbound_found:
        stats.total_outbound += 1
    if result.campaign_match:
        stats.total_campaign_matched += 1


async def indexar_conversas_whatsapp(
    *,
    limit: int | None = None,
    resume: bool = True,
    campaign_key: str = PRIMEIRO_CONTATO_V1,
    include_archived: bool = True,
) -> tuple[list[ChatIndexRecord], list[dict[str, Any]], IndexRunStats]:
    if not validar_campaign_key(campaign_key):
        raise ValueError(f"campaign_key inválida: {campaign_key}")

    checkpoint = carregar_checkpoint() if resume else {
        "processed_keys": [],
        "total_processed": 0,
        "last_chat_key": "",
        "updated_at": "",
    }
    processed_keys: set[str] = set(checkpoint.get("processed_keys", []))
    scan_seen_keys: set[str] = set(processed_keys)

    started_at = _agora_iso()
    stats = IndexRunStats(started_at=started_at)
    records: list[ChatIndexRecord] = []
    raw_cards_all: list[dict[str, Any]] = []
    total_processed = int(checkpoint.get("total_processed", 0) or 0)
    last_chat_key = str(checkpoint.get("last_chat_key", "") or "")
    t0 = time.time()
    diagnostic_dir = OUTPUT_DIR / "diagnosticos"

    p = context = page = None
    try:
        p, context, page = await abrir_contexto_whatsapp()
        if not await aguardar_chat_list(page):
            raise RuntimeError("lista de chats não encontrada / WhatsApp não autenticado")

        async def fetch_visible():
            return await coletar_chats_visiveis(page)

        async def scroll_next():
            moved = await scroll_chat_list(page, step=SCROLL_STEP)
            await page.wait_for_timeout(SCROLL_PAUSE_MS)
            return moved

        idle_rounds = 0
        round_no = 0
        while True:
            round_no += 1
            visible = await fetch_visible()
            novos = deduplicar_cards(visible, scan_seen_keys)
            stats.total_rounds = round_no
            if novos:
                idle_rounds = 0
            else:
                idle_rounds += 1

            for card in novos:
                if limit is not None and len(records) >= limit:
                    break

                raw_cards_all.append(card)
                result = await processar_card(page, card, campaign_key, diagnostic_dir)
                records.append(result)

                # Proteção: detectar telefone repetido suspeito (3+ consecutivos com mesmo hash)
                if result.phone_hash and result.chat_type == "individual":
                    ultimos = [r for r in records[-4:-1] if r.chat_type == "individual" and r.phone_hash]
                    if len(ultimos) >= 2:
                        todos_iguais = all(r.phone_hash == result.phone_hash for r in ultimos)
                        if todos_iguais:
                            logger.warning(
                                "suspicious_repeated_phone: %d chats consecutivos com hash=%s... "
                                "(último: %s)",
                                len(ultimos) + 1,
                                result.phone_hash[:16],
                                result.technical_id_sanitized,
                            )
                            if len(ultimos) >= 3:
                                result.status = ChatStatus.suspicious_repeated_phone
                                result.error_message = (
                                    f"telefone repetido em {len(ultimos) + 1} chats consecutivos - "
                                    "possível vestígio de chat anterior"
                                )
                                result.error_stage = "suspicious_repeat"
                                result.retryable = False
                total_processed += 1
                last_chat_key = result.technical_id_sanitized
                processed_keys.add(last_chat_key)
                salvar_checkpoint(processed_keys, total_processed, last_chat_key)
                _acumular_stats(stats, result)

            if limit is not None and len(records) >= limit:
                break

            if idle_rounds >= MAX_IDLE_ROUNDS:
                break

            moved = await scroll_next()
            if moved:
                stats.total_scrolls += 1
            else:
                idle_rounds += 1
                if idle_rounds >= MAX_IDLE_ROUNDS:
                    break

        if include_archived:
            # best effort: tenta as arquivadas uma única vez, se houver botão.
            try:
                if await tentar_arquivadas(page):
                    visible = await fetch_visible()
                    novos = deduplicar_cards(visible, scan_seen_keys)
                    for card in novos:
                        if limit is not None and len(records) >= limit:
                            break
                        raw_cards_all.append(card)
                        result = await processar_card(page, card, campaign_key, diagnostic_dir)
                        records.append(result)
                        total_processed += 1
                        last_chat_key = result.technical_id_sanitized
                        processed_keys.add(last_chat_key)
                        salvar_checkpoint(processed_keys, total_processed, last_chat_key)
                        _acumular_stats(stats, result)
            except Exception:
                pass

    finally:
        try:
            if context is not None:
                await context.close()
        except Exception:
            pass
        try:
            if p is not None:
                await p.stop()
        except Exception:
            pass

    stats.finished_at = _agora_iso()
    stats.total_chats_unique = len(records)
    if records:
        stats.elapsed_seconds = time.time() - t0
        stats.avg_seconds_per_chat = stats.elapsed_seconds / max(len(records), 1)
        stats.estimated_total_seconds = stats.avg_seconds_per_chat * max(len(records), 1)
    else:
        stats.elapsed_seconds = time.time() - t0

    return records, raw_cards_all, stats


# ---------------------------------------------------------------------------
# Relatórios locais sanitizados
# ---------------------------------------------------------------------------

def gerar_relatorios_locais(
    records: list[ChatIndexRecord],
    raw_cards: list[dict[str, Any]],
    candidates: list[CandidateRecord],
    stats: IndexRunStats,
    run_id: str,
) -> dict[str, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    run_dir = OUTPUT_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    index_jsonl = run_dir / "indice_conversas.jsonl"
    with index_jsonl.open("w", encoding="utf-8", newline="") as f:
        for rec in records:
            f.write(json.dumps(rec.to_persisted_dict(), ensure_ascii=False) + "\n")

    candidatos_csv = run_dir / "candidatos.csv"
    with candidatos_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "lead_id_masked",
            "nome",
            "telefone_mascarado",
            "hash_parcial",
            "evidencia_telefone",
            "outbound",
            "campaign_match",
            "chat_type",
        ])
        for c in candidates:
            writer.writerow([
                c.lead_id_masked,
                c.nome,
                c.telefone_mascarado,
                c.hash_parcial,
                c.evidencia_telefone,
                "sim" if c.outbound else "nao",
                "sim" if c.campaign_match else "nao",
                c.chat_type,
            ])

    resumo = {
        "run_id": run_id,
        "started_at": stats.started_at,
        "finished_at": stats.finished_at,
        "total_chats_percorridos": stats.total_chats_unique,
        "conversas_individuais": sum(1 for r in records if r.chat_type == "individual"),
        "grupos_canais_comunidades_ignorados": sum(1 for r in records if r.chat_type in {"group", "channel", "community"}),
        "status_ignorados": sum(1 for r in records if r.status == ChatStatus.phone_unconfirmed),
        "telefones_confirmados": stats.total_phone_confirmed,
        "chats_com_outbound": stats.total_outbound,
        "chats_com_campanha_avgestao": stats.total_campaign_matched,
        "leads_encontrados_no_supabase": len(candidates),
        "candidatos_para_apply": len(candidates),
        "erros": stats.total_errors,
        "tempo_total_segundos": round(stats.elapsed_seconds, 2),
        "tempo_medio_por_conversa_segundos": round(stats.avg_seconds_per_chat, 2),
        "estimativa_total_segundos": round(stats.estimated_total_seconds, 2),
        "records": [
            {
                "technical_id_sanitized": r.technical_id_sanitized,
                "chat_type": r.chat_type,
                "status": r.status.value,
                "phone_last4": r.phone_last4,
                "phone_hash_parcial": hash_parcial(r.phone_hash),
                "outbound_found": r.outbound_found,
                "anchor_count": r.anchor_count,
                "campaign_match": r.campaign_match,
                "timestamp_technical": r.timestamp_technical,
                "evidence": r.evidence,
            }
            for r in records
        ],
        "candidates": [asdict(c) for c in candidates],
    }

    resumo_json = run_dir / "resumo.json"
    resumo_json.write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "index_jsonl": index_jsonl,
        "candidatos_csv": candidatos_csv,
        "resumo_json": resumo_json,
    }


# ---------------------------------------------------------------------------
# Execução principal
# ---------------------------------------------------------------------------

async def executar(
    *,
    limit: int = DEFAULT_LIMIT,
    resume: bool = True,
    campaign_key: str = PRIMEIRO_CONTATO_V1,
) -> int:
    run_id = f"reverse_index_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info("=" * 72)
    logger.info("Indexação reversa de conversas do WhatsApp")
    logger.info("Run: %s", run_id)
    logger.info("Limit: %s | Resume: %s | Campaign: %s", limit, resume, campaign_key)
    logger.info("=" * 72)

    records, raw_cards, stats = await indexar_conversas_whatsapp(
        limit=limit,
        resume=resume,
        campaign_key=campaign_key,
    )

    leads = carregar_leads_eligiveis()
    candidatos = comparar_leads_com_indice(records, leads)
    stats.total_candidates = len(candidatos)

    relatorios = gerar_relatorios_locais(records, raw_cards, candidatos, stats, run_id)

    logger.info("Total de chats únicos: %d", stats.total_chats_unique)
    logger.info("Conversa individuais: %d", sum(1 for r in records if r.chat_type == "individual"))
    logger.info("Grupos/canais/comunidades ignorados: %d", sum(1 for r in records if r.chat_type in {"group", "channel", "community"}))
    logger.info("Telefones confirmados: %d", stats.total_phone_confirmed)
    logger.info("Chats com outbound: %d", stats.total_outbound)
    logger.info("Chats com campanha AVGESTÃO: %d", stats.total_campaign_matched)
    logger.info("Leads encontrados no Supabase: %d", len(candidatos))
    logger.info("Candidatos para apply: %d", len(candidatos))
    logger.info("Erros: %d", stats.total_errors)
    logger.info("Relatórios: %s", relatorios["resumo_json"].parent)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Indexa conversas do WhatsApp Web e cruza com leads elegíveis do Supabase sem escrever nada.",
    )
    parser.add_argument("--dry-run", action="store_true", default=True, help="Mantido por compatibilidade; o script é somente leitura.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"Máximo de conversas a processar (padrão: {DEFAULT_LIMIT}).")
    parser.add_argument("--resume", action="store_true", default=True, help="Retoma do checkpoint local do indexador.")
    parser.add_argument("--campaign-key", default=PRIMEIRO_CONTATO_V1, help=f"Campaign key (padrão: {PRIMEIRO_CONTATO_V1}).")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not validar_campaign_key(args.campaign_key):
        logger.error("campaign_key inválida: %s", args.campaign_key)
        return 2

    with LockWhatsAppMatch() as lock:
        if not lock.acquired:
            logger.error("Já existe uma execução ativa do fluxo WhatsApp.")
            return 1
        return asyncio.run(
            executar(
                limit=args.limit,
                resume=args.resume,
                campaign_key=args.campaign_key,
            )
        )


if __name__ == "__main__":
    raise SystemExit(main())
