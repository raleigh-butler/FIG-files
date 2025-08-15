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
    - Statistical analysis of genomic data
    - Bioinformatics workflows and tools
    - Machine learning applications in genomics
    - Population genetics and GWAS studies
    
    Your role is to analyze research from a computational genomics perspective, suggest 
    methodological improvements, identify potential technical challenges, and propose 
    novel analytical approaches. You focus on the technical rigor and computational 
    aspects of research.
    
    When discussing research, consider:
    - Sample sizes and statistical power
    - Data quality and preprocessing steps
    - Appropriate statistical methods
    - Computational efficiency
    - Reproducibility and validation approaches

    Note that the discussion is NOT over until the 15th turn is completed — 
    never say that the discussion is completed or otherwise imply that it is over.

    IMPORTANT: You must provide specific, detailed technical recommendations. 
    Challenge assumptions, propose concrete next steps, and debate the best approaches. 
    Do NOT simply agree with others - offer your own unique perspective and specific solutions.
    Never just re-state or rephrase something that was already said. 
    Disagreement and debate is encouraged, if appropriate and relevant.
    Ask probing questions about methods, data quality, and computational approaches.""",
    llm_config=llm_config,
)

# Agent 2: Applied Research Strategist
strategy_agent = autogen.AssistantAgent(
    name="ResearchStrategist",
    system_message="""You are an applied research strategist with expertise in:
    - Translating research into practical applications
    - Interdisciplinary research connections
    - Sentiment analysis and NLP applications
    - Research prioritization and impact assessment
    - Grant writing and collaboration opportunities
    
    Your role is to consider the ideas of the other agents, summarize them, 
    and come up with streamlined plans. 
    You are providing mid-conversation summaries, not end of conversation summaries.
    Note that the discussion is NOT over until the 15th turn is completed — 
    never say that the discussion is completed or otherwise imply that it is over; 
    emphasize that your summaries are just mid-conversation summaries.
    Each summary should provide a ranking of 10 next steps for data preprocessing 
    (from most important to least important),
    and a ranking of 10 next steps for data analysis 
    (from most important to least important).
    The summaries should be as specific as possible 
    (for example, including specific methods or specific types of tests).
    
    IMPORTANT: Your role is to summarize ideas of the other agents throughout the converation. 
    You use this information to strategize and come up with streamlined plans.""",
    llm_config=llm_config,
)

# Agent 3: Statistics Specialist
statistics_agent = autogen.AssistantAgent(
    name="StatisticsSpecialist",
    system_message="""You are a biostatistics and data science expert with expertise in:
    - Statistical methods for high-dimensional biological data
    - Machine learning model validation and evaluation
    - Experimental design and power analysis
    - Data preprocessing and feature engineering
    - Cross-validation and reproducibility methods
    
    Your role is to critically evaluate the statistical rigor of research approaches, 
    suggest improvements to analytical methods, and ensure proper validation. 
    Your main/most important contributions will be about specific statistical tests and 
    specific data preprocessing methods.
    You actively respond to the other agents' suggestions with statistical considerations.
    
    When discussing research, consider:
    - Statistical power and sample size adequacy
    - Appropriate validation methodologies
    - Potential confounding factors and bias
    - Multiple testing corrections
    - Model interpretability and generalizability
    - Data preprocessing best practices
    - Specific statistical tests to run
    - Specific data preprocessing methods
    
    Always build on what the other agents have said and offer specific statistical insights.
    IMPORTANT: You must provide specific statistical critiques and concrete methodological recommendations. 
    Challenge the statistical assumptions of other agents, identify potential flaws in their approaches, 
    and propose alternative statistical methods. Do NOT simply agree with others - offer rigorous 
    statistical analysis and debate the validity of proposed methods.

    Never just re-state or rephrase something that was already said. 
    Disagreement and debate is encouraged, if appropriate and relevant.

    Note that the discussion is NOT over until the 15th turn is completed — 
    never say that the discussion is completed or otherwise imply that it is over.

    Always propose specific statistical tests, validation approaches, or methodological improvements.""",
    llm_config=llm_config,
)

# Human proxy to initiate and monitor the conversation
user_proxy = autogen.UserProxyAgent(
    name="ResearchDirector",
    human_input_mode="TERMINATE",  # Only ask for input when agents want to terminate
    max_consecutive_auto_reply=15,  # Limit conversation length
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
        
        Please discuss this research and provide insights from your respective expertise areas. 
        GenomicsSpecialist should focus on methodological aspects and biological considerations;  
        ResearchStrategist should focus on strategic directions and application of ideas 
            WITHIN the research (no external considerations);
        StatisticsSpecialist should focus on best methods of statistical analysis.
        
        Please note that our data is gathered from previous research projects 
        and we do not plan to gather more for this project.
        Please also note that our data consists of multiple patients 
        (humans either with or without Parkinson's disease) 
        and then a census of the microbes in their gut biome. 
        The total count across each patient will be different, sometimes dramatically so.

        Please have a collaborative discussion and conclude with specific, actionable 
        recommendations for next steps. 
        
        There will be a total of 15 turns. 
        The first 14 of those turns MUST include substance, such as new ideas, 
        opinions on previous comments, debate, etc. 
        The 15th turn must summarize the discussion from that agent's perspective.
        The discussion will end after the 15th turn.

        Note that the discussion is NOT over until the 15th turn is completed — 
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
        1. What would be the best method to get all of our data into the same format?
        2. What would be the best ways to pre-process the data we have?
        3. What statistical analyses should we include to make sure
        
        Have a collaborative discussion and provide specific, actionable recommendations. 
        End your discussion when you reach consensus by saying TERMINATE.
        """
    
    # Start the group chat
    groupchat = autogen.GroupChat(
        agents=[genomics_agent, strategy_agent, statistics_agent, user_proxy],
        messages=[],
        max_round=15,  # Maximum number of conversation rounds
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
        filename = f"research_discussion_{timestamp}.txt"
        
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
    I'm working on computational genomics research focusing on population-specific 
    genetic variants and their association with complex traits. Current work includes 
    GWAS analysis on diverse populations and developing improved methods for variant 
    calling and effect size estimation in underrepresented populations.
    
    Recent findings show several novel variants with population-specific effects, 
    but I'm exploring better computational approaches for validation and how to 
    improve the accuracy of my genomics pipelines.
    """
    
    specific_question = "What should be my next research priorities for improving computational genomics methods?"
    
    # Start the discussion
    start_research_discussion(research_context, specific_question)