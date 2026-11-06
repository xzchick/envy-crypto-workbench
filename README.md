<p align="center">
  <img src="assets/readme/hero.svg" width="100%" alt="ENVY Cryptography Workbench: a native desktop window for offline encoding, classical ciphers and text analysis on macOS, Windows and Linux" />
</p>

<p align="center"><b>Encode, run classical ciphers, and analyze text — offline, in a real native app window.</b><br />
Base64 and hex, ROT and Atbash, chained recipes, and frequency analysis with a ROT brute force. From ENVY BLACK VEIL, as a standalone app.</p>

<p align="center">
  <a href="https://github.com/xzchick/envy-crypto-workbench/actions/workflows/tests.yml"><img src="https://github.com/xzchick/envy-crypto-workbench/actions/workflows/tests.yml/badge.svg" alt="Cross-platform build" /></a>
</p>
<p align="center">
  <img src="https://img.shields.io/badge/macOS-supported-ff3db4?style=for-the-badge&logo=apple&logoColor=white&labelColor=050713" alt="macOS supported" />
  <img src="https://img.shields.io/badge/Windows-supported-35e8ff?style=for-the-badge&logo=windows&logoColor=white&labelColor=050713" alt="Windows supported" />
  <img src="https://img.shields.io/badge/Linux-supported-ac8cff?style=for-the-badge&logo=linux&logoColor=white&labelColor=050713" alt="Linux supported" /><br />
  <img src="https://img.shields.io/badge/no_dependencies-pure_Python-ff3db4?style=flat-square&labelColor=050713" alt="No dependencies, pure Python" />
  <img src="https://img.shields.io/badge/Python-3.10+-8547e8?style=flat-square&logo=python&logoColor=white&labelColor=050713" alt="Python 3.10 or newer" />
  <img src="https://img.shields.io/badge/license-MIT-35e8ff?style=flat-square&labelColor=050713" alt="MIT license" />
</p>

<p align="center">
  <a href="#install"><b>Install</b></a> ·
  <a href="#works-on">Compatibility</a> ·
  <a href="#using-it">Using it</a> ·
  <a href="#honest-by-design">What it isn't</a> ·
  <a href="#build--test">Build</a>
</p>

<p align="center">
  <img src="assets/readme/window.png" width="88%" alt="The workbench window: input text, operation buttons for Base64, hex, ROT, Atbash and reverse, a recipe list and the output, in the ENVY neon theme" />
</p>

<p align="center"><sub>A real native window — not a browser view. The title pulses, the stars twinkle, and a light travels the accent bar.</sub></p>

<a name="features"></a>
<img src="assets/readme/section-features.svg" width="100%" alt="What it does" />

<img src="assets/readme/features.svg" width="100%" alt="Encodings, classical ciphers, chained recipes, frequency analysis, ROT brute force, offline and honest" />

Paste text, add operations, and watch the result update live. Stack up to 16 steps into a **recipe** (say, Base64-decode then ROT13) and run them top to bottom. The **Analysis** tab shows byte and letter frequency, Shannon entropy, the index of coincidence, and a **ROT brute force** that prints all 26 shifts at once — enough to crack a classic cipher puzzle in seconds.

<p align="center">
  <img src="assets/readme/analysis.png" width="80%" alt="The Analysis tab: entropy and index of coincidence, and a ROT brute force listing all 26 shifts, with ROT 13 revealing Hello, World!" />
</p>

<a name="works-on"></a>
<img src="assets/readme/section-works-on.svg" width="100%" alt="Works on macOS, Windows and Linux" />

<p align="center">
  <img src="assets/readme/os-macos.svg" width="32.5%" alt="macOS: native Cocoa window, bundled Python and Qt, no dependencies, app bundle or pip" />
  <img src="assets/readme/os-windows.svg" width="32.5%" alt="Windows: native Win32 window, bundled Python and Qt, no dependencies, exe bundle or pip" />
  <img src="assets/readme/os-linux.svg" width="32.5%" alt="Linux: X11 or Wayland window, bundled Python and Qt, no dependencies, tarball or pip" />
</p>

<img src="assets/readme/compat.svg" width="100%" alt="Feature compatibility by operating system" />

### Requirements

| | 🍎 macOS | 🪟 Windows | 🐧 Linux |
|---|---|---|---|
| **OS version** | macOS 11 Big Sur or newer | Windows 10 or 11 (64-bit) | A current x86_64 or arm64 desktop |
| **Standalone bundle** | Nothing else to install | Nothing else to install | Standard desktop libraries (X11 or Wayland) |
| **From pip** | Python 3.10+ | Python 3.10+ | Python 3.10+ and a desktop session |
| **Dependencies** | None (pure Python + Qt) | None | None |
| **Network** | None, ever | None, ever | None, ever |

<a name="install"></a>
<img src="assets/readme/section-install.svg" width="100%" alt="Install" />

A **standalone bundle** that needs no Python, or **pip** if you already have Python 3.10+.

### Standalone bundle (no Python) — coming with v0.1.0

When the v0.1.0 release is published, download a bundle from **Releases**:

| File | System | Run it |
|---|---|---|
| `envy-crypto-v0.1.0-macos-arm64.tar.gz` | macOS (Apple Silicon) | `tar -xzf` it, then open `envy-crypto` |
| `envy-crypto-v0.1.0-windows-x86_64.zip` | Windows (64-bit) | Unzip, then run `envy-crypto.exe` |
| `envy-crypto-v0.1.0-linux-x86_64.tar.gz` | Linux (64-bit) | `tar -xzf` it, then run `./envy-crypto` |
| `envy_crypto_workbench-0.1.0-py3-none-any.whl` | Any OS with Python 3.10+ | `pip install` the wheel |
| `SHA256SUMS.txt` | — | Verify your download first |

Running `envy-crypto` with no arguments opens the window.

### From pip (Python 3.10+)

```sh
git clone https://github.com/xzchick/envy-crypto-workbench.git
cd envy-crypto-workbench
python3 -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install .
envy-crypto                    # opens the window
```

<a name="using-it"></a>
<img src="assets/readme/section-use.svg" width="100%" alt="Using it: window or terminal" />

**In the window**

- Type or paste text, then click operations to add them to the recipe; the output updates live.
- Set the ROT shift with the spinner before adding a **Shift letters (ROT)** step.
- Open the **Analysis** tab for entropy, index of coincidence and the 26-shift ROT brute force.

**In the terminal**

```sh
envy-crypto run --op base64-decode message.txt out.txt
envy-crypto run --op rot --shift 13 message.txt out.txt
envy-crypto analyze cipher.txt          # prints frequency, entropy and ROT previews
envy-crypto recipe --recipe steps.json in.txt out.txt
```

Every `run` writes a **new** file and never overwrites your original.

<a name="honest-by-design"></a>
<img src="assets/readme/section-safety.svg" width="100%" alt="Honest by design: not modern encryption" />

These are **reversible encodings and teaching ciphers**, not security. Base64, hex, ROT and Atbash can be undone by anyone — they hide nothing. Frequency and entropy **describe** text; they never prove that something is encrypted, random, or evidence of wrongdoing.

> [!IMPORTANT]
> To actually protect a file, use **[ENVY Vault](https://github.com/xzchick/envy-vault)** (AES-256-GCM), not this workbench.

<a name="build--test"></a>
<img src="assets/readme/section-build.svg" width="100%" alt="Build and test" />

```sh
python -m unittest discover -s tests -v          # unit tests (no display needed)
pip install pyinstaller build
python scripts/build_release_bundle.py           # standalone bundle + wheel + sdist + checksums
python scripts/smoke_test_release.py             # launch the built bundle and check it runs
```

CI runs all of this on Ubuntu, Windows and macOS for every push. Regenerate the README artwork with `python scripts/render_readme_art.py`.

<p align="center"><sub>MIT licensed. Part of ENVY BLACK VEIL, packaged as a standalone app. Offline; no telemetry, no network, no accounts.</sub></p>
