# openair

**Turn Skills into apps, making AI capabilities easier to use and manage.**

Skills are typically used through conversations in Codex. openair aims to turn those capabilities into apps you can open directly: choose a tool in your browser, enter your input, get results, and manage and expand your own app collection.

openair consists of two local services: **AirCode** and **AirThink**. AirCode lets apps use AI through your local Codex installation. AirThink provides an app collection with over a hundred apps and supports importing apps you build yourself.

## Why openair?

- **Give Skills an app interface**: Turn task workflows into interactive pages for everyday use.
- **Use your own Codex**: Apps call your local Codex CLI through AirCode, using your existing sign-in environment.
- **Make use of your subscription**: Use your Codex subscription to help reduce everyday costs and spending on usage-based model APIs. Actual costs and available usage depend on your subscription and usage patterns.
- **Discover and manage apps in one place**: Search apps, browse by category, and access your own apps from a single page.
- **Customize as needed**: Build apps on [ithinkair](https://www.ithinkair.com), export their source code, and import them into your local app collection.

## How It Works

```text
App in your browser
      │
      ▼
AirThink (3130)
App pages, files, and app management
      │
      ▼
AirCode (3131)
Task and workflow execution
      │
      ▼
Local Codex CLI
      │
      ▼
AI processes the task and returns results to the app
```

AirCode runs AI tasks through `codex exec`. Before using the apps, make sure the Windows user running the services can successfully use Codex from the command line.

## Quick Start

### 1. Set Up Your Environment

The current startup scripts target **Windows**. You will need:

- Python 3, with working `python` and `pip` commands.
- Codex CLI installed, signed in, and able to run tasks, with `codex` on your `PATH`.
- A modern browser and a network connection for installing dependencies and accessing AI services.

Check your environment in PowerShell and install `waitress`, which is required to start the services:

```powershell
python --version
python -m pip --version
codex --version
python -m pip install waitress
```

Both services check for missing Python dependencies at startup and install them through pip. The first startup may take a while, so watch the output in the service windows. Some apps may also require additional tools or runtime environments.

### 2. Start the Services

Navigate to the `openair` directory and run:

```powershell
cd openair
.\start.bat
```

You can also open the `openair` folder in File Explorer and double-click `start.bat`.

The script starts AirThink and AirCode. Once it detects a service listening on port `3130`, it automatically opens:

**[http://127.0.0.1:3130/index.html](http://127.0.0.1:3130/index.html)**

Keep both service windows open while using the apps. AirCode may still be installing dependencies when the page opens; wait for it to finish starting before running AI tasks. Close both service windows when you are done to stop the services.

> The startup script first forcibly terminates any processes using ports `3130` and `3131`. Make sure these ports are not being used by other services you need to keep running.

### 3. Open an App

Search by keyword or browse by category on the app collection page, then click an app card to open it.

The first time you open the page, you will be asked to enter a **User Key**. This is AirThink's local access key, separate from your Codex sign-in credentials or any model API key:

- Keys are stored in `AirThink/apps/userkey.json` as a JSON array of strings. Before use, you can set it to your own key, for example `["your-own-local-key"]`.
- If the file does not exist, the first non-empty key submitted will be saved as the local key.
- After successful verification, your browser saves the key for future access.

## Included Apps

The collection includes nearly a hundred apps across the following categories:

| Category | Use Cases |
| --- | --- |
| Writing & Content | Content creation, articles, and copywriting |
| Images & Design | Image processing and visual design |
| Slides & Visualization | Presentations, charts, and information displays |
| Learning & Teaching | Study aids and teaching tools |
| Research & Productivity | Information processing, research, and office tasks |
| Speech & Language | Speech, language learning, and conversion |
| Life & Personal Growth | Everyday tools and personal development |
| Traditional Culture | Apps related to traditional culture |

You can open these apps directly from the local collection. AI tasks run through your own Codex installation.

## Create and Import Your Own Apps

1. Visit [https://www.ithinkair.com](https://www.ithinkair.com), or click "Create App" (创建应用) in the app collection.
2. Build an app for your needs, then export its source code as a ZIP archive.
3. Return to the local app collection, click "Import App" (导入应用), and select the exported `.zip` file.
4. Once the import is complete, open the app under "My Apps" (我的应用).

Keep the exported archive's original directory structure. The importer reads `AirThink/apps/`, `AirThink/files/`, and `AirThink/skills/` from the ZIP, imports the apps and related resources locally, and updates the app list. Existing files at matching paths will be overwritten during import.

## Project Structure

```text
openair/
├── start.bat              # Starts both services and opens the browser
├── AirCode/
│   ├── app.py             # Task service entry point
│   ├── startweb.py         # HTTP server startup entry point (3131)
│   ├── run.bat
│   ├── worker/            # Workflows, AI calls, and task execution
│   ├── utilities/         # File handling, communication, and other utilities
│   └── SERVERFILES/       # Task files and Codex working directory
└── AirThink/
    ├── app.py             # App, file, import, and communication services
    ├── startweb.py         # HTTP server startup entry point (3130)
    ├── run.bat
    ├── apps/              # App collection pages, app source code, and local configuration
    ├── files/             # App resources and uploaded files
    └── skills/            # Skill files and resources
```

AirThink also uses port `3133` for its WebSocket service.

## FAQ

**The browser did not open automatically, or the page is inaccessible.**

Check the output in the AirThink window to confirm that dependency installation has finished and the service has started successfully. Then open the [app collection page](http://127.0.0.1:3130/index.html) manually. When starting from the command line, make sure you first navigate to the `openair` directory, because the startup script uses relative paths.

**The page opens, but AI tasks produce no results.**

Check the output in the AirCode window to confirm that the service has started. Also verify that the same Windows user can successfully run Codex tasks in a terminal. Being able to run `codex --version` alone does not mean you are signed in or have available usage.

**App import failed.**

Select a source code ZIP archive exported from ithinkair and preserve its internal directory structure, including `AirThink/apps/`. Check the AirThink window for specific error messages.

## Running the Services

The services currently listen on `0.0.0.0`. AirCode runs Codex tasks with `danger-full-access` and disables per-action approvals. Run the services and import apps only in a trusted personal environment. Do not expose the services directly to the public internet.

## Contributing

Bug reports, suggestions, and code contributions are welcome. When reporting an issue, include steps to reproduce it, error messages from the relevant service, and your Python and Codex CLI versions. Remove keys and personal data before sharing logs.
