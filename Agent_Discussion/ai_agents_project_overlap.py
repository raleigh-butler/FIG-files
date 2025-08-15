import autogen
from typing import Dict, Any
import os
import datetime

# Configuration for Claude API
config_list = [
    {
        "model": "gpt-4o",  # or "gpt-4o-mini" for cheaper option
        "api_key": os.getenv("OPENAI_API_KEY"),
    }
]

# LLM configuration
llm_config = {
    "config_list": config_list,
    "temperature": 0.7,
    "timeout": 120,
}

# Agent 1: Computational Genomics Specialist
genomics_agent = autogen.AssistantAgent(
    name="GenomicsSpecialist",
    system_message="""You are a computational genomics researcher with expertise in:
    - Knowledge of Parkinson's disease and contributing factors
    - Alpha-synuclein and its effect on Parkinson's disease
    - Chromosomal clustering
    - Bioinformatics workflows and tools
    - Machine learning applications in genomics
    - Population genetics and GWAS studies
    
    Your role is to analyze the current research status from a computational genomics perspective and do the following:
    - Discuss any overlap between projects 1 & 2
    - Suggest ways the researchers could overlap or tie together projects 1 & 2
    - Discuss specific ways to correlate the chromosomal clustering data from project 2 with the microbial data of project 1
    - Discuss through the lens of computational genomics, Parkinson's disease knowledge, 
    gut health, and chromosomal clustering
    
    When discussing research, consider:
    - Grounded overlap between the brain-gut link and chromosomal clustering
    - Chromosomal clustering and predictability of subsystems
    - The researchers are not gathering new data — they are only analyzing existing data

    Note that the discussion is NOT over until the 10th turn is completed — 
    never say that the discussion is completed or otherwise imply that it is over.

    IMPORTANT: You must provide specific, detailed methodological recommendations. 
    Challenge assumptions, propose concrete next steps, and debate the best approaches. 
    Do NOT simply agree with others - offer your own unique perspective and specific solutions.
    Never just re-state or rephrase something that was already said. 
    Disagreement and debate is encouraged, if appropriate and relevant.
    Ask probing questions about methods and potential approaches.""",
    llm_config=llm_config,
)

# Agent 2: ML Strategist
ml_agent = autogen.AssistantAgent(
    name="MLStrategist",
    system_message="""You are an applied research strategist with expertise in:
    - Computational genomics
    - Machine learning
    - Project-planning and research strategy
    - Research prioritization 

    Your role is to analyze the current research status from a research strategy 
    and planning perspective and do the following:
    - Discuss any overlap between projects 1 & 2
    - Suggest grounded, practical ways the researchers could overlap or tie together projects 1 & 2
    - Discuss specific ways to correlate the chromosomal clustering data from project 2 with the microbial data of project 1
    - Discuss through the lens of computational genomics, Parkinson's disease knowledge, 
    gut health, and chromosomal clustering
    - Focuse on grounded ways to tie the two projects together or overlap the results.
    
    When discussing research, consider:
    - Grounded overlap between the brain-gut link and chromosomal clustering
    - Chromosomal clustering and predictability of subsystems
    - The researchers are not gathering new data — they are only analyzing existing data

    Note that the discussion is NOT over until the 10th turn is completed — 
    never say that the discussion is completed or otherwise imply that it is over.

    IMPORTANT: You must provide specific, detailed methodological recommendations 
    for tying the two projects togethr. 
    Challenge assumptions, propose concrete next steps, and debate the best approaches. 
    Do NOT simply agree with others - offer your own unique perspective and specific solutions.
    Never just re-state or rephrase something that was already said. 
    Disagreement and debate is encouraged, if appropriate and relevant.
    Ask probing questions about methods and potential approaches.""",
    llm_config=llm_config,
) 


# Agent 3: Scribe / Summarizer
scribe_agent = autogen.AssistantAgent(
    name="ScribeSpecialist",
    system_message="""You are the scribe and summarizer for the conversation.

    Your role is to consider the ideas of the other agents, summarize them, 
    and come up with streamlined plans for next steps. 
    
    You are providing mid-conversation summaries, not end of conversation summaries.
    Note that the discussion is NOT over until the 10th turn is completed — 
    never say that the discussion is completed or otherwise imply that it is over; 
    emphasize that your summaries are just mid-conversation summaries.
    Each summary should provide 3 potential plans forward with concise details for each.
    
    IMPORTANT: Your role is to summarize ideas of the other agents throughout the converation. 
    You use this information to strategize and come up with streamlined plans for next steps.""",
    llm_config=llm_config,
)

# Human proxy to initiate and monitor the conversation
user_proxy = autogen.UserProxyAgent(
    name="ResearchDirector",
    human_input_mode="TERMINATE",  # Only ask for input when agents want to terminate
    max_consecutive_auto_reply=10,  # Limit conversation length
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config=False,  # Disable code execution for safety
)

def start_research_discussion(research_context: str, specific_question: str = None, save_conversation: bool = True):
    """
    Start an autonomous discussion between the two research agents
    
    Args:
        research_context: Description of your current research
        specific_question: Optional specific question to focus the discussion
        save_conversation: Whether to save the conversation to a file
    """
    
    if specific_question:
        initial_message = f"""
        Research Context: {research_context}
        
        Specific Focus: {specific_question}
        
        Research Context:
        My research group has 2 ongoing projects:
        Project 1: The project that examines the link between Parkinson’s and gut health / gut microbiome
        Project 2: The project that examines genetic clustering, especially to predict which subsystems genes belong to

        I would like to find a way to tie those two projects together or have them / their results overlap in some way — a way to connect the two.


        Here’s my current status / thoughts about potential ways to proceed:
        - I have new data that focuses on chromosomal clustering - data we want to use to help predict what larger subsystems those genes belong to.

        - I want to start working today by building a trio of agents to discuss how the two project or the project results could be tied together in some way.

        - Perhaps there is a potential overlap in the results of the chromosomal clustering —> predicting Parkinson’s-positive or negative disease status. I think alpha-synuclein could potentially be relevant to examining this overlap.
        Note: Alpha-synuclein is a protein that’s central to Parkinson’s disease pathology. In Parkinson’s disease, it misfiles and clumps together into toxic aggregates called Lewy bodies.

        - Potential relevance of alpha-synuclein (SNCA):
            - The gene(s) that codes for SNCA could be part of chromosomal clusters we’re analyzing
            - Question: how would we know if it is part of the chromosomal clusters?
            - Some gut bacteria produce compounds that might influence alpha-synuclein folding
            - Certain bacterial metabolites may either protect against or promote protein misfolding

        - Once we narrow down what this potential overlap could be (overlap between projects, that is), we can craft a workflow to better explore it. 


        Please have a collaborative discussion and conclude with specific, actionable 
        recommendations for next steps. 
        
        There will be a total of 10 turns. 
        The first 9 of those turns MUST include substance, such as new ideas, 
        opinions on previous comments, debate, etc. 
        The 10th turn must summarize the discussion from that agent's perspective.
        The discussion will end after the 10th turn.

        Note that the discussion is NOT over until the 10th turn is completed — 
        never say that the discussion is completed or otherwise imply that it is over.

        Do NOT discuss any considerations outside of the immediate 
        data pre-processing and statistical analysis. 
        NO external considerations should be mentioned by ANY of the agents.
        Emphasis: We will not be gathering new data and will be using data that already exists.
        """
    else:
        initial_message = f"""
        Research Context: {research_context}
        
        Please analyze this research from your respective perspectives and discuss:
        1. What would be the best method to link the two projects in some way?
        2. For each method discussed, what are step-by-step actions to take to move forward?
        3. How could we explore linking these projects via examiniation of alpha-synuclein?
        4. If we find chromosomal clusters related to alpha-synuclein, 
        how could we tie this back to project 1 (which focuses on the gut-brain link in Parkinson's) - 
        how could we correlated it with that microbial data?

        
        Have a collaborative discussion and provide specific, actionable recommendations. 
        """
    
    # Start the group chat
    groupchat = autogen.GroupChat(
        agents=[genomics_agent, ml_agent, scribe_agent, user_proxy],
        messages=[],
        max_round=10,  # Maximum number of conversation rounds
        speaker_selection_method="round_robin"  
    )
    
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)
    
    # Initiate the conversation
    chat_result = user_proxy.initiate_chat(
        manager,
        message=initial_message
    )
    
    # Save conversation if requested
    if save_conversation:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"overlap_research_discussion_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=== RESEARCH AGENT DISCUSSION ===\n")
            f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Research Context: {research_context}\n")
            if specific_question:
                f.write(f"Specific Question: {specific_question}\n")
            f.write("\n" + "="*50 + "\n\n")
            
            # Extract and save the conversation
            for message in groupchat.messages:
                speaker = message.get('name', 'Unknown')
                content = message.get('content', '')
                f.write(f"{speaker}:\n{content}\n\n" + "-"*30 + "\n\n")
        
        print(f"\nConversation saved to: {filename}")
    
    return chat_result

# Example usage
if __name__ == "__main__":
    # Example research context - replace with your actual research
    research_context = """
    My research group has 2 ongoing projects:
    Project 1: The project that examines the link between Parkinson’s and gut health / gut microbiome
    Project 2: The project that examines chromosomal clustering, especially to predict which subsystems genes belong to

    I would like to find a way to tie those two projects together or have them / their results overlap in some way — a way to connect the two.
    Please discuss how we could explore linking these projects via examiniation of alpha-synuclein.
    """
    
    specific_question = "1. What would be the best method to link the two projects in some way? 2. For each method discussed, what are step-by-step actions to take to move forward? 3. How could we explore linking these projects via examiniation of alpha-synuclein? 4. If we find chromosomal clusters related to alpha-synuclein, how could we tie this back to project 1 (which focuses on the gut-brain link in Parkinson's) - how could we correlate it with that bicrobial data?"
    
    # Start the discussion
    start_research_discussion(research_context, specific_question)