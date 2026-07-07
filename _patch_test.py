#!/usr/bin/env python3
"""Update test to match new async pattern with timeout"""
import os

os.chdir(r'C:\projetos\script-mapear-comercios-whatsapp-dedup')

with open('tests/test_browser_lifecycle.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """def test_enviar_leads_async_usa_sessao_whatsapp():
    \"\"\"_enviar_leads_async usa SessaoWhatsApp como context manager.\"\"\"
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._enviar_leads_async)
    assert 'SessaoWhatsApp' in source
    assert 'async with' in source"""

new = """def test_enviar_leads_async_usa_sessao_whatsapp():
    \"\"\"_enviar_leads_async usa SessaoWhatsApp com timeout.\"\"\"
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._enviar_leads_async)
    assert 'SessaoWhatsApp' in source
    assert 'wait_for' in source"""

assert old in content, 'TEST PATCH: old text not found'
content = content.replace(old, new)

with open('tests/test_browser_lifecycle.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('TEST PATCH OK')
