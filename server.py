from flask import Flask, request, jsonify, render_template_string, session
import json, os, sys

sys.path.insert(0, os.path.dirname(__file__))
from xtream import XtreamClient

app = Flask(__name__)
app.secret_key = "pinkiptv2026_xc"

# Opcional: exige cabeçalho X-PINK-API-Key em todos os /api/* (defina PINK_API_KEY no ambiente).
# PINK_BIND=127.0.0.1 — só acessível na própria máquina; PINK_PORT=8080
PINK_API_KEY = os.environ.get("PINK_API_KEY", "").strip()
PINK_BIND = os.environ.get("PINK_BIND", "0.0.0.0")
PINK_PORT = int(os.environ.get("PINK_PORT", "8080"))


@app.before_request
def _pink_api_guard():
    if not request.path.startswith("/api/"):
        return None
    if not PINK_API_KEY:
        return None
    if request.headers.get("X-PINK-API-Key", "") != PINK_API_KEY:
        return jsonify({"ok": False, "error": "unauthorized"}), 401


def _profiles_file():
    r"""Mesmo critério que app.py: Documents\PINK-IPTV no Windows, ~/PINK-IPTV noutros."""
    if sys.platform == "win32":
        docs = os.path.join(os.path.expanduser("~"), "Documents", "PINK-IPTV")
    else:
        docs = os.path.join(os.path.expanduser("~"), "PINK-IPTV")
    os.makedirs(docs, exist_ok=True)
    return os.path.join(docs, "profiles.json")


PROFILES_FILE = _profiles_file()


def load_profiles():
    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_profiles(p):
    with open(PROFILES_FILE, "w", encoding="utf-8") as f:
        json.dump(p, f, indent=2)


def _vod_tracks_payload(prof, vod_id, full=False):
    """Áudio e legendas reportados pelo painel (get_vod_info). Por defeito só o essencial para mostrar disponibilidade."""
    c = XtreamClient(prof["url"], prof["username"], prof["password"])
    info = c.get_vod_info(vod_id)
    base = (prof.get("url") or "").rstrip("/")
    parsed = XtreamClient.parse_vod_info_tracks(info, base or None)
    audio_tracks = [{"id": a["index"], "label": a["label"]} for a in parsed["audio"]]
    subtitle_tracks = [
        {"id": s["index"], "label": s["label"], "url": s.get("url")}
        for s in parsed["subtitles"]
    ]
    out = {
        "ok": True,
        "vod_id": vod_id,
        "audio": audio_tracks,
        "subtitles": subtitle_tracks,
        "audio_count": len(audio_tracks),
        "subtitle_count": len(subtitle_tracks),
    }
    if not full:
        return out
    try:
        vod_info_safe = json.loads(json.dumps(info, default=str))
    except (TypeError, ValueError):
        vod_info_safe = info
    out["vod_info"] = vod_info_safe
    out["meta"] = {
        "root_keys": parsed["root_keys"],
        "info_keys": parsed["info_keys"],
        "streams_count": len(parsed["streams_from_server"] or []),
    }
    out["audio_detail"] = [
        {"id": a["index"], "label": a["label"], "source": a.get("source"), "raw": a["raw"]}
        for a in parsed["audio"]
    ]
    out["subtitles_detail"] = [
        {
            "id": s["index"],
            "label": s["label"],
            "url": s.get("url"),
            "source": s.get("source"),
            "raw": s["raw"],
        }
        for s in parsed["subtitles"]
    ]
    out["audio_from_server"] = parsed["audio_from_server"]
    out["subtitles_from_server"] = parsed["subtitles_from_server"]
    out["streams_from_server"] = parsed["streams_from_server"]
    out["movie_data_from_server"] = parsed["movie_data_from_server"]
    return out


HTML = r"""<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PINK IPTV - XC Style</title>
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
  *{margin:0;padding:0;box-sizing:border-box;font-family:'Montserrat',sans-serif;}
  :root{
    --bg: #0D0015;
    --bg-card: #180022;
    --bg-card2: #200030;
    --primary: #FF0080;
    --primary-2: #CC0066;
    --primary-glow: rgba(255,0,128,0.25);
    --text: #ffffff;
    --text-muted: #bb88cc;
    --border: #3D0055;
  }
  body { background: var(--bg); color: var(--text); height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
  
  /* --- LANDING SCREEN (Clean) --- */
  #landing-screen {
    display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh;
    background: radial-gradient(ellipse at 50% 30%, #4A0070 0%, #25003A 50%, var(--bg) 100%);
  }
  .landing-logo { text-align: center; }
  .landing-logo i { font-size: 80px; color: var(--primary); margin-bottom: 16px; filter: drop-shadow(0 0 30px var(--primary)); }
  .landing-logo h1 { font-size: 60px; font-weight: 800; letter-spacing: 5px; background: linear-gradient(135deg, #FF66CC 0%, #FF0080 50%, #CC00FF 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
  .landing-logo p { color: var(--text-muted); font-size: 14px; margin-top: 10px; letter-spacing: 4px; text-transform: uppercase; }
  .btn-main {
    padding: 18px 60px; background: linear-gradient(135deg, #FF0080, #CC00FF); color: white; border: none;
    border-radius: 50px; font-size: 18px; font-weight: 800; cursor: pointer; transition: 0.3s; margin-top: 50px;
    box-shadow: 0 10px 30px rgba(255,0,128,0.5); letter-spacing: 2px;
  }
  .btn-main:hover { transform: translateY(-4px); box-shadow: 0 16px 40px rgba(255,0,128,0.7); }

  /* --- LOGIN SCREEN (Hidden by default) --- */
  #login-screen {
    display: none; flex-direction: column; align-items: center; justify-content: center; height: 100vh;
    background: radial-gradient(ellipse at 50% 40%, #3D005A 0%, #1A0030 40%, var(--bg) 100%);
    padding: 20px; position: relative;
  }
  .btn-back-landing {
    position: absolute; top: 30px; left: 40px; background: none; border: none; color: var(--text-muted);
    font-size: 16px; cursor: pointer; display: flex; align-items: center; gap: 10px; font-weight: 600;
  }
  .btn-back-landing:hover { color: var(--primary); }
  .login-box {
    background: var(--bg-card); padding: 40px; border-radius: 16px; border: 1px solid var(--border);
    box-shadow: 0 20px 60px rgba(255,0,128,0.15); display: flex; flex-direction: column;
    justify-content: center; width: 100%; max-width: 440px;
  }
  .login-logo { text-align: center; margin-bottom: 30px; }
  .login-logo h1 { font-size: 28px; font-weight: 800; letter-spacing: 3px; }
  .login-logo span { color: var(--primary); }
  .btn-switch {
    width: 100%; padding: 12px; background: none; color: var(--text-muted);
    border: 1px solid var(--border); border-radius: 8px; font-size: 14px; font-weight: 600;
    cursor: pointer; transition: 0.3s; margin-top: 10px; display: flex; align-items: center;
    justify-content: center; gap: 8px;
  }
  .btn-switch:hover { border-color: var(--primary); color: var(--primary); }

  /* Modal Utilizadores */
  #saved-modal {
    display: none; position: fixed; top:0; left:0; width:100%; height:100%;
    background: rgba(0,0,0,0.85); z-index: 8000; align-items: center; justify-content: center;
  }
  .saved-box {
    background: var(--bg-card); border-radius: 14px; border: 1px solid var(--border);
    width: 90%; max-width: 520px; max-height: 70vh; display: flex; flex-direction: column;
    box-shadow: 0 20px 60px rgba(255,0,128,0.2);
  }
  .saved-header {
    padding: 20px 24px; border-bottom: 1px solid var(--border); display: flex;
    justify-content: space-between; align-items: center; font-weight: 800;
    color: var(--primary); letter-spacing: 1px;
  }
  .saved-header button { background: none; border: none; color: var(--text-muted); font-size: 20px; cursor: pointer; }
  .saved-header button:hover { color: var(--primary); }
  .users-scroll { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; }
  .user-card {
    background: #000; border: 1px solid var(--border); border-radius: 8px; padding: 15px;
    display: flex; align-items: center; gap: 15px; cursor: pointer; transition: 0.2s;
  }
  .user-card:hover { border-color: var(--primary); box-shadow: 0 4px 20px rgba(255,0,128,0.2); }
  .user-icon { width: 42px; height: 42px; border-radius: 50%; background: linear-gradient(135deg, #FF0080, #CC00FF); display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; flex-shrink:0; }
  .user-details { flex: 1; overflow: hidden; }
  .user-details strong { display: block; font-size: 15px; }
  .user-details span { font-size: 12px; color: var(--text-muted); }
  .btn-del-user { background: none; border: none; color: var(--text-muted); padding: 10px; cursor: pointer; }
  .btn-del-user:hover { color: var(--primary); }
  .input-group { margin-bottom: 15px; position: relative; }
  .input-group i { position: absolute; left: 15px; top: 15px; color: var(--text-muted); }
  .input-group input {
    width: 100%; padding: 14px 14px 14px 45px; background: #000; border: 1px solid var(--border);
    color: var(--text); border-radius: 8px; font-size: 14px; outline: none; transition: 0.3s;
  }
  .input-group input:focus { border-color: var(--primary); }
  .btn-login {
    width: 100%; padding: 14px; background: linear-gradient(135deg, #FF0080, #CC00FF); color: white; border: none;
    border-radius: 8px; font-size: 16px; font-weight: 700; cursor: pointer; transition: 0.3s; margin-top: 10px;
    box-shadow: 0 6px 20px rgba(255,0,128,0.4); letter-spacing: 1px;
  }
  .btn-login:hover { transform: translateY(-2px); box-shadow: 0 10px 28px rgba(255,0,128,0.6); }
  .login-msg { text-align: center; margin-top: 15px; font-size: 13px; color: var(--primary); min-height: 18px; }

  /* --- HOME HUB --- */
  #home-screen { display: none; flex-direction: column; height: 100vh; padding: 30px 50px; background: radial-gradient(ellipse at 50% 0%, #3A0058 0%, #1A0030 40%, var(--bg) 100%); }
  .top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 50px; }
  .top-logo h2 { font-weight: 800; letter-spacing: 2px; font-size: 28px; }
  .top-logo span { color: var(--primary); }
  .user-info { text-align: right; font-size: 13px; color: var(--text-muted); }
  .user-info strong { color: var(--text); font-size: 15px; }
  
  .cards-container { display: flex; justify-content: center; gap: 30px; flex: 1; align-items: center; }
  .hub-card {
    background: var(--bg-card); border: 2px solid var(--border); border-radius: 16px;
    width: 280px; height: 320px; display: flex; flex-direction: column; align-items: center; justify-content: center;
    cursor: pointer; transition: 0.3s; text-align: center;
  }
  .hub-card i { font-size: 70px; color: var(--text-muted); margin-bottom: 20px; transition: 0.3s; }
  .hub-card h3 { font-size: 28px; font-weight: 800; letter-spacing: 2px; }
  .hub-card:hover { border-color: var(--primary); transform: translateY(-10px); box-shadow: 0 10px 40px rgba(255,0,128,0.4); }
  .hub-card:hover i { color: var(--primary); transform: scale(1.1); filter: drop-shadow(0 0 12px var(--primary)); }

  .bottom-bar { display: flex; justify-content: space-between; margin-top: auto; padding-top: 20px; border-top: 1px solid var(--border); }
  .icon-btn { background: none; border: none; color: var(--text-muted); font-size: 24px; cursor: pointer; transition: 0.3s; }
  .icon-btn:hover { color: var(--primary); }
  .switch-user-btn { background: var(--bg-card); border: 1px solid var(--border); color: white; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 13px; font-weight: 600; }
  .switch-user-btn:hover { border-color: var(--primary); color: var(--primary); }

  /* --- LIST SCREEN --- */
  #list-screen { display: none; height: 100vh; flex-direction: column; }
  .list-header { padding: 15px 30px; background: var(--bg-card); border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 20px; }
  .list-header h2 { font-size: 20px; font-weight: 600; width: 200px; }
  .content-search { flex: 1; position: relative; max-width: 400px; margin-left: auto; }
  .content-search i { position: absolute; left: 15px; top: 12px; color: var(--text-muted); }
  .content-search input { width: 100%; padding: 10px 15px 10px 40px; background: #000; border: 1px solid var(--border); color: white; border-radius: 20px; outline: none; font-size: 14px; }
  .content-search input:focus { border-color: var(--primary); }
  
  .list-body { display: flex; flex: 1; overflow: hidden; }
  .sidebar { width: 300px; background: var(--bg-card); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
  .sidebar-search { padding: 15px; border-bottom: 1px solid var(--border); }
  .sidebar-search input { width: 100%; padding: 10px 15px; background: #000; border: 1px solid var(--border); color: white; border-radius: 6px; outline: none; }
  .cat-list { flex: 1; overflow-y: auto; }
  .cat-item { padding: 15px 20px; border-bottom: 1px solid var(--border); cursor: pointer; font-size: 14px; transition: 0.2s; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .cat-item:hover, .cat-item.active { background: linear-gradient(135deg, #FF0080, #CC00FF); color: white; border-color: transparent; }
  
  .content-area { flex: 1; display: flex; flex-direction: column; background: var(--bg); }
  .channels-grid { flex: 1; overflow-y: auto; padding: 20px; display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 15px; align-content: start; }
  .channel-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 15px; text-align: center; cursor: pointer; transition: 0.2s; display: flex; flex-direction: column; align-items: center; gap: 10px; }
  .channel-card:hover { border-color: var(--primary); background: #200030; box-shadow: 0 4px 20px rgba(255,0,128,0.2); }
  .ch-logo { width: 80px; height: 80px; object-fit: contain; background: #000; border-radius: 8px; padding: 5px; }
  .ch-name { font-size: 13px; font-weight: 600; width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  
  /* --- EPISODES MODAL --- */
  #episodes-modal {
    display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.9); z-index: 9000; align-items: center; justify-content: center;
  }
  .episodes-box {
    background: var(--bg-card); width: 90%; max-width: 600px; max-height: 80vh;
    border-radius: 12px; border: 1px solid var(--border); display: flex; flex-direction: column;
  }
  .ep-header { padding: 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; }
  .ep-header h3 { font-size: 18px; color: var(--primary); }
  .btn-close-ep { background: none; border: none; color: var(--text-muted); font-size: 20px; cursor: pointer; }
  .btn-close-ep:hover { color: white; }
  .ep-list { padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
  .ep-item {
    background: #000; padding: 15px; border-radius: 8px; border: 1px solid var(--border);
    cursor: pointer; display: flex; justify-content: space-between; align-items: center;
  }
  .ep-item:hover { border-color: var(--primary); }
  .ep-item i { color: var(--primary); }

  /* --- INTERNAL PLAYER SCREEN --- */
  #player-screen {
    display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: #000; z-index: 9999; flex-direction: column;
  }
  .smart-bar {
    position: absolute; top: 0; left: 0; width: 100%; padding: 20px 30px;
    background: linear-gradient(to bottom, rgba(0,0,0,0.9) 0%, transparent 100%);
    display: flex; justify-content: space-between; align-items: center;
    gap: 12px;
    opacity: 0; transition: opacity 0.3s; z-index: 10000;
  }
  #player-screen:hover .smart-bar { opacity: 1; }
  /* Botão X sempre visível — nunca desaparece */
  #btn-always-close {
    position: absolute; top: 16px; right: 16px; z-index: 10001;
    background: rgba(0,0,0,0.7); color: white; border: 2px solid rgba(255,255,255,0.3);
    width: 44px; height: 44px; border-radius: 50%; font-size: 18px;
    cursor: pointer; display: flex; align-items: center; justify-content: center;
    transition: 0.2s;
  }
  #btn-always-close:hover { background: var(--primary); border-color: var(--primary); transform: scale(1.1); }
  .smart-bar h2 { color: white; font-size: 20px; font-weight: 600; text-shadow: 0 2px 4px rgba(0,0,0,0.8); min-width: 0; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  #trackBtns { flex-shrink: 0; display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
  .btn-close-player {
    background: rgba(232,0,58,0.8); color: white; border: none; width: 44px; height: 44px;
    border-radius: 50%; font-size: 20px; cursor: pointer; display: flex; align-items: center; justify-content: center;
    transition: 0.2s;
  }
  .btn-close-player:hover { background: var(--primary); transform: scale(1.1); }
  video { width: 100%; height: 100%; outline: none; }
  
  .btn-track { background: rgba(255,255,255,0.1); color: white; border: 1px solid rgba(255,255,255,0.2); padding: 8px 15px; border-radius: 8px; cursor: pointer; font-weight: 600; transition: 0.2s; display:flex; gap:8px; align-items:center; font-size:13px; }
  .btn-track:hover { background: var(--primary); border-color: var(--primary); }
  .track-menu { display: none; position: absolute; top: 80px; right: 30px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 10px; width: 200px; z-index: 10001; box-shadow: 0 5px 15px rgba(0,0,0,0.8); }
  .track-menu h4 { font-size: 12px; color: var(--text-muted); margin-bottom: 10px; padding-bottom: 5px; border-bottom: 1px solid var(--border); }
  .track-option { padding: 8px 10px; font-size: 13px; cursor: pointer; border-radius: 4px; margin-bottom: 2px; transition: 0.2s; }
  .track-option:hover { background: rgba(255,255,255,0.1); }
  .track-option.active { color: var(--primary); font-weight: bold; }

  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--primary); }
</style>
</head>
<body>

<!-- LANDING SCREEN (Clean Home) -->
<div id="landing-screen">
  <div class="landing-logo">
    <i class="fa-solid fa-tv"></i>
    <h1>PINK IPTV</h1>
    <p>O Teu Entretenimento Sem Limites</p>
  </div>
  <button class="btn-main" onclick="showLogin()"><i class="fa-solid fa-users"></i>&nbsp;&nbsp;ENTRAR</button>
</div>

<!-- LOGIN SCREEN -->
<div id="login-screen" style="display:none">
  <button class="btn-back-landing" onclick="showLanding()"><i class="fa-solid fa-arrow-left"></i> Voltar</button>
  
  <div class="login-box">
    <div class="login-logo">
      <h1>PINK<span>IPTV</span></h1>
    </div>
    <div class="input-group">
      <i class="fa-solid fa-user-tag"></i>
      <input type="text" id="fName" placeholder="Nome (ex: A Minha TV)">
    </div>
    <div class="input-group">
      <i class="fa-solid fa-user"></i>
      <input type="text" id="fUser" placeholder="Utilizador">
    </div>
    <div class="input-group">
      <i class="fa-solid fa-lock"></i>
      <input type="password" id="fPass" placeholder="Palavra-passe">
    </div>
    <div class="input-group">
      <i class="fa-solid fa-link"></i>
      <input type="text" id="fUrl" placeholder="http://url_do_servidor.com:porta">
    </div>
    <button class="btn-login" onclick="addNewUser()">ADICIONAR UTILIZADOR</button>
    <div class="login-msg" id="loginMsg"></div>
    <button class="btn-switch" onclick="openSavedUsers()">
      <i class="fa-solid fa-users"></i> TROCAR UTILIZADOR
    </button>
  </div>
</div>

<!-- MODAL UTILIZADORES GUARDADOS -->
<div id="saved-modal">
  <div class="saved-box">
    <div class="saved-header">
      <span><i class="fa-solid fa-users"></i> UTILIZADORES GUARDADOS</span>
      <button onclick="closeSavedUsers()"><i class="fa-solid fa-xmark"></i></button>
    </div>
    <div class="users-scroll" id="usersList">
      <div style="text-align:center; padding:40px; color:#888">A carregar...</div>
    </div>
  </div>
</div>

<!-- HOME HUB -->
<div id="home-screen" style="display:none">
  <div class="top-bar">
    <div class="top-logo"><h2>PINK<span>IPTV</span></h2></div>
    <div class="user-info">
      <div id="hubUser"><strong>Username</strong></div>
      <div id="hubExp">Expiration: ---</div>
    </div>
  </div>
  
  <div class="cards-container">
    <div class="hub-card" onclick="openList('live')">
      <i class="fa-solid fa-tv"></i>
      <h3>LIVE TV</h3>
    </div>
    <div class="hub-card" onclick="openList('vod')">
      <i class="fa-solid fa-film"></i>
      <h3>MOVIES</h3>
    </div>
    <div class="hub-card" onclick="openList('series')">
      <i class="fa-solid fa-clapperboard"></i>
      <h3>SERIES</h3>
    </div>
  </div>
  
  <div class="bottom-bar">
    <div></div>
    <button class="switch-user-btn" onclick="logout()"><i class="fa-solid fa-house"></i> VOLTAR AO INÍCIO</button>
  </div>
</div>

<!-- LIST SCREEN -->
<div id="list-screen" style="display:none">
  <div class="list-header">
    <button class="icon-btn" onclick="goHome()"><i class="fa-solid fa-arrow-left"></i></button>
    <h2 id="listTitle">LIVE TV</h2>
    <div class="content-search">
      <i class="fa-solid fa-search"></i>
      <input type="text" id="searchInput" placeholder="Search in this category..." onkeyup="filterContent(this.value)">
    </div>
  </div>
  <div class="list-body">
    <div class="sidebar">
      <div class="sidebar-search">
        <input type="text" placeholder="Search Category..." onkeyup="filterCats(this.value)">
      </div>
      <div class="cat-list" id="catList"></div>
    </div>
    <div class="content-area">
      <div class="channels-grid" id="channelGrid">
        <div style="grid-column: 1/-1; text-align:center; padding: 50px; color: #888;">Select a category to load content</div>
      </div>
    </div>
  </div>
</div>

<!-- EPISODES MODAL -->
<div id="episodes-modal">
  <div class="episodes-box">
    <div class="ep-header">
      <h3 id="epSeriesTitle">Series Name</h3>
      <button class="btn-close-ep" onclick="closeEpisodes()"><i class="fa-solid fa-xmark"></i></button>
    </div>
    <div class="ep-list" id="epList">
      <div style="text-align:center; color:#888">Loading episodes...</div>
    </div>
  </div>
</div>

<!-- INTERNAL PLAYER SCREEN -->
<div id="player-screen">
  <!-- Botão X sempre visível, nunca desaparece -->
  <button id="btn-always-close" onclick="closePlayer()" title="Fechar (ESC)"><i class="fa-solid fa-xmark"></i></button>
  <div class="smart-bar">
    <button class="btn-close-player" onclick="closePlayer()"><i class="fa-solid fa-arrow-left"></i></button>
    <h2 id="playerTitle">Channel Name</h2>
    <div style="display:flex; gap:15px;" id="trackBtns">
      <button class="btn-track" id="audioBtn" onclick="toggleMenu('audioMenu')"><i class="fa-solid fa-volume-high"></i> Áudio</button>
      <button class="btn-track" id="subBtn" onclick="toggleMenu('subMenu')"><i class="fa-solid fa-closed-captioning"></i> Legendas</button>
    </div>
  </div>
  
  <!-- Menus de Áudio e Legendas (preenchidos dinamicamente via API) -->
  <div id="audioMenu" class="track-menu">
     <h4>Faixas de Áudio</h4>
     <div id="audioList"></div>
  </div>
  <div id="subMenu" class="track-menu">
     <h4>Legendas</h4>
     <div id="subList"></div>
  </div>

  <video id="videoPlayer" controls autoplay></video>
</div>

<script>
const PINK_API_KEY = __PINK_API_KEY_JS__;
let state = { cats_live: [], cats_vod: [], cats_series: [], currentMode: 'live', currentContent: [] };
let hls = null;

async function api(path, body=null){
  const hdrs = {};
  if (PINK_API_KEY) hdrs['X-PINK-API-Key'] = PINK_API_KEY;
  const opts = body
    ? {method:'POST', headers:Object.assign({'Content-Type':'application/json'}, hdrs), body:JSON.stringify(body)}
    : {headers: hdrs};
  const r = await fetch('/api'+path, opts);
  return r.json();
}

function showLanding() {
  document.getElementById('login-screen').style.display = 'none';
  document.getElementById('home-screen').style.display = 'none';
  document.getElementById('list-screen').style.display = 'none';
  document.getElementById('player-screen').style.display = 'none';
  document.getElementById('landing-screen').style.display = 'flex';
}

// Arrancar sempre na landing screen
document.addEventListener('DOMContentLoaded', function() { showLanding(); });

function showLogin() {
  document.getElementById('landing-screen').style.display = 'none';
  document.getElementById('login-screen').style.display = 'flex';
}

async function loadSavedUsers() {
  const r = await api('/profiles');
  const el = document.getElementById('usersList');
  if(!r.length) {
    el.innerHTML = '<div style="text-align:center; padding:40px; color:#888">Nenhum utilizador guardado.</div>';
    return;
  }
  el.innerHTML = r.map((p, i) => `
    <div class="user-card" onclick="loginSaved(${i})">
      <div class="user-icon">${p.name[0].toUpperCase()}</div>
      <div class="user-details">
        <strong>${esc(p.name)}</strong>
        <span>${esc(p.username)} • ${esc(p.url)}</span>
      </div>
      <button class="btn-del-user" onclick="event.stopPropagation(); deleteUser(${i})"><i class="fa-solid fa-trash"></i></button>
    </div>
  `).join('');
}

function openSavedUsers() {
  loadSavedUsers();
  document.getElementById('saved-modal').style.display = 'flex';
}

function closeSavedUsers() {
  document.getElementById('saved-modal').style.display = 'none';
}

async function deleteUser(i) {
  await api('/profiles/delete', {index: i});
  loadSavedUsers();
}

async function addNewUser(){
  const name = document.getElementById('fName').value.trim() || 'My IPTV';
  const user = document.getElementById('fUser').value.trim();
  const pass = document.getElementById('fPass').value.trim();
  const url = document.getElementById('fUrl').value.trim();
  const msg = document.getElementById('loginMsg');
  
  if(!user || !pass || !url) { msg.textContent = 'Please fill Username, Password and URL'; return; }
  msg.style.color = '#888'; msg.textContent = 'Connecting & Saving...';
  
  const r = await api('/profiles/add', {name, url, username:user, password:pass});
  if(r.ok){
    document.getElementById('fName').value = document.getElementById('fUser').value = document.getElementById('fPass').value = document.getElementById('fUrl').value = '';
    msg.textContent = '';
    loadSavedUsers();
    loginSaved(r.index);
  } else {
    msg.style.color = 'var(--primary)';
    msg.textContent = 'Failed: ' + (r.error || 'Invalid credentials');
  }
}

async function loginSaved(i) {
  closeSavedUsers();
  const msg = document.getElementById('loginMsg');
  msg.style.color = '#888'; msg.textContent = 'A ligar...';
  
  const r = await api('/login', {index: i});
  if(r.ok){
    state.cats_live = r.cats_live;
    state.cats_vod = r.cats_vod;
    state.cats_series = r.cats_series;
    
    document.getElementById('hubUser').innerHTML = `<strong>${esc(r.user.username)}</strong>`;
    let exp = r.user.exp_date;
    if(exp && exp !== "null") {
      let d = new Date(exp * 1000);
      document.getElementById('hubExp').textContent = `Expiration: ${d.toLocaleDateString()}`;
    } else {
      document.getElementById('hubExp').textContent = `Expiration: Unlimited`;
    }
    
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('home-screen').style.display = 'flex';
    msg.textContent = '';
  } else {
    msg.style.color = 'var(--primary)';
    msg.textContent = 'Login Failed: ' + (r.error || 'Error');
  }
}

function logout() {
  showLanding();
}

function goHome() {
  document.getElementById('list-screen').style.display = 'none';
  document.getElementById('home-screen').style.display = 'flex';
}

function openList(mode) {
  state.currentMode = mode;
  document.getElementById('home-screen').style.display = 'none';
  document.getElementById('list-screen').style.display = 'flex';
  
  let title = mode === 'live' ? 'LIVE TV' : (mode === 'vod' ? 'MOVIES' : 'SERIES');
  document.getElementById('listTitle').textContent = title;
  document.getElementById('searchInput').value = ''; 
  
  let cats = mode === 'live' ? state.cats_live : (mode === 'vod' ? state.cats_vod : state.cats_series);
  renderCats(cats);
  document.getElementById('channelGrid').innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 50px; color: #888;">Select a category</div>';
}

function renderCats(cats) {
  const el = document.getElementById('catList');
  el.innerHTML = cats.map(c => 
    `<div class="cat-item" onclick="loadContent('${c.category_id}', this)">${esc(c.category_name)}</div>`
  ).join('');
}

function filterCats(val) {
  let cats = state.currentMode === 'live' ? state.cats_live : (state.currentMode === 'vod' ? state.cats_vod : state.cats_series);
  val = val.toLowerCase();
  let filtered = cats.filter(c => c.category_name.toLowerCase().includes(val));
  renderCats(filtered);
}

async function loadContent(catId, el) {
  document.querySelectorAll('.cat-item').forEach(x => x.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('searchInput').value = ''; 
  
  const grid = document.getElementById('channelGrid');
  grid.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 50px; color: #888;"><i class="fa-solid fa-circle-notch fa-spin" style="font-size:30px; color:var(--primary)"></i><br><br>Loading...</div>';
  
  const r = await api('/channels', {cat_id: catId, mode: state.currentMode});
  if(!r.streams || !r.streams.length) {
    state.currentContent = [];
    grid.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 50px; color: #888;">No content found</div>';
    return;
  }
  
  state.currentContent = r.streams;
  renderContent(state.currentContent);
}

function renderContent(streams) {
  const grid = document.getElementById('channelGrid');
  if(!streams.length) {
    grid.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 50px; color: #888;">No results match your search</div>';
    return;
  }
  grid.innerHTML = streams.map(s => {
    let iconHtml = s.icon ? `<img src="${s.icon}" class="ch-logo" onerror="this.style.display='none'">` : `<div class="ch-logo" style="display:flex;align-items:center;justify-content:center;font-size:24px;color:#555"><i class="fa-solid fa-tv"></i></div>`;
    let safeUrl = esc(s.stream_url).replace(/'/g, "\\'");
    let safeName = esc(s.name).replace(/'/g, "\\'");
    let clickAction = s.stream_url.startsWith('javascript') ? s.stream_url : `playChannel('${safeUrl}', '${safeName}')`;
    if (!s.stream_url.startsWith('javascript') && state.currentMode === 'vod' && s.stream_id != null && s.stream_id !== '') {
      clickAction = `playChannel('${safeUrl}', '${safeName}', ${s.stream_id})`;
    }
    
    return `
    <div class="channel-card" onclick="${clickAction}">
      ${iconHtml}
      <div class="ch-name" title="${esc(s.name)}">${esc(s.name)}</div>
    </div>`;
  }).join('');
}

function filterContent(val) {
  val = val.toLowerCase();
  let filtered = state.currentContent.filter(s => s.name.toLowerCase().includes(val));
  renderContent(filtered);
}

// --- SERIES EPISODES ---
async function loadSeriesEpisodes(seriesId, seriesName) {
  document.getElementById('episodes-modal').style.display = 'flex';
  document.getElementById('epSeriesTitle').textContent = seriesName;
  const el = document.getElementById('epList');
  el.innerHTML = '<div style="text-align:center; color:#888"><i class="fa-solid fa-circle-notch fa-spin"></i> Loading...</div>';
  
  const r = await api('/series_info', {series_id: seriesId});
  if(!r.episodes || !r.episodes.length) {
    el.innerHTML = '<div style="text-align:center; color:#888">No episodes found.</div>';
    return;
  }
  
  el.innerHTML = r.episodes.map(ep => {
    let safeUrl = esc(ep.stream_url).replace(/'/g, "\\'");
    let safeName = esc(ep.name).replace(/'/g, "\\'");
    let eid = (ep.episode_id != null && ep.episode_id !== '') ? ep.episode_id : 'null';
    return `
    <div class="ep-item" onclick="closeEpisodes(); playChannel('${safeUrl}', '${safeName}', ${eid})">
      <div><strong>Season ${ep.season}</strong> - ${esc(ep.name)}</div>
      <i class="fa-solid fa-play"></i>
    </div>`;
  }).join('');
}

function closeEpisodes() {
  document.getElementById('episodes-modal').style.display = 'none';
}

function toggleMenu(id) {
  document.getElementById('audioMenu').style.display = 'none';
  document.getElementById('subMenu').style.display = 'none';
  if(id) document.getElementById(id).style.display = 'block';
}

function selectAudioTrack(idx) {
  try {
    if (hls && hls.audioTracks && hls.audioTracks.length > idx) {
      hls.audioTrack = idx;
    }
  } catch(e) { console.warn(e); }
}

async function selectSubtitle(url, label) {
  const video = document.getElementById('videoPlayer');
  if(!url) return;
  try {
    const resp = await fetch(url);
    const blob = await resp.blob();
    const u = URL.createObjectURL(blob);
    video.querySelectorAll('track[data-pink]').forEach(t => t.remove());
    const tr = document.createElement('track');
    tr.kind = 'subtitles';
    tr.label = label || 'sub';
    tr.src = u;
    tr.setAttribute('data-pink', '1');
    video.appendChild(tr);
    const L = video.textTracks.length;
    if(L) video.textTracks[L-1].mode = 'showing';
  } catch(e) { console.error(e); }
}

/** Apenas o que get_vod_info / painel devolve — sem misturar manifesto HLS. */
async function loadTracks(vodId) {
  if(vodId == null || vodId === 'null') return;
  const r = await api('/vod_info', {vod_id: vodId});

  const audioList = document.getElementById('audioList');
  const subList = document.getElementById('subList');
  audioList.innerHTML = '';
  subList.innerHTML = '';
  document.getElementById('audioBtn').style.display = '';
  document.getElementById('subBtn').style.display = '';

  if (!r.ok) {
    audioList.innerHTML = '<div style="color:#c66;font-size:12px;padding:8px">Não foi possível ler faixas do servidor (sessão ou ID).</div>';
    subList.innerHTML = '<div style="color:#c66;font-size:12px;padding:8px">Não foi possível ler legendas do servidor.</div>';
    return;
  }

  if(r.audio && r.audio.length >= 1) {
    r.audio.forEach(t => {
      audioList.innerHTML += `<div class="track-option" onclick="selectAudioTrack(${t.id}); toggleMenu(null);">${esc(t.label)}${t.source ? `<div style="font-size:11px;color:#888;margin-top:4px">${esc(t.source)}</div>` : ''}</div>`;
    });
  } else {
    audioList.innerHTML = '<div style="color:#888;font-size:12px;padding:8px">O servidor não listou faixas de áudio para este título.</div>';
  }

  if(r.subtitles && r.subtitles.length) {
    r.subtitles.forEach(t => {
      if(t.url) {
        const u = (t.url || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'");
        const lab = (t.label || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'");
        subList.innerHTML += `<div class="track-option" onclick="selectSubtitle('${u}','${lab}'); toggleMenu(null);">${esc(t.label || '')}${t.source ? `<div style="font-size:11px;color:#888;margin-top:4px">${esc(t.source)}</div>` : ''}</div>`;
      } else {
        subList.innerHTML += `<div class="track-option" style="opacity:0.65;cursor:default;font-size:12px">${esc(t.label || '')} <span style="color:#666">(sem URL no servidor)</span>${t.source ? `<div style="font-size:11px;color:#666;margin-top:4px">${esc(t.source)}</div>` : ''}</div>`;
      }
    });
  } else {
    subList.innerHTML = '<div style="color:#888;font-size:12px;padding:8px">O servidor não listou legendas para este título.</div>';
  }
}

// --- INTERNAL PLAYER LOGIC ---
function playChannel(url, name, vodId=null) {
  document.getElementById('player-screen').style.display = 'flex';
  document.getElementById('playerTitle').textContent = name;

  // Live TV — sem áudio nem legendas
  const isLive = state.currentMode === 'live';
  document.getElementById('audioBtn').style.display = isLive ? 'none' : '';
  document.getElementById('subBtn').style.display   = isLive ? 'none' : '';
  document.getElementById('audioMenu').style.display = 'none';
  document.getElementById('subMenu') && (document.getElementById('subMenu').style.display = 'none');

  document.getElementById('audioList').innerHTML = '<div style="color:#888; font-size:12px; padding:8px">A ler faixas da origem...</div>';
  document.getElementById('subList').innerHTML = '<div style="color:#888; font-size:12px; padding:8px">A verificar legendas...</div>';
  
  if (vodId != null && vodId !== '' && vodId !== 'null') {
    loadTracks(vodId);
  } else {
    // Live TV — o browser não consegue ler faixas em tempo real
    document.getElementById('audioList').innerHTML = '<div style="color:#888; font-size:12px; padding:8px">Disponível na App Windows (motor VLC)</div>';
    document.getElementById('subList').innerHTML = '<div style="color:#888; font-size:12px; padding:8px">Disponível na App Windows (motor VLC)</div>';
  }
  const video = document.getElementById('videoPlayer');
  
  if (url.includes('.m3u8') && Hls.isSupported()) {
    if(hls) { hls.destroy(); }
    hls = new Hls();
    hls.loadSource(url);
    hls.attachMedia(video);
    hls.on(Hls.Events.MANIFEST_PARSED, function() {
      video.play();
    });
  } else {
    // Fallback for mp4 or native HLS support (Safari)
    video.src = url;
    video.play();
  }
}

document.addEventListener('keydown', e => { if(e.key === 'Escape') closePlayer(); });

function closePlayer() {
  document.getElementById('player-screen').style.display = 'none';
  toggleMenu(null);
  const video = document.getElementById('videoPlayer');
  video.pause();
  video.src = '';
  if(hls) { hls.destroy(); hls = null; }
}

function esc(t){return (t||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;')}

</script>
</body>
</html>"""

_HTML_RENDERED = HTML.replace("__PINK_API_KEY_JS__", json.dumps(PINK_API_KEY))


@app.route("/")
def index():
    return render_template_string(_HTML_RENDERED)

@app.route("/api/profiles")
def get_profiles():
    return jsonify(load_profiles())

@app.route("/api/profiles/add", methods=["POST"])
def add_profile():
    data = request.json
    c = XtreamClient(data["url"], data["username"], data["password"])
    ok, result = c.authenticate()
    if not ok:
        return jsonify({"ok": False, "error": result})
        
    p = load_profiles()
    p.append(data)
    save_profiles(p)
    return jsonify({"ok": True, "index": len(p)-1})

@app.route("/api/profiles/delete", methods=["POST"])
def del_profile():
    p = load_profiles()
    idx = request.json.get("index", -1)
    if 0 <= idx < len(p):
        p.pop(idx)
        save_profiles(p)
    return jsonify({"ok": True})

@app.route("/api/login", methods=["POST"])
def do_login():
    p = load_profiles()
    idx = request.json.get("index", -1)
    if idx < 0 or idx >= len(p):
        return jsonify({"ok": False, "error": "Invalid profile"})
    prof = p[idx]
    c = XtreamClient(prof["url"], prof["username"], prof["password"])
    ok, result = c.authenticate()
    if not ok:
        return jsonify({"ok": False, "error": result})
    
    session["profile"] = prof
    cats_live = c.get_live_categories()
    cats_vod  = c.get_vod_categories()
    cats_series = c.get_series_categories()
    
    return jsonify({
        "ok": True, "user": result,
        "cats_live": cats_live, "cats_vod": cats_vod, "cats_series": cats_series
    })

@app.route("/api/channels", methods=["POST"])
def get_channels():
    prof = session.get("profile")
    if not prof: return jsonify({"ok": False, "error": "Not authenticated"})
    data = request.json
    c = XtreamClient(prof["url"], prof["username"], prof["password"])
    
    if data["mode"] == "live":
        streams = c.get_live_streams(data["cat_id"])
    elif data["mode"] == "vod":
        streams = c.get_vod_streams(data["cat_id"])
    elif data["mode"] == "series":
        streams = c.get_series(data["cat_id"])
    else:
        streams = []
        
    result = []
    for s in (streams or []):
        if data["mode"] == "series":
            sid  = s.get("series_id")
            icon = s.get("cover", "")
            url  = f"javascript:loadSeriesEpisodes('{sid}', '{s.get('name', '').replace(chr(39), '')}')"
        else:
            sid  = s.get("stream_id")
            icon = s.get("stream_icon", "")
            url  = c.get_stream_url(sid, data["mode"])
        row = {"name": s.get("name","?"), "icon": icon, "stream_url": url}
        if data["mode"] == "vod" and sid is not None:
            row["stream_id"] = sid
        result.append(row)
    return jsonify({"ok": True, "streams": result})

@app.route("/api/vod_info", methods=["POST"])
def get_vod_info():
    """Resposta leve: só áudio e legendas (disponibilidade). Acrescente ?full=1 para JSON completo de depuração."""
    prof = session.get("profile")
    if not prof:
        return jsonify({"ok": False, "error": "Not authenticated"})
    data = request.json or {}
    vod_id = data.get("vod_id")
    if vod_id is None:
        return jsonify({"ok": False, "error": "vod_id required"})
    full = request.args.get("full", "").lower() in ("1", "true", "yes")
    return jsonify(_vod_tracks_payload(prof, vod_id, full=full))


@app.route("/api/media_tracks", methods=["POST"])
def media_tracks():
    """Mesmo conteúdo leve que /api/vod_info (sem ?full): apenas faixas de áudio e legendas do servidor."""
    prof = session.get("profile")
    if not prof:
        return jsonify({"ok": False, "error": "Not authenticated"})
    data = request.json or {}
    vod_id = data.get("vod_id")
    if vod_id is None:
        return jsonify({"ok": False, "error": "vod_id required"})
    return jsonify(_vod_tracks_payload(prof, vod_id, full=False))

@app.route("/api/series_info", methods=["POST"])
def get_series_info():
    prof = session.get("profile")
    if not prof: return jsonify({"ok": False, "error": "Not authenticated"})
    data = request.json
    c = XtreamClient(prof["url"], prof["username"], prof["password"])
    
    info = c.get_series_info(data["series_id"])
    episodes_dict = info.get("episodes", {})
    
    result = []
    if isinstance(episodes_dict, dict):
        for season, eps in episodes_dict.items():
            for ep in eps:
                eid = ep.get("id")
                ext = ep.get("container_extension", "mp4")
                url = c.get_stream_url(eid, "series", ext)
                title = ep.get("title", f"Episódio {ep.get('episode_num')}")
                result.append({
                    "name": title,
                    "stream_url": url,
                    "season": season,
                    "episode_id": eid,
                })
    
    return jsonify({"ok": True, "episodes": result})

if __name__ == "__main__":
    app.run(host=PINK_BIND, port=PINK_PORT, debug=False)
