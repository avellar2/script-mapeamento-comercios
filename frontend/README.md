# Dashboard - Comércios da Baixada Fluminense

Frontend para visualização dos comércios mapeados na Baixada Fluminense.

## 📊 Funcionalidades

- **Estatísticas em tempo real**: Total de comércios, com/sem site, cidades cobertas
- **Filtros dinâmicos**: Busca por nome, cidade, categoria e presença de site
- **Cards interativos**: Informações detalhadas de cada comércio com hover effects
- **Design responsivo**: Funciona em desktop, tablet e mobile

## 🚀 Como usar

### Opção 1 - PowerShell (Windows, sem instalar nada) ✨ RECOMENDADO
Dê duplo clique em `iniciar.bat` - o dashboard abrirá automaticamente.

### Opção 2 - Versão Standalone (abrir direto no navegador)
1. Execute `gerar-standalone.bat` (requer Node.js instalado)
2. Abra `dashboard-standalone.html` no navegador
3. Os dados já ficam embutidos no arquivo HTML

### Opção 3 - Python (se tiver Python instalado)
Execute `python server.py` na pasta `frontend`

### Nota:
Opções 1 e 3 usam um servidor local porque navegadores bloqueiam carregamento de JSON via `file://` por segurança (CORS). A opção 2 contorna isso embutindo os dados no HTML.

## 🎨 Design

- **Tema**: Data Editorial com visual moderno de dashboard
- **Paleta**: Laranja/âmbar sobre fundo escuro profundo
- **Tipografia**: Space Grotesk (títulos) + Outfit (corpo)
- **Animações**: Stagger fade-in, hover effects, contadores animados

## 📁 Estrutura dos dados

Cada comércio possui:
- `nome`: Nome do estabelecimento
- `endereco`: Endereço completo
- `telefone`: Telefone de contato
- `email`: E-mail (quando disponível)
- `categoria`: Tipo de comércio
- `tem_site`: Booleano indicando presença de website
- `url_site`: URL do site (quando aplicável)
- `avaliacao`: Nota no Google Maps
- `cidade`: Cidade da Baixada Fluminense

## 🔧 Personalização

Edite as variáveis CSS em `:root` para customizar cores:
- `--accent-primary`: Cor principal (laranja)
- `--accent-secondary`: Cor secundária (ciano)
- `--bg-deep`: Fundo da página
- `--bg-card`: Fundo dos cards
