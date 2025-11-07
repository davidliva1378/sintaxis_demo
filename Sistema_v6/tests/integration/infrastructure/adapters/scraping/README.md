# Integration Tests - Scraping

Integration tests for the PlaywrightScraperAdapter that connect to the real PJN portal.

## Prerequisites

### 1. Install Test Dependencies

```bash
pip install -r requirements-dev.txt
```

This will install:
- pytest
- pytest-asyncio
- playwright

### 2. Install Playwright Browsers

```bash
playwright install chromium
```

### 3. Set Environment Variables

These tests require valid PJN credentials:

```bash
# Linux/Mac
export PJN_USUARIO="your_username"
export PJN_PASSWORD="your_password"
export PJN_URL="https://scw.pjn.gov.ar"  # Optional, has default

# Windows Command Prompt
set PJN_USUARIO=your_username
set PJN_PASSWORD=your_password
set PJN_URL=https://scw.pjn.gov.ar

# Windows PowerShell
$env:PJN_USUARIO="your_username"
$env:PJN_PASSWORD="your_password"
$env:PJN_URL="https://scw.pjn.gov.ar"
```

## Running Tests

### Run All Integration Tests

```bash
pytest tests/integration/ -v
```

### Run Only Scraping Integration Tests

```bash
pytest tests/integration/infrastructure/adapters/scraping/ -v
```

### Run Without Credentials (will skip)

If you don't set credentials, tests will be automatically skipped:

```bash
pytest tests/integration/infrastructure/adapters/scraping/ -v
# Output: SKIPPED [1] ... PJN credentials not available
```

### Run Specific Test

```bash
pytest tests/integration/infrastructure/adapters/scraping/test_playwright_scraper_adapter.py::TestPlaywrightScraperAdapter::test_extraer_expedientes_sin_credenciales -v
```

### Run with Debug Output

```bash
pytest tests/integration/ -v -s
```

The `-s` flag shows print statements and playwright output.

## Test Structure

### `conftest.py`
Provides fixtures for:
- `test_settings`: Settings with temporary storage
- `pjn_credentials`: Credentials from environment (or None)
- `pjn_login_url`: PJN URL from environment
- `skip_if_no_credentials`: Auto-skip marker

### `test_playwright_scraper_adapter.py`

**TestPlaywrightScraperAdapter** - Tests requiring credentials:
- `test_extraer_expedientes_sin_credenciales`: Extract all expedientes
- `test_extraer_entradas_con_credenciales`: Extract entradas/notifications
- `test_extraer_actuaciones_con_credenciales`: Extract actuaciones from first expediente

**TestPlaywrightScraperAdapterSinCredenciales** - Tests without credentials:
- `test_initialization_with_defaults`: Basic initialization
- `test_initialization_with_custom_session_file`: Custom session path

## Expected Behavior

### With Valid Credentials

Tests will:
1. Launch headless browser
2. Authenticate with PJN portal
3. Extract data
4. Validate structure
5. Print summary of extracted data

Example output:
```
✓ Extracted 25 expedientes
  First: CNM 0001/2024 - CASO DE PRUEBA...
✓ Extracted 10 entradas
  First: CNM 0002/2024 - 2024-01-15 - NOTIFICACION...
✓ Extracted actuaciones for CNM 0001/2024
  Encabezado: CNM 0001/2024
  Total actuaciones: 45
  First actuacion: 2024-01-10 - PROVIDENCIA
```

### Without Credentials

Tests will skip:
```
SKIPPED [3] ... PJN credentials not available. Set PJN_USUARIO and PJN_PASSWORD env vars.
```

### On Errors

If there are connection issues, authentication failures, or selector changes:
- Tests will fail with descriptive error messages
- Check the error output for details
- Verify credentials and network connectivity
- Check if PJN portal structure has changed

## Troubleshooting

### Playwright Browser Not Found

```bash
playwright install chromium
```

### Authentication Fails

- Verify credentials are correct
- Try logging in manually to the portal
- Check if there are CAPTCHA requirements

### Timeout Errors

- Increase timeout in settings (default: 30000ms)
- Check network connectivity
- Portal might be slow or under maintenance

### No Expedientes/Entradas Found

- This is normal if your account has no data
- Some tests will skip automatically
- Use an account with existing cases for full testing

## Continuous Integration

For CI/CD pipelines, use secrets management:

```yaml
# GitHub Actions example
- name: Run Integration Tests
  env:
    PJN_USUARIO: ${{ secrets.PJN_USUARIO }}
    PJN_PASSWORD: ${{ secrets.PJN_PASSWORD }}
  run: pytest tests/integration/ -v
```

**Note:** Be cautious running these tests in CI - they connect to the real portal and may trigger rate limiting or security alerts.
