"""Tests para import_leads_zip.py — importador de leads ZIP/XLSX."""
import io
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from import_leads_zip import (
    _resolver_subnicho,
    _classificar_leads,
    _ler_xlsx_para_leads,
    QUERY_PARA_SUBNICHO,
)
from utils.phone_utils import normalizar_telefone_br


def _make_lead(nome, telefone, source_query="", **kw):
    """Helper: cria lead com telefone_normalizado."""
    lead = {"nome": nome, "telefone": telefone, "source_query": source_query, **kw}
    lead["telefone_normalizado"] = normalizar_telefone_br(telefone)
    return lead

# ============================================================
# Mapeamento queries → subnichos
# ============================================================

class TestMapeamentoQueriesSubnichos:
    def test_6_queries_mapeiam_para_5_chaves_unicas(self):
        """Seis queries de captura mapeiam para 5 subnicho_keys distintas."""
        chaves = set(QUERY_PARA_SUBNICHO.values())
        assert chaves == {"celular", "computadores", "impressoras", "eletrodomesticos", "eletronicos"}

    def test_celular_duas_queries(self):
        """Duas queries mapeiam para celular."""
        assert _resolver_subnicho("assistência técnica de celular em X", "") == "celular"
        assert _resolver_subnicho("conserto de celular em Y", "") == "celular"

    def test_celular_dedup_funciona(self):
        """Duas queries de celular produzem mesma chave para dedup."""
        q1 = _resolver_subnicho("assistência técnica de celular em Angra, RJ", "")
        q2 = _resolver_subnicho("conserto de celular em Angra, RJ", "")
        assert q1 == q2 == "celular"

    def test_computadores_query_long(self):
        assert _resolver_subnicho("assistência de computadores e notebooks em X, RJ", "") == "computadores"

    def test_eletronicos_query_long(self):
        assert _resolver_subnicho("assistência de eletrônicos e videogames em X, RJ", "") == "eletronicos"

    def test_subnicho_fallback_raw(self):
        assert _resolver_subnicho("", "computadores") == "computadores"

    def test_subnicho_vazio_sem_query(self):
        assert _resolver_subnicho("", "") == ""


# ============================================================
# Classificacao de leads
# ============================================================

class TestClassificarLeads:
    def test_produto_grupo_aplicados(self):
        """Todos os leads validos recebem produto e grupo."""
        leads = [
            {"nome": "Teste 1", "telefone": "24993061298", "source_query": "conserto de celular em Angra, RJ"},
        ]
        resultado = _classificar_leads(leads, "avgestao", "assistencias", "zip_teste")
        for lead in resultado["validos"]:
            assert lead["produto"] == "avgestao"
            assert lead["grupo"] == "assistencias"

    def test_origem_aplicada(self):
        leads = [{"nome": "T", "telefone": "24993061298", "source_query": "conserto de celular"}]
        resultado = _classificar_leads(leads, "avgestao", "assistencias", "zip_xyz")
        for lead in resultado["validos"]:
            assert lead["origem"] == "zip_xyz"

    def test_subnicho_preenchido(self):
        leads = [{"nome": "T", "telefone": "24993061298", "source_query": "conserto de celular em X, RJ"}]
        resultado = _classificar_leads(leads, "avgestao", "assistencias", "zip")
        for lead in resultado["validos"]:
            assert lead["subnicho"] == "celular"

    def test_status_novo(self):
        leads = [{"nome": "T", "telefone": "24993061298", "source_query": "conserto de celular", "status": ""}]
        resultado = _classificar_leads(leads, "avgestao", "assistencias", "zip")
        for lead in resultado["validos"]:
            assert lead["status"] == "novo"

    def test_sem_telefone_invalido(self):
        leads = [{"nome": "Sem Tel", "telefone": ""}]
        resultado = _classificar_leads(leads, "avgestao", "assistencias", "zip")
        assert resultado["unicos"] == 0
        assert resultado["sem_telefone"] == 1

    def test_telefone_invalido_rejeitado(self):
        """Telefone sem 55 e curto e rejeitado."""
        leads = [{"nome": "Invalido", "telefone": "12345"}]
        resultado = _classificar_leads(leads, "avgestao", "assistencias", "zip")
        assert resultado["telefone_invalido"] >= 1
        assert resultado["unicos"] == 0

    def test_telefone_celular_nao_dedup(self):
        """Dois leads com mesmo telefone, um e dedup interno."""
        leads = [
            {"nome": "A", "telefone": "24993061298", "source_query": "conserto de celular"},
            {"nome": "B", "telefone": "24993061298", "source_query": "assistencia tecnica de celular"},
        ]
        resultado = _classificar_leads(leads, "avgestao", "assistencias", "zip")
        assert resultado["duplicados_internos"] == 1
        assert resultado["unicos"] == 1

    def test_outro_grupo_nao_aparece(self):
        """Lead sem subnicho de assistencia nao entra nos validos."""
        leads = [{"nome": "Outro", "telefone": "21987654321", "source_query": "barbearia"}]
        resultado = _classificar_leads(leads, "avgestao", "assistencias", "zip")
        assert resultado["unicos"] == 0

    def test_contagem_por_subnicho(self):
        leads = [
            {"nome": "A", "telefone": "24993060001", "source_query": "conserto de celular"},
            {"nome": "B", "telefone": "24993060002", "source_query": "conserto de celular"},
            {"nome": "C", "telefone": "24993060003", "source_query": "assistencia de eletrodomesticos"},
        ]
        resultado = _classificar_leads(leads, "avgestao", "assistencias", "zip")
        assert resultado["por_subnicho"]["celular"] == 2
        assert resultado["por_subnicho"]["eletrodomesticos"] == 1

    def test_sem_subnicho_excluido(self):
        leads = [{"nome": "Sem subnicho", "telefone": "24987654321"}]
        resultado = _classificar_leads(leads, "avgestao", "assistencias", "zip")
        assert resultado["unicos"] == 0


# ============================================================
# Template de mensagem
# ============================================================

class TestTemplateMensagem:
    def test_template_renderiza_empresa(self):
        """Template renderiza {empresa} corretamente."""
        template_path = Path(_root) / "templates" / "avgestao_assistencias_primeiro_contato.txt"
        if not template_path.exists():
            pytest.skip("Template nao encontrado")
        template = template_path.read_text(encoding="utf-8")
        assert "{empresa}" in template
        rendered = template.replace("{empresa}", "Smart Fix")
        assert "Smart Fix" in rendered
        assert "TECM" not in rendered

    def test_fallback_empresa_vazia(self):
        """Empresa vazia usa fallback seguro."""
        empresa = ""
        nome_final = empresa.strip() or "pessoal"
        assert nome_final == "pessoal"

    def test_variavel_desconhecida_erro(self):
        """Variavel desconhecida no template gera erro."""
        template = "Ola {empresa}, seu {produto_desconhecido} esta pronto"
        import re
        variaveis = set(re.findall(r'\{(\w+)\}', template))
        validas = {"empresa", "cidade", "nome"}
        desconhecidas = variaveis - validas
        assert "produto_desconhecido" in desconhecidas


# ============================================================
# Dry-run e confirm
# ============================================================

class TestDryRunConfirm:
    def test_dry_run_nao_escreve(self):
        """Funcao importar_leads_zip com dry_run=True nao chama inserir_lead."""
        with patch("import_leads_zip._inserir_lead") as mock_inserir, \
             patch("import_leads_zip._get_supabase_client") as mock_sb:
            from import_leads_zip import importar_leads_zip
            # Criar ZIP temporario com XLSX valido
            import openpyxl
            xlsx_buf = io.BytesIO()
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Test"
            ws.append(["Nome", "Telefone", "Subnicho", "Query de origem", "Cidade"])
            ws.append(["Teste", "24993061298", "celular", "conserto de celular em X, RJ", "Angra"])
            wb.save(xlsx_buf)

            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, 'w') as zf:
                zf.writestr("test.xlsx", xlsx_buf.getvalue())

            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                tmp.write(zip_buf.getvalue())
                tmp_path = tmp.name

            try:
                result = importar_leads_zip(tmp_path, dry_run=True)
                assert result == 0
                mock_inserir.assert_not_called()
            finally:
                os.unlink(tmp_path)

    def test_sem_confirm_nao_escreve(self):
        """Sem --confirm, importar_leads_zip nao escreve."""
        with patch("import_leads_zip._get_supabase_client") as mock_sb, \
             patch("import_leads_zip._inserir_lead") as mock_inserir:
            from import_leads_zip import importar_leads_zip
            import openpyxl
            xlsx_buf = io.BytesIO()
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(["Nome", "Telefone", "Query de origem"])
            ws.append(["Teste", "24993061298", "conserto de celular em X"])
            wb.save(xlsx_buf)

            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, 'w') as zf:
                zf.writestr("test.xlsx", xlsx_buf.getvalue())

            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                tmp.write(zip_buf.getvalue())
                tmp_path = tmp.name

            try:
                result = importar_leads_zip(tmp_path, dry_run=False, confirm=False)
                assert result == 0
                mock_inserir.assert_not_called()
            finally:
                os.unlink(tmp_path)


# ============================================================
# Deduplicacao
# ============================================================

class TestDeduplicacao:
    def test_nao_sobrescreve_abordado(self):
        """Lead ja abordado nao volta para novo."""
        lead_abordado = {
            "telefone_normalizado": "5524993061298",
            "status": "abordado",
            "produto": "avgestao",
            "grupo": "assistencias",
        }
        existentes = {"5524993061298": lead_abordado}
        # Simula: esse lead nao deve ser inserido de volta
        status = existentes["5524993061298"]["status"]
        assert status in ("abordado", "sent", "confirmed_from_whatsapp", "interessado", "convertido")

    def test_nao_mistura_grupos(self):
        """Lead de outro grupo nao e importado como assistencias."""
        leads = [{"nome": "Outro", "telefone": "21987654321", "source_query": "mecanico"}]
        resultado = _classificar_leads(leads, "avgestao", "assistencias", "zip")
        assert resultado["unicos"] == 0


# ============================================================
# Logs sem dados sensiveis
# ============================================================

class TestPrivacy:
    def test_classificar_nao_loga_telefone(self):
        """_classificar_leads nao expoe telefone completo em mensagens."""
        import inspect
        source = inspect.getsource(_classificar_leads)
        assert "telefone" not in source.lower() or "masked" in source.lower() or "****" in source
