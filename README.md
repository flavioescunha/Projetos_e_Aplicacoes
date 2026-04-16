<picture>
  <source media="(prefers-color-scheme: dark)" srcset="caminho/para/print-modo-escuro.png">
  <source media="(prefers-color-scheme: light)" srcset="caminho/para/print-modo-claro.png">
  <img alt="Print do Aplicativo" src="caminho/para/print-padrao.png">
</picture>

# 📊 Gerenciador de Investimentos Pessoal

Um aplicativo de código aberto para desktop, desenvolvido em Python, focado em ajudar você a gerenciar sua carteira de investimentos e alcançar seus objetivos financeiros de forma inteligente e automatizada.

Ao contrário de planilhas complexas, este gerenciador possui um motor financeiro embutido que calcula rentabilidade real, corrige metas pela inflação e sugere onde aportar seu dinheiro com base no balanceamento ideal da sua carteira.

> **Baixe agora a versão mais recente sem precisar instalar o Python:** [👉 CLIQUE AQUI PARA BAIXAR O .EXE](https://github.com/flavioescunha/Projetos_e_Aplicacoes/releases/).

---

## 📸 Telas do Aplicativo

Dados fictícios:

<img width="1052" height="682" alt="tela_inicial" src="https://github.com/user-attachments/assets/95107336-9fa7-42fc-8f23-941c4094f063" />

<img width="1052" height="682" alt="tela_aplicacoes" src="https://github.com/user-attachments/assets/0afc5085-fa94-4ed5-9fba-f810a019235d" />

---

## 🚀 Principais Funcionalidades

O Gerenciador foi construído com foco em automação matemática. Ele faz o trabalho pesado por você:

* **📈 Cálculo de TIR (Rentabilidade Real):** Usa o método de Newton-Raphson para calcular a Taxa Interna de Retorno (TIR) exata da sua carteira, lidando com aportes e resgates em datas irregulares.
* **🏦 Correção Automática pela Inflação:** Conecta-se diretamente à API do Banco Central do Brasil (SGS 433) para buscar o IPCA. Suas metas financeiras de longo prazo são atualizadas automaticamente para garantir que você não perca o poder de compra.
* **🎯 Motor de Sugestão de Aportes:** Você define sua "Carteira Ideal" (ex: 25% Tesouro, 20% CDB, 5% Cripto). O aplicativo analisa suas aplicações e sugere exatamente onde você deve colocar o dinheiro do mês para rebalancear o portfólio.
* **🧮 Cálculo de PMT:** Avalia quanto falta para o seu objetivo, o tempo restante e calcula a parcela mensal exata que você precisa investir.
* **🔄 Distribuição em Cascata:** Com um clique, redistribua seu saldo global proporcionalmente entre todos os seus objetivos financeiros baseando-se no que mais precisa de aportes.
* **🚗 Ativos Físicos:** Permite registrar carros, imóveis ou saldo de FGTS compondo o Valor Presente (PV) dos seus objetivos.

---

## 💻 Como usar (Para Usuários)

1. Vá até a aba [Releases](https://github.com/flavioescunha/Projetos_e_Aplicacoes/releases/).
2. Baixe o arquivo `.exe` da versão mais recente.
3. Coloque o arquivo em uma pasta da sua preferência e dê um clique duplo.

> ⚠️ **Aviso sobre o Windows SmartScreen (Falso Positivo):**
> Como este é um projeto independente e gratuito, o Windows pode exibir uma tela azul ou um aviso do *Controle Inteligente de Aplicativos* dizendo que o programa foi bloqueado ou é desconhecido. Isso é um falso positivo comum em programas feitos em Python. Para abrir, clique em **"Mais informações"** e depois em **"Executar mesmo assim"** (ou clique em "Saiba mais" para liberar no Smart App Control).

4. **Pronto!** O aplicativo vai criar automaticamente um arquivo `dados_investimentos.json` na mesma pasta para salvar seu progresso. Faça backup desse arquivo regularmente!
