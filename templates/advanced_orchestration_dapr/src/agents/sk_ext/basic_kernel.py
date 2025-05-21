from openai import AsyncAzureOpenAI
from semantic_kernel.kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from config import config

# See https://techcommunity.microsoft.com/blog/azuredevcommunityblog/using-keyless-authentication-with-azure-openai/4111521
credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(
    credential, "https://cognitiveservices.azure.com/.default"
)


def create_client() -> AsyncAzureOpenAI:
    return AsyncAzureOpenAI(
        azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
        azure_deployment=config.AZURE_OPENAI_MODEL,
        azure_ad_token_provider=token_provider,
        api_version=config.AZURE_OPENAI_API_VERSION,
    )


def create_service(service_id: str = "default"):
    return AzureChatCompletion(
        deployment_name=config.AZURE_OPENAI_MODEL,
        async_client=create_client(),
        service_id=service_id,
    )


# NOTE: we use a function to create a new kernel instance,
# so to allow each agent to have its own and be truly isolated
# Of course, when hosted together agents may share a single instace
def create_kernel(service_id: str = "default") -> Kernel:
    kernel = Kernel()

    kernel.add_service(create_service(service_id))

    return kernel
