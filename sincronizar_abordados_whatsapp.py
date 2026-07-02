#!/usr/bin/env python3
"""
sincronizar_abordados_whatsapp.py — Sincronização retroativa WhatsApp Web → Supabase.

Lê leads não-confirmados, pesquisa cada telefone no WhatsApp Web (perfil próprio
profiles/whatsapp_match), procura bolha de mensagem de saída, faz fingerprint
contra a campanha atual, e só confirma com correspondência via RPC.

Padrão: --dry-run (zero escrita no Supabase).
--apply: atualiza Supabase (requer SUPABASE_SERVICE_ROLE_KEY no .env).
--reconcile: reavalia needs_reconciliation.

NUNCA envia mensagens. Apenas leitura do WhatsApp.

Requer para --dry-run:
  SUPABASE_URL, SUPABASE_ANON_KEY

Requer para --apply:
  SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Configura logging antes de qualquer import
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sincronizador")

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from config.lock_whatsapp_match import LockWhatsAppMatch
from utils.campaign_key import PRIMEIRO_CONTATO_V1, validar_campaign_key
from utils.phone_utils import normalizar_telefone_br
from whatsapp_match import (
    MatchStatus,
    fazer_match_completo,
)

# ============================================================
# CONSTANTES
# ============================================================

PROFILE_DIR = Path("profiles/whatsapp_match")
OUTPUT_DIR = Path("output/avgestao/sincronizador")
CHECKPOINT_FILE = OUTPUT_DIR / "checkpoint.json"
DEFAULT_LIMIT = 20
INTERVALO_MIN = 3  # segundos entre pesquisas
INTERVALO_MAX = 7


# ============================================================
# SUPABASE CLIENT (leitura de leads)
# ============================================================

def _get_supabase_client():
    """Retorna cliente Supabase com anon key para leitura de leads."""
    try:
        from supabase import create_client
    except ImportError:
        logger.error("Pacote 'supabase' não instalado. pip install supabase")
        return None

    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
        except ImportError:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, _, v = line.partition("=")
                        os.environ.setdefault(k.strip(), v.strip())

    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_ANON_KEY", "")
    if not url or not key:
        logger.error("SUPABASE_URL e SUPABASE_ANON_KEY não encontrados no .env")
        return None

    return create_client(url, key)


def _rpc_exists(client, rpc_name: str) -> bool:
    """Verifica se uma RPC existe no Supabase (tolerante a pre-migration)."""
    try:
        result = client.rpc(rpc_name, {"p_phone_normalized": "0", "p_campaign_key": "x"}).execute()
        return True
    except Exception:
        return False


def carregar_leads_nao_abordados(
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
    campaign_key: str = PRIMEIRO_CONTATO_V1,
) -> list[dict[str, Any]]:
    """
    Carrega leads que ainda não foram confirmados como abordados.

    Filtra por status 'novo' ou 'pronto_para_enviar'.
    Em dry-run, não depende de lead_outreach (pode não existir).

    Args:
        limit: Máximo de leads
        offset: Deslocamento
        campaign_key: Chave da campanha

    Returns:
        Lista de leads
    """
    client = _get_supabase_client()
    if not client:
        return []

    try:
        result = (
            client.table("leads")
            .select("id,nome,telefone,whatsapp,telefone_normalizado,cidade,bairro,categoria,nicho,produto,grupo,status")
            .in_("status", ["novo", "pronto_para_enviar"])
            .limit(limit)
            .offset(offset)
            .order("created_at")
            .execute()
        )
        leads = result.data if result.data else []
        logger.info("Carregados %d leads não abordados (offset=%d)", len(leads), offset)
        return leads
    except Exception as e:
        logger.error("Erro ao carregar leads: %s", e)
        return []


def carregar_leads_para_reconciliar(
    limit: int = DEFAULT_LIMIT,
    campaign_key: str = PRIMEIRO_CONTATO_V1,
) -> list[dict[str, Any]]:
    """
    Carrega leads em estado needs_reconciliation para reavaliação.

    Se a tabela lead_outreach não existir (pré-migration), retorna vazio.

    Args:
        limit: Máximo de leads
        campaign_key: Chave da campanha

    Returns:
        Lista de leads
    """
    client = _get_supabase_client()
    if not client:
        return []

    try:
        # Tenta acessar lead_outreach — se não existir, retorna vazio
        result = (
            client.table("lead_outreach")
            .select("lead_id,phone_normalized,campaign_key,status")
            .eq("status", "needs_reconciliation")
            .eq("campaign_key", campaign_key)
            .limit(limit)
            .execute()
        )
        if not result.data:
            return []

        lead_ids = [r["lead_id"] for r in result.data if r.get("lead_id")]
        if not lead_ids:
            return []

        leads_result = (
            client.table("leads")
            .select("id,nome,telefone,whatsapp,telefone_normalizado,cidade,bairro,categoria,nicho,produto,grupo,status")
            .in_("id", lead_ids)
            .execute()
        )
        return leads_result.data if leads_result.data else []
    except Exception as e:
        logger.info("lead_outreach ainda não disponível (pré-migration): %s", e)
        return []


# ============================================================
# CHECKPOINT
# ============================================================

def salvar_checkpoint(dados: dict) -> None:
    """Salva checkpoint para resume."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CHECKPOINT_FILE.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(CHECKPOINT_FILE)
    except Exception as e:
        logger.warning("Erro ao salvar checkpoint: %s", e)


def carregar_checkpoint() -> Optional[dict]:
    """Carrega checkpoint salvo."""
    if CHECKPOINT_FILE.exists():
        try:
            return json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Erro ao carregar checkpoint: %s", e)
    return None


# ============================================================
# RELATÓRIOS
# ============================================================

def gerar_relatorios(
    resultados: list[Any],
    run_id: str,
    dry_run: bool,
) -> dict[str, Path]:
    """
    Gera CSVs e JSON de resumo dos resultados.

    Args:
        resultados: Lista de MatchResult
        run_id: Identificador da execução
        dry_run: Se True, indica dry-run no nome dos arquivos

    Returns:
        Dict com caminhos dos arquivos gerados
    """
    prefixo = "dryrun" if dry_run else "apply"
    run_dir = OUTPUT_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # CSV de matches
    matches_path = run_dir / f"{prefixo}_matches.csv"
    with open(matches_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "lead_id", "telefone_mascarado", "status", "chat_encontrado",
            "mensagem_saida", "campaign_match", "timestamp",
            "motivo",
        ])
        for r in resultados:
            tel_mask = _mascarar(r.phone_normalized) if r.phone_normalized else ""
            writer.writerow([
                r.lead_id,
                tel_mask,
                r.status.value,
                "sim" if r.chat_found else "nao",
                "sim" if r.outbound_found else "nao",
                "sim" if r.campaign_match else "nao" if r.campaign_match is False else "n/a",
                r.message_timestamp or "",
                r.error_message or r.status.name,
            ])

    # JSON de resumo
    resumo = {
        "run_id": run_id,
        "dry_run": dry_run,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total": len(resultados),
        "matches": sum(1 for r in resultados if r.status == MatchStatus.MATCHED),
        "ambiguous": sum(1 for r in resultados if r.status == MatchStatus.AMBIGUOUS),
        "no_outbound": sum(1 for r in resultados if r.status == MatchStatus.NO_OUTBOUND),
        "no_chat": sum(1 for r in resultados if r.status == MatchStatus.NO_CHAT),
        "groups": sum(1 for r in resultados if r.status in (MatchStatus.GROUP, MatchStatus.CHANNEL, MatchStatus.COMMUNITY)),
        "errors": sum(1 for r in resultados if r.status == MatchStatus.ERROR),
        "resultados": [
            {
                "lead_id": r.lead_id,
                "telefone_mascarado": _mascarar(r.phone_normalized) if r.phone_normalized else "",
                "status": r.status.value,
                "campaign_match": r.campaign_match,
            }
            for r in resultados
        ],
    }
    resumo_path = run_dir / f"{prefixo}_resumo.json"
    with open(resumo_path, "w", encoding="utf-8") as f:
        json.dump(resumo, f, indent=2, ensure_ascii=False)

    return {
        "matches_csv": matches_path,
        "resumo_json": resumo_path,
    }


def _mascarar(telefone: str) -> str:
    """Mascara telefone mantendo DDD e últimos 4 dígitos."""
    if not telefone:
        return ""
    digitos = "".join(c for c in str(telefone) if c.isdigit())
    if len(digitos) <= 6:
        return digitos[:2] + "****" + digitos[-2:]
    return digitos[:4] + "****" + digitos[-4:]


# ============================================================
# PLAYWRIGHT SETUP
# ============================================================

async def setup_playwright():
    """Inicializa o Playwright com perfil persistente dedicado."""
    from playwright.async_api import async_playwright

    p = await async_playwright().start()
    profile_path = str(PROFILE_DIR.resolve())

    # Garante que o diretório do perfil existe
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    context = await p.chromium.launch_persistent_context(
        user_data_dir=profile_path,
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
        ],
    )

    page = await context.new_page()
    await page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

    # Aguarda QR code ou login
    try:
        await page.wait_for_selector('div[data-testid="chat-list"]', timeout=120000)
        logger.info("WhatsApp Web carregado com sessão ativa")
    except Exception:
        logger.info("Aguardando QR code...")
        try:
            await page.wait_for_selector('div[data-testid="chat-list"]', timeout=240000)
            logger.info("WhatsApp Web carregado")
        except Exception:
            logger.error("Timeout ao aguardar login do WhatsApp")
            await context.close()
            await p.stop()
            return None, None

    return p, (context, page)


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

async def executar_sincronizacao(
    dry_run: bool = True,
    limit: int = DEFAULT_LIMIT,
    resume: bool = False,
    reconcile: bool = False,
    campaign_key: str = PRIMEIRO_CONTATO_V1,
) -> None:
    """
    Executa a sincronização.

    Args:
        dry_run: Se True, não altera o Supabase
        limit: Máximo de leads
        resume: Se True, carrega checkpoint
        reconcile: Se True, reavalia needs_reconciliation
        campaign_key: Chave da campanha
    """
    run_id = f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info("=" * 60)
    logger.info("Sincronizador WhatsApp - %s", run_id)
    logger.info("Modo: %s | Limite: %d | Reconciliar: %s",
                "DRY-RUN" if dry_run else "APPLY", limit, reconcile)
    logger.info("Campaign key: %s", campaign_key)
    logger.info("=" * 60)

    # Carrega checkpoint se solicitado
    offset = 0
    if resume:
        cp = carregar_checkpoint()
        if cp:
            offset = cp.get("offset", 0)
            logger.info("Retomando do offset %d", offset)

    # Carrega leads
    if reconcile:
        leads = carregar_leads_para_reconciliar(limit=limit, campaign_key=campaign_key)
        logger.info("Modo reconciliação: %d leads em needs_reconciliation", len(leads))
    else:
        leads = carregar_leads_nao_abordados(limit=limit, offset=offset, campaign_key=campaign_key)

    if not leads:
        logger.info("Nenhum lead para processar.")
        return

    # Inicializa Playwright
    p, (context, page) = await setup_playwright()
    if not p:
        return

    resultados = []
    diagnostic_dir = OUTPUT_DIR / run_id / "diagnosticos"

    # Em dry-run: verifica se a RPC get_outreach_state existe (pré-migration)
    outreach_disponivel = False
    if not dry_run:
        client_check = _get_supabase_client()
        if client_check:
            outreach_disponivel = _rpc_exists(client_check, "get_outreach_state")
            if not outreach_disponivel:
                logger.warning("RPC get_outreach_state não disponível (pré-migration). "
                               "Modo --apply exigirá migration primeiro.")

    try:
        for i, lead in enumerate(leads):
            lead_id = lead.get("id", "")
            nome = lead.get("nome", "sem nome")
            tel = lead.get("whatsapp", "") or lead.get("telefone", "") or ""

            logger.info("[%d/%d] Processando: %s (%s)", i + 1, len(leads), nome, _mascarar(tel))

            phone_normalized = normalizar_telefone_br(tel)
            if not phone_normalized:
                logger.warning("  Telefone inválido, pulando")
                continue

            # Em modo apply: verifica estado via RPC (se disponível)
            if not dry_run and outreach_disponivel:
                try:
                    from outreach_client import get_outreach_state
                    state = get_outreach_state(phone_normalized, campaign_key)
                    if state and state.get("outcome") == "found" and state.get("status") in (
                        "sent", "confirmed_from_whatsapp", "needs_reconciliation"
                    ):
                        logger.info("  Já possui registro bloqueador: %s", state.get("status"))
                        continue
                except Exception:
                    logger.info("  outreach_state indisponível (pré-migration), continuando")

            # Executa match no WhatsApp
            result = await fazer_match_completo(
                page,
                lead_id=lead_id,
                phone_normalized=phone_normalized,
                campaign_key=campaign_key,
                diagnostic_dir=str(diagnostic_dir),
            )

            logger.info("  Status: %s | Chat: %s | Saída: %s | Match: %s",
                        result.status.value,
                        "sim" if result.chat_found else "nao",
                        "sim" if result.outbound_found else "nao",
                        "sim" if result.campaign_match else "nao" if result.campaign_match is False else "n/a")

            resultados.append(result)

            # Se não for dry-run e tiver match, confirma no Supabase
            if not dry_run and result.status == MatchStatus.MATCHED and outreach_disponivel:
                if result.message_timestamp and result.message_fingerprint:
                    from outreach_client import confirm_outreach_from_whatsapp
                    resp = confirm_outreach_from_whatsapp(
                        phone_normalized=phone_normalized,
                        campaign_key=campaign_key,
                        lead_id=lead_id,
                        message_timestamp=result.message_timestamp,
                        fingerprint=result.message_fingerprint,
                        campaign_match=True,
                    )
                    if resp and resp.get("outcome") == "confirmed":
                        logger.info("  ✓ Confirmado no Supabase")
                    else:
                        logger.warning("  ✗ Falha ao confirmar: %s", resp)
                else:
                    logger.warning("  Sem timestamp/fingerprint, pulando confirmação")
            elif not dry_run and not outreach_disponivel:
                logger.info("  Match detectado, mas migration ainda não aplicada. "
                            "Registrado apenas no relatório local.")

            # Salva checkpoint
            salvar_checkpoint({
                "run_id": run_id,
                "offset": offset + i + 1,
                "processed": i + 1,
                "last_lead_id": lead_id,
                "dry_run": dry_run,
                "reconcile": reconcile,
            })

            # Intervalo aleatório entre pesquisas
            intervalo = random.uniform(INTERVALO_MIN, INTERVALO_MAX)
            logger.debug("  Aguardando %.1fs...", intervalo)
            await asyncio.sleep(intervalo)

    except KeyboardInterrupt:
        logger.info("Interrompido pelo usuário")
    except Exception as e:
        logger.error("Erro na execução: %s", e)
    finally:
        await context.close()
        await p.stop()

    # Gera relatórios
    relatorios = gerar_relatorios(resultados, run_id, dry_run)

    # Resumo final
    logger.info("=" * 60)
    logger.info("RESUMO FINAL")
    logger.info("Total examinado: %d", len(resultados))
    logger.info("Matches confirmados: %d", sum(1 for r in resultados if r.status == MatchStatus.MATCHED))
    logger.info("Ambíguos: %d", sum(1 for r in resultados if r.status == MatchStatus.AMBIGUOUS))
    logger.info("Sem mensagem de saída: %d", sum(1 for r in resultados if r.status == MatchStatus.NO_OUTBOUND))
    logger.info("Sem conversa: %d", sum(1 for r in resultados if r.status == MatchStatus.NO_CHAT))
    logger.info("Grupos/canais: %d", sum(1 for r in resultados if r.status in (MatchStatus.GROUP, MatchStatus.CHANNEL, MatchStatus.COMMUNITY)))
    logger.info("Erros: %d", sum(1 for r in resultados if r.status == MatchStatus.ERROR))
    logger.info("Relatórios salvos em: %s", OUTPUT_DIR / run_id)
    logger.info("=" * 60)


# ============================================================
# CLI
# ============================================================


# ============================================================
# MODO TEST-PHONE (controle direcionado)
# ============================================================

async def executar_test_phone(
    campaign_key: str = PRIMEIRO_CONTATO_V1,
) -> None:
    """
    Testa um unico telefone informado via WHATSAPP_MATCH_TEST_PHONE.
    Modo seguro: dry-run, sem escrita, sem reserva, sem settle.
    """
    test_phone_raw = os.environ.get("WHATSAPP_MATCH_TEST_PHONE", "").strip()
    phone_normalized = normalizar_telefone_br(test_phone_raw)
    if not phone_normalized:
        logger.error("Telefone de teste invalido")
        return

    phone_masked = phone_normalized[:4] + "****" + phone_normalized[-4:]
    run_id = f"testphone_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    logger.info("=" * 60)
    logger.info("MODO TEST-PHONE - %s", run_id)
    logger.info("Telefone: %s", phone_masked)
    logger.info("Campaign key: %s", campaign_key)
    logger.info("=" * 60)

    # Cria lead ficticio para o matcher
    fake_lead = {
        "id": "test-phone-0000",
        "nome": "TESTE",
        "telefone": "",
        "whatsapp": phone_normalized,
        "telefone_normalizado": phone_normalized,
        "cidade": "",
        "bairro": "",
        "categoria": "",
        "nicho": "",
        "produto": "avgestao",
        "grupo": "assistencias",
        "status": "novo",
    }

    # Inicializa Playwright
    p, (context, page) = await setup_playwright()
    if not p:
        return

    diagnostic_dir = OUTPUT_DIR / run_id / "diagnosticos"

    try:
        start_total = time.time()
        result = await fazer_match_completo(
            page,
            lead_id=fake_lead["id"],
            phone_normalized=phone_normalized,
            campaign_key=campaign_key,
            diagnostic_dir=str(diagnostic_dir),
        )
        elapsed_total = time.time() - start_total

        # Relatorio
        logger.info("=" * 60)
        logger.info("RESULTADO TEST-PHONE")
        logger.info("=" * 60)
        logger.info("Telefone: %s", phone_masked)
        logger.info("Campo encontrado: %s", "sim" if result.selector_used else "nao")
        logger.info("Selector usado: %s", result.selector_used or "nenhum")
        logger.info("Chat encontrado: %s", "sim" if result.chat_found else "nao")
        logger.info("Mensagem de saida: %s", "sim" if result.outbound_found else "nao")
        logger.info("Campaign match: %s", "sim" if result.campaign_match else "nao" if result.campaign_match is False else "n/a")
        logger.info("Estado final: %s", result.status.value)
        logger.info("Tempo total: %.1fs", elapsed_total)

        if result.status == MatchStatus.NO_CHAT:
            logger.warning(
                "ATENCAO: resultado no_chat. "
                "A busca lateral nao encontrou conversa para este telefone. "
                "Verifique se o numero esta correto e se possui conversa ativa."
            )
        elif result.status == MatchStatus.SEARCH_FIELD_NOT_FOUND:
            logger.error("Campo de busca nao encontrado - problema de seletor")
        elif result.status == MatchStatus.LOGIN_REQUIRED:
            logger.error("WhatsApp nao autenticado")
        else:
            logger.info("Busca executada com sucesso: %s", result.status.value)

    except Exception as e:
        logger.error("Erro durante teste: %s", e)
    finally:
        await context.close()
        await p.stop()

    logger.info("=" * 60)
    logger.info("FIM TEST-PHONE")
    logger.info("=" * 60)

def main():
    parser = argparse.ArgumentParser(
        description="Sincronização retroativa WhatsApp Web → Supabase",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s --dry-run --limit 10
  %(prog)s --apply --limit 100
  %(prog)s --reconcile --limit 20
  %(prog)s --resume --dry-run --limit 50
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Modo simulação: não altera o Supabase (padrão). "
             "Requer apenas SUPABASE_URL e SUPABASE_ANON_KEY.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica as atualizações no Supabase (requer SUPABASE_SERVICE_ROLE_KEY no .env). "
             "NÃO USE em produção sem validar com --dry-run primeiro.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Máximo de leads (padrão: {DEFAULT_LIMIT})",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Retoma do último checkpoint",
    )
    parser.add_argument(
        "--reconcile",
        action="store_true",
        help="Reavalia leads em needs_reconciliation",
    )
    parser.add_argument(
        "--campaign-key",
        default=PRIMEIRO_CONTATO_V1,
        help=f"Chave da campanha (padrão: {PRIMEIRO_CONTATO_V1})",
    )
    parser.add_argument(
        "--test-phone",
        action="store_true",
        help="Modo direcionado: testa apenas um telefone da variavel "
             "de ambiente WHATSAPP_MATCH_TEST_PHONE. Requer --dry-run.",
    )

    args = parser.parse_args()

    # Valida modo test-phone
    if args.test_phone:
        test_phone = os.environ.get("WHATSAPP_MATCH_TEST_PHONE", "").strip()
        if not test_phone:
            logger.error(
                "WHATSAPP_MATCH_TEST_PHONE nao definida. "
                "Defina a variavel de ambiente com o telefone de teste."
            )
            sys.exit(1)
        if not args.dry_run:
            logger.error("--test-phone requer --dry-run")
            sys.exit(1)
        phone_norm = normalizar_telefone_br(test_phone)
        if not phone_norm:
            logger.error("Telefone de teste invalido apos normalizacao")
            sys.exit(1)
        logger.info("Modo TEST-PHONE: usando telefone da variavel de ambiente")

    # Se --apply foi passado, desativa dry-run
    if args.apply:
        args.dry_run = False

    # Valida campaign_key
    if not validar_campaign_key(args.campaign_key):
        logger.error("Campaign key inválida: %s", args.campaign_key)
        sys.exit(1)

    # Adquire lock exclusivo
    with LockWhatsAppMatch() as lock:
        if not lock.acquired:
            logger.error(
                "Já existe uma sincronização ativa. "
                "Aguardar a execução atual terminar ou verificar "
                "se o lock está preso em output/avgestao/whatsapp_match.lock"
            )
            sys.exit(1)

        # Executa
        if args.test_phone:
            asyncio.run(executar_test_phone(
                campaign_key=args.campaign_key,
            ))
        else:
            asyncio.run(executar_sincronizacao(
                dry_run=args.dry_run,
                limit=args.limit,
                resume=args.resume,
                reconcile=args.reconcile,
                campaign_key=args.campaign_key,
            ))


if __name__ == "__main__":
    main()
