"""Cliente de la API de Kommo. TODA llamada a Kommo sale por aquí.

El límite lo rompe la suma de procesos, no uno solo: por eso cada solicitud pide
turno al contador compartido en Postgres (kw.turno) y, si el contador no responde,
no se llama (falla cerrado).
"""
import time

import requests

ESPERA_MAXIMA_S = 30


class CuotaAgotada(RuntimeError):
    """El limitador cortó o Kommo frenó. No se reintenta en caliente."""


class TokenRechazado(RuntimeError):
    """Kommo respondió 401: el token venció o lo revocaron."""


class Kommo:
    def __init__(self, db, cuenta: str, token: str, dominio: str = "kommo.com"):
        self.db, self.cuenta = db, cuenta
        self.base = f"https://{cuenta}.{dominio}/api/v4"
        self.http = requests.Session()
        self.http.headers["Authorization"] = f"Bearer {token}"

    def _turno(self):
        esperado = 0.0
        while True:
            with self.db() as con:
                ms = con.execute("select kw.turno(%s)", (self.cuenta,)).fetchone()[0]
            if ms == 0:
                return
            if ms < 0:
                raise CuotaAgotada(f"freno de mano activo en {self.cuenta}")
            esperado += ms / 1000
            if esperado > ESPERA_MAXIMA_S:
                raise CuotaAgotada(f"más de {ESPERA_MAXIMA_S} s esperando turno")
            time.sleep(ms / 1000)

    def _frenar(self, cuenta, segundos):
        with self.db() as con:
            con.execute("select kw.frenar(%s, %s)", (cuenta, segundos))

    def llamar(self, metodo: str, ruta: str, **kw):
        self._turno()
        r = self.http.request(metodo, f"{self.base}/{ruta.lstrip('/')}", timeout=30, **kw)
        if r.status_code == 204:                 # sin contenido: no existe o fin de páginas
            return None
        if r.status_code == 401:
            raise TokenRechazado("Kommo rechazó el token")
        if r.status_code == 429:                 # freno de toda la cuenta, sin reintentar
            self._frenar(self.cuenta, 60)
            raise CuotaAgotada("429 de Kommo")
        if r.status_code == 403 and "json" not in r.headers.get("Content-Type", ""):
            # 403 sin JSON = bloqueo por IP: frena TODO el servidor una hora.
            self._frenar("*", 3600)
            raise CuotaAgotada("403 de Kommo: posible bloqueo por IP")
        r.raise_for_status()
        return r.json() if r.content else None

    def get(self, ruta, **params):
        return self.llamar("GET", ruta, params=params or None)

    def post(self, ruta, cuerpo):
        return self.llamar("POST", ruta, json=cuerpo)

    def paginar(self, ruta, limite=250, **params):
        """Cada página cuesta 1 solicitud: siempre el máximo de 250."""
        for pagina in range(1, 2001):
            datos = self.get(ruta, page=pagina, limit=limite, **params)
            lote = next(iter((datos or {}).get("_embedded", {}).values()), [])
            if not lote:
                return
            yield from lote
            if "next" not in (datos.get("_links") or {}):
                return
