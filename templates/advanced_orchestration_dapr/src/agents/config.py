import os
from dotenv import load_dotenv

load_dotenv(override=True, verbose=True)


class Config:
    """
    Configuration class to load environment variables and validate them.
    """

    APPLICATIONINSIGHTS_CONNECTIONSTRING = os.getenv("APPLICATIONINSIGHTS_CONNECTIONSTRING")
    APPLICATIONINSIGHTS_SERVICE_NAME = os.getenv("APPLICATIONINSIGHTS_SERVICE_NAME", "agents")

    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")

    def validate(self):
        if not self.APPLICATIONINSIGHTS_CONNECTIONSTRING:
            raise ValueError("APPLICATIONINSIGHTS_CONNECTIONSTRING is not set")
        if not self.AZURE_OPENAI_ENDPOINT:
            raise ValueError("AZURE_OPENAI_ENDPOINT is not set")
        if not self.AZURE_OPENAI_MODEL:
            raise ValueError("AZURE_OPENAI_MODEL is not set")
        if not self.AZURE_OPENAI_API_VERSION:
            raise ValueError("AZURE_OPENAI_API_VERSION is not set")


config = Config()
config.validate()
