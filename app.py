"""
PINK IPTV - Windows Application
Motor: python-vlc (suporte total a todos os codecs, faixas de áudio e legendas dinâmicas)
"""
import flet as ft
import json
import os
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from xtream import XtreamClient
import vpn

# Tentar importar VLC
try:
    import vlc
    VLC_OK = True
except Exception:
    VLC_OK = False

# --- TEMA PROFISSIONAL ROSA ---
BG          = "#0D0015"
BG_CARD     = "#180022"
BG_CARD_2   = "#200030"
PRIMARY     = "#FF0080"
PRIMARY_2   = "#CC0066"
ACCENT      = "#CC00FF"
TEXT        = "#FFFFFF"
MUTED       = "#9080A0"
BORDER      = "#2D1040"
GREEN       = "#22C55E"

def _get_profiles_path():
    # Pasta fixa: Documents\PINK-IPTV\ (sempre acessível no Windows)
    if sys.platform == "win32":
        docs = os.path.join(os.path.expanduser("~"), "Documents", "PINK-IPTV")
    else:
        docs = os.path.join(os.path.expanduser("~"), "PINK-IPTV")
    os.makedirs(docs, exist_ok=True)
    return os.path.join(docs, "profiles.json")

PROFILES_FILE = _get_profiles_path()

def load_profiles():
    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_profiles(p):
    try:
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(p, f, indent=2)
    except Exception as e:
        print(f"Erro ao guardar perfis: {e}")


def main(page: ft.Page):
    page.title = "PINK IPTV"
    page.bgcolor = BG
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    try:
        page.window.width  = 1280
        page.window.height = 800
        page.window.min_width  = 900
        page.window.min_height = 600
    except:
        pass

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            if main_view.content == player_view:
                close_player()
    page.on_keyboard_event = on_keyboard

    # --- ESTADO GLOBAL ---
    state = {
        "c": None,
        "cats_live": [], "cats_vod": [], "cats_series": [],
        "current_mode": "live",
        "profiles": load_profiles(),
        "vlc_instance": vlc.Instance("--no-xlib") if VLC_OK else None,
        "media_player": None,
        "smart_bar_timer": None,
        "smart_bar_visible": True,
        "last_vod_info_full": None,
    }

    if VLC_OK:
        state["media_player"] = state["vlc_instance"].media_player_new()

    main_view = ft.Container(expand=True, bgcolor=BG)
    page.add(main_view)

    # ─────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────
    def txt(t, size=14, color=TEXT, weight=None, align=None):
        return ft.Text(t, size=size, color=color, weight=weight, text_align=align)

    def inp(label, pwd=False):
        return ft.TextField(
            label=label, password=pwd, can_reveal_password=pwd,
            bgcolor="#000", border_color=BORDER, focused_border_color=PRIMARY,
            border_radius=8, color=TEXT,
            label_style=ft.TextStyle(color=MUTED, size=11),
            content_padding=ft.padding.symmetric(horizontal=14, vertical=14),
        )

    def red_btn(label, on_click, icon=None):
        row_content = []
        if icon:
            row_content.append(ft.Icon(icon, color=TEXT, size=16))
        row_content.append(txt(label, weight="bold"))
        return ft.Container(
            content=ft.Row(row_content, alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, 0), end=ft.Alignment(1, 0),
                colors=[PRIMARY, ACCENT],
            ),
            border_radius=10, padding=14,
            alignment=ft.Alignment(0, 0), on_click=on_click, ink=True,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.4, PRIMARY), spread_radius=0),
        )

    def ghost_btn(label, on_click, icon=None):
        row_content = []
        if icon:
            row_content.append(ft.Icon(icon, color=MUTED, size=14))
        row_content.append(txt(label, color=MUTED, size=13))
        return ft.Container(
            content=ft.Row(row_content, alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            border=ft.border.all(1, BORDER), border_radius=8, padding=12,
            alignment=ft.Alignment(0, 0), on_click=on_click, ink=True,
        )

    # ─────────────────────────────────────────────────────────
    # ECRÃ 1: LOGIN
    # ─────────────────────────────────────────────────────────
    f_name = inp("Nome (Ex: A Minha TV)")
    f_url  = inp("URL do Servidor  (http://...)")
    f_user = inp("Utilizador")
    f_pass = inp("Palavra-passe", pwd=True)
    login_msg = txt("", size=12, color=PRIMARY, align=ft.TextAlign.CENTER)

    def do_login(e=None, profile=None):
        login_msg.value = "A ligar..."
        login_msg.color = MUTED
        page.update()
        if profile:
            url, user, pwd = profile["url"], profile["username"], profile["password"]
        else:
            name = f_name.value.strip() or "My IPTV"
            url  = f_url.value.strip()
            user = f_user.value.strip()
            pwd  = f_pass.value.strip()
            if not url or not user or not pwd:
                login_msg.value = "Preenche URL, Utilizador e Palavra-passe!"
                login_msg.color = PRIMARY
                page.update()
                return
            p = state["profiles"]
            p.append({"name": name, "url": url, "username": user, "password": pwd})
            save_profiles(p)

        c = XtreamClient(url, user, pwd)
        ok, result = c.authenticate()
        if ok:
            state["c"] = c
            state["cats_live"]   = c.get_live_categories()
            state["cats_vod"]    = c.get_vod_categories()
            state["cats_series"] = c.get_series_categories()
            login_msg.value = ""
            show_hub(result)
        else:
            login_msg.value = f"Erro: {result}"
            login_msg.color = PRIMARY
            page.update()

    # Dialog de utilizadores guardados
    saved_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=340)

    def refresh_saved():
        saved_col.controls.clear()
        if not state["profiles"]:
            saved_col.controls.append(txt("Nenhum utilizador guardado.", color=MUTED))
        else:
            for i, p in enumerate(state["profiles"]):
                def _card(i=i, p=p):
                    return ft.Container(
                        content=ft.Row([
                            ft.CircleAvatar(
                                content=txt(p["name"][0].upper(), weight="bold"),
                                bgcolor=PRIMARY, radius=20,
                            ),
                            ft.Column([
                                txt(p["name"], weight="bold"),
                                txt(f"{p['username']} • {p['url']}", size=11, color=MUTED),
                            ], expand=True, spacing=2),
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE, icon_color=MUTED,
                                on_click=lambda e, idx=i: _del_saved(idx)
                            ),
                        ]),
                        padding=12, bgcolor="#000", border_radius=8,
                        border=ft.border.all(1, BORDER),
                        on_click=lambda e, prof=p: [_close_saved(), do_login(profile=prof)],
                        ink=True,
                    )
                saved_col.controls.append(_card())
        try: page.update()
        except: pass

    saved_dialog = ft.AlertDialog(
        title=txt("Utilizadores Guardados", weight="bold", color=PRIMARY),
        content=ft.Container(saved_col, width=460),
        bgcolor=BG_CARD, shape=ft.RoundedRectangleBorder(radius=12),
    )

    def _open_saved(e):
        refresh_saved()
        page.dialog = saved_dialog
        saved_dialog.open = True
        page.update()

    def _close_saved():
        saved_dialog.open = False
        page.update()

    def _del_saved(idx):
        state["profiles"].pop(idx)
        save_profiles(state["profiles"])
        refresh_saved()

    login_view = ft.Container(
        content=ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.TV, size=60, color=PRIMARY),
                txt("PINK IPTV", size=32, weight="bold", color=PRIMARY),
                txt("A tua experiência IPTV profissional", size=12, color=MUTED),
                ft.Container(height=24),
                f_name, f_url, f_user, f_pass,
                ft.Container(height=10),
                red_btn("ADICIONAR UTILIZADOR", do_login, icon=ft.Icons.PERSON_ADD),
                login_msg,
                ft.Container(height=8),
                ghost_btn("TROCAR UTILIZADOR", _open_saved, icon=ft.Icons.PEOPLE),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            padding=40, border_radius=16,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                colors=[BG_CARD, BG_CARD_2],
            ),
            border=ft.border.all(1, BORDER), width=440,
            shadow=ft.BoxShadow(blur_radius=40, color=ft.Colors.with_opacity(0.2, PRIMARY), spread_radius=0),
        ),
        alignment=ft.Alignment(0, 0), expand=True,
        gradient=ft.RadialGradient(
            center=ft.Alignment(0, -0.3), radius=1.0,
            colors=[BG_CARD_2, BG],
        ),
    )

    # ─────────────────────────────────────────────────────────
    # ECRÃ 2: HUB PRINCIPAL
    # ─────────────────────────────────────────────────────────
    hub_username = txt("", size=15, weight="bold")

    def _hub_card(icon, label, mode):
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=80, color=PRIMARY),
                ft.Container(height=10),
                txt(label, size=24, weight="bold"),
            ], alignment=ft.MainAxisAlignment.CENTER,
               horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=280, height=320, border_radius=18,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                colors=[BG_CARD, BG_CARD_2],
            ),
            border=ft.border.all(1, BORDER),
            shadow=ft.BoxShadow(blur_radius=30, color=ft.Colors.with_opacity(0.15, PRIMARY), spread_radius=0),
            on_click=lambda e, m=mode: show_list(m),
            ink=True,
        )

    hub_view = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.TV, size=32, color=PRIMARY),
                    txt("PINK IPTV", size=28, weight="bold", color=PRIMARY),
                ], spacing=8),
                ft.Column([
                    hub_username,
                    ft.Row([
                        ft.Container(width=8, height=8, bgcolor=GREEN, border_radius=4),
                        txt("Ligado", size=11, color=MUTED),
                    ], spacing=6),
                ], horizontal_alignment=ft.CrossAxisAlignment.END),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(
                ft.Row([
                    _hub_card(ft.Icons.TV,            "LIVE TV", "live"),
                    _hub_card(ft.Icons.MOVIE,         "MOVIES",  "vod"),
                    _hub_card(ft.Icons.VIDEO_LIBRARY, "SERIES",  "series"),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=30),
                expand=True, alignment=ft.Alignment(0, 0),
            ),
            ft.Row([
                ft.TextButton(
                    "VOLTAR AO INÍCIO",
                    icon=ft.Icons.LOGOUT, icon_color=MUTED,
                    on_click=lambda e: show_login(),
                ),
            ], alignment=ft.MainAxisAlignment.END),
        ]),
        padding=40, expand=True,
    )

    # ─────────────────────────────────────────────────────────
    # ECRÃ 3: LISTA DE CANAIS
    # ─────────────────────────────────────────────────────────
    list_title   = txt("LIVE TV", size=20, weight="bold")
    cat_col      = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
    content_grid = ft.GridView(
        expand=True, max_extent=180, child_aspect_ratio=0.75,
        spacing=12, run_spacing=12,
    )

    # Dialog de episódios
    ep_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=400)
    ep_dialog = ft.AlertDialog(
        title=txt("Episódios", weight="bold", color=PRIMARY),
        content=ft.Container(ep_col, width=520),
        bgcolor=BG_CARD, shape=ft.RoundedRectangleBorder(radius=12),
    )

    def open_series_modal(series_id, series_name):
        ep_dialog.title.value = series_name
        ep_col.controls.clear()
        ep_col.controls.append(txt("A carregar episódios...", color=MUTED))
        page.dialog = ep_dialog
        ep_dialog.open = True
        page.update()

        c   = state["c"]
        info = c.get_series_info(series_id)
        eps  = info.get("episodes", {})
        ep_col.controls.clear()

        if isinstance(eps, dict) and eps:
            for season, episode_list in sorted(eps.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
                ep_col.controls.append(
                    ft.Container(
                        txt(f"Temporada {season}", size=11, color=PRIMARY, weight="bold"),
                        padding=ft.padding.only(top=8, bottom=4)
                    )
                )
                for ep in episode_list:
                    eid   = ep.get("id")
                    ext   = ep.get("container_extension", "mp4")
                    url   = c.get_stream_url(eid, "series", ext)
                    title = ep.get("title", f"Ep. {ep.get('episode_num')}")
                    ep_col.controls.append(
                        ft.Container(
                            content=ft.Row([
                                txt(title, expand=True),
                                ft.Icon(ft.Icons.PLAY_CIRCLE_FILL, color=PRIMARY),
                            ]),
                            padding=14, bgcolor="#000", border_radius=8,
                            border=ft.border.all(1, BORDER),
                            on_click=lambda e, u=url, t=title, eid=eid: _play_ep(u, t, eid),
                            ink=True,
                        )
                    )
        else:
            ep_col.controls.append(txt("Nenhum episódio encontrado.", color=MUTED))
        page.update()

    def _play_ep(url, title, episode_id=None):
        ep_dialog.open = False
        page.update()
        open_player(url, title, episode_id)

    def load_content(cat_id):
        content_grid.controls.clear()
        content_grid.controls.append(ft.ProgressRing(color=PRIMARY))
        page.update()

        c    = state["c"]
        mode = state["current_mode"]
        streams = (
            c.get_live_streams(cat_id) if mode == "live" else
            c.get_vod_streams(cat_id)  if mode == "vod"  else
            c.get_series(cat_id)
        )

        content_grid.controls.clear()
        for s in (streams or []):
            name = s.get("name", "?")
            if mode == "series":
                sid = s.get("series_id")
                icon = s.get("cover", "")
                action = lambda e, _id=sid, _n=name: open_series_modal(_id, _n)
            elif mode == "vod":
                sid = s.get("stream_id")
                icon = s.get("stream_icon", "")
                url = c.get_stream_url(sid, mode)
                action = lambda e, u=url, n=name, mid=sid: open_player(u, n, mid)
            else:
                sid = s.get("stream_id")
                icon = s.get("stream_icon", "")
                url = c.get_stream_url(sid, mode)
                action = lambda e, u=url, n=name: open_player(u, n, None)

            img = (
                ft.Image(src=icon, fit="contain", expand=True)
                if icon else
                ft.Icon(ft.Icons.TV, size=36, color=MUTED)
            )
            content_grid.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=img, expand=True,
                            bgcolor="#000", border_radius=6, padding=4,
                            alignment=ft.Alignment(0, 0),
                        ),
                        txt(name, size=11, weight="bold",
                            align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                       spacing=6),
                    bgcolor=BG_CARD, border_radius=8,
                    border=ft.border.all(1, BORDER), padding=10,
                    on_click=action, ink=True,
                )
            )
        if not streams:
            content_grid.controls.append(txt("Sem conteúdo nesta categoria.", color=MUTED))
        page.update()

    list_view = ft.Container(
        content=ft.Column([
            ft.Container(
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: show_hub(None)),
                    list_title,
                ]),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                bgcolor=BG_CARD,
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
            ),
            ft.Row([
                ft.Container(content=cat_col, width=280, bgcolor=BG_CARD,
                             border=ft.border.only(right=ft.BorderSide(1, BORDER))),
                ft.Container(content=content_grid, expand=True, padding=16),
            ], expand=True, spacing=0),
        ], spacing=0),
        expand=True,
    )

    # ─────────────────────────────────────────────────────────
    # ECRÃ 4: PLAYER COM VLC + SMART BAR
    # ─────────────────────────────────────────────────────────
    player_title   = txt("", size=18, weight="bold")
    audio_menu     = ft.Column(spacing=4, visible=False)
    subtitle_menu  = ft.Column(spacing=4, visible=False)
    audio_btn      = ft.IconButton(ft.Icons.VOLUME_UP, icon_color=TEXT, tooltip="Áudio")
    subtitle_btn   = ft.IconButton(ft.Icons.CLOSED_CAPTION, icon_color=TEXT, tooltip="Legendas")
    vod_info_dump_btn = ft.IconButton(
        ft.Icons.INFO_OUTLINE,
        icon_color=MUTED,
        tooltip="Ver JSON completo de get_vod_info (tudo o que o servidor enviou)",
        visible=False,
    )
    fullscreen_btn = ft.IconButton(ft.Icons.FULLSCREEN, icon_color=TEXT, tooltip="Ecrã Inteiro (F11 ou duplo-clique)")
    close_btn      = ft.IconButton(ft.Icons.CLOSE, icon_color=TEXT, tooltip="Fechar", on_click=lambda e: close_player())
    back_btn       = ft.IconButton(ft.Icons.ARROW_BACK, icon_color=TEXT, tooltip="Voltar", on_click=lambda e: close_player())

    def _toggle_audio_menu(e):
        audio_menu.visible = not audio_menu.visible
        subtitle_menu.visible = False
        page.update()

    def _toggle_sub_menu(e):
        subtitle_menu.visible = not subtitle_menu.visible
        audio_menu.visible = False
        page.update()

    def _toggle_fullscreen(e):
        try:
            page.window.full_screen = not page.window.full_screen
        except:
            pass
        page.update()

    audio_btn.on_click      = _toggle_audio_menu
    subtitle_btn.on_click   = _toggle_sub_menu
    fullscreen_btn.on_click = _toggle_fullscreen

    smart_bar = ft.Container(
        content=ft.Row([
            back_btn,
            ft.Container(player_title, expand=True, padding=ft.padding.only(left=10)),
            audio_btn,
            subtitle_btn,
            vod_info_dump_btn,
            fullscreen_btn,
            ft.Container(width=8),
            close_btn,
        ]),
        padding=ft.padding.symmetric(horizontal=10, vertical=12),
        gradient=ft.LinearGradient(
            begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
            colors=[ft.Colors.with_opacity(0.95, ft.Colors.BLACK), ft.Colors.TRANSPARENT],
        ),
        animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_IN_OUT),
        opacity=1.0,
    )

    _hide_timer = [None]

    def _hide_smart_bar():
        time.sleep(4)
        if main_view.content == player_view:
            smart_bar.opacity = 0.0
            try: page.update()
            except: pass

    def _show_smart_bar(e=None):
        smart_bar.opacity = 1.0
        try: page.update()
        except: pass
        # Cancela timer anterior e inicia novo
        t = threading.Thread(target=_hide_smart_bar, daemon=True)
        _hide_timer[0] = t
        t.start()

    audio_panel = ft.Container(
        content=ft.Column([
            ft.Container(
                txt("🔊  FAIXAS DE ÁUDIO", size=11, color=PRIMARY, weight="bold"),
                padding=ft.padding.only(bottom=6),
            ),
            audio_menu,
        ]),
        bgcolor=BG_CARD, border_radius=10, padding=14,
        border=ft.border.all(1, BORDER),
        width=240, visible=False,
    )

    subtitle_panel = ft.Container(
        content=ft.Column([
            ft.Container(
                txt("💬  LEGENDAS", size=11, color=PRIMARY, weight="bold"),
                padding=ft.padding.only(bottom=6),
            ),
            subtitle_menu,
        ]),
        bgcolor=BG_CARD, border_radius=10, padding=14,
        border=ft.border.all(1, BORDER),
        width=240, visible=False,
    )

    # Container preto onde o VLC renderiza o vídeo
    vlc_frame = ft.Container(expand=True, bgcolor="#000000")

    def _double_tap_fullscreen(e):
        try:
            page.window.full_screen = not page.window.full_screen
        except:
            pass
        page.update()

    # Duplo-clique = fullscreen
    mouse_detector = ft.GestureDetector(
        on_hover=lambda e: _show_smart_bar(),
        on_tap=lambda e: _show_smart_bar(),
        on_double_tap=_double_tap_fullscreen,
        content=ft.Container(expand=True, bgcolor=ft.Colors.TRANSPARENT),
    )

    player_view = ft.Stack([
        vlc_frame,
        mouse_detector,
        ft.Column([
            smart_bar,
            ft.Row([
                ft.Container(expand=True),
                ft.Column([audio_panel, subtitle_panel], spacing=6),
                ft.Container(width=16),
            ]),
        ]),
    ], expand=True)

    def _apply_subtitle_url(sub_url: str) -> bool:
        """Carrega legenda externa (URL da API) para ficheiro temporário e entrega ao VLC."""
        mp = state.get("media_player")
        if not mp or not sub_url:
            return False
        try:
            low = sub_url.lower().split("?")[0]
            if low.endswith(".vtt"):
                suf = ".vtt"
            elif low.endswith(".srt"):
                suf = ".srt"
            else:
                suf = ".srt"
            fd, path = tempfile.mkstemp(suffix=suf)
            os.close(fd)
            urllib.request.urlretrieve(sub_url, path)
            mp.video_set_subtitle_file(path)
            return True
        except (urllib.error.URLError, OSError, ValueError) as ex:
            print(f"Legenda URL: {ex}")
            return False

    def _populate_tracks():
        """
        Lista áudio/legendas conforme get_vod_info do painel. Sem misturar etiquetas do VLC.
        O VLC só é usado para aplicar a faixa de áudio (índice = posição na lista do servidor).
        """
        mp = state["media_player"]
        if not mp:
            return

        for _ in range(16):
            if mp.get_state() == vlc.State.Playing:
                break
            time.sleep(0.5)

        client = state.get("c")
        mid = state.get("api_media_id")
        api_audio = []
        api_subs = []
        state["last_vod_info_full"] = None
        if mid and client:
            try:
                raw = client.get_vod_info(mid)
                state["last_vod_info_full"] = raw
                parsed = XtreamClient.parse_vod_info_tracks(raw, client.url.rstrip("/"))
                api_audio = parsed.get("audio") or []
                api_subs = parsed.get("subtitles") or []
            except Exception as ex:
                print(f"get_vod_info: {ex}")
                state["last_vod_info_full"] = {"_fetch_error": str(ex)}

        raw_vlc_audio = mp.audio_get_track_description() or []
        vlc_audio = [(tid, tname) for tid, tname in raw_vlc_audio if tid != -1]

        def _audio_label_col(
            row: dict,
            extra: str | None = None,
            vlc_line: str | None = None,
        ) -> ft.Column:
            label = row.get("label") or ""
            src = row.get("source") or ""
            children = [txt(label, size=13)]
            if vlc_line:
                children.append(txt(vlc_line, size=10, color=MUTED))
            if src:
                children.append(txt(src, size=10, color=MUTED))
            if extra:
                children.append(txt(extra, size=10, color=MUTED))
            return ft.Column(children, spacing=2, tight=True)

        audio_menu.controls.clear()
        if api_audio:
            for i, row in enumerate(api_audio):
                vlc_line = None
                if i < len(vlc_audio):
                    tname = vlc_audio[i][1]
                    vn = tname.decode() if isinstance(tname, bytes) else str(tname)
                    if vn and vn.strip() and vn.strip().lower() not in ("disable", "desativar"):
                        vlc_line = f"No leitor: {vn.strip()}"
                if i < len(vlc_audio):
                    tid = vlc_audio[i][0]

                    def _set_audio_srv(e, track_id=tid):
                        state["media_player"].audio_set_track(track_id)
                        audio_panel.visible = False
                        page.update()

                    audio_menu.controls.append(
                        ft.Container(
                            _audio_label_col(row, vlc_line=vlc_line),
                            padding=10, border_radius=6, bgcolor="#000",
                            border=ft.border.all(1, BORDER),
                            on_click=_set_audio_srv, ink=True,
                        )
                    )
                else:
                    audio_menu.controls.append(
                        ft.Container(
                            _audio_label_col(
                                row,
                                extra=f"(servidor pos. {i + 1}; leitor não expõe esta posição)",
                                vlc_line=vlc_line,
                            ),
                            padding=10,
                            border_radius=6,
                            bgcolor="#000",
                            border=ft.border.all(1, BORDER),
                        )
                    )
        else:
            for track_id, track_name in raw_vlc_audio:
                if track_id == -1:
                    continue
                name_str = track_name.decode() if isinstance(track_name, bytes) else str(track_name)

                def _set_audio(e, tid=track_id):
                    state["media_player"].audio_set_track(tid)
                    audio_panel.visible = False
                    page.update()

                audio_menu.controls.append(
                    ft.Container(
                        txt(name_str, size=13),
                        padding=10, border_radius=6, bgcolor="#000",
                        border=ft.border.all(1, BORDER),
                        on_click=_set_audio, ink=True,
                    )
                )

        subtitle_menu.controls.clear()

        def _off_subs(e):
            try:
                state["media_player"].video_set_spu(-1)
            except Exception:
                pass
            subtitle_panel.visible = False
            page.update()

        subtitle_menu.controls.append(
            ft.Container(
                txt("Desligar legendas", size=13, color=MUTED),
                padding=10, border_radius=6, bgcolor="#000",
                border=ft.border.all(1, BORDER),
                on_click=_off_subs, ink=True,
            )
        )

        for sub in api_subs:
            url = sub.get("url")
            label = sub.get("label") or ""
            src = sub.get("source") or ""

            if url:

                def _set_ext_sub(e, u=url):
                    if _apply_subtitle_url(u):
                        subtitle_panel.visible = False
                        page.update()

                subtitle_menu.controls.append(
                    ft.Container(
                        ft.Column(
                            [txt(label, size=13)]
                            + ([txt(src, size=10, color=MUTED)] if src else []),
                            spacing=2,
                            tight=True,
                        ),
                        padding=10, border_radius=6, bgcolor="#000",
                        border=ft.border.all(1, BORDER),
                        on_click=_set_ext_sub, ink=True,
                    )
                )
            else:
                subtitle_menu.controls.append(
                    ft.Container(
                        ft.Column(
                            [txt(label, size=13), txt("(sem URL no servidor)", size=10, color=MUTED)]
                            + ([txt(src, size=10, color=MUTED)] if src else []),
                            spacing=2,
                            tight=True,
                        ),
                        padding=10, border_radius=6, bgcolor="#000",
                        border=ft.border.all(1, BORDER),
                    )
                )

        if not api_subs:
            subtitle_menu.controls.append(
                ft.Container(
                    txt("Nenhuma legenda listada pelo servidor para este título.", size=12, color=MUTED),
                    padding=10,
                )
            )

        is_live = state.get("current_mode") == "live"
        if (not is_live) and len(audio_menu.controls) == 0:
            audio_menu.controls.append(
                ft.Container(
                    txt("Nenhuma faixa de áudio listada pelo servidor para este título.", size=12, color=MUTED),
                    padding=10,
                )
            )

        # Botões sempre visíveis em filme/série; entradas = só painel (get_vod_info) + mensagens se vazio
        audio_btn.visible = not is_live
        subtitle_btn.visible = not is_live
        vod_info_dump_btn.visible = (not is_live) and bool(mid) and (
            state.get("last_vod_info_full") is not None
        )

        audio_panel.visible = False
        subtitle_panel.visible = False

        try:
            page.update()
        except Exception:
            pass

    def _show_full_vod_json(e):
        raw = state.get("last_vod_info_full")
        if raw is None:
            return
        try:
            body = json.dumps(raw, indent=2, ensure_ascii=False, default=str)
        except Exception:
            body = str(raw)
        if len(body) > 100_000:
            body = body[:100_000] + "\n… [truncado a 100000 caracteres]"

        dlg = ft.AlertDialog(
            modal=True,
            title=txt("get_vod_info — resposta completa do servidor", size=16, weight="bold"),
            content=ft.Container(
                ft.TextField(
                    value=body,
                    multiline=True,
                    read_only=True,
                    expand=True,
                    min_lines=16,
                    max_lines=22,
                    text_size=11,
                ),
                width=720,
                height=440,
            ),
        )

        def close_dump(_):
            dlg.open = False
            page.update()

        dlg.actions = [ft.TextButton("Fechar", on_click=close_dump)]
        page.dialog = dlg
        dlg.open = True
        page.update()

    vod_info_dump_btn.on_click = _show_full_vod_json

    def _embed_vlc():
        """Embute o VLC na janela Flet (Windows: set_hwnd)."""
        mp = state["media_player"]
        if not mp:
            return
        try:
            if sys.platform == "win32":
                import ctypes
                # Obtém o HWND da janela Flet
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                mp.set_hwnd(hwnd)
            elif sys.platform.startswith("linux"):
                import ctypes
                # No Linux, usa XID (não aplicável na versão de produção Windows)
                pass
        except Exception as ex:
            print(f"VLC embed error: {ex}")

    def open_player(url, name, api_media_id=None):
        state["api_media_id"] = api_media_id
        state["last_vod_info_full"] = None
        player_title.value = name
        audio_menu.controls.clear()
        subtitle_menu.controls.clear()
        audio_btn.visible      = False
        subtitle_btn.visible   = False
        vod_info_dump_btn.visible = False
        audio_panel.visible    = False
        subtitle_panel.visible = False
        smart_bar.opacity = 1.0
        main_view.content = player_view
        page.update()
        _show_smart_bar()

        # LIVE TV — esconder botões de áudio e legendas completamente
        is_live = state.get("current_mode") == "live"
        audio_btn.visible    = not is_live
        subtitle_btn.visible = not is_live
        page.update()

        if VLC_OK:
            mp = state["media_player"]
            mp.stop()
            media = state["vlc_instance"].media_new(url)
            mp.set_media(media)

            def _start():
                time.sleep(0.5)
                _embed_vlc()
                mp.play()
                # Só procuramos faixas se NÃO for Live TV (filmes/séries)
                if not is_live:
                    threading.Thread(target=_populate_tracks, daemon=True).start()
            threading.Thread(target=_start, daemon=True).start()
        else:
            # VLC não instalado — aviso
            main_view.content = ft.Container(
                ft.Column([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=60, color=PRIMARY),
                    txt("python-vlc não instalado!", size=18, weight="bold"),
                    txt("Instala com:  pip install python-vlc", color=MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=16),
                alignment=ft.Alignment(0, 0), expand=True,
            )
            page.update()

    def close_player():
        if VLC_OK and state["media_player"]:
            state["media_player"].stop()
        main_view.content = list_view
        page.update()

    # ─────────────────────────────────────────────────────────
    # NAVEGAÇÃO
    # ─────────────────────────────────────────────────────────
    def show_login():
        if VLC_OK and state["media_player"]:
            state["media_player"].stop()
        main_view.content = login_view
        page.update()

    def show_hub(user_info):
        if user_info:
            hub_username.value = user_info.get("username", "")
        main_view.content = hub_view
        page.update()

    def show_list(mode):
        state["current_mode"] = mode
        list_title.value = {"live": "LIVE TV", "vod": "MOVIES", "series": "SERIES"}[mode]
        cats = state[f"cats_{mode}"]
        cat_col.controls.clear()
        for c in cats:
            cname = c.get("category_name", "?")
            cid   = c.get("category_id")
            cat_col.controls.append(
                ft.Container(
                    txt(cname, size=13),
                    padding=14,
                    border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
                    on_click=lambda e, _id=cid: load_content(_id),
                    ink=True,
                )
            )
        content_grid.controls.clear()
        content_grid.controls.append(
            txt("Selecciona uma categoria.", color=MUTED)
        )
        main_view.content = list_view
        page.update()

    # Arrancar no Login
    show_login()

    # Desligar VPN quando a app fecha
    def on_disconnect(e):
        vpn.stop()

    page.on_disconnect = on_disconnect


# ── Arranque ─────────────────────────────────
if __name__ == "__main__":
    # VPN liga em segundo plano antes da app aparecer
    vpn.start_async()
    try:
        ft.run(main)
    except AttributeError:
        ft.app(target=main)
