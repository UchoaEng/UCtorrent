# UCtorrent

[🇧🇷 Leia em português](#-português)

UCtorrent is a Windows desktop BitTorrent client written in Python. It provides a PySide6 desktop interface, a local FastAPI WebUI/API, SQLite persistence, RSS automation, categories, tags, logs, safety checks, and a modular libtorrent-backed core.

## Legal Use

Use UCtorrent only for public files, open source releases, Linux ISOs, public datasets, public domain material, your own backups, and content distributed with permission. UCtorrent does not include piracy search plugins, illegal indexers, captcha bypass, or integrations with illegal trackers.

## Requirements

- Python 3.11+
- A libtorrent Python binding compatible with your Python and Windows build
- PySide6
- FastAPI and Uvicorn
- SQLite

Install dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install libtorrent
```

Do not install `python-libtorrent` with pip for this project; on Windows that package name often has no matching distribution. Use `libtorrent`.

If `libtorrent` is not available for your Python build, install a compatible libtorrent binding from a Python version/package source that matches your platform. UCtorrent starts with a clear dependency error for real downloads until libtorrent is installed.

## Run

```powershell
python -m uctorrent.main
```

Closing the main window keeps UCtorrent running in the Windows tray. Use the tray menu to open the window again or exit the application. Theme changes in Settings are applied immediately without restarting.

## Build Windows executable

From the project root:

```powershell
.\scripts\build_exe.ps1
```

The default folder build creates:

```text
dist\UCtorrent\UCtorrent.exe
```

For a single-file release executable:

```powershell
.\scripts\build_exe.ps1 -OneFile
```

That command creates:

```text
dist\UCtorrent.exe
```

The executable stores runtime files next to itself:

```text
data\
downloads\
logs\
```

Before building, make sure the same virtual environment has a compatible `libtorrent` binding installed if real torrent transfers are needed. Build dependencies are kept in `requirements-build.txt`.

## Features

- Add `.torrent` files and magnet links.
- Drag-and-drop `.torrent` files and magnets, including batch add with shared options.
- Pause, resume, force start, remove, recheck, reannounce, recover sources, and move torrents in bulk.
- Show progress, size, status, speed, ratio, category, tags, trackers, peers, pieces, logs, and save path.
- Persist torrents, files, trackers, peers, categories, tags, RSS data, settings, and logs in SQLite.
- Restore local configuration from `data/config.json`.
- Use a local FastAPI API and lightweight WebUI.
- Manage categories and tags.
- Read RSS feeds and define rule matching helpers.
- Create `.torrent` files through libtorrent when available.
- Warn about dangerous file extensions and validate magnets, URLs, and paths.
- Support light, dark, and system themes through PySide6 QSS.
- Minimize to the Windows tray when closing the main window.

## WebUI/API

By default the local API starts on:

```text
http://127.0.0.1:8080/
```

Default development credentials:

```text
username: admin
password: admin
```

Change these in `data/config.json` before exposing the service beyond local development. CORS is restricted by configuration.

Important endpoints:

- `POST /api/auth/login`
- `GET /api/torrents`
- `POST /api/torrents/add-file`
- `POST /api/torrents/add-magnet`
- `POST /api/torrents/batch`
- `POST /api/torrents/{id}/pause`
- `POST /api/torrents/{id}/resume`
- `POST /api/torrents/{id}/remove`
- `GET /api/categories`
- `GET /api/tags`
- `GET /api/rss/feeds`
- `GET /api/logs`
- `WebSocket /api/events`

## Project Structure

```text
uctorrent/
  main.py
  app/
    core/
    ui/
    api/
    database/
    services/
    utils/
  web/
data/
downloads/
logs/
tests/
```

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q uctorrent tests
```

The tests cover validation, formatting, config read/write, SQLite CRUD, RSS rules, safety checks, API auth, API torrent listing, batch behavior, desktop UI logic, theme switching, and executable-safe API logging.

## Git/release hygiene

- Do not commit `.venv/`, `build/`, `UCtorrent.spec`, logs, local database, local config, session state, or downloaded files.
- The folder build under `dist\UCtorrent\` is ignored.
- The single-file executable `dist\UCtorrent.exe` is not committed: it is larger than GitHub's 100 MB file limit. Build it with `.\scripts\build_exe.ps1 -OneFile` and attach it to a GitHub Release instead.

## Known Limitations

- Real BitTorrent transfer requires a compatible libtorrent Python binding.
- The initial WebUI is intentionally lightweight; the desktop UI is the primary interface.
- Some advanced libtorrent features are exposed through clean abstractions and can be expanded as binding support is verified on the target machine.

## Troubleshooting

- If the desktop does not open, confirm `PySide6` is installed in the active virtual environment.
- If adding torrents reports that libtorrent is unavailable, try `python -m pip install libtorrent` inside the active virtual environment.
- If port `8080` is unavailable, UCtorrent automatically tries the next free port and writes the selected WebUI/API URL to the log.
- Logs are written to `logs/app.log` and the SQLite `logs` table.

---

## 🇧🇷 Português

# UCtorrent

O UCtorrent é um cliente BitTorrent para desktop Windows escrito em Python. Tem interface desktop em PySide6, WebUI/API local em FastAPI, persistência em SQLite, automação por RSS, categorias, tags, logs, verificações de segurança e um núcleo modular baseado em libtorrent.

### Uso legal

Use o UCtorrent apenas para arquivos públicos, releases open source, ISOs de Linux, datasets públicos, material em domínio público, seus próprios backups e conteúdo distribuído com permissão. O UCtorrent não inclui plugins de busca de pirataria, indexadores ilegais, burla de captcha nem integrações com trackers ilegais.

### Requisitos

Python 3.11+, um binding Python do libtorrent compatível com o seu Python e Windows, PySide6, FastAPI e Uvicorn, e SQLite.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install libtorrent
```

Não instale `python-libtorrent` pelo pip neste projeto; no Windows esse nome costuma não ter distribuição compatível. Use `libtorrent`. Se ele não estiver disponível para o seu Python, instale um binding compatível com a sua plataforma; até lá, o UCtorrent abre mostrando um erro claro de dependência para downloads reais.

### Executar

```powershell
python -m uctorrent.main
```

Fechar a janela principal mantém o UCtorrent rodando na bandeja do Windows; use o menu da bandeja para reabrir ou sair. Mudanças de tema nas configurações valem na hora, sem reiniciar.

### Gerar o executável Windows

```powershell
.\scripts\build_exe.ps1            # pasta: dist\UCtorrent\UCtorrent.exe
.\scripts\build_exe.ps1 -OneFile   # arquivo único: dist\UCtorrent.exe
```

O executável guarda `data\`, `downloads\` e `logs\` ao lado dele. Antes do build, garanta que o mesmo ambiente virtual tenha o `libtorrent` instalado se precisar de transferências reais. As dependências de build ficam em `requirements-build.txt`.

### Recursos

- Adicionar arquivos `.torrent` e links magnet, inclusive arrastando e soltando e em lote com opções compartilhadas.
- Pausar, retomar, forçar início, remover, rechecar, reanunciar, recuperar fontes e mover torrents em lote.
- Ver progresso, tamanho, status, velocidade, ratio, categoria, tags, trackers, peers, peças, logs e pasta de destino.
- Guardar torrents, arquivos, trackers, peers, categorias, tags, RSS, configurações e logs no SQLite, com configuração local em `data/config.json`.
- API FastAPI local e WebUI leve.
- Categorias, tags, feeds RSS e regras de correspondência.
- Criar arquivos `.torrent` pelo libtorrent.
- Alertas de extensões perigosas e validação de magnets, URLs e caminhos.
- Temas claro, escuro e do sistema via QSS do PySide6.
- Minimizar para a bandeja do Windows ao fechar a janela.

### WebUI/API

Por padrão a API local sobe em `http://127.0.0.1:8080/`, com credenciais de desenvolvimento `admin` / `admin`. **Troque essas credenciais em `data/config.json`** antes de expor o serviço fora do ambiente local; o CORS é restrito por configuração. Os principais endpoints estão listados na versão em inglês acima (autenticação, torrents, lote, categorias, tags, RSS, logs e o WebSocket `/api/events`).

### Testes

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q uctorrent tests
```

Cobrem validação, formatação, leitura e escrita de configuração, CRUD no SQLite, regras de RSS, verificações de segurança, autenticação e listagem da API, lote, lógica da interface desktop, troca de tema e logging seguro no executável.

### Git e releases

- Não versione `.venv/`, `build/`, `UCtorrent.spec`, logs, banco local, configuração local, estado de sessão ou arquivos baixados.
- O build em pasta (`dist\UCtorrent\`) é ignorado.
- O executável de arquivo único (`dist\UCtorrent.exe`) não vai para o repositório, porque passa do limite de 100 MB por arquivo do GitHub. Gere com `.\scripts\build_exe.ps1 -OneFile` e anexe a uma Release.

### Limitações conhecidas

- Transferências reais exigem um binding Python do libtorrent compatível.
- A WebUI inicial é propositalmente leve; a interface desktop é a principal.
- Alguns recursos avançados do libtorrent estão atrás de abstrações e podem crescer conforme o suporte do binding for confirmado na máquina.

### Solução de problemas

- **O desktop não abre:** confirme que o `PySide6` está instalado no ambiente virtual ativo.
- **"libtorrent indisponível" ao adicionar torrents:** rode `python -m pip install libtorrent` no ambiente virtual ativo.
- **Porta `8080` ocupada:** o UCtorrent tenta a próxima porta livre e grava a URL escolhida no log.
- Os logs ficam em `logs/app.log` e na tabela `logs` do SQLite.