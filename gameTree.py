class GameTreeNode:
    def __init__(self, action, reward=0, node_type="system"):
        self.action = action
        self.reward = reward
        self.node_type = node_type  # "system" or "user"
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)

    def print_tree(self, level=0):
        prefix = "[USER]" if self.node_type == "user" else "[SYS]"
        print("  " * level + f"{prefix} {self.action} (Reward: {self.reward:.2f})")
        for child in self.children:
            child.print_tree(level + 1)


class DBTGameTree:
    def __init__(self, actions):
        self.actions = actions
        self.root = GameTreeNode("Start", node_type="system")
        self.current_node = self.root

    def add_user_utterance(self, utterance):
        """Insert user utterance node before expanding DBT actions."""
        user_node = GameTreeNode(
            action=utterance,
            reward=0,
            node_type="user"
        )
        self.current_node.add_child(user_node)
        self.current_node = user_node

    def expand_tree(self, reward_data):
        """Expand DBT actions from the user utterance node."""
        self.current_node.children = []  # overwrite old expansions
        for action, reward in reward_data.items():
            self.current_node.add_child(
                GameTreeNode(action, reward, node_type="system")
            )

    def select_best_action(self):
        """Select DBT action with highest expected utility."""
        if not self.current_node.children:
            return None, 0

        best_action_node = max(
            self.current_node.children,
            key=lambda x: x.reward
        )

        self.current_node = best_action_node
        return best_action_node.action, best_action_node.reward

    def print_tree(self):
        self.root.print_tree()


def data_extraction(data_dict):
    utility_scores = {}
    for key, values in list(data_dict['predictions'].items())[:-1]:
        utility_score = sum(
            float(state["probability"]) * float(state["reward"])
            for state in values["possible_states"]
        )
        utility_scores[key] = utility_score

    print("All Utility Scores:", utility_scores)
    return utility_scores


def data_extraction_behavior(data_dict):
    utility_scores = {}

    for key, values in list(data_dict['predictions'].items())[:-1]:
        utility_score = sum(
            float(state["probability"]) *
            sum(float(behavior["reward"]) for behavior in state["behaviors"])
            for state in values["possible_states"]
        )

        utility_scores[key] = utility_score

    print("All Utility Scores:", utility_scores)
    return utility_scores

actions = [
    "Mindfulness",
    "Distress Tolerance",
    "Interpersonal Effectiveness",
    "Emotion Regulation"
]

game_tree = DBTGameTree(actions)


def dataImport(user_utterance, reward_data):
    # Add user utterance first
    game_tree.add_user_utterance(user_utterance)

    # Extract rewards
    extracted_rewards = data_extraction_behavior(reward_data)

    # Expand DBT action tree
    game_tree.expand_tree(extracted_rewards)

    # Select best DBT action
    best_action, reward = game_tree.select_best_action()
    print(f"Best Action = {best_action}, Reward = {reward:.2f}")

    # Print full tree
    game_tree.print_tree()

    return best_action
