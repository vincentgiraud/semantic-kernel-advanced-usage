from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(
    credential, "https://cognitiveservices.azure.com/.default"
)

agent = ChatCompletionAgent(
    service=AzureChatCompletion(ad_token_provider=token_provider),
    name="ChatAgent",
    instructions="You invent jokes to have a fun conversation with the user.",
)
