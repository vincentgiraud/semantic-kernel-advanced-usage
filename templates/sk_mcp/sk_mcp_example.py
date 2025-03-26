#!/usr/bin/env python
# Jokes MCP Server - Using SK Agents to generate and evaluate jokes

import os
from typing import Dict
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context
from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.contents import ChatHistory
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

from semantic_kernel.agents.strategies import (
    TerminationStrategy,
    DefaultTerminationStrategy
)

# Load environment variables
load_dotenv()

# Create an MCP server
mcp = FastMCP("Joke Generator")

# Helper functions to create kernel and agents
def create_kernel() -> Kernel:
    """Create a kernel with OpenAI service."""
    kernel = Kernel()
    kernel.add_service(
            AzureChatCompletion(
                service_id="gpt-4o",
                deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY")
            )
        )
    return kernel

# Create specialized agents for joke generation
class JokeVotingTerminationStrategy(TerminationStrategy):
    """A strategy that terminates when voting is complete."""
    
    async def should_agent_terminate(self, agent, history):
        """Check if voting is complete."""
        if len(history) < 2:
            return False
        
        last_message = history[-1].content.lower()
        return "voting complete" in last_message or "voting finished" in last_message

# MCP Tools for joke generation
@mcp.tool()
async def generate_jokes(topic: str, number_of_jokes: int = 3, ctx: Context = None) -> str:
    """Generate multiple jokes on a given topic using a team of comedian agents."""
    
    # Report progress
    if ctx:
        ctx.info(f"Generating {number_of_jokes} jokes about {topic}...")
    
    # Create the joke writer agents
    kernel = create_kernel()
    
    # Create different comedian personas with unique styles
    comedians = [
        ("OneLiners", "You are a comedian who specializes in clever one-liners and wordplay. Your jokes are short, witty, and punchy."),
        ("Observational", "You are an observational comedian who finds humor in everyday situations. You notice absurd details that others miss."),
        ("Satirical", "You are a satirical comedian who uses irony, sarcasm, and exaggeration to critique the topic humorously.")
    ]
    
    print("Defining comedians...")

    agents = []
    for i in range(min(number_of_jokes, len(comedians))):
        name, instructions = comedians[i]
        agent = ChatCompletionAgent(
            kernel=create_kernel(),
            name=name,
            instructions=f"{instructions} Create exactly ONE joke about {topic}. Keep it concise, clean, and suitable for all audiences.",
        )
        agents.append(agent)
    
    # Create the moderator agent
    moderator = ChatCompletionAgent(
        kernel=create_kernel(),
        name="Moderator",
        instructions="You are a comedy show moderator. Your job is to facilitate the joke creation process. Keep the conversation focused on joke creation."
    )
    
    # Create the group chat with all agents
    group_chat = AgentGroupChat(
        agents=[moderator] + agents,
        termination_strategy=DefaultTerminationStrategy(maximum_iterations=len(agents) + 1),
    )
    
    # Start the chat with the topic
    await group_chat.add_chat_message(f"Each comedian should create exactly ONE joke about: {topic}")
    
    # Collect all jokes
    conversation = []
    async for response in group_chat.invoke():
        conversation.append(f"{response.name}: {response.content}")
        # Report progress
        if ctx:
            await ctx.report_progress(len(conversation), (len(agents) + 2) * 1)
    print(conversation)
    return "\n\n".join(conversation)

@mcp.tool()
async def review_jokes(jokes: str, ctx: Context = None) -> str:
    """Have a comedy critic review and rate several jokes."""
    
    if ctx:
        ctx.info("Reviewing jokes...")
    
    # Create a critic agent
    kernel = create_kernel()
    critic = ChatCompletionAgent(
        kernel=kernel,
        name="ComedyCritic",
        instructions="""
        You are a professional comedy critic with decades of experience evaluating humor.
        Review each joke carefully and rate it on a scale of 1-10.
        For each joke, provide:
        1. The rating (1-10)
        2. A brief explanation of the rating
        3. One specific suggestion for improvement
        Be constructive but honest in your criticism.
        """
    )
    
    # Create a chat history with the jokes
    chat_history = ChatHistory()
    chat_history.add_user_message(f"Please review these jokes:\n\n{jokes}")
    
    # Get the critic's response
    response = await critic.get_response(chat_history)
    
    return response.content

@mcp.tool()
async def vote_on_jokes(jokes: str, ctx: Context = None) -> Dict:
    """Have a panel of comedy experts vote on the best jokes and explain their decision."""
    
    if ctx:
        ctx.info("Voting on jokes...")
    
    # Create the voting panel agents
    kernel = create_kernel()
    
    judge1 = ChatCompletionAgent(
        kernel=create_kernel(),
        name="ComedyVeteran",
        instructions="You are a veteran comedian with 30+ years of stand-up experience. You value timing and delivery."
    )
    
    judge2 = ChatCompletionAgent(
        kernel=create_kernel(),
        name="ComedyWriter",
        instructions="You are an award-winning comedy writer for TV shows. You value clever wordplay and subverted expectations."
    )
    
    judge3 = ChatCompletionAgent(
        kernel=create_kernel(),
        name="AudienceMember",
        instructions="You represent the average audience member. You value jokes that are relatable and easy to understand."
    )
    
    moderator = ChatCompletionAgent(
        kernel=create_kernel(),
        name="VotingHost",
        instructions="""
        You are the host of a comedy competition.
        Your job is to:
        1. Have each judge vote for their favorite joke and explain why
        2. Tally the votes and announce the winning joke
        3. Conclude with "Voting complete" when finished
        If there's a tie, make the final decision yourself.
        """
    )
    
    # Create the group chat with all judges
    group_chat = AgentGroupChat(
        agents=[moderator, judge1, judge2, judge3],
        termination_strategy=JokeVotingTerminationStrategy(maximum_iterations=8),
    )
    
    # Start the voting process
    await group_chat.add_chat_message(f"Here are the jokes to vote on:\n\n{jokes}\n\nEach judge should vote for their favorite joke and explain why.")
    
    # Collect the voting conversation
    voting_results = []
    async for response in group_chat.invoke():
        voting_results.append(f"{response.name}: {response.content}")
        # Report progress
        if ctx:
            await ctx.report_progress(len(voting_results), 8)
    
    # Extract the winner
    full_conversation = "\n\n".join(voting_results)
    
    winner_extraction_agent = ChatCompletionAgent(
        kernel=create_kernel(),
        name="ResultsProcessor",
        instructions="Extract the winning joke from the voting results."
    )
    
    extraction_history = ChatHistory()
    extraction_history.add_user_message(f"Extract the winning joke and runner-up from these voting results, and explain why the winner won:\n\n{full_conversation}")
    extraction_response = await winner_extraction_agent.get_response(extraction_history)
    
    # Return the results
    return {
        "voting_conversation": full_conversation,
        "results_summary": extraction_response.content
    }

@mcp.prompt()
def joke_topics_prompt() -> str:
    """Prompt for generating joke topics."""
    return """
    Please suggest 5 specific joke topics that would be funny and engaging.
    For each topic, provide:
    1. The topic name
    2. Why it might be comedically rich
    3. A specific angle or approach for jokes on this topic
    
    Aim for topics that are relatable, not overly controversial, and have potential for clever humor.
    """

@mcp.resource("jokes://sample")
def get_sample_jokes() -> str:
    """Provide some sample jokes as a resource."""
    return """
    # Sample Jokes
    
    ## Technology
    - Why don't programmers like nature? It has too many bugs and no debugging tool.
    - I told my computer I needed a break, and now it won't stop sending me vacation ads.
    
    ## Food
    - I'm on a seafood diet. Every time I see food, I eat it.
    - My doctor told me to watch what I eat, so I ordered a pizza and stared at it for hours.
    
    ## Animals
    - What do you call a parade of rabbits hopping backwards? A receding hare-line.
    - I tried to organize a hide-and-seek competition for dogs, but it was a disaster. All the good boys were found immediately.
    """


async def gen():
    return await generate_jokes("Technology", 3)

# Run the server when this script is executed directly
if __name__ == "__main__":
    mcp.run()
    # Uncomment the line below to run the server
    # asyncio.run(gen())