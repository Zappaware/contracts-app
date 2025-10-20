# Contracts Aruba

A web application for managing contracts built with NiceGUI and Python.

## Project Overview

This is a contract management system for Aruba Bank that provides functionality to:
- Manage active, pending, expired, and terminated contracts
- Add new contracts and vendors
- View vendor information
- User authentication and login

## Prerequisites

- Python 3.13 or higher
- [uv](https://docs.astral.sh/uv/) package manager

## Installation

### Using uv (Recommended)

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd contracts-aruba
   ```

3. **Install dependencies using uv**:
   ```bash
   uv sync
   ```

4. **Activate the virtual environment**:
   ```bash
   source .venv/bin/activate
   ```

### Alternative: Using pip with requirements.txt

If you prefer using pip, you can use the provided `requirements.txt`:

1. **Create a virtual environment**:
   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Using uv


1. **Run the application**:
   ```bash
   uv run main.py
   ```

### Using pip

1. **Activate the virtual environment**:
   ```bash
   source .venv/bin/activate
   ```

2. **Run the application**:
   ```bash
   python main.py
   ```

## Accessing the Application

Once the application is running, you can access it at:
- **Local URL**: http://localhost:5000
- **Network URL**: http://0.0.0.0:5000

The application will automatically open in your default web browser.

## Project Structure

```
contracts-aruba/
├── components/          # Reusable UI components
│   └── header.py       # Navigation header component
├── pages/              # Application pages
│   ├── active_contracts.py
│   ├── expired_contracts.py
│   ├── home_page.py
│   ├── login.py
│   ├── new_contract.py
│   ├── new_vendor.py
│   ├── pending_contracts.py
│   ├── terminated_contracts.py
│   └── vendor_info.py
├── main.py             # Main application entry point
├── pyproject.toml      # Project configuration and dependencies
├── requirements.txt    # Pip-compatible requirements file
├── uv.lock            # uv lock file for reproducible builds
└── README.md          # This file
```

## Features

- **Authentication**: Login system with user session management
- **Contract Management**: 
  - View active, pending, expired, and terminated contracts
  - Create new contracts
- **Vendor Management**:
  - Add new vendors
  - View vendor information
- **Responsive UI**: Modern web interface built with NiceGUI

## Development

### Adding Dependencies

When adding new dependencies, use uv:

```bash
uv add package-name
```

This will automatically update both `pyproject.toml` and `uv.lock`.

### Updating Dependencies

```bash
uv sync --upgrade
```

## Troubleshooting

1. **Port already in use**: If port 5000 is already in use, you can modify the port in `main.py`:
   ```python
   ui.run(title="Aruba Bank", port=5001, storage_secret="aruba_bank_secret")
   ```

2. **Python version issues**: Ensure you're using Python 3.13 or higher. Check with:
   ```bash
   python --version
   ```

3. **Dependencies not found**: Make sure the virtual environment is activated and dependencies are installed:
   ```bash
   source .venv/bin/activate
   uv sync
   ```

## License

This project is proprietary software for Aruba Bank.
