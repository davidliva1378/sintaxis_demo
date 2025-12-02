
from infrastructure.config import get_settings
import os

print(f"Current working directory: {os.getcwd()}")
settings = get_settings()
print(f"DB User: {settings.database.user}")
print(f"DB Password length: {len(settings.database.password)}")
print(f"DB Password is empty: {settings.database.password == ''}")
print(f"DB Host: {settings.database.host}")

print(f"PJN User: {settings.auth.usuario}")
print(f"PJN Password length: {len(settings.auth.password) if settings.auth.password else 0}")
print(f"PJN Password is empty: {not settings.auth.password}")
