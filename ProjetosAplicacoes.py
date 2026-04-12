import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import json
import os
from datetime import datetime
import requests
import calendar
import tkinter.font as tkfont
from datetime import datetime, timedelta

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

ARQUIVO_JSON = "dados_investimentos.json"

class AppInvest(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gerenciador de Investimentos")
        self.geometry("1050x650")

        style = ttk.Style()
        # O padding funciona como (esquerda, topo, direita, baixo)
        # Aumente os valores de topo e baixo (atualmente 10) se precisar de mais espaço
        style.configure("Treeview.Heading", padding=(0, 10, 0, 10))

        self.dados = self.carregar_dados()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- HEADER SUPERIOR ---
        self.frame_top = ctk.CTkFrame(self)
        self.frame_top.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        self.label_titulo = ctk.CTkLabel(self.frame_top, text="Meu Patrimônio", font=("Roboto", 24, "bold"))
        self.label_titulo.pack(side="left", padx=20, pady=10)

        self.btn_novo = ctk.CTkButton(self.frame_top, text="+ Novo", command=self.acao_botao_novo)
        self.btn_novo.pack(side="right", padx=20)


        # --- BARRA DE ABAS E SALDOS ---
        self.frame_menu = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_menu.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.frame_menu.grid_columnconfigure(0, weight=1) 
        self.frame_menu.grid_columnconfigure(1, weight=0) 
        self.frame_menu.grid_columnconfigure(2, weight=1) 

        # ESQUERDA: Agora exibe o Montante Total em Aplicações dos Objetivos
        self.label_total_aplicar = ctk.CTkLabel(self.frame_menu, text="Montante em Objetivos: R$ 0,00", font=("Roboto", 16, "bold"), text_color="#E67E22")
        self.label_total_aplicar.grid(row=0, column=0, sticky="w", padx=(10, 0))

        # CENTRO: Botões de Abas
        self.abas = ctk.CTkSegmentedButton(self.frame_menu, values=["Objetivos", "Aplicações"], command=self.mudar_aba)
        self.abas.set("Objetivos") 
        self.abas.grid(row=0, column=1)

        # DIREITA: Saldo Total das Aplicações
        self.label_saldo_total = ctk.CTkLabel(self.frame_menu, text="Saldo Total: R$ 0,00", font=("Roboto", 16, "bold"), text_color="#2FA572")
        self.label_saldo_total.grid(row=0, column=2, sticky="e", padx=(0, 10))


        # --- ÁREA DE CONTEÚDO DAS TABELAS ---
        self.frame_conteudo = ctk.CTkFrame(self)
        self.frame_conteudo.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.frame_conteudo.grid_columnconfigure(0, weight=1)
        self.frame_conteudo.grid_rowconfigure(0, weight=1)

        self.tab_obj = ctk.CTkFrame(self.frame_conteudo, fg_color="transparent")
        self.tab_app = ctk.CTkFrame(self.frame_conteudo, fg_color="transparent")

        self.tab_obj.grid(row=0, column=0, sticky="nsew")
        self.tab_app.grid(row=0, column=0, sticky="nsew")

        self.setup_tabela_objetivos()
        self.setup_tabela_aplicacoes()
        
        self.tab_obj.tkraise()
        self.atualizar_tabelas_principais()

    def abrir_config_taxa_pmt(self, recarregar=True):
        janela = self.criar_janela_secundaria("Configurar Taxa do PMT", 450, 250)
        
        # O grab_set() "trava" o clique no app de fundo enquanto essa tela estiver aberta
        janela.grab_set()

        ctk.CTkLabel(janela, text="Como deseja projetar os juros dos seus aportes?", font=("Roboto", 14, "bold")).pack(pady=10)

        var_modo = tk.StringVar(value=self.dados.get("config_taxa_pmt", {}).get("modo", "fixo"))

        frame_radios = ctk.CTkFrame(janela, fg_color="transparent")
        frame_radios.pack(pady=10)

        rb_auto = ctk.CTkRadioButton(frame_radios, text="Automático (Usar TIR Real da Carteira)", variable=var_modo, value="auto")
        rb_auto.grid(row=0, column=0, sticky="w", pady=5, columnspan=2)

        rb_fixo = ctk.CTkRadioButton(frame_radios, text="Taxa Fixa (% ao mês):", variable=var_modo, value="fixo")
        rb_fixo.grid(row=1, column=0, sticky="w", pady=5)

        ent_taxa = ctk.CTkEntry(frame_radios, width=70)
        ent_taxa.grid(row=1, column=1, padx=10)
        
        # Preenche com 0,5% ou o que já estiver salvo
        valor_atual = self.dados.get("config_taxa_pmt", {}).get("valor", 0.005) * 100
        ent_taxa.insert(0, f"{valor_atual:.2f}".replace(".", ","))

        def salvar():
            modo = var_modo.get()
            valor = 0.005
            if modo == "fixo":
                try:
                    valor = float(ent_taxa.get().replace(",", ".")) / 100
                except ValueError:
                    messagebox.showerror("Erro", "Valor inválido!", parent=janela)
                    return
            
            self.dados["config_taxa_pmt"] = {"modo": modo, "valor": valor}
            self.salvar_dados()
            janela.destroy()
            
            # Recarrega as tabelas para aplicar a nova regra na hora
            if recarregar:
                self.atualizar_tabelas_principais()

        ctk.CTkButton(janela, text="Salvar Preferência", command=salvar).pack(pady=15)
        
        # Faz o sistema "esperar" essa janela fechar antes de continuar processando o resto
        self.wait_window(janela)
        
        # Prevenção: se o usuário fechar no 'X' sem salvar, gravamos o padrão para ele não ficar preso num loop
        if "config_taxa_pmt" not in self.dados:
            self.dados["config_taxa_pmt"] = {"modo": "fixo", "valor": 0.005}
            self.salvar_dados()

    

    # --- LÓGICA DE DATAS E MATEMÁTICA FINANCEIRA --

    def calcular_xirr(self, transacoes):
        """
        Calcula a TIR anualizada para fluxos de caixa em datas irregulares.
        transacoes: lista de tuplas (datetime, valor_float)
        """
        if not transacoes:
            return 0.0

        # Ordenar cronologicamente
        transacoes.sort(key=lambda x: x[0])
        data_inicial = transacoes[0][0]

        # Verifica se há pelo menos um fluxo negativo e um positivo
        tem_positivo = any(v > 0 for _, v in transacoes)
        tem_negativo = any(v < 0 for _, v in transacoes)
        if not (tem_positivo and tem_negativo):
            return 0.0

        # Função do Valor Presente Líquido (VPL)
        def xnpv(taxa):
            if taxa <= -1.0: # Evita raiz complexa ou divisão por zero
                return float('inf')
            total = 0.0
            for data, valor in transacoes:
                dias = (data - data_inicial).days
                total += valor / ((1.0 + taxa) ** (dias / 365.0))
            return total

        # Método de Newton-Raphson para zerar o VPL
        taxa_estimada = 0.10 # Chute inicial de 10% ao ano
        for _ in range(100): # Tenta até 100 vezes
            f_x = xnpv(taxa_estimada)
            if abs(f_x) < 1e-5: # Precisão alcançada
                return taxa_estimada
            
            # Derivada (aproximação numérica)
            f_x_mais_delta = xnpv(taxa_estimada + 0.0001)
            derivada = (f_x_mais_delta - f_x) / 0.0001
            
            if derivada == 0:
                break
                
            taxa_estimada = taxa_estimada - (f_x / derivada)

        return taxa_estimada

    def calcular_tir_media_carteira(self):
        """
        Varre as aplicações, monta o fluxo de caixa consolidado e calcula a TIR.
        O primeiro movimento de cada aplicação é SEMPRE tratado como aporte.
        """
        fluxo_caixa = []
        saldo_total_hoje = 0.0
        hoje = datetime.now()

        for app_info in self.dados.get("aplicacoes", {}).values():
            saldo_total_hoje += app_info.get("saldo", 0.0)
            movimentos = app_info.get("movimentos", [])
            
            # 1. Extrai e converte as datas para podermos ordenar cronologicamente
            movimentos_processados = []
            for mov in movimentos:
                if len(mov) >= 3:
                    data_str = mov[0]
                    desc = str(mov[1]).lower()
                    valor = float(mov[2])
                    
                    try:
                        data_mov = datetime.strptime(data_str, "%d/%m/%Y")
                        movimentos_processados.append({'data': data_mov, 'desc': desc, 'valor': valor})
                    except ValueError:
                        continue # Ignora datas inválidas
            
            # 2. Ordena os movimentos da aplicação da data mais antiga para a mais nova
            movimentos_processados.sort(key=lambda x: x['data'])
            
            # 3. Varre os movimentos ordenados
            for i, mov in enumerate(movimentos_processados):
                
                # Pegamos o valor absoluto (sempre positivo) para podermos controlar o sinal manualmente
                valor_absoluto = abs(mov['valor'])
                
                # --- A GRANDE SACADA ESTÁ AQUI ---
                # Se for o movimento de abertura (índice 0), força a ser um Aporte (-)
                if i == 0:
                    fluxo_caixa.append((mov['data'], -valor_absoluto))
                    continue 
                
                # Para os demais movimentos, segue a regra normal das palavras
                if "aporte" in mov['desc'] or "compra" in mov['desc'] or "depósito" in mov['desc'] or "deposito" in mov['desc']:
                    # Aporte: Dinheiro sai do bolso (Negativo)
                    fluxo_caixa.append((mov['data'], -valor_absoluto))
                    
                elif "saque" in mov['desc'] or "venda" in mov['desc'] or "resgate" in mov['desc']:
                    # Saque: Dinheiro entra no bolso (Positivo)
                    fluxo_caixa.append((mov['data'], valor_absoluto))

        # Adiciona o saldo atual como um grande "resgate" final na data de hoje
        if saldo_total_hoje > 0:
            fluxo_caixa.append((hoje, saldo_total_hoje))

        # Calcula a TIR
        tir_anual = self.calcular_xirr(fluxo_caixa)
        
        # Converte para porcentagem
        tir_percentual = tir_anual * 100

           
        return tir_percentual

    def corrigir_valor_pela_inflacao(self, valor_inicial, data_inicial_str):
        """
        Corrige um valor pelo IPCA (SGS 433) calculando pro-rata para aportes no meio do mês
        e extrapolando datas recentes sem divulgação oficial usando a média dos últimos 12 meses.
        """
        try:
            data_inicial = datetime.strptime(data_inicial_str, "%d/%m/%Y")
            hoje = datetime.now()
        except ValueError:
            return valor_inicial

        # Se a data for no futuro ou hoje, não há inflação a aplicar
        if data_inicial >= hoje:
            return valor_inicial

        # Força a busca a partir do dia 01 do mês do aporte para pegar a taxa daquele mês
        data_busca_str = f"01/{data_inicial.strftime('%m/%Y')}"
        data_final_str = hoje.strftime("%d/%m/%Y")
        
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json&dataInicial={data_busca_str}&dataFinal={data_final_str}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            dados = response.json()
        except Exception:
            # Em caso de erro de conexão com o BCB, retorna o valor sem correção
            return valor_inicial
            
        if not dados:
            return valor_inicial

        valor_corrigido = float(valor_inicial)
        ultimas_taxas = [] # Guarda histórico para a projeção final

        # 1. Aplicando os meses com dados oficiais do Banco Central
        for item in dados:
            mes_ano = item['data'] # Formato da API é DD/MM/AAAA, sempre dia 01
            taxa_mensal = float(item['valor']) / 100.0
            ultimas_taxas.append(taxa_mensal)
            
            dt_mes = datetime.strptime(mes_ano, "%d/%m/%Y")
            dias_no_mes = calendar.monthrange(dt_mes.year, dt_mes.month)[1]

            fator_aplicar = 1 + taxa_mensal

            # É o mês de início? Calcula apenas a fração de dias desde o aporte até o fim do mês
            if dt_mes.year == data_inicial.year and dt_mes.month == data_inicial.month:
                dias_restantes = dias_no_mes - data_inicial.day + 1
                if dias_restantes < dias_no_mes:
                    fator_aplicar = (1 + taxa_mensal) ** (dias_restantes / dias_no_mes)

            valor_corrigido *= fator_aplicar

        # 2. Extrapolação (Pro-rata para os dias sem dados até 'hoje')
        # Pega a data da última leitura da API e encontra qual foi o último dia daquele mês
        ultima_data_api = datetime.strptime(dados[-1]['data'], "%d/%m/%Y")
        dias_no_ultimo_mes = calendar.monthrange(ultima_data_api.year, ultima_data_api.month)[1]
        data_fim_cobertura = ultima_data_api.replace(day=dias_no_ultimo_mes)
        
        # Se hoje for maior que o último dia coberto pelo BCB, precisamos projetar o resto
        if hoje > data_fim_cobertura:
            dias_descobertos = (hoje - data_fim_cobertura).days
            
            # Pega até os últimos 12 meses para fazer uma média (anualizada)
            taxas_para_media = ultimas_taxas[-12:] if len(ultimas_taxas) >= 12 else ultimas_taxas
            
            if taxas_para_media:
                media_mensal_projetada = sum(taxas_para_media) / len(taxas_para_media)
                
                # Assume meses de 30 dias para a projeção matemática padrão de mercado
                fator_extrapolado = (1 + media_mensal_projetada) ** (dias_descobertos / 30.0)
                valor_corrigido *= fator_extrapolado

        return valor_corrigido

    def calcular_meses_restantes(self, data_fim_str):
        try:
            f = "%d/%m/%Y"
            d_fim = datetime.strptime(data_fim_str, f)
            hoje = datetime.now()
            if d_fim <= hoje: return 1 
            n = (d_fim.year - hoje.year) * 12 + (d_fim.month - hoje.month)
            return max(n, 1) 
        except ValueError:
            return 1

    def calcular_pmt(self, pv, fv, n, i=0.005):
        if n <= 0: return 0
        if i == 0: return max(0, (fv - pv) / n)
        
        futuro_pv = pv * ((1 + i) ** n)
        falta = fv - futuro_pv
        
        if falta <= 0: return 0
        
        fator_anuidade = (((1 + i) ** n) - 1) / i
        pmt = falta / (fator_anuidade * (1 + i))
        return pmt

    def carregar_dados(self):
        carteira_default = {
            "Tesouro Selic": 25.0,
            "Tesouro Aposentadoria +Renda Extra": 25.0,
            "CDB": 20.0,
            "DIVD11": 4.17,
            "BOVA11": 4.17,
            "IVVB11": 4.16,
            "KNCA11": 2.08,
            "IFRA11": 2.08,
            "KNCR11": 2.08,
            "BTLG11": 2.08,
            "HGLG11": 2.09,
            "LVBI11": 2.09,
            "Bitcoin": 5.0
        }
        
        dados_padrao = {"objetivos": {}, "aplicacoes": {}, "carteira_ideal": carteira_default}
        
        if os.path.exists(ARQUIVO_JSON):
            try:
                with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    # Adiciona a carteira ideal em JSONs antigos que não tinham essa chave
                    if "carteira_ideal" not in dados:
                        dados["carteira_ideal"] = carteira_default
                    return dados
            except Exception:
                return dados_padrao
        return dados_padrao
        
        dados_padrao = {"objetivos": {}, "aplicacoes": {}, "carteira_ideal": carteira_default}
        
        if os.path.exists(ARQUIVO_JSON):
            try:
                with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    # Adiciona a carteira ideal em JSONs antigos que não tinham essa chave
                    if "carteira_ideal" not in dados:
                        dados["carteira_ideal"] = carteira_default
                    return dados
            except Exception:
                return dados_padrao
        return dados_padrao

    def salvar_dados(self):
        with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
            json.dump(self.dados, f, indent=4, ensure_ascii=False)

    def mudar_aba(self, valor_selecionado):
        if valor_selecionado == "Objetivos":
            self.tab_obj.tkraise()
        else:
            self.tab_app.tkraise()

    def acao_botao_novo(self):
        if self.abas.get() == "Objetivos":
            self.abrir_janela_objetivo()
        else:
            self.abrir_janela_aplicacao()

    # --- SETUP DAS TABELAS ---

    def ajustar_larguras_tabela(self, tree):
        """
        Ajusta a largura das colunas dinamicamente para o maior valor entre:
        o conteúdo das células ou a maior linha do cabeçalho.
        """
        # Pega a fonte padrão usada pelo sistema para medir os pixels
        fonte = tkfont.nametofont("TkDefaultFont")
        
        for col in tree["columns"]:
            texto_titulo = tree.heading(col, "text")
            
            # Quebra o título onde houver \n e pega a largura da maior linha do título
            larguras_titulo = [fonte.measure(linha) for linha in texto_titulo.split("\n")]
            largura_maxima = max(larguras_titulo) if larguras_titulo else 0
            
            # Varre todas as linhas de dados daquela coluna para ver se algum valor é maior
            for item in tree.get_children(""):
                valor = str(tree.set(item, col))
                largura_celula = fonte.measure(valor)
                if largura_celula > largura_maxima:
                    largura_maxima = largura_celula
            
            # Aplica a largura final com 20 pixels de margem de respiro
            largura_final = largura_maxima + 20
            tree.column(col, width=largura_final, minwidth=largura_final)

    def redistribuir_saldos_global(self):
        # 1. Trava de segurança
        if not messagebox.askyesno("Confirmar Redistribuição", 
                                   "Isso irá zerar a alocação atual de todos os seus objetivos e redistribuir todo o seu dinheiro investido proporcionalmente ao que falta (calculado pelo PMT).\n\nDeseja continuar?"):
            return

        # 2. Pegar TODO o dinheiro das aplicações
        saldo_total_apps = sum(app.get("saldo", 0.0) for app in self.dados.get("aplicacoes", {}).values())
        
        if saldo_total_apps <= 0:
            messagebox.showinfo("Aviso", "Você não tem saldo em aplicações para redistribuir.")
            return

        # 3. Preparar a base de cálculo (Simulando saldo = 0)
        objetivos_calc = []
        for nome_obj, info in self.dados.get("objetivos", {}).items():
            meta = info.get('meta', info.get('montante', 0.0))
            inicio = info.get('inicio', '')
            fim = info.get('fim', '')
            outros_ativos = info.get('outros_ativos', 0.0)
            
            meta_atualizada = self.corrigir_valor_pela_inflacao(meta, inicio) if inicio else meta
            
            # Aqui está o truque: o Valor Presente (pv) ignora o saldo atual!
            pv_base = outros_ativos 
            falta = max(0, meta_atualizada - pv_base)
            
            n = self.calcular_meses_restantes(fim)
            # O PMT calculado aqui é o PMT "puro", como se você não tivesse saldo no objetivo
            pmt = self.calcular_pmt(pv_base, meta_atualizada, n, 0.005)
            
            objetivos_calc.append({
                "nome": nome_obj,
                "falta_calculo": falta,
                "pmt": pmt,
                "novo_saldo": 0.0
            })

        # 4. O Motor de Distribuição em Cascata
        valor_restante = saldo_total_apps
        objetivos_ativos = [obj for obj in objetivos_calc if obj["falta_calculo"] > 0 and obj["pmt"] > 0]

        while valor_restante > 0.01 and objetivos_ativos:
            soma_pmt_atual = sum(obj["pmt"] for obj in objetivos_ativos)
            
            if soma_pmt_atual == 0:
                break
                
            teve_estouro = False
            
            for obj in objetivos_ativos:
                proporcao = obj["pmt"] / soma_pmt_atual
                fatia = valor_restante * proporcao
                
                if fatia > obj["falta_calculo"]:
                    obj["novo_saldo"] += obj["falta_calculo"]
                    valor_restante -= obj["falta_calculo"]
                    
                    obj["falta_calculo"] = 0 
                    teve_estouro = True
                    break 
                    
            if not teve_estouro:
                for obj in objetivos_ativos:
                    proporcao = obj["pmt"] / soma_pmt_atual
                    fatia = valor_restante * proporcao
                    obj["novo_saldo"] += fatia
                    obj["falta_calculo"] -= fatia
                
                valor_restante = 0 
                
            objetivos_ativos = [obj for obj in objetivos_ativos if obj["falta_calculo"] > 0]

        # 5. Aplicar os novos saldos e salvar
        for obj in objetivos_calc:
            self.dados["objetivos"][obj["nome"]]["saldo"] = obj["novo_saldo"]
            
        self.salvar_dados()
        self.atualizar_tabelas_principais()
        
        messagebox.showinfo("Sucesso", "Patrimônio redistribuído com sucesso para todos os objetivos!")

    def setup_tabela_objetivos(self):
        # Frame de rodapé para os aportes distribuídos (fica abaixo da tabela)
        self.frame_rodape_obj = ctk.CTkFrame(self.tab_obj, fg_color="transparent")
        self.frame_rodape_obj.pack(side="bottom", fill="x", pady=(10, 0))

        self.btn_fazer_aportes = ctk.CTkButton(self.frame_rodape_obj, text="Fazer Aportes", fg_color="green", command=self.fazer_aportes_distribuidos)
        self.btn_fazer_aportes.pack(side="left", padx=(0, 15))

        self.btn_redistribuir = ctk.CTkButton(self.frame_rodape_obj, text="Redistribuir Saldo Global 🔄", fg_color="#D35400", hover_color="#A04000", command=self.redistribuir_saldos_global)
        self.btn_redistribuir.pack(side="left", padx=(0, 15))

        self.label_diferenca = ctk.CTkLabel(self.frame_rodape_obj, text="Diferença a Distribuir: R$ 0,00", font=("Roboto", 14, "bold"))
        self.label_diferenca.pack(side="left")

        # NOVA COLUNA ADICIONADA: "meta_atualizada"
        colunas = ("nome", "fim", "meta", "meta_atualizada", "pv_atual", "saldo_obj", "falta", "aporte_mensal", "aporte_distrib")
        self.tree_obj = ttk.Treeview(self.tab_obj, columns=colunas, show='headings')
        
        self.tree_obj.heading("nome", text="Objetivo")
        self.tree_obj.heading("fim", text="Prazo Final")
        self.tree_obj.heading("meta", text="Meta Original\n(VF)")
        self.tree_obj.heading("meta_atualizada", text="Meta\nAtualizada")
        self.tree_obj.heading("pv_atual", text="Montante Atual\n(PV)")
        self.tree_obj.heading("saldo_obj", text="Mont. em\nAplicações") 
        self.tree_obj.heading("falta", text="Falta")
        self.tree_obj.heading("aporte_mensal", text="Aporte Mensal\nRequerido")
        self.tree_obj.heading("aporte_distrib", text="Aporte\nDistribuído")

        self.tree_obj.bind("<Double-1>", self.on_double_click_obj)
        self.tree_obj.pack(side="top", expand=True, fill="both")

    def setup_tabela_aplicacoes(self):
        # Frame superior da aba de aplicações
        self.frame_top_app = ctk.CTkFrame(self.tab_app, fg_color="transparent")
        self.frame_top_app.pack(side="top", fill="x", pady=(0, 10))
        
        self.label_sugestao = ctk.CTkLabel(self.frame_top_app, text="Sugestão para aplicar em: -", font=("Roboto", 14, "bold"), text_color="#E74C3C")
        self.label_sugestao.pack(side="left", padx=10)
        
        self.btn_editar_carteira = ctk.CTkButton(self.frame_top_app, text="Editar Percentuais ⚙️", command=self.abrir_janela_editar_carteira, width=140)
        self.btn_editar_carteira.pack(side="right", padx=10)

        # Tabela com coluna Tipo
        colunas = ("nome", "tipo", "valor_atual") 
        self.tree_app = ttk.Treeview(self.tab_app, columns=colunas, show='headings')
        self.tree_app.heading("nome", text="Aplicação")
        self.tree_app.heading("tipo", text="Categoria")
        self.tree_app.heading("valor_atual", text="Saldo Atual (R$)")
        
        self.tree_app.bind("<Double-1>", self.on_double_click_app)
        self.tree_app.pack(expand=True, fill="both", pady=(0, 10)) 

        # --- Frame de rodapé da aba de aplicações (AGORA SÓ COM A TIR) ---
        self.frame_rodape_app = ctk.CTkFrame(self.tab_app, fg_color="transparent")
        self.frame_rodape_app.pack(side="bottom", fill="x", pady=(0, 10))

        # Label da TIR (Rentabilidade)
        self.label_tir = ctk.CTkLabel(self.frame_rodape_app, text="Rentabilidade (TIR): 0.00% a.m.", font=("Roboto", 14, "bold"), text_color="#27AE60")
        self.label_tir.pack(side="right", padx=10) # <-- Mudei para right para ficar bonito sob o valor!
        # ---------------------------------------------------

        # NOVO: Botão para alterar a Taxa do PMT
        self.btn_config_taxa = ctk.CTkButton(self.frame_rodape_app, text="⚙️ Taxa PMT", width=110, fg_color="#34495E", hover_color="#2C3E50", command=self.abrir_config_taxa_pmt)
        self.btn_config_taxa.pack(side="right", padx=10)
        
    def formatar_moeda(self, valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def atualizar_tabelas_principais(self):
        # ==============================================================
        # NOVO: 0. CÁLCULO DA TIR E DECISÃO DA TAXA DO PMT
        # ==============================================================
        try:
            tir_anual_pct = self.calcular_tir_media_carteira()
            # Converte a TIR Anual (ex: 6.17%) para Mensal em Decimal (ex: 0.005)
            tir_mensal_decimal = ((1 + (tir_anual_pct / 100)) ** (1/12)) - 1
        except Exception:
            tir_anual_pct = 0.0
            tir_mensal_decimal = 0.005

        if hasattr(self, 'label_tir'):
            self.label_tir.configure(text=f"Rentabilidade (TIR): {tir_anual_pct:.2f}% a.a.")

        # Regra da Primeira Vez: Pergunta ao usuário se a TIR for maluca
        if "config_taxa_pmt" not in self.dados:
            if tir_mensal_decimal < 0 or tir_mensal_decimal > 0.015:
                # Chama a tela e congela essa função (recarregar=False para não rodar duplicado)
                self.abrir_config_taxa_pmt(recarregar=False)
            else:
                self.dados["config_taxa_pmt"] = {"modo": "auto", "valor": 0.005}
                self.salvar_dados()

        # Define qual taxa será usada no cálculo de fato
        config_taxa = self.dados.get("config_taxa_pmt", {"modo": "fixo", "valor": 0.005})
        if config_taxa["modo"] == "auto":
            # Piso de segurança: se estiver no Automático, não deixa usar taxa negativa no PMT
            taxa_pmt = max(tir_mensal_decimal, 0.001) 
        else:
            taxa_pmt = config_taxa.get("valor", 0.005)


        # ==============================================================
        # 1. Calcular Saldo Geral das Aplicações
        # ==============================================================
        saldo_geral_app = 0.0
        saldos_por_categoria = {cat: 0.0 for cat in self.dados.get("carteira_ideal", {}).keys()}
        saldos_por_categoria["Outros"] = 0.0

        for item in self.tree_app.get_children(): self.tree_app.delete(item)
        
        for nome_app, info in self.dados["aplicacoes"].items():
            saldo_app = info['saldo']
            tipo_app = info.get('tipo', 'Outros')
            saldo_geral_app += saldo_app
            
            if tipo_app in saldos_por_categoria:
                saldos_por_categoria[tipo_app] += saldo_app
            else:
                saldos_por_categoria["Outros"] += saldo_app
                
            self.tree_app.insert("", "end", values=(nome_app, tipo_app, self.formatar_moeda(saldo_app)))

        self.label_saldo_total.configure(text=f"Saldo Total: {self.formatar_moeda(saldo_geral_app)}")

        # 1.5 Motor de sugestão de aporte
        sugestao_texto = "Sugestão para aplicar em: -"
        soma_pmt_total = 0.0
        
        for nome_obj, info in self.dados.get("objetivos", {}).items():
            meta = info.get('meta', info.get('montante', 0.0))
            inicio = info.get('inicio', '')
            fim = info.get('fim', '')
            outros_ativos = info.get('outros_ativos', 0.0)
            saldo_atual = info.get('saldo', 0.0)
            
            meta_atualizada = self.corrigir_valor_pela_inflacao(meta, inicio) if inicio else meta
            pv_base = saldo_atual + outros_ativos
            falta = max(0, meta_atualizada - pv_base)
            
            if falta > 0 and fim:
                n = self.calcular_meses_restantes(fim)
                # NOVO: USANDO A TAXA DINÂMICA
                pmt = self.calcular_pmt(pv_base, meta_atualizada, n, taxa_pmt)
                if pmt > 0:
                    soma_pmt_total += pmt

        total_aportado_30d = 0.0
        hoje = datetime.now()
        limite_30dias = hoje - timedelta(days=30)

        for app_nome, app_info in self.dados.get("aplicacoes", {}).items():
            movimentos = app_info.get("movimentos", [])
            for mov in movimentos:
                if len(mov) >= 3:
                    data_str, desc, valor_mov = mov[0], str(mov[1]).lower(), float(mov[2])
                    try:
                        data_mov = datetime.strptime(data_str, "%d/%m/%Y")
                        if data_mov >= limite_30dias and valor_mov > 0:
                            if "aporte" in desc or "compra" in desc or "depósito" in desc or "deposito" in desc:
                                total_aportado_30d += valor_mov
                    except ValueError:
                        continue 

        valor_sugerido = soma_pmt_total - total_aportado_30d

        if "carteira_ideal" in self.dados and self.dados["carteira_ideal"]:
            if saldo_geral_app > 0:
                maior_defasagem_relativa = -999999
                categoria_sugerida = None
                
                for cat, pct_ideal in self.dados["carteira_ideal"].items():
                    if pct_ideal <= 0: continue
                        
                    pct_atual = (saldos_por_categoria.get(cat, 0.0) / saldo_geral_app) * 100.0
                    defasagem_relativa = (pct_ideal - pct_atual) / pct_ideal
                    
                    if defasagem_relativa > maior_defasagem_relativa:
                        maior_defasagem_relativa = defasagem_relativa
                        categoria_sugerida = cat
                
                if categoria_sugerida and maior_defasagem_relativa > 0.01:
                    if valor_sugerido <= 0:
                        sugestao_texto = f"Sugestão: {categoria_sugerida} | Você já depositou o suficiente este mês! 🎯"
                    else:
                        valor_br = f"R$ {valor_sugerido:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        sugestao_texto = f"Sugestão: {categoria_sugerida} | Aportar: {valor_br}"
                else:
                    sugestao_texto = "Carteira perfeitamente balanceada"
            else:
                categoria_sugerida = max(self.dados["carteira_ideal"], key=self.dados["carteira_ideal"].get)
                if valor_sugerido <= 0:
                    sugestao_texto = f"Sugestão: {categoria_sugerida} | Você já depositou o suficiente este mês! 🎯"
                else:
                    valor_br = f"R$ {valor_sugerido:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    sugestao_texto = f"Sugestão: {categoria_sugerida} | Aportar: {valor_br}"
        
        if hasattr(self, 'label_sugestao'):
            self.label_sugestao.configure(text=sugestao_texto)

        # ==============================================================
        # 2. Primeira varredura nos objetivos
        # ==============================================================
        saldo_geral_obj = 0.0
        soma_pmt = 0.0
        objetivos_calc = []
        
        for nome_obj, info in self.dados["objetivos"].items():
            meta = info.get('meta', info.get('montante', 0.0))
            inicio = info.get('inicio', '')
            
            meta_atualizada = self.corrigir_valor_pela_inflacao(meta, inicio) if inicio else meta
            outros_ativos = info.get('outros_ativos', 0.0)
            saldo = info.get('saldo', 0.0) 
            fim = info.get('fim', '')

            saldo_geral_obj += saldo
            pv = outros_ativos + saldo
            falta = max(0, meta_atualizada - pv)

            n = self.calcular_meses_restantes(fim)
            # NOVO: USANDO A TAXA DINÂMICA
            pmt = self.calcular_pmt(pv, meta_atualizada, n, taxa_pmt) 
            soma_pmt += pmt
            
            objetivos_calc.append({
                "nome": nome_obj, "fim": fim, "meta": meta, 
                "meta_atualizada": meta_atualizada,
                "pv": pv, "saldo": saldo, "falta": falta, "pmt": pmt
            })
        
        self.ajustar_larguras_tabela(self.tree_app)
        self.ajustar_larguras_tabela(self.tree_obj)
        self.label_total_aplicar.configure(text=f"Montante em Objetivos: {self.formatar_moeda(saldo_geral_obj)}")

        # ==============================================================
        # 3. e 4. Calcular diferença e Distribuição em Cascata
        # ==============================================================
        diferenca_total = max(0.0, saldo_geral_app - saldo_geral_obj)
        self.label_diferenca.configure(text=f"Diferença a Distribuir: {self.formatar_moeda(diferenca_total)}")
        
        self.distribuicao_atual = {obj["nome"]: 0.0 for obj in objetivos_calc}
        for item in self.tree_obj.get_children(): self.tree_obj.delete(item)
        
        valor_restante = diferenca_total
        for obj in objetivos_calc: obj["falta_calculo"] = obj["falta"]
        objetivos_ativos = [obj for obj in objetivos_calc if obj["falta_calculo"] > 0 and obj["pmt"] > 0]

        while valor_restante > 0.01 and objetivos_ativos:
            soma_pmt_atual = sum(obj["pmt"] for obj in objetivos_ativos)
            if soma_pmt_atual == 0: break 
                
            teve_estouro = False
            for obj in objetivos_ativos:
                proporcao = obj["pmt"] / soma_pmt_atual
                fatia = valor_restante * proporcao
                
                if fatia > obj["falta_calculo"]:
                    self.distribuicao_atual[obj["nome"]] += obj["falta_calculo"]
                    valor_restante -= obj["falta_calculo"]
                    obj["falta_calculo"] = 0 
                    teve_estouro = True
                    break 
                    
            if not teve_estouro:
                for obj in objetivos_ativos:
                    proporcao = obj["pmt"] / soma_pmt_atual
                    fatia = valor_restante * proporcao
                    self.distribuicao_atual[obj["nome"]] += fatia
                    obj["falta_calculo"] -= fatia
                valor_restante = 0 

            objetivos_ativos = [obj for obj in objetivos_ativos if obj["falta_calculo"] > 0]

        # 5. Inserir os resultados na tabela
        for obj in objetivos_calc:
            distribuido = self.distribuicao_atual.get(obj["nome"], 0.0)
            self.tree_obj.insert("", "end", values=(
                obj["nome"], obj["fim"], 
                self.formatar_moeda(obj["meta"]), 
                self.formatar_moeda(obj["meta_atualizada"]),
                self.formatar_moeda(obj["pv"]), 
                self.formatar_moeda(obj["saldo"]), 
                self.formatar_moeda(obj["falta"]), 
                self.formatar_moeda(obj["pmt"]),
                self.formatar_moeda(distribuido)
            ))

    def fazer_aportes_distribuidos(self):
        if not hasattr(self, 'distribuicao_atual') or not self.distribuicao_atual:
            return
            
        teve_aporte = False
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        
        for nome, valor in self.distribuicao_atual.items():
            if valor > 0.01: # Evita criar movimentos zerados ou de centavos perdidos
                ativo_atual = self.dados["objetivos"][nome].get("outros_ativos", 0.0)
                
                # Injeta a movimentação no histórico
                self.dados["objetivos"][nome]["movimentos"].append((data_hoje, "Aporte (Dinheiro)", valor, ativo_atual))
                # Atualiza o saldo do objetivo
                self.dados["objetivos"][nome]["saldo"] += valor
                teve_aporte = True
                
        if teve_aporte:
            self.salvar_dados()
            self.atualizar_tabelas_principais()
            messagebox.showinfo("Sucesso", "Aportes distribuídos e registrados com sucesso em seus objetivos!")
        else:
            messagebox.showinfo("Aviso", "Não há valor pendente para distribuir.")

    def criar_janela_secundaria(self, titulo, largura, altura):
        janela = ctk.CTkToplevel(self)
        janela.title(titulo)
        self.update_idletasks() 
        x_pai, y_pai = self.winfo_rootx(), self.winfo_rooty()
        larg_pai, alt_pai = self.winfo_width(), self.winfo_height()

        pos_x = x_pai + (larg_pai // 2) - (largura // 2)
        pos_y = y_pai + (alt_pai // 2) - (altura // 2)

        janela.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
        janela.transient(self)   
        janela.focus_force()     
        janela.grab_set()        
        return janela

    # --- JANELAS DE INSERÇÃO ---

    def abrir_janela_aplicacao(self, nome_preenchido=""):
        # Aumentei um pouco a janela para caber o novo campo sem espremer
        janela = self.criar_janela_secundaria("Gerenciar Aplicação", 750, 550)

        # --- Frame superior para Nome e Categoria ---
        frame_dados_app = ctk.CTkFrame(janela, fg_color="transparent")
        frame_dados_app.pack(pady=10, padx=20, fill="x")
        frame_dados_app.grid_columnconfigure((0,1), weight=1)

        ctk.CTkLabel(frame_dados_app, text="Nome da Aplicação:", font=("Roboto", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        ent_nome = ctk.CTkEntry(frame_dados_app)
        ent_nome.insert(0, nome_preenchido)
        ent_nome.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        ctk.CTkLabel(frame_dados_app, text="Categoria na Carteira:", font=("Roboto", 12, "bold")).grid(row=0, column=1, sticky="w", pady=(0, 5))
        
        opcoes_carteira = list(self.dados.get("carteira_ideal", {}).keys()) + ["Outros"]
        combo_tipo_app = ctk.CTkComboBox(frame_dados_app, values=opcoes_carteira)
        combo_tipo_app.grid(row=1, column=1, sticky="ew")

        tipo_atual = "Outros"
        if nome_preenchido in self.dados["aplicacoes"]:
            tipo_atual = self.dados["aplicacoes"][nome_preenchido].get("tipo", "Outros")
            if tipo_atual not in opcoes_carteira:
                opcoes_carteira.append(tipo_atual)
                combo_tipo_app.configure(values=opcoes_carteira)
        combo_tipo_app.set(tipo_atual)

        # Função auxiliar para pegar o saldo base no momento da digitação
        def obter_saldo_base():
            nome = ent_nome.get().strip()
            if nome in self.dados.get("aplicacoes", {}):
                return self.dados["aplicacoes"][nome].get("saldo", 0.0)
            return 0.0

        # --- Frame de Inserção de Movimentos ---
        frame_mov = ctk.CTkFrame(janela)
        frame_mov.pack(padx=20, pady=10, fill="x")
        for i in range(5): frame_mov.grid_columnconfigure(i, weight=1) # Agora com 5 colunas

        ent_data = ctk.CTkEntry(frame_mov, placeholder_text="DD/MM/AAAA", width=90)
        ent_data.grid(row=0, column=0, padx=5, pady=15)
        
        ent_valor = ctk.CTkEntry(frame_mov, placeholder_text="Valor", width=100)
        ent_valor.grid(row=0, column=1, padx=5, pady=15)
        
        tipo_mov = ctk.CTkComboBox(frame_mov, values=["Aporte", "Resgate", "Atualização"], width=110)
        tipo_mov.grid(row=0, column=2, padx=5, pady=15)

        # NOVO: Campo de Saldo Total
        ent_saldo = ctk.CTkEntry(frame_mov, placeholder_text="Sd. Total", width=100)
        ent_saldo.grid(row=0, column=3, padx=5, pady=15)

        # --- LÓGICA DE PREENCHIMENTO INTELIGENTE ---
        def on_valor_focusout(event=None):
            """Quando o usuário digita o VALOR, calcula o Saldo Total projetado."""
            try:
                val_str = ent_valor.get().replace(",", ".").strip()
                if not val_str: return
                val_float = float(val_str)
                
                saldo_base = obter_saldo_base()
                if tipo_mov.get() == "Resgate":
                    novo_saldo = saldo_base - abs(val_float)
                else:
                    novo_saldo = saldo_base + val_float
                
                ent_saldo.delete(0, 'end')
                ent_saldo.insert(0, f"{novo_saldo:.2f}".replace(".", ","))
            except ValueError:
                pass

        def on_saldo_focusout(event=None):
            """Quando o usuário digita o SALDO TOTAL, calcula a diferença no Valor e muda para Atualização."""
            try:
                saldo_str = ent_saldo.get().replace(",", ".").strip()
                if not saldo_str: return
                novo_saldo_digitado = float(saldo_str)
                
                saldo_base = obter_saldo_base()
                diferenca = novo_saldo_digitado - saldo_base
                
                # Se mudou o saldo diretamente, assumimos que é uma Atualização de rendimento
                tipo_mov.set("Atualização")
                
                ent_valor.delete(0, 'end')
                ent_valor.insert(0, f"{diferenca:.2f}".replace(".", ","))
            except ValueError:
                pass

        # Conecta os eventos aos campos
        ent_valor.bind("<FocusOut>", on_valor_focusout)
        tipo_mov.configure(command=on_valor_focusout) # Se ele mudar de Aporte pra Resgate no clique, já recalcula
        ent_saldo.bind("<FocusOut>", on_saldo_focusout)


        # --- LÓGICA DO BOTÃO ADICIONAR ---
        def adicionar_movimento():
            nome = ent_nome.get().strip()
            data = ent_data.get().strip()
            valor_str = ent_valor.get().replace(",", ".").strip()
            tipo = tipo_mov.get()

            if not nome or not data or not valor_str: return
            try: valor_float = abs(float(valor_str)) # Sempre tratamos o bruto como positivo
            except ValueError: return

            # SEGURANÇA DE SINAL
            if tipo == "Resgate":
                valor_exibicao = -valor_float
            else:
                valor_exibicao = valor_float

            # Atualiza o saldo real da aplicação
            self.dados["aplicacoes"][nome]["saldo"] += valor_exibicao
            saldo_momento = self.dados["aplicacoes"][nome]["saldo"]

            self.dados["aplicacoes"][nome]["movimentos"].append((data, tipo, valor_exibicao, saldo_momento))
            self.salvar_dados()
            
            # Insere na tabela
            tree_movs.insert("", "end", values=(data, tipo, self.formatar_moeda(valor_exibicao), self.formatar_moeda(saldo_momento)))
            self.atualizar_tabelas_principais()

            # Atualiza o Label bonitão lá embaixo
            lbl_saldo_rodape.configure(text=f"Saldo Atual: {self.formatar_moeda(saldo_momento)}")

            # Limpa os campos para o próximo
            ent_data.delete(0, 'end')
            ent_valor.delete(0, 'end')
            ent_saldo.delete(0, 'end')
            ent_data.focus()

        ctk.CTkButton(frame_mov, text="Adicionar", fg_color="green", width=100, command=adicionar_movimento).grid(row=0, column=4, padx=5, pady=15)

        # --- TABELA COM 4 COLUNAS ---
        tree_movs = ttk.Treeview(janela, columns=("data", "tipo", "valor", "saldo"), show='headings', height=10)
        tree_movs.heading("data", text="Data")
        tree_movs.heading("tipo", text="Tipo")
        tree_movs.heading("valor", text="Valor")
        tree_movs.heading("saldo", text="Sd. Total") # Nova coluna para histórico visual
        tree_movs.pack(padx=20, pady=5, fill="both", expand=True)

        # --- FUNÇÃO PARA REMOVER MOVIMENTO NA APLICAÇÃO ---
        def remover_movimento_app():
            selecionado = tree_movs.selection()
            if not selecionado: return
            
            nome = ent_nome.get().strip()
            item_index = tree_movs.index(selecionado)
            
            if messagebox.askyesno("Confirmar", "Excluir este lançamento?"):
                mov = self.dados["aplicacoes"][nome]["movimentos"][item_index]
                
                # Subtrai o valor que havia sido somado (Estorno)
                self.dados["aplicacoes"][nome]["saldo"] -= mov[2]
                
                # Remove da lista
                del self.dados["aplicacoes"][nome]["movimentos"][item_index]
                
                self.salvar_dados()
                tree_movs.delete(selecionado)
                
                # Atualiza o rodapé
                novo_saldo = self.dados["aplicacoes"][nome]["saldo"]
                lbl_saldo_rodape.configure(text=f"Saldo Atual: {self.formatar_moeda(novo_saldo)}")
                self.atualizar_tabelas_principais()

        # Coloque este botão logo abaixo da tree_movs.pack()
        btn_del_mov = ctk.CTkButton(janela, text="Excluir Lançamento Selecionado", fg_color="#C0392B", command=remover_movimento_app)
        btn_del_mov.pack(pady=5)

        if nome_preenchido in self.dados["aplicacoes"]:
            for mov in self.dados["aplicacoes"][nome_preenchido]["movimentos"]:
                # Puxa o saldo se existir (dados antigos tinham só 3 posições)
                sd_hist = mov[3] if len(mov) > 3 else 0.0
                tree_movs.insert("", "end", values=(mov[0], mov[1], self.formatar_moeda(mov[2]), self.formatar_moeda(sd_hist)))
        
        if hasattr(self, 'ajustar_larguras_tabela'):
            self.ajustar_larguras_tabela(tree_movs)

        # --- LABEL DO SALDO ATUAL ---
        lbl_saldo_rodape = ctk.CTkLabel(janela, text="Saldo Atual: R$ 0,00", font=("Roboto", 18, "bold"), text_color="#2FA572")
        lbl_saldo_rodape.pack(pady=(10, 0))
        
        # Inicia o label com o saldo se a aplicação já existir
        if nome_preenchido in self.dados.get("aplicacoes", {}):
            lbl_saldo_rodape.configure(text=f"Saldo Atual: {self.formatar_moeda(self.dados['aplicacoes'][nome_preenchido].get('saldo', 0.0))}")


        # --- BOTÕES FINAIS ---
        frame_botoes = ctk.CTkFrame(janela, fg_color="transparent")
        frame_botoes.pack(pady=15)

        def fechar_e_salvar():
            nome = ent_nome.get().strip()
            if nome in self.dados["aplicacoes"]:
                self.dados["aplicacoes"][nome]["tipo"] = combo_tipo_app.get()
                self.salvar_dados()
                self.atualizar_tabelas_principais()
            janela.destroy()

        ctk.CTkButton(frame_botoes, text="Fechar", command=fechar_e_salvar).pack(side="left", padx=10)

        def excluir_aplicacao():
            resposta = messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir a aplicação '{nome_preenchido}'?", parent=janela)
            if resposta:
                if nome_preenchido in self.dados["aplicacoes"]:
                    del self.dados["aplicacoes"][nome_preenchido]
                    self.salvar_dados()
                    self.atualizar_tabelas_principais()
                    janela.destroy()

        if nome_preenchido in self.dados["aplicacoes"]:
            ctk.CTkButton(frame_botoes, text="Excluir Aplicação (Tudo) 🗑️", fg_color="#E74C3C", hover_color="#C0392B", command=excluir_aplicacao).pack(side="right", padx=10)

            

    def abrir_janela_objetivo(self, nome_preenchido=""):
        janela = self.criar_janela_secundaria("Gerenciar Objetivo", 800, 680)

        frame_info = ctk.CTkFrame(janela)
        frame_info.pack(padx=20, pady=10, fill="x")
        frame_info.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(frame_info, text="Nome do Objetivo:").grid(row=0, column=0, padx=10, pady=(10,0), sticky="w")
        ent_nome = ctk.CTkEntry(frame_info, width=250)
        ent_nome.insert(0, nome_preenchido)
        ent_nome.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(frame_info, text="Meta Original / Valor Final (R$):").grid(row=0, column=1, padx=10, pady=(10,0), sticky="w")
        ent_meta = ctk.CTkEntry(frame_info, width=250)
        ent_meta.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(frame_info, text="Data Início (DD/MM/AAAA):").grid(row=2, column=0, padx=10, pady=(10,0), sticky="w")
        ent_inicio = ctk.CTkEntry(frame_info, width=250)
        ent_inicio.grid(row=3, column=0, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(frame_info, text="Data Fim (DD/MM/AAAA):").grid(row=2, column=1, padx=10, pady=(10,0), sticky="w")
        ent_fim = ctk.CTkEntry(frame_info, width=250)
        ent_fim.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(frame_info, text="Descrição de Outros Ativos (Ex: Carro HB20 2019, Saldo FGTS Caixa):").grid(row=4, column=0, columnspan=2, padx=10, pady=(10,0), sticky="w")
        txt_descricao = ctk.CTkTextbox(frame_info, height=45)
        txt_descricao.grid(row=5, column=0, columnspan=2, padx=10, pady=(5, 10), sticky="ew")

        valor_ativo_atual = 0.0

        if nome_preenchido in self.dados["objetivos"]:
            info = self.dados["objetivos"][nome_preenchido]
            ent_inicio.insert(0, info.get("inicio", ""))
            ent_fim.insert(0, info.get("fim", ""))
            ent_meta.insert(0, str(info.get("meta", info.get("montante", 0))))
            txt_descricao.insert("1.0", info.get("descricao_ativos", ""))
            valor_ativo_atual = info.get("outros_ativos", 0.0)

        def atualizar_dict_objetivo():
            nome = ent_nome.get().strip()
            if not nome: return None

            if nome not in self.dados["objetivos"]:
                self.dados["objetivos"][nome] = {"saldo": 0.0, "outros_ativos": 0.0, "movimentos": []}
            
            self.dados["objetivos"][nome]["inicio"] = ent_inicio.get().strip()
            self.dados["objetivos"][nome]["fim"] = ent_fim.get().strip()
            self.dados["objetivos"][nome]["meta"] = float(ent_meta.get().replace(",", ".") or 0)
            self.dados["objetivos"][nome]["descricao_ativos"] = txt_descricao.get("1.0", "end-1c").strip()
            
            if "movimentos" not in self.dados["objetivos"][nome]:
                self.dados["objetivos"][nome]["movimentos"] = []
                self.dados["objetivos"][nome]["saldo"] = 0.0
                if "outros_ativos" not in self.dados["objetivos"][nome]:
                    self.dados["objetivos"][nome]["outros_ativos"] = 0.0

            return nome

        # --- FRAME DE MOVIMENTOS ---
        frame_mov = ctk.CTkFrame(janela)
        frame_mov.pack(padx=20, pady=10, fill="x")
        for i in range(5): frame_mov.grid_columnconfigure(i, weight=1)

        ctk.CTkLabel(frame_mov, text="Data", font=("Roboto", 12)).grid(row=0, column=0, padx=5, pady=(10, 0))
        ctk.CTkLabel(frame_mov, text="Valor Lançado (R$)", font=("Roboto", 12)).grid(row=0, column=1, padx=5, pady=(10, 0))
        ctk.CTkLabel(frame_mov, text="Tipo de Movimento", font=("Roboto", 12)).grid(row=0, column=2, padx=5, pady=(10, 0))
        ctk.CTkLabel(frame_mov, text="Valor do Ativo (R$)", font=("Roboto", 12)).grid(row=0, column=3, padx=5, pady=(10, 0))

        ent_data = ctk.CTkEntry(frame_mov, placeholder_text="DD/MM/AAAA", width=90)
        ent_data.grid(row=1, column=0, padx=5, pady=(0, 15))
        
        ent_valor = ctk.CTkEntry(frame_mov, width=110)
        ent_valor.grid(row=1, column=1, padx=5, pady=(0, 15))
        
        tipo_mov = ctk.CTkComboBox(frame_mov, values=["Aporte (Dinheiro)", "Resgate (Dinheiro)", "Atualizar Ativo"], width=160)
        tipo_mov.grid(row=1, column=2, padx=5, pady=(0, 15))

        ent_valor_ativo = ctk.CTkEntry(frame_mov, width=110)
        ent_valor_ativo.grid(row=1, column=3, padx=5, pady=(0, 15))
        ent_valor_ativo.insert(0, str(valor_ativo_atual))

        def adicionar_movimento():
            nome = atualizar_dict_objetivo()
            if not nome:
                messagebox.showwarning("Aviso", "Preencha o nome do objetivo primeiro!", parent=janela)
                return

            data = ent_data.get().strip()
            valor_str = ent_valor.get().replace(",", ".").strip()
            valor_ativo_str = ent_valor_ativo.get().replace(",", ".").strip()
            tipo = tipo_mov.get()

            if not data:
                messagebox.showwarning("Aviso", "Preencha a data do movimento!", parent=janela)
                return

            try: 
                valor_float = abs(float(valor_str)) if valor_str else 0.0 # Pegamos sempre o positivo primeiro
                valor_ativo_float = float(valor_ativo_str) if valor_ativo_str else 0.0
            except ValueError: 
                messagebox.showwarning("Aviso", "Valor inválido!", parent=janela)
                return

            self.dados["objetivos"][nome]["outros_ativos"] = valor_ativo_float

            # SEGURANÇA DE SINAL
            if "Resgate" in tipo:
                valor_exibicao = -valor_float # Força ser negativo
            elif "Atualizar Ativo" in tipo:
                valor_exibicao = 0.0
            else:
                valor_exibicao = valor_float # Aporte: Força ser positivo

            # Atualiza o saldo do objetivo
            self.dados["objetivos"][nome]["saldo"] += valor_exibicao
            
            self.dados["objetivos"][nome]["movimentos"].append((data, tipo, valor_exibicao, valor_ativo_float))
            self.salvar_dados()
            
            tree_movs.insert("", "end", values=(data, tipo, self.formatar_moeda(valor_exibicao), self.formatar_moeda(valor_ativo_float)))
            self.atualizar_tabelas_principais()

            ent_data.delete(0, 'end')
            ent_valor.delete(0, 'end')

        btn_add = ctk.CTkButton(frame_mov, text="Adicionar", fg_color="green", width=90, command=adicionar_movimento)
        btn_add.grid(row=1, column=4, padx=5, pady=(0, 15))

        colunas_mov = ("data", "tipo", "valor", "valor_ativo")
        tree_movs = ttk.Treeview(janela, columns=colunas_mov, show='headings', height=6)
        tree_movs.heading("data", text="Data")
        tree_movs.heading("tipo", text="Tipo")
        tree_movs.heading("valor", text="Valor Lançado")
        tree_movs.heading("valor_ativo", text="Saldo do Ativo")
        
        tree_movs.column("data", width=90, anchor="center")
        tree_movs.column("tipo", width=160, anchor="w")
        tree_movs.column("valor", width=120, anchor="e")
        tree_movs.column("valor_ativo", width=120, anchor="e")
        tree_movs.pack(padx=20, pady=5, fill="both", expand=True)

        # --- BOTÃO DE EXCLUIR MOVIMENTO (ABAIXO DA TREEVIEW) ---
        def remover_movimento():
            selecionado = tree_movs.selection()
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um movimento para excluir!", parent=janela)
                return
            
            if messagebox.askyesno("Confirmar", "Deseja excluir este movimento?"):
                item = tree_movs.item(selecionado)
                valores = item['values'] # [data, tipo, valor, valor_ativo]
                
                # Encontra o índice na lista original (comparando os dados)
                nome = ent_nome.get().strip()
                movimentos = self.dados["objetivos"][nome]["movimentos"]
                
                for i, mov in enumerate(movimentos):
                    # Formata o valor do banco para comparar com o da tabela
                    if mov[0] == valores[0] and mov[1] == valores[1]:
                        # Estorna o valor do saldo antes de excluir
                        self.dados["objetivos"][nome]["saldo"] -= mov[2]
                        del movimentos[i]
                        break
                
                self.salvar_dados()
                tree_movs.delete(selecionado)
                self.atualizar_tabelas_principais()

        btn_remover_mov = ctk.CTkButton(janela, text="Remover Movimento Selecionado", fg_color="#C0392B", command=remover_movimento)
        btn_remover_mov.pack(pady=5)

        if nome_preenchido in self.dados["objetivos"]:
            for mov in self.dados["objetivos"][nome_preenchido].get("movimentos", []):
                val_lancado = self.formatar_moeda(mov[2])
                val_ativo = self.formatar_moeda(mov[3]) if len(mov) > 3 else "-" 
                tree_movs.insert("", "end", values=(mov[0], mov[1], val_lancado, val_ativo))

        def salvar_tudo_e_fechar():
            try:
                atualizar_dict_objetivo()
                self.salvar_dados()
                self.atualizar_tabelas_principais()
                janela.destroy()
            except ValueError:
                messagebox.showerror("Erro", "Campos financeiros devem ser números!", parent=janela)

        # --- FRAME DE BOTÕES INFERIORES ---
        frame_botoes_obj = ctk.CTkFrame(janela, fg_color="transparent")
        frame_botoes_obj.pack(pady=15)

        ctk.CTkButton(frame_botoes_obj, text="Salvar Informações e Fechar", command=salvar_tudo_e_fechar).pack(side="left", padx=10)

        def excluir_objetivo():
            resposta = messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o objetivo '{nome_preenchido}' e todo o seu histórico?", parent=janela)
            if resposta:
                if nome_preenchido in self.dados["objetivos"]:
                    del self.dados["objetivos"][nome_preenchido]
                    self.salvar_dados()
                    self.atualizar_tabelas_principais()
                    janela.destroy()

        if nome_preenchido in self.dados["objetivos"]:
            ctk.CTkButton(frame_botoes_obj, text="Excluir Objetivo (Tudo) 🗑️", fg_color="#E74C3C", hover_color="#C0392B", command=excluir_objetivo).pack(side="right", padx=10)

    def on_double_click_app(self, event):
        selecao = self.tree_app.selection()
        if not selecao: return
        nome = self.tree_app.item(selecao[0], "values")[0]
        self.abrir_janela_aplicacao(nome)

    def on_double_click_obj(self, event):
        selecao = self.tree_obj.selection()
        if not selecao: return
        nome = self.tree_obj.item(selecao[0], "values")[0]
        self.abrir_janela_objetivo(nome)


    def abrir_janela_editar_carteira(self):
        janela = self.criar_janela_secundaria("Editar Carteira Ideal", 550, 600)
        
        ctk.CTkLabel(janela, text="Configurar Percentuais Ideais (%)", font=("Roboto", 16, "bold")).pack(pady=10)
        
        frame_lista = ctk.CTkScrollableFrame(janela, height=350)
        frame_lista.pack(fill="both", expand=True, padx=20, pady=5)
        
        entradas = {}
        
        def adicionar_linha(cat="", pct=0.0):
            row_frame = ctk.CTkFrame(frame_lista, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            
            ent_cat = ctk.CTkEntry(row_frame, width=300, placeholder_text="Nome do Ativo/Categoria")
            ent_cat.insert(0, cat)
            ent_cat.pack(side="left", padx=5)
            
            ent_pct = ctk.CTkEntry(row_frame, width=80, placeholder_text="%")
            ent_pct.insert(0, str(pct))
            ent_pct.pack(side="left", padx=5)
            
            def remover():
                row_frame.destroy()
                if row_frame in entradas:
                    del entradas[row_frame]

            btn_rm = ctk.CTkButton(row_frame, text="X", width=30, fg_color="#E74C3C", command=remover)
            btn_rm.pack(side="left", padx=5)
            
            entradas[row_frame] = (ent_cat, ent_pct)

        for cat, pct in self.dados.get("carteira_ideal", {}).items():
            adicionar_linha(cat, pct)
            
        ctk.CTkButton(janela, text="+ Adicionar Linha", command=lambda: adicionar_linha()).pack(pady=10)
        
        def salvar():
            nova_carteira = {}
            soma = 0.0
            for r_frame, (e_cat, e_pct) in entradas.items():
                c = e_cat.get().strip()
                p_str = e_pct.get().replace(",", ".").strip()
                if c and p_str:
                    try:
                        p = float(p_str)
                        nova_carteira[c] = p
                        soma += p
                    except ValueError:
                        messagebox.showerror("Erro", f"Valor percentual inválido em '{c}'", parent=janela)
                        return
            
            # Validação amigável
            if abs(soma - 100.0) > 0.01:
                if not messagebox.askyesno("Aviso", f"A soma dos percentuais bateu em {soma}%. O mercado indica manter em 100%.\nDeseja salvar mesmo assim?", parent=janela):
                    return
                    
            self.dados["carteira_ideal"] = nova_carteira
            self.salvar_dados()
            self.atualizar_tabelas_principais()
            janela.destroy()

        ctk.CTkButton(janela, text="Salvar Nova Carteira", fg_color="green", command=salvar).pack(pady=10)

if __name__ == "__main__":
    app = AppInvest()
    app.mainloop()