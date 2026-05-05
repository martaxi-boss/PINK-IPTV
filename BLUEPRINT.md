# 🐾 PINK-IPTV - Master Blueprint & Architecture

Este documento contém toda a arquitetura, design e regras de negócio para o desenvolvimento do aplicativo **PINK-IPTV**. 
Ele foi criado para ser entregue ao **Claude 3.5 Sonnet** para a fase de codificação final.

## 1. Visão Geral do Projeto
* **Nome:** PINK-IPTV
* **Objetivo:** Criar um aplicativo de IPTV moderno, rápido e focado em uma experiência de usuário (UX) premium. Zero configurações complexas.
* **Plataformas Alvo:** Foco inicial total em **Windows (.exe)**. A arquitetura será feita de forma que a portabilidade para Android (.apk) seja possível no futuro, mas o Windows é a prioridade 1.
* **Protocolo:** Exclusivo para **Xtream Codes API** (Não usaremos arquivos M3U locais).

## 2. Stack Tecnológico
* **Linguagem:** Python 3.12+
* **Framework UI:** [Flet](https://flet.dev/) (Motor Flutter).
* **Requisições HTTP:** `httpx` (Para comunicação rápida e assíncrona com a API do Xtream Codes).
* **Player de Vídeo e Codecs Embutidos:** O aplicativo deve vir com **todos os codecs de áudio e vídeo já integrados** (ex: usando `python-vlc` com as DLLs do VLC embutidas ou `mpv`). O usuário **NÃO** pode ser obrigado a instalar pacotes de codecs (como K-Lite) ou players externos. Tudo roda "Out of the Box".

## 3. Design System: Tema "Pink Panther" 🐆
O aplicativo deve fugir do padrão "sério e chato" dos apps de IPTV comuns. Ele terá uma identidade visual forte baseada na Pantera Cor-de-Rosa.

* **Cores Principais:**
  * **Background Principal:** `#1A0B12` (Um tom de vinho/preto muito escuro e elegante).
  * **Background Secundário (Cards/Painéis):** `#2D1422`
  * **Cor de Destaque (Accent):** `#FF1493` (Rosa Choque / Deep Pink) para botões, bordas ativas e ícones.
  * **Texto Principal:** `#FFFFFF` (Branco puro para legibilidade).
  * **Texto Secundário:** `#FFB6C1` (Rosa claro para subtítulos e dicas).
* **Tipografia:** Fontes modernas e arredondadas (ex: *Poppins* ou *Montserrat* se possível, ou a fonte padrão do sistema com pesos em Bold para títulos).
* **Bordas:** Arredondadas (`border_radius=15` em botões e cards).

## 4. Integração Xtream Codes API
A comunicação com o servidor IPTV será feita exclusivamente via `player_api.php`.

**Endpoints Essenciais:**
1. **Autenticação:** `GET {url}/player_api.php?username={user}&password={pass}`
2. **Categorias Ao Vivo:** `&action=get_live_categories`
3. **Canais Ao Vivo:** `&action=get_live_streams&category_id={id}`
4. **Categorias VOD (Filmes):** `&action=get_vod_categories`
5. **Filmes (VOD):** `&action=get_vod_streams&category_id={id}`
6. **Link de Reprodução (Live):** `{url}/live/{user}/{pass}/{stream_id}.m3u8` (ou .ts)

## 5. Integração VPN Invisível (Anti-Bloqueio) 🛡️
Esta é a funcionalidade "Killer Feature" do app. Para evitar bloqueios de operadoras (Traffic Shaping/ISP Blocking), o app terá uma VPN embutida (Surfshark via WireGuard ou OpenVPN).

* **Experiência do Usuário (UX):** 100% Transparente (Invisível). O usuário **NÃO** precisa saber o que é VPN, não precisa configurar nada, nem apertar botão de "Conectar". Ele apenas faz o login no IPTV e assiste.
* **Como vai funcionar:**
  * O app terá os arquivos de configuração do WireGuard/OpenVPN embutidos no código.
  * Ao iniciar o aplicativo (ou ao dar "Play" em um canal), um processo em background levanta o túnel VPN silenciosamente.
  * Todo o tráfego de vídeo passa pelo túnel criptografado, garantindo que o stream nunca trave por bloqueio da operadora.
  * Ao fechar o app, a conexão VPN é encerrada automaticamente.

## 6. Fluxo de Telas (App Flow)

### Tela 1: Login
* Logo da Pantera Cor-de-Rosa no topo.
* 3 Campos de texto (URL, Usuário, Senha) com bordas rosa.
* Botão "ENTRAR" grande e chamativo.
* Validação de erro amigável.

### Tela 2: Dashboard Principal (Hub)
* Menu lateral ou inferior (Mobile) com: TV Ao Vivo, Filmes, Séries, Configurações.
* Saudação ao usuário (ex: "Bem-vindo, {user}").
* Exibição das categorias em formato de grade (Grid).

### Tela 3: Lista de Canais/Conteúdo
* Lista dos canais da categoria selecionada.
* Exibição do Logo do canal (`stream_icon`).
* Barra de pesquisa rápida para filtrar canais pelo nome.

### Tela 4: Player de Vídeo (Experiência Imersiva no Windows)
* **Janela Frameless (Sem bordas do Windows):** O aplicativo usará uma janela customizada, sem aquela barra padrão do Windows.
* **Barra Inteligente (Smart Bar) no Topo:**
  * Uma barra de controles moderna e elegante na parte superior da tela.
  * **Auto-Hide:** Quando o usuário está assistindo, a barra desaparece em segundos (fade out). Se ele mexer o mouse, a barra reaparece suavemente.
  * **Controles Integrados:** Botão de Fullscreen (Tela Cheia), Avançar/Retroceder, Volume e Fechar/Voltar.
* **Codecs Nativos:** O player rodará qualquer formato (H.264, H.265, AAC, AC3, etc.) sem exigir que o usuário instale nada.

---

## 7. Ficheiros já criados na pasta /root/PINK-IPTV/

| Ficheiro | Descrição |
|---|---|
| `app.py` | Estrutura da interface Flet (tela de login) |
| `xtream.py` | Motor de conexão à API Xtream Codes (testado) |
| `vpn_config.conf` | Configuração WireGuard Surfshark (servidor Amsterdão) |
| `test_credentials.conf` | Credenciais de teste IPTV |
| `mockup.html` | Mockup visual HTML de todas as telas |
| `requirements.txt` | Dependências: flet, httpx, python-vlc |

## 8. Credenciais de Teste (Servidor IPTV)
* **URL:** `http://gccthmgw.zvpnm.com`
* **Utilizador:** `BX9CNQKV`
* **Senha:** `MCHY4AP8`
* **Nota:** Servidor bloqueia IPs de datacenter. Testar apenas no Windows com IP residencial.

---

## 🤖 PROMPT COMPLETO PARA O CLAUDE 3.5 SONNET

> Olá! Tenho um projeto chamado **PINK-IPTV** na pasta `/root/PINK-IPTV/`. Lê o ficheiro `BLUEPRINT.md` para entender a arquitectura completa.
>
> **Resumo rápido:**
> - App de IPTV em Python + Flet para Windows
> - Tema visual "Pink Panther" (fundo escuro `#0d0008`, destaque rosa `#FF1493`)
> - Usa API Xtream Codes (sem M3U)
> - VPN WireGuard (Surfshark) invisível e embutida — o utilizador não sabe que existe
> - Janela frameless com Smart Bar auto-hide no player
> - Codecs embutidos via python-vlc (zero instalações pelo utilizador)
> - Pantera cor-de-rosa engraçada e cartoon no ecrã de login
>
> **Já existe:**
> - `xtream.py` — motor de conexão testado
> - `app.py` — esqueleto da UI
> - `vpn_config.conf` — configuração WireGuard Surfshark
> - `mockup.html` — ver o design visual de referência
>
> **O que precisas de fazer:**
> 1. Refaz o `app.py` completo com as 4 telas (Login, Dashboard, Lista de Canais, Player)
> 2. Cria o módulo `vpn_manager.py` que lê o `vpn_config.conf` e liga/desliga o WireGuard em background
> 3. O player usa `python-vlc` com Smart Bar auto-hide
> 4. Tudo modular, limpo e pronto para compilar para `.exe` com PyInstaller
>
> Começa pela Tela de Login com a pantera engraçada e o tema rosa. Segue o `mockup.html` como referência visual.
