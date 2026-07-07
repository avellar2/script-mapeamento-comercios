#!/usr/bin/env python3
"""Apply all fixes to campanha_whatsapp.py"""
import sys, os

os.chdir(r'C:\projetos\script-mapear-comercios-whatsapp-dedup')

with open('campanha_whatsapp.py', 'r', encoding='utf-8') as f:
    content = f.read()

# PATCH 1: registrar_estagio with send_clicked and outbound_confirmed
old1 = '    def registrar_estagio(self, lead_id: str, stage: str) -> None:\n        """Registra stage atual de um lead no envio (para recovery)."""\n        pending = self._data.setdefault("pending_stages", {})\n        pending[lead_id] = {\n            "stage": stage,\n            "updated_at": datetime.now(FUSO).isoformat(),\n        }\n        self._data["last_lead_id"] = lead_id\n        self.salvar()'

new1 = '    def registrar_estagio(self, lead_id: str, stage: str, send_clicked: bool | None = None, outbound_confirmed: bool | None = None) -> None:\n        """Registra stage atual de um lead no envio (para recovery)."""\n        pending = self._data.setdefault("pending_stages", {})\n        entry: dict[str, Any] = {\n            "stage": stage,\n            "updated_at": datetime.now(FUSO).isoformat(),\n        }\n        if send_clicked is not None:\n            entry["send_clicked"] = send_clicked\n        if outbound_confirmed is not None:\n            entry["outbound_confirmed"] = outbound_confirmed\n        pending[lead_id] = entry\n        self._data["last_lead_id"] = lead_id\n        self.salvar()'

assert old1 in content, 'PATCH1: old text not found'
content = content.replace(old1, new1)
print('PATCH 1 OK')

# PATCH 2: sender_lock_waiting/timeout/acquired stages
old2 = "            with LockWhatsAppSender() as sender_lock:\n                if not sender_lock.acquired:\n                    logger.error(\"Perfil de envio esta em uso. Abortando.\")\n                    for r in safe_leads:\n                        if not self.dry_run:\n                            settle_lead(r[\"reservation_id\"], r[\"reservation_token\"], \"released\", obs=\"sender_lock_ocupado\")\n                        self.checkpoint.registrar_falha(r[\"lead\"][\"id\"], \"sender_lock_ocupado\")\n                    return 1\n\n                asyncio.run(self._enviar_leads_async(safe_leads))"

new2 = "            # --- Stage: sender_lock_waiting ---\n            for r in safe_leads:\n                self.checkpoint.registrar_estagio(r[\"lead\"][\"id\"], \"sender_lock_waiting\")\n\n            with LockWhatsAppSender() as sender_lock:\n                if not sender_lock.acquired:\n                    logger.error(\"Perfil de envio esta em uso. Abortando.\")\n                    for r in safe_leads:\n                        self.checkpoint.registrar_estagio(r[\"lead\"][\"id\"], \"sender_lock_timeout\")\n                        if not self.dry_run:\n                            settle_lead(r[\"reservation_id\"], r[\"reservation_token\"], \"released\", obs=\"sender_lock_ocupado\")\n                        self.checkpoint.registrar_falha(r[\"lead\"][\"id\"], \"sender_lock_ocupado\", \"sender_lock_timeout\")\n                    return 1\n\n                for r in safe_leads:\n                    self.checkpoint.registrar_estagio(r[\"lead\"][\"id\"], \"sender_lock_acquired\")\n\n                asyncio.run(self._enviar_leads_async(safe_leads))"

assert old2 in content, 'PATCH2: old text not found'
content = content.replace(old2, new2)
print('PATCH 2 OK')

# PATCH 3: sender_session_opening timeout with async context manager
# We need to wrap the SessaoWhatsApp opening with a timeout
old3 = "        async with SessaoWhatsApp(profile_dir) as sessao:\n            page = sessao.page\n            if not page:\n                logger.error(\"Nao foi possivel abrir WhatsApp Web (perfil sender)\")\n                for r in safe_leads:\n                    if not self.dry_run:\n                        settle_lead(r[\"reservation_id\"], r[\"reservation_token\"], \"released\", obs=\"sender_browser_falha\")\n                    self.checkpoint.registrar_falha(r[\"lead\"][\"id\"], \"sender_browser_falha\", \"sender_browser_falha\")\n                    self.checkpoint.limpar_estagio(r[\"lead\"][\"id\"])"

new3 = "        # --- Stage: sender_session_opening ---\n        for r in safe_leads:\n            self.checkpoint.registrar_estagio(r[\"lead\"][\"id\"], \"sender_session_opening\")\n\n        sessao = None\n        try:\n            sessao = await asyncio.wait_for(\n                SessaoWhatsApp(profile_dir).__aenter__(),\n                timeout=60,\n            )\n        except asyncio.TimeoutError:\n            logger.error(\"Timeout ao abrir sessao sender (60s)\")\n            for r in safe_leads:\n                self.checkpoint.registrar_estagio(r[\"lead\"][\"id\"], \"sender_session_timeout\")\n                if not self.dry_run:\n                    settle_lead(r[\"reservation_id\"], r[\"reservation_token\"], \"released\", obs=\"sender_session_timeout\")\n                self.checkpoint.registrar_falha(r[\"lead\"][\"id\"], \"sender_session_timeout\", \"sender_session_timeout\")\n                self.checkpoint.limpar_estagio(r[\"lead\"][\"id\"])\n            return\n\n        try:\n            page = sessao.page\n            if not page:\n                logger.error(\"Nao foi possivel abrir WhatsApp Web (perfil sender)\")\n                for r in safe_leads:\n                    self.checkpoint.registrar_estagio(r[\"lead\"][\"id\"], \"sender_session_timeout\")\n                    if not self.dry_run:\n                        settle_lead(r[\"reservation_id\"], r[\"reservation_token\"], \"released\", obs=\"sender_browser_falha\")\n                    self.checkpoint.registrar_falha(r[\"lead\"][\"id\"], \"sender_browser_falha\", \"sender_session_timeout\")\n                    self.checkpoint.limpar_estagio(r[\"lead\"][\"id\"])"

assert old3 in content, 'PATCH3: old text not found'
content = content.replace(old3, new3)
print('PATCH 3 OK')

# PATCH 4: Add sender_session_opened stage after page is confirmed, and close the session properly
# Find the part after the page validation where we continue to the sending loop
# Also need to add a finally block to close the session
old4 = "                return\n\n            enviados = 0"
new4 = "                return\n\n            for r in safe_leads:\n                self.checkpoint.registrar_estagio(r[\"lead\"][\"id\"], \"sender_session_opened\")\n\n            enviados = 0"

assert old4 in content, 'PATCH4: old text not found'
content = content.replace(old4, new4)
print('PATCH 4 OK')

# PATCH 5: Add finally block to close session - we need to add session cleanup
# Find the last line before "def _settle_nao_seguros"
old5 = "                if i < len(safe_leads) - 1:\n                    self.safety.aguardar_intervalo()\n\n    def _settle_nao_seguros"

new5 = "                if i < len(safe_leads) - 1:\n                    self.safety.aguardar_intervalo()\n\n        finally:\n            if sessao is not None:\n                try:\n                    await sessao.__aexit__(None, None, None)\n                except Exception:\n                    pass\n\n    def _settle_nao_seguros"

assert old5 in content, 'PATCH5: old text not found'
content = content.replace(old5, new5)
print('PATCH 5 OK')

# PATCH 6: Fix needs_manual_reconciliation - only when send_clicked=true
# Find the settle block after send_clicked
old6 = "                if settle_result and settle_result.get(\"outcome\") == \"settled\":\n                    logger.info(\"  Settle confirmado\")\n                    self.checkpoint.registrar_estagio(lead_id, \"settle_sent_done\")\n                else:\n                    logger.warning(\"  Settle: %s\", settle_result)\n                    self.checkpoint.registrar_estagio(lead_id, \"needs_manual_reconciliation\")"

new6 = "                if settle_result and settle_result.get(\"outcome\") == \"settled\":\n                    logger.info(\"  Settle confirmado\")\n                    self.checkpoint.registrar_estagio(lead_id, \"settle_sent_done\", send_clicked=True, outbound_confirmed=True)\n                else:\n                    logger.warning(\"  Settle: %s\", settle_result)\n                    self.checkpoint.registrar_estagio(lead_id, \"outbound_confirming\", send_clicked=True)\n                    self.checkpoint.registrar_estagio(lead_id, \"needs_manual_reconciliation\", send_clicked=True, outbound_confirmed=False)"

assert old6 in content, 'PATCH6: old text not found'
content = content.replace(old6, new6)
print('PATCH 6 OK')

# PATCH 7: send_clicked_unknown should NOT be needs_manual_reconciliation
old7 = "                except asyncio.TimeoutError:\n                    logger.warning(\"  Timeout ao enviar mensagem (20s)\")\n                    self.checkpoint.registrar_estagio(lead_id, \"send_clicked_unknown\")\n                    _failed(\"envio_timeout_possivelmente_enviado\")\n                    self.checkpoint.registrar_falha(lead_id, \"envio_timeout\", \"send_clicked_unknown\")\n                    self.safety.registrar_erro()\n                    self.checkpoint.limpar_estagio(lead_id)\n                    continue"

new7 = "                except asyncio.TimeoutError:\n                    logger.warning(\"  Timeout ao enviar mensagem (20s)\")\n                    self.checkpoint.registrar_estagio(lead_id, \"send_clicked_needs_reconciliation\", send_clicked=True, outbound_confirmed=False)\n                    _failed(\"envio_timeout_possivelmente_enviado\")\n                    self.checkpoint.registrar_falha(lead_id, \"envio_timeout\", \"send_clicked_needs_reconciliation\")\n                    self.safety.registrar_erro()\n                    self.checkpoint.limpar_estagio(lead_id)\n                    continue"

assert old7 in content, 'PATCH7: old text not found'
content = content.replace(old7, new7)
print('PATCH 7 OK')

# PATCH 8: update send_clicked stage to include send_clicked=True
old8 = "                self.checkpoint.registrar_estagio(lead_id, \"send_clicked\")\n\n                logger.info("

new8 = "                self.checkpoint.registrar_estagio(lead_id, \"send_clicked\", send_clicked=True)\n\n                logger.info("

assert old8 in content, 'PATCH8: old text not found'
content = content.replace(old8, new8)
print('PATCH 8 OK')

# Write result
with open('campanha_whatsapp.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('ALL PATCHES APPLIED SUCCESSFULLY')
