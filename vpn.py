"""
PINK-IPTV — Módulo VPN Invisível
Ativa o WireGuard (Surfshark) em segundo plano no Windows.
O utilizador nunca vê nada — a VPN liga sozinha quando a app abre
e desliga automaticamente quando o processo termina (mesmo em crash).
"""

import os
import sys
import subprocess
import tempfile
import threading
import atexit
import logging

logger = logging.getLogger("vpn")

VPN_CONFIG = """[Interface]
PrivateKey = mNsHxQ+ydQmmmuN3qFpUsne3BkHJzgYXGtkJClvyiVY=
Address = 10.14.0.2/16
DNS = 162.252.172.57, 149.154.159.92

[Peer]
PublicKey = Lxg3jAOKcBA9tGBtB6vEWMFl5LUEB6AwOpuniYn1cig=
AllowedIPs = 0.0.0.0/0
Endpoint = nl-ams.prod.surfshark.com:51820
PersistentKeepalive = 25
"""

TUNNEL_NAME = "pinkiptv"
_vpn_process  = None   # processo wg-quick — morre com a app
_config_path  = None
_vpn_active   = False


def _is_windows() -> bool:
    return sys.platform == "win32"


def _find_wg_quick() -> str | None:
    """Encontra wg-quick.exe — incluído com WireGuard para Windows."""
    candidates = [
        r"C:\Program Files\WireGuard\wg-quick.exe",
        r"C:\Program Files (x86)\WireGuard\wg-quick.exe",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    try:
        result = subprocess.run(
            ["where", "wg-quick"], capture_output=True, text=True
        )
        if result.returncode == 0:
            return result.stdout.strip().splitlines()[0]
    except Exception:
        pass
    return None


def _find_wireguard_exe() -> str | None:
    """Encontra wireguard.exe para instalar como serviço."""
    candidates = [
        r"C:\Program Files\WireGuard\wireguard.exe",
        r"C:\Program Files (x86)\WireGuard\wireguard.exe",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def _write_config() -> str:
    """Escreve a config VPN numa pasta temporária."""
    config_dir = os.path.join(tempfile.gettempdir(), "pinkiptv_vpn")
    os.makedirs(config_dir, exist_ok=True)
    path = os.path.join(config_dir, f"{TUNNEL_NAME}.conf")
    with open(path, "w") as f:
        f.write(VPN_CONFIG)
    return path


def _cleanup():
    """
    Chamado automaticamente pelo Python ao fechar o processo —
    mesmo em crash. Garante que a VPN é sempre desligada.
    """
    stop()


# Registo automático: quando o processo Python terminar (normal ou crash),
# o Python chama _cleanup() sozinho — a VPN desliga sempre.
atexit.register(_cleanup)


def start() -> bool:
    """
    Ativa a VPN como serviço Windows invisível.
    Retorna True se ligou, False caso contrário.
    Nunca lança exceção.
    """
    global _vpn_active, _config_path

    if not _is_windows():
        logger.info("VPN: Ignorada (ambiente não-Windows).")
        return False

    if _vpn_active:
        return True

    wg_exe = _find_wireguard_exe()
    if not wg_exe:
        logger.warning("VPN: WireGuard não encontrado. App funciona sem VPN.")
        return False

    try:
        _config_path = _write_config()

        # Instala o túnel como serviço Windows silencioso
        run_kw: dict = dict(capture_output=True, timeout=15)
        if sys.platform == "win32":
            run_kw["creationflags"] = getattr(
                subprocess, "CREATE_NO_WINDOW", 0
            )
        result = subprocess.run(
            [wg_exe, "/installtunnelservice", _config_path],
            **run_kw,
        )

        if result.returncode == 0:
            _vpn_active = True
            logger.info("VPN: Surfshark Amsterdam ativo.")
            return True
        else:
            logger.warning(f"VPN: Falhou ao instalar serviço: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"VPN: Erro inesperado: {e}")
        return False


def stop() -> None:
    """Desativa a VPN e limpa ficheiros temporários."""
    global _vpn_active, _config_path

    if not _is_windows() or not _vpn_active:
        return

    wg_exe = _find_wireguard_exe()
    if wg_exe:
        try:
            run_kw = dict(capture_output=True, timeout=10)
            if sys.platform == "win32":
                run_kw["creationflags"] = getattr(
                    subprocess, "CREATE_NO_WINDOW", 0
                )
            subprocess.run(
                [wg_exe, "/uninstalltunnelservice", TUNNEL_NAME],
                **run_kw,
            )
            logger.info("VPN: Desligada.")
        except Exception as e:
            logger.error(f"VPN: Erro ao desligar: {e}")

    _vpn_active = False

    # Apagar ficheiro de config temporário
    try:
        if _config_path and os.path.exists(_config_path):
            os.remove(_config_path)
    except Exception:
        pass


def start_async() -> None:
    """Liga a VPN numa thread separada para não atrasar o arranque da app."""
    t = threading.Thread(target=start, daemon=True, name="vpn-thread")
    t.start()


def is_active() -> bool:
    return _vpn_active
