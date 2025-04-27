import csv
import random

#used AI to generate code based off function contract and adjustments
class TreeNode:
    def __init__(self, question=None, possible_objects=None):
        self.question = question 
        self.possible_objects = possible_objects 
        self.yes = None
        self.no = None

def load_data(csv_file):
    """Loads data from CSV into objects dictionary and questions list."""
    with open(csv_file, newline='') as file:
        reader = csv.reader(file)
        data = list(reader)
    
    if not data:
        return {}, []
    
    questions = data[0][1:]
    objects = {}
    
    for row in data[1:]:
        if not row:  # Skip empty rows
            continue
        obj_name = row[0]
        
        # Pad row with zeros if too short
        expected_length = len(questions) + 1
        padded_row = row + ['0'] * (expected_length - len(row))
        
        characteristics = {
            questions[i]: int(padded_row[i+1]) 
            for i in range(len(questions))
        }
        objects[obj_name] = characteristics
    
    return objects, questions

def best_question(objects, questions):
    """Finds the question that best splits the remaining objects."""
    best_q = None
    best_score = -1  # Higher = better split
    
    for q in questions:
        # Count how many remaining objects have this trait
        yes_count = sum(1 for obj in objects.values() if obj.get(q, 0) == 1)
        no_count = len(objects) - yes_count
        
        # Skip useless questions (all yes or all no)
        if yes_count == 0 or no_count == 0:
            continue
        
        # Score based on how well it splits AND how many objects it distinguishes
        score = min(yes_count, no_count)  # Favors balanced splits
        if score > best_score:
            best_score = score
            best_q = q
    
    return best_q  # Returns None if no useful questions left

def build_tree(objects, questions):
    """Builds decision tree with optimal splits."""
    if not objects:
        return None
        
    if len(objects) == 1 or not questions:
        return TreeNode(possible_objects=list(objects.keys()))
    
    q = best_question(objects, questions)
    if not q:
        return TreeNode(possible_objects=list(objects.keys()))
    
    remaining_questions = [qst for qst in questions if qst != q]
    
    yes_objects = {name: chars for name, chars in objects.items() if chars.get(q, 0) == 1}
    no_objects = {name: chars for name, chars in objects.items() if chars.get(q, 0) == 0}
    
    node = TreeNode(question=q)
    node.yes = build_tree(yes_objects, remaining_questions)
    node.no = build_tree(no_objects, remaining_questions)
    
    return node

def traverse_tree(node):
    """Traverses tree asking questions, shows remaining objects, and handles dead-ends."""
    guess_count = 0
    eliminated = []
    
    def get_all_possible_objects(current_node):
        """Recursively gets all possible objects from this node down."""
        if current_node is None:
            return set()
        if current_node.possible_objects:
            return set(current_node.possible_objects)
        return get_all_possible_objects(current_node.yes) | get_all_possible_objects(current_node.no)
    
    current_node = node
    
    while True:
        # Get current possible objects
        possible_objects = get_all_possible_objects(current_node)
        remaining_objects = [obj for obj in possible_objects if obj not in eliminated]
        
        #print(f"Possible objects remaining: {', '.join(remaining_objects) if remaining_objects else 'None'}")
        
        # Handle dead-end case (no possible objects match)
        if not remaining_objects:
            print("I'm out of ideas! Let me try guessing from all objects...")
            all_objects = get_all_possible_objects(node)
            backup_guess_list = [obj for obj in all_objects if obj not in eliminated]
            random.shuffle(backup_guess_list)
            
            for guess in backup_guess_list:
                guess_count += 1
                answer = input(f"Is your object a {guess}? (yes/no) ").strip().lower()
                while answer not in ["yes", "no"]:
                    answer = input("Please answer 'yes' or 'no': ").strip().lower()
                if answer == "yes":
                    return guess, guess_count, eliminated
                eliminated.append(guess)
            return None, guess_count, eliminated
        
        # Normal leaf node (guessing)
        if current_node.possible_objects:
            random.shuffle(current_node.possible_objects)
            for guess in current_node.possible_objects:
                if guess in eliminated:
                    continue
                guess_count += 1
                answer = input(f"Is your object a {guess}? (yes/no) ").strip().lower()
                while answer not in ["yes", "no"]:
                    answer = input("Please answer 'yes' or 'no': ").strip().lower()
                if answer == "yes":
                    return guess, guess_count, eliminated
                eliminated.append(guess)
            return None, guess_count, eliminated
        
        # Question node
        guess_count += 1
        answer = input(f"{current_node.question}? (yes/no) ").strip().lower()
        while answer not in ["yes", "no"]:
            answer = input("Please answer 'yes' or 'no': ").strip().lower()
        
        current_node = current_node.yes if answer == "yes" else current_node.no

def update_data(csv_file, correct_obj, new_chars, eliminated_objs):
    """Updates CSV with new characteristics."""
    objects, questions = load_data(csv_file)
    
    # Add new characteristics if needed
    for new_char in new_chars:
        if new_char not in questions:
            questions.append(new_char)
            # Initialize all objects to 0 first
            for obj in objects.values():
                obj[new_char] = 0
    
    # Set correct object to 1 for each new characteristic (if exists)
    if correct_obj in objects:
        for new_char in new_chars:
            objects[correct_obj][new_char] = 1
    else:
        # Add new object if it doesn't exist
        objects[correct_obj] = {q: 0 for q in questions}
        for new_char in new_chars:
            objects[correct_obj][new_char] = 1
    
    # Save updated data
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Object"] + questions)
        for obj, chars in objects.items():
            writer.writerow([obj] + [chars.get(q, 0) for q in questions])

def get_hints(correct_obj):
    """Asks user if they want to provide hints and collects them."""
    hints = []
    hint_choice = input("Would you like to give me a hint? (yes/no) ").strip().lower()
    while hint_choice not in ["yes", "no"]:
        hint_choice = input("Please answer 'yes' or 'no': ").strip().lower()
    
    if hint_choice == "yes":
        num_hints = input("How many hints would you like to give? (1/2) ").strip()
        while num_hints not in ["1", "2"]:
            num_hints = input("Please enter 1 or 2: ").strip()
        
        for i in range(int(num_hints)):
            hint = input(f"Enter hint #{i+1} (a characteristic of {correct_obj}): ").strip()
            hints.append(hint)
    
    return hints

def play_round(tree, csv_file):
    """Manages one game round."""
    result, guesses, eliminated = traverse_tree(tree)
    
    if result:
        print(f"Good game! I won in {guesses} guesses.")
        return False
    else:
        print("Congratulations, you stumped me!")
        correct_obj = input("What was your object? ").strip()
        
        # Get hints from user
        hints = get_hints(correct_obj)
        
        if hints:
            update_data(csv_file, correct_obj, hints, eliminated)
            print(f"Thanks for the hints! I'll remember that {correct_obj} has these characteristics:")
            for hint in hints:
                print(f"- {hint}")
        else:
            # If no hints, just continue without adding any characteristics
            print("Okay, I'll try to do better next time!")
        
        return bool(hints)  # Only rebuild tree if we got new hints

def main():
    csv_file = "test_data.csv"
    need_rebuild = True
    tree = None
    
    print("Welcome to 20 Questions!")
    while True:
        if need_rebuild:
            objects, questions = load_data(csv_file)
            tree = build_tree(objects, questions)
            need_rebuild = False
        
        data_updated = play_round(tree, csv_file)
        if data_updated:
            need_rebuild = True
        
        replay = input("\nWould you like to play again? (yes/no) ").strip().lower()
        while replay not in ["yes", "no"]:
            replay = input("Please answer 'yes' or 'no': ").strip().lower()
        
        if replay != "yes":
            print("\nThanks for playing! Goodbye!")
            break

if __name__ == "__main__":
    main()