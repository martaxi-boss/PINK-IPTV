import json
import os
from urllib.parse import urljoin

import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

class XtreamClient:
    def __init__(self, url, username, password):
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.api_url = f"{self.url}/player_api.php"

    def _get(self, params):
        params.update({"username": self.username, "password": self.password})
        try:
            r = httpx.get(self.api_url, params=params, headers=HEADERS, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return None

    @staticmethod
    def _as_dict(blob):
        if blob is None:
            return {}
        if isinstance(blob, dict):
            return blob
        if isinstance(blob, str):
            try:
                return json.loads(blob)
            except json.JSONDecodeError:
                return {}
        return {}

    @staticmethod
    def _resolve_media_url(val: str, base_url: str | None) -> str | None:
        if not val or not isinstance(val, str):
            return None
        v = val.strip()
        if v.startswith("http://") or v.startswith("https://"):
            return v
        if base_url:
            return urljoin(base_url.rstrip("/") + "/", v.lstrip("/"))
        return None

    _AUDIO_NOISE_LANG = frozenset(
        {"und", "unknown", "unk", "soundhandler", "videohandler"}
    )

    @classmethod
    def _primary_language_from_entry(cls, entry: dict) -> str | None:
        if not isinstance(entry, dict):
            return None
        tags = entry.get("tags")
        if isinstance(tags, dict):
            for k in ("language", "LANGUAGE", "lang", "language-tag"):
                v = tags.get(k)
                if v is not None and str(v).strip():
                    t = str(v).strip()
                    if t.lower() not in cls._AUDIO_NOISE_LANG:
                        return t
        for k in (
            "language",
            "lang",
            "language_name",
            "lang_name",
            "title",
            "name",
            "label",
            "stream_display_name",
        ):
            v = entry.get(k)
            if v is not None and str(v).strip():
                t = str(v).strip()
                if t.lower() not in cls._AUDIO_NOISE_LANG:
                    return t
        return None

    @classmethod
    def _human_audio_label(cls, entry: dict, ordinal: int) -> str:
        """Rótulo curto para o cliente: idioma quando existir; senão 'Áudio N' + codec/canais."""
        if not isinstance(entry, dict):
            return f"Áudio {ordinal}"
        lang = cls._primary_language_from_entry(entry)
        tags = entry.get("tags") if isinstance(entry.get("tags"), dict) else {}
        cc = (entry.get("codec_name") or tags.get("codec_name") or "").strip()
        cl = (entry.get("channel_layout") or "").strip()
        tech_parts = [p for p in (cc.upper() if len(cc) <= 8 else cc, cl) if p]
        tech = " · ".join(tech_parts)
        if lang:
            return f"{lang} ({tech})" if tech else lang
        base = f"Áudio {ordinal}"
        return f"{base} ({tech})" if tech else base

    @classmethod
    def _human_subtitle_label(cls, entry: dict, ordinal: int) -> str:
        if not isinstance(entry, dict):
            return f"Legenda {ordinal}"
        lang = cls._primary_language_from_entry(entry)
        if lang:
            return lang
        for k in ("title", "name", "label", "sub_name", "language_name"):
            v = entry.get(k)
            if v and str(v).strip():
                return str(v).strip()
        return cls._label_from_server_dict(entry)

    @staticmethod
    def _label_from_server_dict(entry: dict) -> str:
        """
        Texto de apresentação só a partir de campos existentes na resposta (sem rótulos genéricos inventados).
        Se não houver texto útil, devolve JSON curto do objecto — é o que o servidor enviou.
        """
        if not isinstance(entry, dict):
            return json.dumps(entry, ensure_ascii=False)[:240]
        parts: list[str] = []
        tags = entry.get("tags")
        if isinstance(tags, dict):
            for k in (
                "language",
                "LANGUAGE",
                "lang",
                "title",
                "handler_name",
                "codec_name",
                "language-tag",
            ):
                v = tags.get(k)
                if v is not None and str(v).strip():
                    parts.append(str(v).strip())
        meta = entry.get("metadata")
        if isinstance(meta, dict):
            for k in ("language", "lang", "title", "name"):
                v = meta.get(k)
                if v is not None and str(v).strip():
                    parts.append(str(v).strip())
        langs_val = entry.get("langs") or entry.get("languages")
        if isinstance(langs_val, str) and langs_val.strip():
            parts.append(langs_val.strip())
        elif isinstance(langs_val, list):
            for x in langs_val:
                if x is not None and str(x).strip():
                    parts.append(str(x).strip())
        for k in (
            "language",
            "lang",
            "lang_id",
            "language_id",
            "language_name",
            "lang_name",
            "subtitle_language",
            "sub_lang",
            "label",
            "native",
            "name",
            "title",
            "stream_display_name",
            "audio_lang",
            "display_title",
            "code",
            "iso639",
            "locale",
            "codec_long_name",
            "codec_name",
            "channel_layout",
            "bit_rate",
        ):
            v = entry.get(k)
            if v is not None and str(v).strip():
                parts.append(str(v).strip())
        seen = set()
        uniq = []
        for p in parts:
            if p.lower() not in seen:
                seen.add(p.lower())
                uniq.append(p)
        if uniq:
            return " | ".join(uniq)
        return json.dumps(entry, ensure_ascii=False, sort_keys=True)[:240]

    @staticmethod
    def _subtitle_url_from_entry(s: dict, base_url: str | None) -> str | None:
        if not isinstance(s, dict):
            return None
        for k in (
            "url",
            "subtitle_url",
            "sub_url",
            "link",
            "srt",
            "vtt",
            "file",
            "subtitle_file",
            "sub_file",
            "subtitle_path",
            "filepath",
            "src",
            "direct_source",
            "path",
        ):
            v = s.get(k)
            if isinstance(v, str) and v.strip():
                resolved = XtreamClient._resolve_media_url(v, base_url)
                if resolved:
                    return resolved
        return None

    @classmethod
    def parse_vod_info_tracks(cls, data, base_url: str | None = None):
        """
        Áudio e legendas a partir de get_vod_info, sem descartar entradas por URL duplicada.
        Inclui dados em info, movie_data, raiz da resposta e listas em streams (ffprobe).
        """
        data = data or {}
        audio_out = []
        sub_out = []
        audio_counter = 0
        sub_counter = 0

        info = cls._as_dict(data.get("info"))
        movie_data = cls._as_dict(data.get("movie_data"))

        if not info and movie_data:
            info = cls._as_dict(movie_data.get("info") or movie_data.get("movie_info"))

        def _norm_list(blob):
            if blob is None:
                return []
            if isinstance(blob, dict):
                return [blob]
            if isinstance(blob, list):
                return list(blob)
            if isinstance(blob, str) and blob.strip():
                try:
                    parsed = json.loads(blob.strip())
                    if isinstance(parsed, list):
                        return list(parsed)
                    if isinstance(parsed, dict):
                        return [parsed]
                except json.JSONDecodeError:
                    pass
                return [blob.strip()]
            return []

        def _audio_entry_dict(a):
            if isinstance(a, dict):
                return a
            if isinstance(a, str) and a.strip():
                return {"lang": a.strip(), "_coerced_from": "string"}
            if isinstance(a, (int, float)):
                return {"name": f"Faixa {int(a)}", "_coerced_from": "number"}
            return None

        def _subtitle_string_label(st: str) -> str:
            base = st.split("?")[0].rstrip("/")
            name = os.path.basename(base) or st
            if len(name) > 80:
                name = name[:77] + "…"
            return name

        audio_parts: list[tuple[str, list]] = []
        for label, blob in (
            ("info.audio", info.get("audio")),
            ("movie_data.audio", movie_data.get("audio") if isinstance(movie_data, dict) else None),
            ("root.audio", data.get("audio")),
            ("info.audio_tracks", info.get("audio_tracks")),
            (
                "movie_data.audio_tracks",
                movie_data.get("audio_tracks") if isinstance(movie_data, dict) else None,
            ),
        ):
            lst = _norm_list(blob)
            if lst:
                audio_parts.append((label, lst))

        for source_label, audio_list in audio_parts:
            for a in audio_list:
                d = _audio_entry_dict(a)
                if not d:
                    continue
                audio_out.append(
                    {
                        "index": audio_counter,
                        "label": cls._human_audio_label(d, audio_counter + 1),
                        "raw": d,
                        "source": source_label,
                    }
                )
                audio_counter += 1

        streams_blob = info.get("streams") or info.get("stream_info")
        if isinstance(streams_blob, str) and streams_blob.strip():
            try:
                dec = json.loads(streams_blob.strip())
                if isinstance(dec, list):
                    streams_blob = dec
                elif isinstance(dec, dict):
                    streams_blob = dec.get("streams") or dec.get("stream_info") or []
                else:
                    streams_blob = []
            except json.JSONDecodeError:
                streams_blob = []
        elif isinstance(streams_blob, dict):
            inner = (
                streams_blob.get("streams")
                or streams_blob.get("stream_info")
                or streams_blob.get("data")
            )
            streams_blob = inner if isinstance(inner, list) else []
        streams_raw = None
        if isinstance(streams_blob, list):
            try:
                streams_raw = json.loads(json.dumps(streams_blob, default=str))
            except (TypeError, ValueError):
                streams_raw = streams_blob

            for idx, ent in enumerate(streams_blob):
                if not isinstance(ent, dict):
                    continue
                ctype = (ent.get("codec_type") or "").lower()
                if ctype == "audio" or (
                    ent.get("codec_name")
                    in ("aac", "mp3", "ac3", "eac3", "opus", "flac", "dts", "truehd")
                ):
                    audio_out.append(
                        {
                            "index": audio_counter,
                            "label": cls._human_audio_label(ent, audio_counter + 1),
                            "raw": ent,
                            "source": f"info.streams[{idx}]",
                        }
                    )
                    audio_counter += 1

        audio_from_server = [x["raw"] for x in audio_out]

        sub_parts: list[tuple[str, list]] = []
        primary_sub = (
            info.get("subtitle")
            or info.get("subtitles")
            or info.get("sub")
        )
        if primary_sub is None and isinstance(movie_data, dict):
            primary_sub = (
                movie_data.get("subtitle")
                or movie_data.get("subtitles")
                or movie_data.get("sub")
            )
        lst = _norm_list(primary_sub)
        if lst:
            sub_parts.append(("info|movie_data.subtitle*", lst))

        for key in ("subtitle", "subtitles", "sub", "custom_sid", "subtitle_track"):
            lst = _norm_list(data.get(key))
            if lst:
                sub_parts.append((f"root.{key}", lst))

        for key in (
            "subtitle_tracks",
            "subs",
            "available_subtitles",
            "subs_ext",
            "subtitle_ext",
            "subtitle_list",
            "sub_list",
            "subs_url",
            "subtitles_url",
            "caption",
            "captions",
            "subtitles_all",
            "all_subs",
        ):
            lst = _norm_list(info.get(key))
            if lst:
                sub_parts.append((f"info.{key}", lst))
            if isinstance(movie_data, dict):
                lst_md = _norm_list(movie_data.get(key))
                if lst_md:
                    sub_parts.append((f"movie_data.{key}", lst_md))
            lst_root = _norm_list(data.get(key))
            if lst_root:
                sub_parts.append((f"root.{key}", lst_root))

        for nk in ("subtitle_url", "sub_url", "external_subtitle", "subtitle_path"):
            lst = _norm_list(info.get(nk))
            if lst:
                sub_parts.append((f"info.{nk}", lst))
            if isinstance(movie_data, dict):
                lst2 = _norm_list(movie_data.get(nk))
                if lst2:
                    sub_parts.append((f"movie_data.{nk}", lst2))
            lst3 = _norm_list(data.get(nk))
            if lst3:
                sub_parts.append((f"root.{nk}", lst3))

        for source_label, sub_list in sub_parts:
            for s in sub_list:
                if isinstance(s, str) and s.strip():
                    st = s.strip()
                    url = cls._subtitle_url_from_entry({"url": st, "path": st}, base_url)
                    label = _subtitle_string_label(st)
                    sub_out.append(
                        {
                            "index": sub_counter,
                            "label": label,
                            "url": url,
                            "raw": {"_string": st},
                            "source": source_label,
                        }
                    )
                    sub_counter += 1
                    continue
                if not isinstance(s, dict):
                    continue
                url = cls._subtitle_url_from_entry(s, base_url)
                label = cls._human_subtitle_label(s, sub_counter + 1)
                sub_out.append(
                    {
                        "index": sub_counter,
                        "label": label,
                        "url": url,
                        "raw": s,
                        "source": source_label,
                    }
                )
                sub_counter += 1

        if isinstance(streams_blob, list):
            for idx, ent in enumerate(streams_blob):
                if not isinstance(ent, dict):
                    continue
                ctype = (ent.get("codec_type") or "").lower()
                is_sub = ctype == "subtitle" or ent.get("codec_name") in (
                    "subrip",
                    "mov_text",
                    "ass",
                    "ssa",
                    "webvtt",
                )
                if not is_sub:
                    continue
                url = cls._subtitle_url_from_entry(ent, base_url)
                label = cls._human_subtitle_label(ent, sub_counter + 1)
                sub_out.append(
                    {
                        "index": sub_counter,
                        "label": label,
                        "url": url,
                        "raw": ent,
                        "source": f"info.streams[{idx}]",
                    }
                )
                sub_counter += 1

        subtitles_primary_copy = _norm_list(primary_sub)
        try:
            subtitles_from_server = json.loads(
                json.dumps(subtitles_primary_copy, default=str)
            )
        except (TypeError, ValueError):
            subtitles_from_server = subtitles_primary_copy

        return {
            "audio": audio_out,
            "subtitles": sub_out,
            "audio_from_server": audio_from_server,
            "subtitles_from_server": subtitles_from_server,
            "streams_from_server": streams_raw,
            "movie_data_from_server": json.loads(json.dumps(movie_data, default=str))
            if movie_data
            else {},
            "root_keys": sorted(data.keys()) if isinstance(data, dict) else [],
            "info_keys": sorted(info.keys()) if isinstance(info, dict) else [],
        }

    def get_vod_info(self, vod_id):
        """Resposta bruta da API Xtream get_vod_info (filmes ou episódios de série)."""
        return self._get({"action": "get_vod_info", "vod_id": vod_id}) or {}

    def authenticate(self):
        try:
            r = httpx.get(self.api_url, params={"username": self.username, "password": self.password}, headers=HEADERS, timeout=15)
            r.raise_for_status()
            data = r.json()
            if "user_info" in data and data["user_info"].get("auth") == 1:
                return True, data["user_info"]
            return False, "Utilizador ou senha incorrectos."
        except httpx.RequestError as e:
            return False, f"Erro de ligação: {str(e)}"
        except Exception as e:
            return False, f"Erro: {str(e)}"

    def get_live_categories(self):
        return self._get({"action": "get_live_categories"}) or []

    def get_live_streams(self, category_id=None):
        params = {"action": "get_live_streams"}
        if category_id:
            params["category_id"] = category_id
        return self._get(params) or []

    def get_vod_categories(self):
        return self._get({"action": "get_vod_categories"}) or []

    def get_vod_streams(self, category_id=None):
        params = {"action": "get_vod_streams"}
        if category_id:
            params["category_id"] = category_id
        return self._get(params) or []

    def get_series_categories(self):
        return self._get({"action": "get_series_categories"}) or []

    def get_series(self, category_id=None):
        params = {"action": "get_series"}
        if category_id:
            params["category_id"] = category_id
        return self._get(params) or []

    def get_series_info(self, series_id):
        return self._get({"action": "get_series_info", "series_id": series_id}) or {}

    def get_stream_url(self, stream_id, stream_type="live", extension="mp4"):
        if stream_type == "live":
            return f"{self.url}/live/{self.username}/{self.password}/{stream_id}.m3u8"
        elif stream_type == "series":
            return f"{self.url}/series/{self.username}/{self.password}/{stream_id}.{extension}"
        return f"{self.url}/movie/{self.username}/{self.password}/{stream_id}.mp4"
