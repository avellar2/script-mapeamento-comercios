# Sistema de Landing Pages por Nicho

Este projeto é uma biblioteca de landing pages reutilizáveis por nicho. Cada template base pode ser personalizado para clientes reais através de arquivos JSON de configuração.

## Estrutura

```
frontend/clinica-sorriso-prime/
├── app/
│   ├── page.tsx                    # Demo base (Clínica Sorriso Prime)
│   ├── previews/[slug]/            # Rota dinâmica de prévias
│   │   ├── page.tsx                # Server component (lê JSON)
│   │   └── PreviewPageClient.tsx   # Client component (renderiza)
│   └── components/                 # Componentes da demo original
├── components/
│   ├── sections/                   # Seções reutilizáveis parameterizadas
│   │   ├── NavigationSection.tsx
│   │   ├── HeroSection.tsx
│   │   ├── ServiceGridSection.tsx
│   │   ├── DifferentialsSection.tsx
│   │   ├── TestimonialsSection.tsx
│   │   ├── LocationSection.tsx
│   │   ├── FAQSection.tsx
│   │   ├── FooterCTASection.tsx
│   │   ├── FooterSection.tsx
│   │   ├── FloatingWhatsAppButton.tsx
│   │   └── ThemeWrapper.tsx
│   └── templates/                  # Templates por nicho
│       ├── DentistTemplate.tsx
│       ├── LawyerTemplate.tsx
│       ├── BeautyTemplate.tsx
│       ├── BarberTemplate.tsx
│       ├── FoodTemplate.tsx
│       ├── TechnicalServiceTemplate.tsx
│       ├── ChurchEventTemplate.tsx
│       ├── RealEstateTemplate.tsx
│       ├── AutoTemplate.tsx
│       ├── CourseTemplate.tsx
│       ├── CustomProductsTemplate.tsx
│       ├── TeamSection.tsx
│       └── TemplateRenderer.tsx
├── data/clients/                   # Configurações dos clientes
│   ├── clinica-sorriso-prime.json
│   └── dr-joao-silva.json
├── lib/
│   ├── clients.ts                  # Leitura dos dados dos clientes
│   └── whatsapp.ts                 # Gerador de link WhatsApp
└── types/
    └── client.ts                   # Tipos TypeScript
```

## Como Adicionar um Novo Cliente

### 1. Criar o arquivo JSON

Crie um arquivo em `data/clients/` com o slug do cliente:

```
data/clients/nome-do-cliente.json
```

### 2. Preencher os campos obrigatórios

```json
{
  "slug": "nome-do-cliente",
  "template": "advogado",
  "businessName": "Nome do Negócio",
  "headline": "Frase principal chamativa",
  "subheadline": "Descrição complementar do negócio.",
  "whatsapp": "5521999999999",
  "city": "Cidade",
  "address": "Endereço completo",
  "services": ["Serviço 1", "Serviço 2"],
  "differentials": ["Diferencial 1", "Diferencial 2"],
  "images": {
    "hero": ["https://images.unsplash.com/..."]
  },
  "brandColors": {
    "primary": "#0F172A",
    "secondary": "#C8A45D",
    "accent": "#25D366"
  }
}
```

### 3. Escolher o template

Valores disponíveis para o campo `template`:

| Valor                  | Nicho                |
|------------------------|----------------------|
| `advogado`            | Advocacia            |
| `dentista`            | Odontologia          |
| `estetica`            | Estética / Beleza    |
| `barbearia`           | Barbearia            |
| `cardapio`            | Cardápio Digital     |
| `assistencia-tecnica` | Assistência Técnica  |
| `igreja-evento`       | Igreja / Evento      |
| `imobiliaria`         | Imobiliária          |
| `automotiva`          | Automotiva           |
| `cursos`              | Cursos / Educação    |
| `personalizado`       | Produtos Personalizados |

### 4. Colocar as fotos do cliente

As URLs das imagens podem ser:
- URLs externas (Unsplash, Imgur, CDN)
- Caminhos relativos a partir da pasta `public/`

Para usar fotos locais, coloque em:
```
public/clients/nome-do-cliente/foto-1.jpg
```

E no JSON referencie como:
```json
"images": {
  "hero": ["/clients/nome-do-cliente/foto-1.jpg"]
}
```

### 5. Acessar a prévia

```
http://localhost:3000/previews/nome-do-cliente
```

Para build de produção:
```bash
npm run build
```

As páginas são geradas estaticamente via `generateStaticParams()`.

## Templates Disponíveis

### `dentista` (Odontologia)
Seções: Navigation, Hero, Services, Differentials, Team, Testimonials, Location, FAQ, FooterCTA, Footer, FloatingWhatsApp

### `advogado` (Advocacia)
Seções: Navigation, Hero, Services, Differentials, Testimonials, Location, FAQ, FooterCTA, Footer, FloatingWhatsApp

### `estetica` (Estética/Beleza)
Seções: Navigation, Hero, Services, Differentials, Testimonials, Location, FooterCTA, Footer, FloatingWhatsApp

### `barbearia` (Barbearia)
Seções: Navigation, Hero, Services, Differentials, Testimonials, Location, FooterCTA, Footer, FloatingWhatsApp

### `cardapio` (Cardápio Digital)
Seções: Navigation, Hero, Services, Differentials, Testimonials, Location, FooterCTA, Footer, FloatingWhatsApp

### `assistencia-tecnica` (Assistência Técnica)
Seções: Navigation, Hero, Services, Differentials, Testimonials, Location, FAQ, FooterCTA, Footer, FloatingWhatsApp

### `igreja-evento` (Igreja/Evento)
Seções: Navigation, Hero, Services, Differentials, Location, FooterCTA, Footer, FloatingWhatsApp

### `imobiliaria` (Imobiliária)
Seções: Navigation, Hero, Services, Differentials, Testimonials, Location, FooterCTA, Footer, FloatingWhatsApp

### `automotiva` (Automotiva)
Seções: Navigation, Hero, Services, Differentials, Testimonials, Location, FAQ, FooterCTA, Footer, FloatingWhatsApp

### `cursos` (Cursos/Educação)
Seções: Navigation, Hero, Services, Differentials, Testimonials, FooterCTA, Footer, FloatingWhatsApp

### `personalizado` (Produtos Personalizados)
Seções: Navigation, Hero, Services, Differentials, Testimonials, Location, FooterCTA, Footer, FloatingWhatsApp

## Campos do JSON de Configuração

### Campos Obrigatórios
| Campo           | Tipo     | Descrição                              |
|-----------------|----------|----------------------------------------|
| `slug`          | string   | Identificador URL do cliente           |
| `template`      | string   | Nome do template (ver tabela acima)    |
| `businessName`  | string   | Nome do negócio                        |
| `headline`      | string   | Frase principal do hero                |
| `subheadline`   | string   | Descrição complementar                 |
| `whatsapp`      | string   | Número WhatsApp (com código país)      |
| `city`          | string   | Cidade                                 |
| `address`       | string   | Endereço completo                      |
| `services`      | string[] | Lista de serviços                      |
| `differentials` | string[] | Lista de diferenciais                  |
| `images`        | object   | URLs de imagens (hero, gallery, team)  |
| `brandColors`   | object   | Cores primary, secondary, accent        |

### Campos Opcionais
| Campo            | Tipo     | Descrição                              |
|------------------|----------|----------------------------------------|
| `neighborhood`   | string   | Bairro                                 |
| `instagram`      | string   | URL do Instagram                       |
| `googleMapsUrl`  | string   | URL de embed do Google Maps            |
| `rating`         | string   | Avaliação (ex: "4.8")                  |
| `reviewsCount`   | string   | Número de avaliações                    |
| `team`           | array    | Membros da equipe                      |
| `testimonials`   | array    | Depoimentos de clientes                |
| `faq`            | array    | Perguntas frequentes                    |
| `navLinks`       | array    | Links de navegação personalizados       |
| `trustSignals`   | string[] | Sinais de confiança no hero            |
| `ctaLabel`       | string   | Texto do botão CTA                     |
| `ctaText`        | string   | Texto descritivo do CTA                |
| `sectionTitles`  | object   | Títulos personalizados por seção        |
| `openingHours`   | string   | Horário de atendimento                  |
| `phone`          | string   | Telefone de contato                     |
| `email`          | string   | Email de contato                        |
| `notes`          | string   | Notas internas sobre o cliente          |

## Link WhatsApp

O link WhatsApp é gerado automaticamente pelo helper em `lib/whatsapp.ts`:

```
https://wa.me/5521999999999?text=Olá, vim pela página e gostaria de mais informações sobre Dr. João Silva Advocacia.
```

A mensagem é personalizada com o nome do negócio.

## Cores da Marca

As cores em `brandColors` controlam o tema da página:
- `primary`: Cor principal (botões, títulos, destaques)
- `primaryLight`: Versão clara (opcional, gerada automaticamente se omitida)
- `primaryDark`: Versão escura (opcional, gerada automaticamente se omitida)
- `secondary`: Cor secundária (detalhes)
- `accent`: Cor de destaque (CTAs, badges)

## Demo Base

A demo original da Clínica Sorriso Prime continua acessível em:
```
http://localhost:3000/
```

Ela não é afetada pelo sistema de templates.

## Desenvolvimento

```bash
# Instalar dependências
npm install

# Rodar em desenvolvimento
npm run dev

# Build de produção
npm run build

# Servir build estático
npx serve out
```