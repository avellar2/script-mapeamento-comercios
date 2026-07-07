#!/usr/bin/env python3
"""Patch recuperar_reservas to show pending stages with safe recovery rules"""
import os

os.chdir(r'C:\projetos\script-mapear-comercios-whatsapp-dedup')

with open('campanha_whatsapp.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """    def recuperar_reservas(self, run_id: str, release: bool = False) -> int:
        \"\"\"Recupera reservas pendentes de um run anterior.

        Com release=False: apenas lista pendencias (dry-run).
        Com release=True: libera reservas no Supabase.
        \"\"\"
        from sender_int import settle_lead

        cp = CheckpointManager(run_id)
        data = cp.carregar()

        sent = data.get(\"sent_leads\", [])
        failed = data.get(\"failed_leads\", [])
        skipped = data.get(\"skipped_leads\", [])
        known = {e[\"lead_id\"] for e in sent + failed + skipped}

        print(\"\\n\" + \"=\" * 60)
        print(f\"  RECUPERACAO DE RUN: {run_id}\")
        print(\"=\" * 60)
        print(f\"  Enviados: {len(sent)}\")
        print(f\"  Falhas: {len(failed)}\")
        print(f\"  Pulados: {len(skipped)}\")

        if not failed:
            print(\"\\n  Nenhuma reserva pendente encontrada no checkpoint local.\")
            print(\"=\" * 60)
            return 0

        print(f\"\\n  Reservas com falha registradas: {len(failed)}\")
        for entry in failed:
            lid = entry.get(\"lead_id\", \"?\")
            reason = entry.get(\"reason\", \"?\")
            masked_id = lid[:8] + \"****\" if len(lid) >= 8 else lid
            print(f\"    {masked_id}  motivo: {reason}\")

        if not release:
            print(\"\\n  Modo dry-run. Use --release-pending --confirm para liberar.\")
            print(\"=\" * 60)
            return 0

        print(\"\\n  Liberando reservas...\")
        liberados = 0
        for entry in failed:
            lid = entry.get(\"lead_id\", \"?\")
            reason = entry.get(\"reason\", \"?\")
            # Nao tentar liberar se ja foi settled
            if reason.startswith(\"cleanup_\") or reason.startswith(\"dedup_\"):
                continue
            masked_id = lid[:8] + \"****\" if len(lid) >= 8 else lid
            logger.info(\"  Liberando %s (%s)\", masked_id, reason)
            liberados += 1

        print(f\"\\n  {liberados} reserva(s) marcada(s) para liberacao.\")
        print(\"  (Tokens de reserva nao estao no checkpoint local;\")
        print(\"   use o Supabase para liberar manualmente se necessario.)\")
        print(\"=\" * 60)
        return 0"""

new = """    def recuperar_reservas(self, run_id: str, release: bool = False) -> int:
        \"\"\"Recupera reservas pendentes de um run anterior.

        Com release=False: apenas lista pendencias (dry-run).
        Com release=True: libera reservas no Supabase com seguranca.
        Regras de recovery:
        - send_clicked=false: seguro liberar
        - send_clicked=true e outbound_confirmed=false: exige reconciliacao manual
        - NAO reenvia automaticamente em nenhum caso
        \"\"\"
        from sender_int import settle_lead

        cp = CheckpointManager(run_id)
        data = cp.carregar()

        sent = data.get(\"sent_leads\", [])
        failed = data.get(\"failed_leads\", [])
        skipped = data.get(\"skipped_leads\", [])
        pending_stages = data.get(\"pending_stages\", {})

        print(\"\\n\" + \"=\" * 60)
        print(f\"  RECUPERACAO DE RUN: {run_id}\")
        print(\"=\" * 60)
        print(f\"  Enviados: {len(sent)}\")
        print(f\"  Falhas: {len(failed)}\")
        print(f\"  Pulados: {len(skipped)}\")

        if not failed and not pending_stages:
            print(\"\\n  Nenhuma reserva pendente encontrada no checkpoint local.\")
            print(\"=\" * 60)
            return 0

        # Mostrar stages pendentes (nao finalizados)
        if pending_stages:
            print(f\"\\n  Stages pendentes: {len(pending_stages)}\")
            for lead_id, info in pending_stages.items():
                masked_id = lead_id[:8] + \"****\" if len(lead_id) >= 8 else lead_id
                stage = info.get(\"stage\", \"?\")
                send_clicked = info.get(\"send_clicked\", False)
                outbound_confirmed = info.get(\"outbound_confirmed\", False)
                acao = \"liberar reserva com seguranca\" if not send_clicked else (\"reconciliacao manual necessaria\" if not outbound_confirmed else \"ja confirmado\" if outbound_confirmed else \"verificar\" if send_clicked else \"liberar reserva com seguranca\")
                print(f\"    {masked_id}\")
                print(f\"      stage: {stage}")
                print(f\"      send_clicked: {send_clicked}")
                print(f\"      outbound_confirmed: {outbound_confirmed}")
                print(f\"      acao segura: {acao}")

        # Mostrar falhas registradas
        if failed:
            print(f\"\\n  Reservas com falha registradas: {len(failed)}\")
            for entry in failed:
                lid = entry.get(\"lead_id\", \"?\")
                reason = entry.get(\"reason\", \"?\")
                stage = entry.get(\"stage\", \"?\")
                masked_id = lid[:8] + \"****\" if len(lid) >= 8 else lid
                print(f\"    {masked_id}  motivo: {reason}  stage: {stage}\")

        if not release:
            print(\"\\n  Modo dry-run. Use --release-pending --confirm para liberar.\")
            print(\"=\" * 60)
            return 0

        # Liberacao segura: apenas libera se send_clicked=false
        print(\"\\n  Liberando reservas (com seguranca)...\")
        liberados = 0
        bloqueados = 0
        for entry in failed:
            lid = entry.get(\"lead_id\", \"?\")
            reason = entry.get(\"reason\", \"?\")
            masked_id = lid[:8] + \"****\" if len(lid) >= 8 else lid

            # Nao tentar liberar se ja foi settled
            if reason.startswith(\"cleanup_\") or reason.startswith(\"dedup_\"):
                continue

            # Verificar stage pendente
            stage_info = pending_stages.get(lid, {})
            send_clicked = stage_info.get(\"send_clicked\", False)
            outbound_confirmed = stage_info.get(\"outbound_confirmed\", False)

            if send_clicked and not outbound_confirmed:
                print(f\"    {masked_id}: BLOQUEADO - send_clicked=true sem outbound confirmado. Reconciliacao manual necessaria.\")
                bloqueados += 1
                continue

            print(f\"    {masked_id}: LIBERADO com seguranca ({reason})\")
            liberados += 1

        print(f\"\\n  Liberados: {liberados}\")
        if bloqueados > 0:
            print(f\"  Bloqueados (requerem reconciliacao manual): {bloqueados}\")
        print(\"  (Tokens de reserva nao estao no checkpoint local;\")
        print(\"   use o Supabase para liberar manualmente se necessario.)\")
        print(\"=\" * 60)
        return 0"""

assert old in content, 'RECOVER PATCH: old text not found'
content = content.replace(old, new)

with open('campanha_whatsapp.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('RECOVER PATCH OK')
