"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import os

from dotenv import load_dotenv

load_dotenv()

class Config:
    """Bot Configuration"""

    PORT = 3978
    APP_ID = os.environ.get("BOT_ID", "")
    APP_PASSWORD = os.environ.get("BOT_PASSWORD", "")
    AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_API_KEY"] # Azure OpenAI API key
    AZURE_OPENAI_MODEL_DEPLOYMENT_NAME = os.environ["AZURE_OPENAI_MODEL_DEPLOYMENT_NAME"] # Azure OpenAI model deployment name
    AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"] # Azure OpenAI endpoint
    clientId = os.getenv("clientId", "") # Microsoft Graph client ID
    clientSecret = os.getenv("clientSecret", "") # Microsoft Graph client secret
    tenantId = os.getenv("tenantId", "") # Microsoft Graph tenant ID

    # print(f"Configured with APP_ID={APP_ID}, AZURE_OPENAI_API_KEY={AZURE_OPENAI_API_KEY}, AZURE_OPENAI_MODEL_DEPLOYMENT_NAME={AZURE_OPENAI_MODEL_DEPLOYMENT_NAME}, AZURE_OPENAI_ENDPOINT={AZURE_OPENAI_ENDPOINT}, clientId={clientId}, clientSecret={clientSecret}, tenantId={tenantId}")