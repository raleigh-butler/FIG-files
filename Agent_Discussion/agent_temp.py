import openai
from typing import List, Dict, Optional
import json

class Agent:
    def __init__(self, name: str, role: str, system_prompt: str, client: openai.OpenAI):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.client = client
    
    def respond(self, conversation_history: List[Dict], temperature: float = 0.7) -> str:
        """Generate response based on conversation history and agent's role"""
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(conversation_history)
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=temperature,
            max_tokens=1000
        )
        
        return response.choices[0].message.content

class MultiAgentSystem:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.conversation_history = []
        
        # Initialize agents
        self.agents = {
            "genomics_specialist": Agent(
                name="Dr. Gene",
                role="Genomics Specialist",
                system_prompt="""You are a genomics specialist with expertise in molecular biology, 
                genetics, and genomic data analysis. Focus on biological interpretation, gene functions, 
                pathways, and clinical relevance. Keep responses scientifically accurate but accessible. 
                Highlight key genomic insights and their biological significance.""",
                client=self.client
            ),
            
            "ml_specialist": Agent(
                name="Dr. Data",
                role="ML Specialist", 
                system_prompt="""You are a machine learning specialist focused on computational approaches 
                to genomic data. Discuss ML models, data preprocessing, feature engineering, and 
                computational challenges. Suggest appropriate algorithms and evaluation metrics. 
                Connect ML concepts to genomic analysis applications.""",
                client=self.client
            ),
            
            "scribe": Agent(
                name="Scribe",
                role="Summarizer",
                system_prompt="""You are a technical scribe who synthesizes complex discussions. 
                Create clear, structured summaries that capture key insights from genomics and ML 
                perspectives. Organize information into: Key Findings, Technical Recommendations, 
                and Next Steps. Make technical content accessible while preserving important details.""",
                client=self.client
            )
        }
    
    def add_user_input(self, user_input: str):
        """Add user context to conversation"""
        self.conversation_history.append({
            "role": "user", 
            "content": f"User Context: {user_input}"
        })
    
    def run_analysis(self, user_input: str) -> Dict[str, str]:
        """Run the full agent workflow"""
        # Clear previous conversation
        self.conversation_history = []
        
        # Add user input
        self.add_user_input(user_input)
        
        # Genomics specialist responds first
        genomics_response = self.agents["genomics_specialist"].respond(self.conversation_history)
        self.conversation_history.append({
            "role": "assistant",
            "content": f"Genomics Specialist: {genomics_response}"
        })
        
        # ML specialist responds
        ml_response = self.agents["ml_specialist"].respond(self.conversation_history)
        self.conversation_history.append({
            "role": "assistant", 
            "content": f"ML Specialist: {ml_response}"
        })
        
        # Scribe summarizes
        summary = self.agents["scribe"].respond(self.conversation_history)
        
        return {
            "user_input": user_input,
            "genomics_analysis": genomics_response,
            "ml_analysis": ml_response,
            "summary": summary
        }
    
    def get_conversation_history(self) -> List[Dict]:
        """Return full conversation history"""
        return self.conversation_history

# Usage example
def main():
    # Initialize system
    api_key = "your-openai-api-key-here"
    system = MultiAgentSystem(api_key)
    
    # Example analysis
    user_query = """
    I have RNA-seq data from cancer patients showing differential expression 
    in the TP53 pathway. I want to build a predictive model for treatment response 
    but I'm concerned about batch effects and small sample size (n=150).
    """
    
    results = system.run_analysis(user_query)
    
    print("=== GENOMICS ANALYSIS ===")
    print(results["genomics_analysis"])
    print("\n=== ML ANALYSIS ===")
    print(results["ml_analysis"])
    print("\n=== SUMMARY ===")
    print(results["summary"])

if __name__ == "__main__":
    main()