#!/usr/bin/env python3
"""
campanha_whatsapp.py - Entrypoint centralizado para campanhas WhatsApp.

Modos:
  plan   Calcula capacidade, consulta leads, mostra plano. Sem browser, sem escrita.
  semi   Para cada lead: reserva, verifica, abre wa.me, exige confirmacao manual.
  auto   Para cada lead: reserva, verifica, envia automaticamente (requer --confirm-live-send).

Uso:
  python campanha_whatsapp.py plan --until 17:00
  python campanha_whatsapp.py semi --until 17:00 --limit 10
  python campanha_whatsapp.py auto --until 17:00 --confirm-live-send
  python campanha_whatsapp.py auto --resume --run-id <RUN_ID> --confirm-live-send
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import signal
import sys
import time
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

_root = str(Path(__file__).resolve().parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from config.lock_whatsapp_sender import LockWhatsAppSender
from utils.phone_utils import normalizar_telefone_br
from utils.campaign_key import PRIMEIRO_CONTATO_V1, validar_campaign_key

logger = logging.getLogger("campanha_whatsapp")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

FUSO = timezone(timedelta(hours=-3))
DEFAULT_INTERVAL_MINUTES = 5
DEFAULT_SAFETY_BUFFER_MINUTES = 5
DEFAULT_VERIFICATION_BUDGET_SECONDS = 15
DEFAULT_MAX_ERRORS = 10
DEFAULT_MAX_CONSECUTIVE_ERRORS = 3
DEFAULT_JITTER_SECONDS = 0
DEFAULT_LIMIT = 30
PROFILE_DIR_NAME = ".whatsapp_business_profile"
CHECKPOINT_DIR = Path("output/avgestao/campanha_runs")


# ============================================================
# Capacidade
# ============================================================

class CapacityCalculator:
    """Calcula quantos envios cabem ate um horario limite."""

    @staticmethod
    def calcular(
        ate_horario: str,
        intervalo_segundos: int,
        tempo_verificacao_segundos: int = DEFAULT_VERIFICATION_BUDGET_SECONDS,
        margem_segundos: int = DEFAULT_SAFETY_BUFFER_MINUTES * 60,
        jitter_segundos: int = DEFAULT_JITTER_SECONDS,
        agora: datetime | None = None,
    ) -> dict[str, Any]:
        now = agora or datetime.now(FUSO)
        partes = ate_horario.split(":")
        if len(partes) != 2:
            return {"erro": f"Formato de horario invalido: {ate_horario}"}
        try:
            hora, minuto = int(partes[0]), int(partes[1])
        except ValueError:
            return {"erro": f"Formato de horario invalido: {ate_horario}"}

        alvo = now.replace(hour=hora, minute=minuto, second=0, microsecond=0)
        if alvo <= now:
            alvo = alvo + timedelta(days=1)

        disponivel_seg = (alvo - now).total_seconds()
        if disponivel_seg <= 0:
            return {
                "minutos_disponiveis": 0,
                "capacidade_teorica": 0,
                "capacidade_segura": 0,
                "horario_ultimo_envio": None,
                "erro": "Horario ja encerrado",
            }

        minutos_disponiveis = disponivel_seg / 60
        tempo_por_envio = intervalo_segundos + tempo_verificacao_segundos + jitter_segundos
        if tempo_por_envio <= 0:
            tempo_por_envio = intervalo_segundos

        capacidade_teorica = max(1, int(disponivel_seg // tempo_por_envio) + 1)
        tempo_seguro = disponivel_seg - margem_segundos
        capacidade_segura = max(0, int(tempo_seguro // tempo_por_envio)) if tempo_seguro > 0 else 0

        if capacidade_segura > 0:
            tempo_ultimo = tempo_verificacao_segundos + (capacidade_segura - 1) * tempo_por_envio
            horario_ultimo = now + timedelta(seconds=tempo_ultimo)
        else:
            horario_ultimo = None

        return {
            "minutos_disponiveis": round(minutos_disponiveis, 1),
            "capacidade_teorica": capacidade_teorica,
            "capacidade_segura": capacidade_segura,
            "horario_ultimo_envio": horario_ultimo.strftime("%H:%M") if horario_ultimo else None,
        }


# ============================================================
# Leads
# ============================================================

class LeadSelector:
    """Seleciona e filtra leads do Supabase."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from supabase import create_client
            except ImportError:
                logger.error("Pacote 'supabase' nao instalado")
                return None

            env_path = Path(_root) / ".env"
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
                logger.error("SUPABASE_URL / SUPABASE_ANON_KEY ausentes")
                return None
            self._client = create_client(url, key)
        return self._client

    def buscar_leads(self, statuses: list[str] | None = None, limit: int = DEFAULT_LIMIT) -> list[dict[str, Any]]:
        client = self._get_client()
        if not client:
            return []
        if statuses is None:
            statuses = ["novo", "pronto_para_enviar"]
        try:
            query = (
                client.table("leads")
                .select("id,nome,whatsapp,telefone,telefone_normalizado,status,produto,grupo")
                .in_("status", statuses)
                .order("created_at")
            )
            if limit:
                query = query.limit(limit)
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error("Erro ao buscar leads: %s", e)
            return []

    @staticmethod
    def filtrar_celular(leads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        filtrados = []
        for lead in leads:
            tel = lead.get("telefone_normalizado") or lead.get("whatsapp") or lead.get("telefone") or ""
            tel_norm = normalizar_telefone_br(str(tel))
            if tel_norm and len(tel_norm) == 13 and tel_norm.startswith("5521"):
                lead["_telefone_normalizado"] = tel_norm
                filtrados.append(lead)
        return filtrados

    @staticmethod
    def embaralhar_e_limitar(leads: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
        shuffled = list(leads)
        random.shuffle(shuffled)
        return shuffled[:n]


# ============================================================
# Verificacao de duplicidade
# ============================================================

class DedupVerifier:
    """Verifica se um lead ja foi contatado via WhatsApp."""

    @staticmethod
    async def verificar(page, lead: dict[str, Any], campaign_key: str, verification_budget: int = DEFAULT_VERIFICATION_BUDGET_SECONDS) -> dict[str, Any]:
        from whatsapp_match.matcher import fazer_match_completo, MatchStatus

        tel_norm = lead.get("_telefone_normalizado", "")
        lead_id = lead.get("id", "")
        diagnostic_dir = str(CHECKPOINT_DIR / "diagnosticos")

        try:
            result = await fazer_match_completo(
                page,
                lead_id=lead_id,
                phone_normalized=tel_norm,
                campaign_key=campaign_key,
                diagnostic_dir=diagnostic_dir,
                verification_budget=verification_budget,
            )
            classification = DedupVerifier._classificar(result)
            return {
                "classification": classification,
                "match_status": result.status.value if result.status else None,
                "outbound_found": result.outbound_found,
                "campaign_match": result.campaign_match,
                "chat_found": result.chat_found,
                "details": result.details,
                "timings": result.timings,
            }
        except Exception as e:
            logger.warning("Erro na verificacao do lead %s: %s", lead_id[:8], e)
            return {"classification": "verification_error", "match_status": "error", "error": str(e)[:200]}

    @staticmethod
    def _classificar(result) -> str:
        from whatsapp_match.matcher import MatchStatus
        if result.status == MatchStatus.NO_CHAT:
            return "safe_to_send"
        elif result.status == MatchStatus.MATCHED:
            return "already_confirmed"
        elif result.status == MatchStatus.AMBIGUOUS:
            return "outbound_other_campaign"
        elif result.status == MatchStatus.AMBIGUOUS_CONTACT:
            return "ambiguous_contact"
        elif result.status == MatchStatus.NO_OUTBOUND:
            return "safe_to_send"
        elif result.status in (MatchStatus.GROUP, MatchStatus.CHANNEL, MatchStatus.COMMUNITY, MatchStatus.STATUS):
            return "ambiguous_contact"
        elif result.status in (MatchStatus.LOGIN_REQUIRED, MatchStatus.ERROR, MatchStatus.SEARCH_FIELD_NOT_FOUND, MatchStatus.MODAL_BLOCKED):
            return "verification_error"
        else:
            return "needs_reconciliation"


# ============================================================
# Envio de mensagem
# ============================================================

class MessageSender:
    """Envia mensagens via wa.me."""

    @staticmethod
    def gerar_link_wa_me(telefone: str, mensagem: str) -> str:
        return f"https://wa.me/{telefone}?text={quote(mensagem)}"

    @staticmethod
    async def abrir_wa_me(page, telefone: str, mensagem: str) -> bool:
        link = MessageSender.gerar_link_wa_me(telefone, mensagem)
        try:
            await page.goto(link, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)
            try:
                await page.wait_for_selector(
                    'div[contenteditable="true"][data-tab="10"], '
                    'div[contenteditable="true"][title], '
                    'footer div[contenteditable="true"]',
                    timeout=15000,
                )
                return True
            except Exception:
                logger.warning("Campo de mensagem nao encontrado apos wa.me")
                return False
        except Exception as e:
            logger.warning("Erro ao abrir wa.me: %s", e)
            return False

    @staticmethod
    async def enviar_mensagem(page) -> bool:
        try:
            send_btn = page.locator(
                'button[aria-label="Enviar"], '
                'button[aria-label="Send"], '
                'span[data-icon="send"], '
                'div[role="button"][aria-label="Enviar"]'
            )
            count = await send_btn.count()
            if count == 0:
                logger.warning("Botao de enviar nao encontrado")
                return False
            await send_btn.first.click(timeout=5000)
            await page.wait_for_timeout(2000)
            try:
                await page.wait_for_selector(
                    'div[data-testid="msg-container"], '
                    'span[data-icon="msg-dblcheck"], '
                    'span[data-icon="msg-check"]',
                    timeout=10000,
                )
                return True
            except Exception:
                return True
        except Exception as e:
            logger.warning("Erro ao enviar mensagem: %s", e)
            return False


# ============================================================
# Checkpoint
# ============================================================

class CheckpointManager:
    """Gerencia checkpoint para retomada."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.dir = CHECKPOINT_DIR / run_id
        self.file = self.dir / "checkpoint.json"
        self._data: dict[str, Any] = {}

    def carregar(self) -> dict[str, Any]:
        if not self.file.exists():
            self._data = {
                "run_id": self.run_id,
                "started_at": datetime.now(FUSO).isoformat(),
                "sent_leads": [],
                "failed_leads": [],
                "skipped_leads": [],
                "last_lead_id": None,
                "total_processed": 0,
            }
            return self._data
        try:
            self._data = json.loads(self.file.read_text(encoding="utf-8"))
            return self._data
        except Exception as e:
            logger.warning("Erro ao carregar checkpoint: %s", e)
            self._data = {
                "run_id": self.run_id,
                "started_at": datetime.now(FUSO).isoformat(),
                "sent_leads": [],
                "failed_leads": [],
                "skipped_leads": [],
                "last_lead_id": None,
                "total_processed": 0,
            }
            return self._data

    def salvar(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        tmp = self.file.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.file)

    def registrar_envio(self, lead_id: str, phone_hash: str) -> None:
        self._data["sent_leads"].append({
            "lead_id": lead_id,
            "phone_hash": phone_hash,
            "sent_at": datetime.now(FUSO).isoformat(),
        })
        self._data["last_lead_id"] = lead_id
        self._data["total_processed"] = len(self._data["sent_leads"]) + len(self._data["failed_leads"]) + len(self._data["skipped_leads"])
        self.salvar()

    def registrar_falha(self, lead_id: str, motivo: str) -> None:
        self._data["failed_leads"].append({
            "lead_id": lead_id,
            "reason": motivo,
            "failed_at": datetime.now(FUSO).isoformat(),
        })
        self._data["total_processed"] = len(self._data["sent_leads"]) + len(self._data["failed_leads"]) + len(self._data["skipped_leads"])
        self.salvar()

    def registrar_skip(self, lead_id: str, motivo: str) -> None:
        self._data["skipped_leads"].append({
            "lead_id": lead_id,
            "reason": motivo,
            "skipped_at": datetime.now(FUSO).isoformat(),
        })
        self._data["total_processed"] = len(self._data["sent_leads"]) + len(self._data["failed_leads"]) + len(self._data["skipped_leads"])
        self.salvar()

    def ja_processado(self, lead_id: str) -> bool:
        for entry in self._data.get("sent_leads", []):
            if entry["lead_id"] == lead_id:
                return True
        for entry in self._data.get("failed_leads", []):
            if entry["lead_id"] == lead_id:
                return True
        for entry in self._data.get("skipped_leads", []):
            if entry["lead_id"] == lead_id:
                return True
        return False

    def get_resumo(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "enviados": len(self._data.get("sent_leads", [])),
            "falhas": len(self._data.get("failed_leads", [])),
            "pulados": len(self._data.get("skipped_leads", [])),
            "total_processado": self._data.get("total_processed", 0),
        }


# ============================================================
# Seguranca
# ============================================================

class SafetyController:
    """Controles de seguranca."""

    def __init__(self, max_errors=DEFAULT_MAX_ERRORS, max_consecutive_errors=DEFAULT_MAX_CONSECUTIVE_ERRORS, interval_seconds=DEFAULT_INTERVAL_MINUTES*60, jitter_seconds=DEFAULT_JITTER_SECONDS):
        self.max_errors = max_errors
        self.max_consecutive_errors = max_consecutive_errors
        self.interval_seconds = interval_seconds
        self.jitter_seconds = jitter_seconds
        self.error_count = 0
        self.consecutive_errors = 0
        self._interrupted = False

    def registrar_erro(self) -> None:
        self.error_count += 1
        self.consecutive_errors += 1

    def registrar_sucesso(self) -> None:
        self.consecutive_errors = 0

    def deve_parar(self) -> tuple[bool, str]:
        if self._interrupted:
            return True, "interrompido_pelo_usuario"
        if self.error_count >= self.max_errors:
            return True, f"max_erros_atingido ({self.error_count})"
        if self.consecutive_errors >= self.max_consecutive_errors:
            return True, f"erros_consecutivos ({self.consecutive_errors})"
        return False, ""

    def aguardar_intervalo(self) -> None:
        jitter = random.uniform(0, self.jitter_seconds) if self.jitter_seconds else 0
        espera = self.interval_seconds + jitter
        logger.info("Aguardando %.0f segundos...", espera)
        time.sleep(espera)

    def sinalizar_interrupcao(self) -> None:
        self._interrupted = True
        logger.info("Interrupcao solicitada. Finalizando lead atual...")

    @staticmethod
    def horario_passou(limite: str) -> bool:
        now = datetime.now(FUSO)
        partes = limite.split(":")
        if len(partes) != 2:
            return False
        try:
            hora, minuto = int(partes[0]), int(partes[1])
        except ValueError:
            return False
        alvo = now.replace(hour=hora, minute=minuto, second=0, microsecond=0)
        return now >= alvo


# ============================================================
# Orquestrador principal
# ============================================================

class CampanhaWhatsApp:
    """Orquestrador principal de campanhas WhatsApp."""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.mode = args.mode
        self.run_id = args.run_id or self._gerar_run_id()
        self.campaign_key = args.campaign_key
        self.limit = args.limit or DEFAULT_LIMIT
        self.until = args.until
        self.interval_seconds = args.interval_minutes * 60
        self.safety_buffer = args.safety_buffer_minutes * 60
        self.verification_budget = args.verification_budget_seconds
        self.dry_run = args.dry_run
        self.confirm_live_send = args.confirm_live_send

        self.lead_selector = LeadSelector()
        self.checkpoint = CheckpointManager(self.run_id)
        self.safety = SafetyController(
            max_errors=args.max_errors,
            max_consecutive_errors=args.max_consecutive_errors,
            interval_seconds=self.interval_seconds,
            jitter_seconds=args.jitter_seconds,
        )
        self._template_text: str | None = None

    def _gerar_run_id(self) -> str:
        agora = datetime.now().strftime("%Y%m%d_%H%M%S")
        sufixo = hashlib.sha1(os.urandom(16)).hexdigest()[:6]
        return f"run_{agora}_{sufixo}"

    def _carregar_template(self) -> str:
        if self._template_text is not None:
            return self._template_text
        if self.args.message_template:
            path = Path(self.args.message_template)
            if path.exists():
                self._template_text = path.read_text(encoding="utf-8").strip()
                return self._template_text
            else:
                logger.warning("Template nao encontrado: %s", path)
        self._template_text = (
            "Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
            "Meu nome e Vanderson e desenvolvi o AVGESTAO para empresas "
            "que trabalham com servicos e orcamentos.\n\n"
            "Estou liberando 15 dias gratuitos para teste.\n\n"
            "Posso criar um acesso para voces testarem?"
        )
        return self._template_text

    def _renderizar_mensagem(self, lead: dict[str, Any]) -> str:
        import re
        template = self._carregar_template()
        variaveis_validas = {"nome", "empresa", "cidade", "segmento"}
        encontradas = set(re.findall(r'\{(\w+)\}', template))
        desconhecidas = encontradas - variaveis_validas
        if desconhecidas:
            logger.error("Variaveis desconhecidas no template: %s", desconhecidas)
            sys.exit(1)
        return template.format(
            nome=lead.get("nome", "Empresa"),
            empresa=lead.get("nome", ""),
            cidade=lead.get("cidade", ""),
            segmento=lead.get("grupo", ""),
        )

    def _hash_mensagem(self, mensagem: str) -> str:
        return hashlib.sha256(mensagem.encode("utf-8")).hexdigest()[:16]

    def run(self) -> int:
        logger.info("=" * 72)
        logger.info("Campanha WhatsApp - Modo: %s", self.mode)
        logger.info("Run ID: %s", self.run_id)
        logger.info("Campaign Key: %s", self.campaign_key)
        logger.info("=" * 72)

        if not validar_campaign_key(self.campaign_key):
            logger.error("campaign_key invalida: %s", self.campaign_key)
            return 2

        checkpoint_data = self.checkpoint.carregar()
        logger.info("Checkpoint: %s", self.checkpoint.get_resumo())

        cap = None
        if self.until:
            cap = CapacityCalculator.calcular(
                ate_horario=self.until,
                intervalo_segundos=self.interval_seconds,
                tempo_verificacao_segundos=self.verification_budget,
                margem_segundos=self.safety_buffer,
            )
            if cap.get("erro"):
                logger.error("Erro no calculo de capacidade: %s", cap["erro"])
                return 1
            logger.info("Capacidade: %s", cap)
            capacidade = cap["capacidade_segura"]
            if capacidade == 0:
                logger.warning("Capacidade segura zero. Nenhum envio possivel.")
                return 0
        else:
            capacidade = self.limit

        statuses = self.args.statuses.split(",") if self.args.statuses else ["novo", "pronto_para_enviar"]
        leads = self.lead_selector.buscar_leads(statuses=statuses, limit=self.limit * 2)
        if not leads:
            logger.warning("Nenhum lead elegivel encontrado.")
            return 0

        leads = LeadSelector.filtrar_celular(leads)
        logger.info("Leads celulares: %d", len(leads))
        leads = LeadSelector.embaralhar_e_limitar(leads, min(capacidade, self.limit))
        logger.info("Leads selecionados: %d", len(leads))

        if self.mode == "plan":
            self._mostrar_plano(leads, cap)
            return 0

        return self._executar(leads)

    def _mostrar_plano(self, leads: list[dict], cap: dict | None) -> None:
        print("\n" + "=" * 60)
        print("  PLANO DE CAMPANHA")
        print("=" * 60)
        if cap:
            print(f"  Horario limite: {self.until}")
            print(f"  Minutos disponiveis: {cap.get('minutos_disponiveis', 'N/A')}")
            print(f"  Capacidade teorica: {cap.get('capacidade_teorica', 'N/A')}")
            print(f"  Capacidade segura: {cap.get('capacidade_segura', 'N/A')}")
        print(f"  Leads selecionados: {len(leads)}")
        print(f"  Intervalo: {self.interval_seconds // 60} min")
        print(f"  Campaign key: {self.campaign_key}")
        print(f"  Run ID: {self.run_id}")
        print("-" * 60)
        for i, lead in enumerate(leads, 1):
            tel = lead.get("_telefone_normalizado", "")
            masked = tel[:4] + "****" + tel[-4:] if len(tel) >= 8 else "****"
            print(f"  {i:3d}. {lead.get('nome', 'N/A')[:40]:40s} {masked}")
        print("=" * 60)
        print("\nNenhuma mensagem enviada. Nenhuma reserva feita.")

    def _executar(self, leads: list[dict]) -> int:
        from sender_int import reserve_lead, settle_lead

        original_handler = signal.getsignal(signal.SIGINT)
        def _handler(sig, frame):
            self.safety.sinalizar_interrupcao()
        signal.signal(signal.SIGINT, _handler)

        page = None
        browser_context = None
        playwright_obj = None

        try:
            if not self.dry_run:
                playwright_obj, browser_context, page = self._abrir_browser()
                if not page:
                    logger.error("Nao foi possivel abrir o WhatsApp Web")
                    return 1

            enviados = 0
            for i, lead in enumerate(leads):
                deve_parar, motivo = self.safety.deve_parar()
                if deve_parar:
                    logger.warning("Parando: %s", motivo)
                    break

                if self.until and SafetyController.horario_passou(self.until):
                    logger.warning("Horario limite atingido: %s", self.until)
                    break

                lead_id = lead.get("id", "")
                if self.checkpoint.ja_processado(lead_id):
                    logger.info("[%d/%d] Lead %s ja processado, pulando", i+1, len(leads), lead_id[:8])
                    continue

                tel_norm = lead.get("_telefone_normalizado", "")
                nome = lead.get("nome", "")
                masked = tel_norm[:4] + "****" + tel_norm[-4:] if len(tel_norm) >= 8 else "****"
                logger.info("=" * 60)
                logger.info("[%d/%d] %s (%s)", i+1, len(leads), nome[:40], masked)

                # 1. Reservar
                if not self.dry_run:
                    reserva = reserve_lead(tel_norm, self.campaign_key, lead_id, "sender:auto")
                    if not reserva:
                        logger.warning("  Reserva retornou None")
                        self.checkpoint.registrar_falha(lead_id, "reserve_none")
                        self.safety.registrar_erro()
                        continue

                    outcome = reserva.get("outcome")
                    if outcome == "already_sent":
                        logger.info("  Ja enviado, pulando")
                        self.checkpoint.registrar_skip(lead_id, "already_sent")
                        continue
                    elif outcome == "already_confirmed":
                        logger.info("  Ja confirmado, pulando")
                        self.checkpoint.registrar_skip(lead_id, "already_confirmed")
                        continue
                    elif outcome == "reserved_by_other":
                        logger.info("  Reservado por outro, pulando")
                        self.checkpoint.registrar_skip(lead_id, "reserved_by_other")
                        continue
                    elif outcome != "reserved":
                        logger.warning("  Reserva falhou: %s", outcome)
                        self.checkpoint.registrar_falha(lead_id, f"reserve_{outcome}")
                        self.safety.registrar_erro()
                        continue

                    reservation_id = reserva.get("reservation_id")
                    reservation_token = reserva.get("reservation_token")
                    logger.info("  Reservado: %s", reservation_id[:8] if reservation_id else "N/A")
                else:
                    reservation_id = "dry-run"
                    reservation_token = "dry-run"

                # 2. Verificar duplicidade
                verification = {"classification": "safe_to_send"}
                if not self.dry_run and page and self.mode == "auto":
                    try:
                        verification = asyncio.run(DedupVerifier.verificar(page, lead, self.campaign_key, self.verification_budget))
                    except Exception as e:
                        logger.warning("  Erro na verificacao: %s", e)
                        verification = {"classification": "verification_error", "error": str(e)[:200]}

                classification = verification.get("classification", "safe_to_send")
                logger.info("  Verificacao: %s", classification)

                # 3. Decidir
                if classification == "safe_to_send":
                    mensagem = self._renderizar_mensagem(lead)
                    msg_hash = self._hash_mensagem(mensagem)

                    if self.mode == "semi" and not self.dry_run:
                        print("\n" + "-" * 60)
                        print(f"  Lead: {nome}")
                        print(f"  Telefone: {masked}")
                        print(f"  Mensagem ({len(mensagem)} chars):")
                        print("  " + mensagem.replace("\n", "\n  "))
                        print("-" * 60)
                        resp = input("  Enviar? (s/N): ").strip().lower()
                        if resp not in ("s", "sim", "y", "yes"):
                            logger.info("  Cancelado pelo usuario")
                            if not self.dry_run:
                                settle_lead(reservation_id, reservation_token, "released", obs="cancelado_pelo_usuario")
                            self.checkpoint.registrar_skip(lead_id, "cancelado_pelo_usuario")
                            continue

                    if self.dry_run:
                        logger.info("  [DRY-RUN] Enviaria: %s", masked)
                        self.checkpoint.registrar_skip(lead_id, "dry_run")
                        self.safety.registrar_sucesso()
                        continue

                    logger.info("  Enviando via wa.me...")
                    link_ok = asyncio.run(MessageSender.abrir_wa_me(page, tel_norm, mensagem))
                    if not link_ok:
                        logger.warning("  Falha ao abrir wa.me")
                        settle_lead(reservation_id, reservation_token, "failed", obs="wa_me_falha")
                        self.checkpoint.registrar_falha(lead_id, "wa_me_falha")
                        self.safety.registrar_erro()
                        continue

                    enviado = asyncio.run(MessageSender.enviar_mensagem(page))
                    if not enviado:
                        logger.warning("  Falha ao enviar mensagem")
                        settle_lead(reservation_id, reservation_token, "failed", obs="envio_falha")
                        self.checkpoint.registrar_falha(lead_id, "envio_falha")
                        self.safety.registrar_erro()
                        continue

                    logger.info("  Mensagem enviada com sucesso!")
                    settle_result = settle_lead(
                        reservation_id, reservation_token, "sent",
                        message_timestamp=datetime.now(timezone.utc).isoformat(),
                        fingerprint=msg_hash, campaign_match=True,
                    )
                    if settle_result and settle_result.get("outcome") == "settled":
                        logger.info("  Settle confirmado")
                    else:
                        logger.warning("  Settle: %s", settle_result)

                    self.checkpoint.registrar_envio(lead_id, msg_hash[:8])
                    self.safety.registrar_sucesso()
                    enviados += 1

                    if i < len(leads) - 1:
                        self.safety.aguardar_intervalo()

                elif classification in ("already_confirmed", "already_contacted_same_campaign"):
                    logger.info("  Ja contatado, pulando")
                    if not self.dry_run:
                        settle_lead(reservation_id, reservation_token, "released", obs=f"dedup_{classification}")
                    self.checkpoint.registrar_skip(lead_id, classification)

                elif classification == "outbound_other_campaign":
                    logger.info("  Outbound de outra campanha, pulando")
                    if not self.dry_run:
                        settle_lead(reservation_id, reservation_token, "needs_reconciliation", obs="outbound_other_campaign")
                    self.checkpoint.registrar_skip(lead_id, "outbound_other_campaign")

                elif classification in ("ambiguous_contact", "phone_unconfirmed"):
                    logger.info("  Contato ambiguo, pulando")
                    if not self.dry_run:
                        settle_lead(reservation_id, reservation_token, "needs_reconciliation", obs=classification)
                    self.checkpoint.registrar_skip(lead_id, classification)

                elif classification == "verification_error":
                    logger.warning("  Erro na verificacao")
                    if not self.dry_run:
                        settle_lead(reservation_id, reservation_token, "released", obs="verification_error")
                    self.checkpoint.registrar_falha(lead_id, "verification_error")
                    self.safety.registrar_erro()

                else:
                    logger.info("  Classificacao desconhecida: %s, pulando", classification)
                    if not self.dry_run:
                        settle_lead(reservation_id, reservation_token, "needs_reconciliation", obs=classification)
                    self.checkpoint.registrar_skip(lead_id, classification)

            logger.info("=" * 60)
            logger.info("Resumo: %s", self.checkpoint.get_resumo())
            return 0

        except KeyboardInterrupt:
            logger.info("Interrompido pelo usuario")
            return 130
        finally:
            signal.signal(signal.SIGINT, original_handler)
            if browser_context:
                try:
                    asyncio.run(browser_context.close())
                except Exception:
                    pass
            if playwright_obj:
                try:
                    asyncio.run(playwright_obj.stop())
                except Exception:
                    pass

    def _abrir_browser(self):
        from playwright.async_api import async_playwright
        profile_dir = Path(_root) / PROFILE_DIR_NAME
        profile_dir.mkdir(parents=True, exist_ok=True)

        async def _open():
            p = await async_playwright().start()
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir.resolve()),
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

        try:
            return asyncio.run(_open())
        except Exception as e:
            logger.error("Erro ao abrir browser: %s", e)
            return None, None, None


# ============================================================
# CLI
# ============================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Orquestrador centralizado de campanhas WhatsApp.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python campanha_whatsapp.py plan --until 17:00
  python campanha_whatsapp.py semi --until 17:00 --limit 10
  python campanha_whatsapp.py auto --until 17:00 --confirm-live-send
  python campanha_whatsapp.py auto --resume --run-id <RUN_ID> --confirm-live-send
""",
    )
    parser.add_argument("mode", choices=["plan", "semi", "auto"], help="Modo de operacao")
    parser.add_argument("--until", type=str, default=None, help="Horario limite (HH:MM)")
    parser.add_argument("--interval-minutes", type=int, default=DEFAULT_INTERVAL_MINUTES, help=f"Intervalo entre envios em minutos (padrao: {DEFAULT_INTERVAL_MINUTES})")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"Maximo de leads (padrao: {DEFAULT_LIMIT})")
    parser.add_argument("--campaign-key", type=str, default=PRIMEIRO_CONTATO_V1, help=f"Campaign key (padrao: {PRIMEIRO_CONTATO_V1})")
    parser.add_argument("--message-template", type=str, default=None, help="Caminho para arquivo de template de mensagem")
    parser.add_argument("--profile", type=str, default=None, help="Caminho para diretorio de perfil do WhatsApp")
    parser.add_argument("--statuses", type=str, default="novo,pronto_para_enviar", help="Status dos leads para selecionar (separado por virgula)")
    parser.add_argument("--dry-run", action="store_true", help="Nao envia mensagens nem escreve no Supabase")
    parser.add_argument("--resume", action="store_true", help="Retoma de checkpoint existente")
    parser.add_argument("--run-id", type=str, default=None, help="ID do run para resume")
    parser.add_argument("--safety-buffer-minutes", type=int, default=DEFAULT_SAFETY_BUFFER_MINUTES, help=f"Margem de seguranca em minutos (padrao: {DEFAULT_SAFETY_BUFFER_MINUTES})")
    parser.add_argument("--verification-budget-seconds", type=int, default=DEFAULT_VERIFICATION_BUDGET_SECONDS, help=f"Tempo maximo de verificacao por lead (padrao: {DEFAULT_VERIFICATION_BUDGET_SECONDS})")
    parser.add_argument("--max-errors", type=int, default=DEFAULT_MAX_ERRORS, help=f"Maximo de erros totais (padrao: {DEFAULT_MAX_ERRORS})")
    parser.add_argument("--max-consecutive-errors", type=int, default=DEFAULT_MAX_CONSECUTIVE_ERRORS, help=f"Maximo de erros consecutivos (padrao: {DEFAULT_MAX_CONSECUTIVE_ERRORS})")
    parser.add_argument("--jitter-seconds", type=int, default=DEFAULT_JITTER_SECONDS, help=f"Jitter maximo entre envios (padrao: {DEFAULT_JITTER_SECONDS})")
    parser.add_argument("--confirm-live-send", action="store_true", help="Confirma envio real no modo auto (obrigatorio para auto)")
    parser.add_argument("--verify-only", action="store_true", help="Apenas verifica duplicidade, nao envia")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.mode == "auto" and not args.confirm_live_send and not args.dry_run:
        logger.error("Modo auto requer --confirm-live-send para enviar mensagens reais. Use --dry-run para teste sem envio.")
        return 2

    if args.mode == "semi" and args.dry_run:
        logger.warning("Modo semi com --dry-run: nenhuma mensagem sera enviada.")

    with LockWhatsAppMatch() as lock:
        if not lock.acquired:
            logger.error("Ja existe uma execucao ativa do fluxo WhatsApp.")
            return 1
        campanha = CampanhaWhatsApp(args)
        return campanha.run()


if __name__ == "__main__":
    raise SystemExit(main())
