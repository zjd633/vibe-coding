# ReplyKey Windows Desktop Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a portable, single-instance Windows tray application that turns copied WeChat text into one editable AI reply draft, pastes only into the still-active WeChat window, and never sends it.

**Architecture:** Keep business rules in platform-neutral Python modules and isolate Win32, OpenAI SDK, credential-store, and Qt integrations behind small adapters. A controller validates the foreground target and clipboard before dispatching one background request, appends only successful interactions to an in-memory session, and delegates safe paste-or-copy behavior to a coordinator that has no Enter/send capability.

**Tech Stack:** Python 3.11, PySide6, OpenAI Python SDK, keyring, ctypes Win32 APIs, pytest, pytest-qt, PyInstaller.

---

### Task 1: Project scaffold and test harness

**Files:**
- Create: `replykey-desktop/pyproject.toml`
- Create: `replykey-desktop/requirements.txt`
- Create: `replykey-desktop/requirements-dev.txt`
- Create: `replykey-desktop/src/replykey/__init__.py`
- Create: `replykey-desktop/tests/conftest.py`

**Steps:**
1. Declare Python 3.11, runtime dependencies, development dependencies, package discovery, and pytest settings.
2. Create a Python 3.11 virtual environment and install dependencies.
3. Run `python -m pytest --collect-only` and verify collection succeeds with no tests.

### Task 2: Configuration, secrets, session, and prompt rules

**Files:**
- Test: `replykey-desktop/tests/test_config.py`
- Test: `replykey-desktop/tests/test_credentials.py`
- Test: `replykey-desktop/tests/test_session.py`
- Test: `replykey-desktop/tests/test_prompting.py`
- Create: `replykey-desktop/src/replykey/config.py`
- Create: `replykey-desktop/src/replykey/credentials.py`
- Create: `replykey-desktop/src/replykey/session.py`
- Create: `replykey-desktop/src/replykey/prompting.py`

**Steps:**
1. Write failing tests for default values, `%APPDATA%` JSON persistence, malformed-file fallback, and absence of API keys from serialized config.
2. Run the focused tests and confirm they fail because the modules are missing.
3. Implement immutable defaults plus validated `AppConfig` and atomic `ConfigStore` persistence.
4. Write failing tests for keyring service/account isolation, empty-key deletion, and exception mapping.
5. Implement `CredentialStore` without logging or returning secrets outside explicit reads.
6. Write failing tests for eight interaction pairs, 30-minute idle expiry, manual clear, and no append on failed work.
7. Implement `ConversationSession` using an injected clock and in-memory interaction pairs.
8. Write failing tests that copied text remains an untrusted user message and that prompts request exactly one plain Chinese draft with selected tone/length.
9. Implement prompt construction and verify all focused tests pass.

### Task 3: Chat Completions provider and contract behavior

**Files:**
- Test: `replykey-desktop/tests/test_provider.py`
- Test: `replykey-desktop/tests/test_provider_contract.py`
- Create: `replykey-desktop/src/replykey/models.py`
- Create: `replykey-desktop/src/replykey/provider.py`

**Steps:**
1. Write failing unit tests for a single `model + messages` request, trimmed single draft extraction, timeout, authentication, rate-limit, connection, empty-content, and incompatible-response errors.
2. Run them and verify the expected missing-provider failures.
3. Implement `ReplyDraft`, stable Chinese-facing provider errors, OpenAI client injection, and `ChatCompletionProvider.generate()`.
4. Write a local HTTP contract fixture covering 200, 401, 429, delayed timeout, empty content, and malformed responses.
5. Verify contract requests contain no provider-specific generation parameters.
6. Add a minimal connection-test method that performs a real one-line request through the configured base URL/model.
7. Run provider tests to green.

### Task 4: Win32 target, hotkey, clipboard, paste, and startup adapters

**Files:**
- Test: `replykey-desktop/tests/test_windows.py`
- Test: `replykey-desktop/tests/test_paste.py`
- Test: `replykey-desktop/tests/test_hotkey.py`
- Test: `replykey-desktop/tests/test_startup.py`
- Create: `replykey-desktop/src/replykey/windows.py`
- Create: `replykey-desktop/src/replykey/hotkey.py`
- Create: `replykey-desktop/src/replykey/clipboard.py`
- Create: `replykey-desktop/src/replykey/paste.py`
- Create: `replykey-desktop/src/replykey/startup.py`

**Steps:**
1. Write failing tests accepting only case-insensitive `Weixin.exe` and `WeChat.exe`, rejecting dead/non-WeChat handles, and parsing supported modifier-plus-key hotkeys.
2. Implement `ForegroundTarget`, process-image lookup, window liveness checks, and hotkey parsing with ctypes.
3. Write failing tests for `RegisterHotKey` conflicts, clean unregister, clipboard read/write retries, and Unicode text handling.
4. Implement a message-loop hotkey service and Win32 clipboard backend.
5. Write failing tests for same-window paste, switched-window copy-only, restoration after paste, and no `VK_RETURN`/Enter event on every path.
6. Implement `PasteCoordinator` with only Ctrl+V injection and a clipboard transaction.
7. Write failing tests for current-user startup enable/disable and path refresh after relocation.
8. Implement the `HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run` adapter and run focused tests to green.

### Task 5: Request controller and concurrency rules

**Files:**
- Test: `replykey-desktop/tests/test_controller.py`
- Create: `replykey-desktop/src/replykey/controller.py`

**Steps:**
1. Write failing tests proving non-WeChat, empty clipboard, paused state, busy state, and immediate duplicate triggers never call the provider.
2. Write failing tests proving failures preserve clipboard/session, successful work appends one interaction, and only a still-foreground original window receives Ctrl+V.
3. Implement injected interfaces, a single-request lock, short duplicate-signature guard, background executor hooks, and status events.
4. Run controller plus all core tests to green.

### Task 6: PySide6 tray application and settings experience

**Files:**
- Test: `replykey-desktop/tests/test_ui.py`
- Test: `replykey-desktop/tests/test_single_instance.py`
- Create: `replykey-desktop/src/replykey/ui/theme.py`
- Create: `replykey-desktop/src/replykey/ui/settings.py`
- Create: `replykey-desktop/src/replykey/ui/tray.py`
- Create: `replykey-desktop/src/replykey/single_instance.py`
- Create: `replykey-desktop/src/replykey/app.py`
- Create: `replykey-desktop/src/replykey/__main__.py`
- Create: `replykey-desktop/assets/replykey.svg`

**Steps:**
1. Write failing Qt tests for labeled single-column fields, inline validation, key masking, connection-test status, and saving non-secret/secret settings to separate stores.
2. Implement the Segoe UI settings window with system light/dark palette support and accessible tab order.
3. Write failing tests for tray action wiring, pause/check states, session clearing, startup toggling, and exit cleanup.
4. Implement tray actions and non-focus notification messages.
5. Write failing tests that a second instance signals the first and exits.
6. Implement a `QLocalServer`/`QLocalSocket` single-instance guard.
7. Add first-run privacy disclosure and compose adapters/controller/background workers in `app.py`.
8. Run Qt tests headlessly and then launch a short smoke test on Windows.

### Task 7: Privacy-safe logging, documentation, and packaging

**Files:**
- Test: `replykey-desktop/tests/test_logging.py`
- Create: `replykey-desktop/src/replykey/logging_setup.py`
- Create: `replykey-desktop/README.md`
- Create: `replykey-desktop/PRIVACY.md`
- Create: `replykey-desktop/ReplyKey.spec`
- Create: `replykey-desktop/scripts/build_portable.ps1`
- Create: `replykey-desktop/scripts/smoke_portable.ps1`

**Steps:**
1. Write a failing test that log records never contain API keys, source chat text, or generated drafts.
2. Implement metadata-only rotating logs under `%APPDATA%\\ReplyKey\\logs` and run the test to green.
3. Document setup, usage, privacy, supported WeChat executables, failure messages, API compatibility limits, and the absolute no-auto-send guarantee.
4. Configure PyInstaller `--onedir --windowed` data/hidden imports and a deterministic portable ZIP script.
5. Add a smoke script that starts `ReplyKey.exe`, confirms one process, starts it again, confirms the count remains one, and closes it cleanly.

### Task 8: Full verification and portable delivery

**Files:**
- Create: `replykey-desktop/dist/ReplyKey/ReplyKey.exe` and runtime files
- Create: `replykey-desktop/dist/ReplyKey-portable.zip`

**Steps:**
1. Run the entire test suite and save the passing count.
2. Run static syntax/import checks under Python 3.11.
3. Build the onedir application and ZIP with no API key present.
4. Run the portable smoke test and inspect the archive contents.
5. Verify the existing prototype directories have no modified timestamps or content changes from this implementation.
6. Report the executable directory, ZIP path, test evidence, and the one remaining user-side acceptance step: entering a real API key and testing inside desktop WeChat.
