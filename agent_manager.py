import importlib
import os
import time
class AgentManager:
    def __init__(self, agent_names):
        self.agents = {name: self.hot_load_agent(name) for name in agent_names}

    def hot_load_agent(self, agent_name):
        return hot_load_agent(agent_name)

    def reload_agents(self):
        for agent_name in self.agents.keys():
            self.agents[agent_name] = self.hot_load_agent(agent_name)

    def get_agent(self, agent_name):
        return self.agents.get(agent_name)

    def watch_agent_files(self, agent_names):
        last_modified = {name: os.path.getmtime(f'agents/{name}.py') for name in agent_names}

        while True:
            time.sleep(5)  # Check every 5 seconds
            for name in agent_names:
                current_mtime = os.path.getmtime(f'agents/{name}.py')
                if current_mtime != last_modified[name]:
                    print(f"Reloading {name} agent...")
                    last_modified[name] = current_mtime
                    self.reload_agents()


def hot_load_agent(agent_name):
    module = importlib.import_module(f'agents.{agent_name}')
    # If your agent class is named same as the module
    agent_class = getattr(module, agent_name.capitalize())
    return agent_class()  # Return a new instance of the agen