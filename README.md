# Visit Counter

![CI](https://github.com/miljkovicdunja/visit-counter/actions/workflows/ci.yml/badge.svg)

Flask aplikacija koja broji posete i čuva brojač u Redis bazi. Sama aplikacija je jednostavna: svaki poziv na   `/visits` uvećava brojač u Redisu i vraća trenutnu vrednost. Fokus nije na kodu, već na svemu oko njega: Docker image, Docker Compose okruženje sa trajnim podacima, healthcheck skripta i CI pipeline na GitHub Actions.


## Arhitektura

```
            Host računar
          localhost:8080
                 │
┌────────────────┼──────── Docker Compose mreža ──────────────────┐
│                ▼                                                │
│   ┌────────────────────┐   redis:6379    ┌───────────────────┐  │
│   │  app               │ ──────────────▶ │  redis            │  │
│   │  Flask + gunicorn  │                 │  redis:7.4-alpine │  │
│   │  port 8080         │                 │  (bez spoljnog    │  │
│   └────────────────────┘                 │   porta)          │  │
│                                          └─────────┬─────────┘  │
└────────────────────────────────────────────────────┼────────────┘
                                                     │
                                          volume: redis-data (/data)
```

| Endpoint | Ponašanje |
|---|---|
| `GET /` | `{"message": "Hello DevOps", "host": "<ID kontejnera>"}` |
| `GET /visits` | Uvećava brojač u Redisu i vraća `{"visits": N}` |
| `GET /health` | `200 {"status": "ok"}` ako je Redis dostupan, inače `503 {"status": "error"}` |

## Preduslovi

- Docker Desktop ili Docker Engine + Docker Compose (Linux)
- Git
- Na Windows-u: WSL2 (Ubuntu) za pokretanje Bash skripte

## Pokretanje

```bash
git clone https://github.com/miljkovicdunja/visit-counter.git
cd visit-counter
cp .env.example .env
docker compose up -d --build
```

Provera (može i u browseru na istim adresama):

```bash
curl http://localhost:8080/
curl http://localhost:8080/visits     # {"visits": 1}
curl http://localhost:8080/health     # {"status": "ok"}
```

Gašenje (podaci ostaju u volume-u):

```bash
docker compose down
```

Brisanje i podataka: `docker compose down -v`

## Konfiguracija

Sva konfiguracija se čita iz promenljivih okruženja (fajl `.env`, šablon je `.env.example`):

| Promenljiva | Opis | Primer |
|---|---|---|
| `APP_PORT` | Port na kom aplikacija sluša (i koji je izložen na hostu) | `8080` |
| `REDIS_HOST` | Adresa Redis servera | `redis` |
| `REDIS_PORT` | Port Redis servera | `6379` |

Promena porta: izmeniti `APP_PORT` u `.env` i ponovo pokrenuti `docker compose up -d`.

## Healthcheck skripta

```bash
./scripts/healthcheck.sh http://localhost:8080
```

Poziva `/health` do 5 puta sa pauzom od 3 sekunde i loguje svaki pokušaj:

```
[2026-11-08 22:50:01] Pokušaj 1/5 - HTTP 200
[2026-11-08 22:50:01] Aplikacija je zdrava.
```

Izlazni kod je `0` ako je aplikacija zdrava, `1` ako nije ni posle 5 pokušaja
ili ako URL nije prosleđen. `HTTP 000` znači da konekcija nije uspostavljena.

## Lokalni razvoj i testovi

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
ruff check .
pytest -v
```

Testovi koriste `fakeredis`, pa im ne treba pokrenut Redis.

## CI

GitHub Actions (`.github/workflows/ci.yml`) se pokreće na svaki push i pull request ka `main` grani:

1. checkout koda
2. instalacija zavisnosti
3. linter (`ruff`)
4. testovi (`pytest`)
5. build Docker image-a (tagovan SHA commita)

Ako bilo koji korak ne prođe, pipeline pada.

## Struktura projekta

```
.
├── .github/workflows/ci.yml   # CI pipeline
├── scripts/healthcheck.sh     # Bash skripta za proveru zdravlja
├── tests/test_app.py          # automatski testovi
├── app.py                     # Flask aplikacija
├── Dockerfile
├── .dockerignore
├── docker-compose.yml
├── .env.example               # šablon konfiguracije
├── requirements.txt           # produkcione zavisnosti
└── requirements-dev.txt       # zavisnosti za testove i linter
```

## Objašnjenje važnijih odluka

- **Python + Flask** – jednostavan i dovoljan za malu aplikaciju sa tri endpointa.
- **gunicorn umesto Flask dev servera** – Flaskov ugrađeni server je namenjen samo razvoju; gunicorn je produkcioni server koji obrađuje više zahteva paralelno (2 workera).
- **`python:3.14-slim` osnovna slika** – zvanična slika sa tačnom verzijom radi ponovljivih buildova; `slim` varijanta je višestruko manja od pune slike. Ista verzija Pythona se koristi lokalno, u CI-ju i u image-u. 
- **Redosled slojeva u Dockerfile-u** – `requirements.txt` se kopira i instalira pre koda, pa izmena koda ne pokreće ponovnu instalaciju zavisnosti (Docker cache).
- **Non-root korisnik** – aplikacija radi kao `appuser`; ako bi neko iskoristio ranjivost u aplikaciji, ne bi imao root prava u kontejneru.
- **Redis bez izloženog porta** – dostupan je samo aplikaciji kroz internu Compose mrežu, što smanjuje površinu za napad.
- **Volume + `appendonly yes`** – podaci Redisa se čuvaju van kontejnera i svaka izmena se upisuje na disk, pa brojač preživljava `docker compose down` i restart.
- **Healthcheck za oba servisa i `depends_on: service_healthy`** – aplikacija se pokreće tek kada Redis odgovara na `PING`; healthcheck aplikacije koristi Python jer slim image nema `curl`.
- **`restart: unless-stopped`** – kontejner se automatski podiže posle pada ili restarta Dockera, osim ako ga ručno zaustavim.
- **503 umesto 500 na `/health`** – 503 jasno kaže da je nedostupna zavisnost, a ne da postoji greška u kodu.
- **Konfiguracija u `.env`** – isti image radi u svakom okruženju; u repozitorijumu je samo `.env.example`.
- **Pinovane verzije zavisnosti, odvojeni `requirements-dev.txt`** – ponovljivi buildovi; alati za testiranje ne ulaze u produkcioni image.
- **`fakeredis` u testovima** – testovi su brzi, nezavisni i rade u CI-ju bez pravog Redisa.

## Problemi na koje sam naišla

- **`SyntaxError` zbog `0.0.0.0` bez navodnika** – adresa je string, pa mora pod navodnike (`host="0.0.0.0"`).
- **pytest nije nalazio testove i modul `app`** – nedostajali su `conftest.py` u korenu i `tests/__init__.py`.
- **`/health` je vraćao 500 u kontejneru** – u `docker logs` sam videla `TypeError` zbog greške u kucanju (`decode_response` umesto `decode_responses`). Testovi to nisu uhvatili jer zamenjuju `get_redis` lažnim Redisom, pa se prava funkcija nije izvršavala.
- **Gunicorn je slušao na portu 8000 umesto 8080** – pokretala sam image napravljen pre ispravke Dockerfile-a. Posle ponovnog builda radi. Naučila sam da posle svake izmene treba ponovo buildovati image i da u logu piše na kom portu aplikacija sluša.
- **Commitovi su završili na pogrešnoj grani** – posle rada na `feature/health-endpoint` nastavila sam da commitujem na toj grani, a Pull Request nisam ni otvorila. Rešila sam otvaranjem PR-a, merge-om i prelaskom na `main` (`git switch main`, `git pull`).
- **`Permission denied` / `Operation not permitted`** – neki fajlovi su imali vlasnika `root`, pa Git i `chmod` nisu mogli da ih menjaju. Rešeno sa `sudo chown -R dunja:dunja ~/visit-counter`.

## Šta bih unapredila da imam više vremena

- **Multi-stage build** da bi image bio još manji.
- **Bezbednosno skeniranje image-a** (Trivy) u pipeline-u.
- **Objavljivanje image-a** u GitHub Container Registry na svaki push na `main`.
- **Makefile** sa prečicama (`make up`, `make test`…).
- **Integracioni test sa pravim Redisom** (npr. pokretanje `docker compose` i
  `healthcheck.sh` u CI-ju), da bi greške poput `decode_responses` bile
  uhvaćene automatski.

## Korišćeni alati

- Claude (AI asistent) – za objašnjenje koncepata (Docker, Compose, CI, Bash), pomoć oko konfiguracije i pomoć pri čitanju grešaka. Svaki deo koda sam prošla i razumela pre commita.
- Zvanična dokumentacija: Docker, Docker Compose, Flask, GitHub Actions
- YouTube - uvod u GitHub Actions, Docker Compose.
- VS Code + WSL2 (Ubuntu), Docker Desktop

