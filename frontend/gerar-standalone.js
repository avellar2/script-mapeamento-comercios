// Gerar versão standalone do dashboard com dados embutidos
// Execute: node gerar-standalone.js

const fs = require('fs');
const path = require('path');

console.log('📦 Gerando versão standalone...');

// Ler o HTML original
let html = fs.readFileSync(path.join(__dirname, 'dashboard.html'), 'utf8');

// Ler os dados JSON
const jsonPath = path.join(__dirname, '../output/progresso.json');
const jsonContent = fs.readFileSync(jsonPath, 'utf8');
const data = JSON.parse(jsonContent);

// Extrair apenas os comercios e criar uma versão compacta
const comerciosCompact = JSON.stringify(data.comercios || []);

// Substituir a função loadData para usar dados embutidos
const newLoadData = `
async function loadData() {
    // Dados embutidos - versão standalone
    comerciosData = ${comerciosCompact};
    initializeApp();
}
`;

// Substituir a função loadData original
html = html.replace(/async function loadData\(\) \{[\s\S]*?\n        \}/, newLoadData.trim());

// Salvar nova versão
fs.writeFileSync(path.join(__dirname, 'dashboard-standalone.html'), html, 'utf8');

console.log(`✅ Versão standalone criada: dashboard-standalone.html`);
console.log(`📊 ${data.comercios.length} comércios incluídos`);
console.log('');
console.log('Abra dashboard-standalone.html diretamente no navegador!');
