# 🎮 OptiScaler Center

<div align="center">

![Version](https://img.shields.io/badge/version-0.1.9-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg)

**Visual manager for installing and configuring OptiScaler in games**

[Releases](https://github.com/JhonathanDomingues/OptiScaler-Center/releases) • [Report Bug](https://github.com/JhonathanDomingues/OptiScaler-Center/issues) • [Request Feature](https://github.com/JhonathanDomingues/OptiScaler-Center/issues)

🌐 **[Leia em Português](README.md)**

</div>

---

## 📸 Interface

![OptiScaler Center - Game Library](imagem/exemplo.png)

*Game library with automatic Steam detection, visual cards with cover art and technology badges (DLSS, FSR, XeSS)*

---

## 📖 About

**OptiScaler Center** is a cross-platform desktop application that simplifies the management of [OptiScaler](https://github.com/optiscaler/OptiScaler) in your games. With a modern and intuitive interface, you can:

- 🔍 **Automatically detect** games installed on Steam
- 🎯 **Identify supported DLLs** (DLSS, FSR, XeSS)
- 📥 **Download and install** different versions of OptiScaler
- 💾 **Automatic backups** of original files before any installation
- 🚀 **Full FSR4 support** with standard DLLs and INT8 versions
- ⚙️ **Advanced DLL settings** without modifying any code
- 🧪 **Beta build downloads** via GitHub Actions

## ✨ Main Features

### 🎮 Game Library
- Automatic detection of Steam libraries (Windows and Linux)
- Visual grid with cover art loaded directly from Steam
- Technology badges per game (DLSS / FSR / XeSS)
- Filters by technology and installation status
- Quick search by name

### 📦 Downloads
- Stable versions via GitHub Releases
- **Beta builds** via GitHub Actions (requires PAT token)
- Local version management

### 🛠️ FSR4 SDK
- Automatically installs the **3 standard FSR4 DLLs**
- Option to replace the upscaler with an **INT8** version (lower memory usage)
- Available INT8 versions: **4.0.1**, **4.0.2c** (and future ones)
- Support for replacing any standard DLL with an external version (via Settings)

### ⚙️ Settings
- Language switching (English / Portuguese) in real time
- GitHub token configuration for beta downloads
- FSR4 DLL management (standard and INT8) without editing code

---

## 🚀 Quick Start

### 📦 Download (Ready-to-use Binaries)

Download the latest version from the [releases page](https://github.com/JhonathanDomingues/OptiScaler-Center/releases):

#### Linux (AppImage) — Recommended 🚀
```bash
chmod +x OptiScalerCenter-Linux-v0.1.9.AppImage
./OptiScalerCenter-Linux-v0.1.9.AppImage
```
No installation required. Works on any Linux distribution.

#### Linux (TAR.GZ)
```bash
tar -xzf OptiScalerCenter-Linux-v0.1.9.tar.gz
./OptiScalerCenter/OptiScalerCenter
```

#### Windows
1. Download `OptiScalerCenter-Windows-v0.1.9.zip`
2. Extract and run `OptiScalerCenter.exe`

---

## ⚙️ How to Configure

### 1. First Launch

When you open the app, click **"Scan Games"** to automatically detect your Steam library. Games will appear as cards with cover art and badges indicating DLSS, FSR, or XeSS support.

### 2. Downloading OptiScaler

Go to the **Downloads** tab and click **"Fetch Versions"** to list available releases. Click **"Download"** on the desired version.

> To download **beta builds**, you need to configure a GitHub token first (see step 4).

### 3. Installing on a Game

In the **Library** tab, click **"Install"** on the game card. The installation dialog lets you configure:

| Option | Description |
|---|---|
| **Version** | Choose an already-downloaded OptiScaler version |
| **Loader DLL** | Entry DLL (default: `dxgi.dll`; use `winmm.dll` for UE4/UE5 games) |
| **FSR4 SDK** | Installs the 3 standard FSR4 DLLs alongside OptiScaler |
| **INT8 Version** | Replaces the FSR4 upscaler with an INT8 version (4.0.1, 4.0.2c…) |

An **automatic backup** of the original files is created before any modification.

### 4. Settings (⚙️ button in the top-right corner)

#### General Tab
- **Language**: Switch between English and Portuguese (Brasil) instantly.

#### GitHub Tab
- **Stable repository**: Base URL for releases (`JhonathanDomingues/OptiScaler-Center`)
- **Access token (PAT)**: Required for downloading beta builds via GitHub Actions.
  - Generate at: GitHub → Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens
  - Required permissions: `Actions: Read` and `Contents: Read`
- **Show betas**: Enables the beta section on the Downloads tab
- **Repository / Workflow / Branch pattern**: Configures where to fetch betas from

#### FSR4 SDK Tab
- **Standard DLLs**: Table with the 3 bundled DLLs. Click **"Override…"** to use an external DLL (useful when AMD releases updates). Click **"Reset"** to go back to the bundled version.
- **INT8 Versions**: Lists all available INT8 versions. Click **"Add INT8 version"** to import an external DLL and **"Remove selected"** to delete custom versions.

### 5. Uninstalling

Click **"Uninstall"** on the game card (only available when OptiScaler is installed). The original files are automatically restored from the backup.

---

## 🔧 Development Installation

```bash
# Clone the repository
git clone https://github.com/JhonathanDomingues/OptiScaler-Center.git
cd OptiScaler-Center

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

### 🏗️ Building Executables

#### Linux
```bash
./build.sh           # Build the executable
./build-appimage.sh  # Build the AppImage (requires build.sh first)
```

#### Windows
```cmd
build.bat
```

---

## 🏗️ Architecture

The project follows **Clean Architecture** principles:

```
┌─────────────────────┐
│  Presentation UI    │  ← PyQt6 Interface
├─────────────────────┤
│  Application Layer  │  ← Use Cases & Services
├─────────────────────┤
│  Domain Layer       │  ← Entities & Business Logic
├─────────────────────┤
│  Infrastructure     │  ← Steam, GitHub, FileSystem
└─────────────────────┘
```

```
OptiScaler-Center/
├── src/
│   ├── presentation/      # PyQt6 interface (widgets, dialogs)
│   ├── application/       # Use cases (install, download, scan)
│   ├── domain/           # Entities and business logic
│   ├── infrastructure/   # Steam, GitHub, filesystem, config
│   └── utils/           # i18n, logger, constants
├── resources/
│   ├── fsr4_sdk/
│   │   ├── standard/     # 3 standard FSR4 DLLs
│   │   └── int8/         # Versioned INT8 DLLs (4.0.1, 4.0.2c…)
│   └── locales/          # Translations (pt_BR.json, en.json)
├── data/                 # YAML config, SQLite database, backups
└── tests/                # Automated tests
```

## 🛠️ Technologies

- **Python 3.10+** — Main language
- **PyQt6** — GUI framework
- **SQLite** — Local database
- **aiohttp** — Async downloads
- **vdf** — Steam file parser (libraries and configuration)
- **requests** — GitHub API integration
- **PyInstaller** — Packaging into executable

## 🗺️ Roadmap

### ✅ Completed (v0.1.9)
- [x] Automatic removal of uninstalled games on re-scan
- [x] Proton/runtime folder filter on Linux
- [x] Installation dialog layout fixed
- [x] Steam game scanner (Windows and Linux)
- [x] Modern interface with Steam-style cards
- [x] Stable and beta downloads from GitHub
- [x] Install/uninstall with automatic backup
- [x] FSR4 SDK support (standard + versioned INT8)
- [x] Settings dialog (language, GitHub, FSR4)
- [x] Individual standard DLL override without modifying code
- [x] Full i18n (PT-BR / EN) working in AppImage
- [x] UE4/UE5 folder detection

### 🔄 In Development
- [ ] Per-game configuration profiles
- [ ] Batch update for multiple games
- [ ] Advanced search filters

### 🔮 Planned
- [ ] Epic / GOG / EA / Ubisoft integration
- [ ] Application auto-update
- [ ] Cloud sync for configurations
- [ ] Portable mode

## 🤝 Contributing

1. 🍴 Fork the project
2. 🔨 Create a branch (`git checkout -b feature/MyFeature`)
3. ✅ Commit your changes (`git commit -m 'feat: description'`)
4. 📤 Push to the branch (`git push origin feature/MyFeature`)
5. 🎉 Open a Pull Request

## 🐛 Reporting Bugs

[Open an issue](https://github.com/JhonathanDomingues/OptiScaler-Center/issues) with:
- Clear description of the problem and steps to reproduce
- Application version and operating system
- Log file contents from `~/.local/share/optiscaler-center/logs/` (Linux) or `%APPDATA%\optiscaler-center\logs\` (Windows)

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [OptiScaler](https://github.com/optiscaler/OptiScaler) — For the amazing project
- [AMD FidelityFX](https://gpuopen.com/fidelityfx/) — For the FSR4 SDK

---

<div align="center">

**Made for the gaming community**

[⬆ Back to top](#-optiscaler-center)

</div>
