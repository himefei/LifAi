from typing import List, Dict
from .memory import AgentMemory
from .tools import ToolRegistry

class TaskPlanner:
    def __init__(self, memory: AgentMemory, tools: ToolRegistry):
        self.memory = memory
        self.tools = tools
        
    def create_plan(self, task: str) -> List[Dict]:
        # Create step-by-step plan
        pass 