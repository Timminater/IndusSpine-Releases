# Unraid: Docker R14 + PostgreSQL

## Nederlands

Download de [R14-release met checksums en testbewijzen](https://github.com/Timminater/IndusSpine-Releases/releases/tag/v0.3.6-docker-r14.20261103).
Dit is een Linux amd64-testrelease. De lokaal met Nuitka gebouwde image staat
publiek in `ghcr.io/timminater/indusspine`; uw server hoeft niets te bouwen en
heeft geen GitHub-inlog nodig. Het oude `indusspine-public` blijft behouden.

Voer als root uit op een nieuwe installatie. Vervang `192.0.2.10` door het
LAN-adres van uw server:

```bash
mkdir -p /mnt/user/Docker/indusspine
cd /mnt/user/Docker/indusspine
curl -fLO https://github.com/Timminater/IndusSpine-Releases/releases/download/v0.3.6-docker-r14.20261103/indusspine-0.3.6-docker-r14.20261103-unraid-linux-amd64.tar.gz
curl -fLO https://github.com/Timminater/IndusSpine-Releases/releases/download/v0.3.6-docker-r14.20261103/indusspine-0.3.6-docker-r14.20261103-unraid-linux-amd64.tar.gz.sha256
sha256sum -c indusspine-0.3.6-docker-r14.20261103-unraid-linux-amd64.tar.gz.sha256
tar -xzf indusspine-0.3.6-docker-r14.20261103-unraid-linux-amd64.tar.gz --strip-components=1
sha256sum -c SHA256SUMS
bash prepare.sh 192.0.2.10 18446
docker compose pull
docker compose up -d --wait
docker compose ps
```

Open `https://192.0.2.10:18446`. Het unieke adminwachtwoord staat in de private
`.env`. Lees de meegeleverde `INSTALL.md` voor lokale CA-vertrouwensinstelling,
backups en upgrades. De lokale CA staat onder
`data/caddy/caddy/pki/authorities/local/root.crt`; de browser vertrouwt deze
niet automatisch. PostgreSQL heeft geen gepubliceerde hostpoort.

De wizard begint met **Licentie**, met online/offline-activering, en daarna
**Installatie**. Opslag neemt de PostgreSQL-instelling over en controleert die
bij openen zonder datawijzigingen. Opslaan en verder test ook schrijven en
teruglezen. SQLite krijgt een pad in blijvende, schrijfbare appdata. Een
mislukte opslagtest blijft zichtbaar in de wizard. De publieke URL hoeft u
tijdens onboarding niet in te vullen; het basisadres opent de webinterface.

De voorbereiding start geen trial. U kiest online/offline-licentie of de
achtuurstrial bij onboarding. Een trial starten wist meetdata/spool/buffers
van deze installatie. Bewaar `.env`, `license-secrets`, hostidentiteit en
appdata samen met een consistente PostgreSQL-backup. Gebruik geen bestaande
installatiemap voor deze eerste-installatieopdrachten.

App-image (ook als `latest` beschikbaar; het pakket gebruikt de vaste digest):

```text
ghcr.io/timminater/indusspine:v0.3.6-docker-r14.20261103
ghcr.io/timminater/indusspine@sha256:259b3e54b4d2fdfea435b5e0d4168f5407d4b562336cdd2409e6c8531d849544
```

## English

Download the release linked above and run the commands in a new persistent
directory, replacing `192.0.2.10` with your server's LAN IP. The installer pulls
the prebuilt public Linux amd64 app and PostgreSQL images pinned by digest;
no build or registry login is required. The generated private `.env` contains
the unique admin password. Follow the included `INSTALL.md` for local CA
trust, backups and upgrades. PostgreSQL exposes no host port.

Preparation leaves the trial unstarted. Starting the capped eight-hour trial
clears this installation's measurements, spool and buffers. Preserve `.env`,
external trial key, host identity, app data and a consistent PostgreSQL backup.
This preview was tested on native Unraid and an isolated compiled local stack;
paid activation and physical PLCs were not tested. The release includes the
exact checksums, build report and functional test report.

Onboarding starts with **License** (including online/offline activation), then
**Installation**. Storage inherits and checks the configured PostgreSQL
connection; Save and continue tests writing and read-back. The SQLite default
uses writable persistent app data. Public URL is no longer part of onboarding,
and the base address opens the web interface.
