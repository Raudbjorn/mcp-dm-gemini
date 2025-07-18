import argparse
import requests
import json

def search_rulebook(args):
    """Search for rulebook content"""
    payload = {
        "query": args.query,
        "rulebook": args.rulebook,
        "content_type": args.content_type,
        "max_results": args.max_results
    }
    response = requests.post("http://localhost:8000/tools/search_rulebook", json=payload)
    print(json.dumps(response.json(), indent=2))

def manage_campaign(args):
    """Manage campaign data"""
    payload = {
        "action": args.action,
        "campaign_id": args.campaign_id,
        "data_type": args.data_type,
        "data_id": args.data_id,
        "data": json.loads(args.data) if args.data else None
    }
    response = requests.post("http://localhost:8000/tools/manage_campaign", json=payload)
    print(json.dumps(response.json(), indent=2))

def add_rulebook(args):
    """Add a new rulebook"""
    payload = {
        "pdf_path": args.pdf_path,
        "rulebook_name": args.rulebook_name,
        "system": args.system
    }
    response = requests.post("http://localhost:8000/tools/add_rulebook", json=payload)
    print(json.dumps(response.json(), indent=2))

def get_personality(args):
    """Get the personality for a rulebook"""
    payload = {"rulebook_name": args.rulebook_name}
    response = requests.post("http://localhost:8000/tools/get_rulebook_personality", json=payload)
    print(json.dumps(response.json(), indent=2))

def get_char_creation_rules(args):
    """Get the character creation rules for a rulebook"""
    payload = {"rulebook_name": args.rulebook_name}
    response = requests.post("http://localhost:8000/tools/get_character_creation_rules", json=payload)
    print(json.dumps(response.json(), indent=2))

def generate_backstory(args):
    """Generate a backstory for a character"""
    payload = {
        "rulebook_name": args.rulebook_name,
        "character_details": json.loads(args.character_details),
        "player_params": args.player_params
    }
    response = requests.post("http://localhost:8000/tools/generate_backstory", json=payload)
    print(json.dumps(response.json(), indent=2))

def generate_npc(args):
    """Generate an NPC"""
    payload = {
        "rulebook_name": args.rulebook_name,
        "player_level": args.player_level,
        "npc_description": args.npc_description
    }
    response = requests.post("http://localhost:8000/tools/generate_npc", json=payload)
    print(json.dumps(response.json(), indent=2))

def interactive_char_creation(args):
    """Interactive character creation session"""
    print("--- Interactive Character Creation ---")
    
    # Get character creation rules
    print(f"\nFetching character creation rules for '{args.rulebook_name}'...")
    rules_payload = {"rulebook_name": args.rulebook_name}
    rules_response = requests.post("http://localhost:8000/tools/get_character_creation_rules", json=rules_payload)
    if rules_response.status_code == 200:
        print("\n--- Character Creation Rules ---")
        print(rules_response.json()['rules'])
        print("---------------------------------")
    else:
        print("Could not retrieve character creation rules. Please proceed with manual character creation.")

    # Get character details
    print("\nEnter your character's details:")
    char_details = {}
    char_details['name'] = input("Name: ")
    char_details['class'] = input("Class: ")
    char_details['race'] = input("Race: ")
    char_details['level'] = int(input("Level: "))

    # Generate backstory
    if input("\nGenerate a backstory for this character? (y/n): ").lower() == 'y':
        player_params = input("Any specific details you want to include in the backstory? (optional): ")
        backstory_payload = {
            "rulebook_name": args.rulebook_name,
            "character_details": char_details,
            "player_params": player_params
        }
        backstory_response = requests.post("http://localhost:8000/tools/generate_backstory", json=backstory_payload)
        if backstory_response.status_code == 200:
            print("\n--- Generated Backstory ---")
            print(backstory_response.json()['backstory'])
            print("--------------------------")
            char_details['backstory'] = backstory_response.json()['backstory']
        else:
            print("Could not generate a backstory.")

    # Save character
    if input("\nSave this character? (y/n): ").lower() == 'y':
        save_payload = {
            "action": "create",
            "campaign_id": args.campaign_id,
            "data_type": "character",
            "data": char_details
        }
        save_response = requests.post("http://localhost:8000/tools/manage_campaign", json=save_payload)
        if save_response.status_code == 200:
            print("\nCharacter saved successfully!")
        else:
            print("\nError saving character.")
            print(save_response.text)

def interactive_npc_creation(args):
    """Interactive NPC creation session"""
    print("--- Interactive NPC Creation ---")
    
    # Get NPC details
    print("\nEnter the NPC's details:")
    npc_description = input("Description: ")
    player_level = int(input("Average player level: "))

    # Generate NPC
    npc_payload = {
        "rulebook_name": args.rulebook_name,
        "player_level": player_level,
        "npc_description": npc_description
    }
    npc_response = requests.post("http://localhost:8000/tools/generate_npc", json=npc_payload)
    if npc_response.status_code == 200:
        print("\n--- Generated NPC ---")
        print(npc_response.json()['npc'])
        print("--------------------")
        npc_data = {"description": npc_description, "generated_npc": npc_response.json()['npc']}
    else:
        print("Could not generate an NPC.")
        return

    # Save NPC
    if input("\nSave this NPC? (y/n): ").lower() == 'y':
        save_payload = {
            "action": "create",
            "campaign_id": args.campaign_id,
            "data_type": "npc",
            "data": npc_data
        }
        save_response = requests.post("http://localhost:8000/tools/manage_campaign", json=save_payload)
        if save_response.status_code == 200:
            print("\nNPC saved successfully!")
        else:
            print("\nError saving NPC.")
            print(save_response.text)


def main():
    parser = argparse.ArgumentParser(
        description="CLI for the TTRPG Assistant MCP Server",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Search command
    search_parser = subparsers.add_parser(
        "search", 
        help="Search for rulebook content",
        description="Search for rules, spells, monsters, and items in your TTRPG rulebooks.",
        epilog="Example: python cli.py search \"what are the rules for grappling\""
    )
    search_parser.add_argument("query", help="The search query")
    search_parser.add_argument("--rulebook", help="The name of the rulebook to search in")
    search_parser.add_argument("--content_type", help="The type of content to search for (e.g., rule, spell)")
    search_parser.add_argument("--max_results", type=int, default=5, help="The maximum number of results to return")
    search_parser.set_defaults(func=search_rulebook)

    # Campaign command
    campaign_parser = subparsers.add_parser(
        "campaign", 
        help="Manage campaign data",
        description="Store, retrieve, and manage campaign-specific data like characters, NPCs, locations, and plot points.",
        epilog="""Examples:
  python cli.py campaign create "my-campaign" "character" --data '{"name": "Gandalf", "class": "Wizard"}'
  python cli.py campaign export "my-campaign" > campaign_backup.json
  python cli.py campaign import "my-campaign" --data "$(cat campaign_backup.json)"
"""
    )
    campaign_parser.add_argument("action", choices=["create", "read", "update", "delete", "export", "import"], help="The action to perform")
    campaign_parser.add_argument("campaign_id", help="The ID of the campaign")
    campaign_parser.add_argument("data_type", nargs='?', default=None, help="The type of data (e.g., character, npc)")
    campaign_parser.add_argument("--data_id", help="The ID of the data entry")
    campaign_parser.add_argument("--data", help="The data to store (in JSON format)")
    campaign_parser.set_defaults(func=manage_campaign)

    # Add rulebook command
    add_rulebook_parser = subparsers.add_parser(
        "add-rulebook", 
        help="Add a new rulebook",
        description="Process and add a new PDF rulebook to the system.",
        epilog="Example: python cli.py add-rulebook \"path/to/your/rulebook.pdf\" \"My Awesome Rulebook\" \"D&D 5e\""
    )
    add_rulebook_parser.add_argument("pdf_path", help="The path to the PDF file")
    add_rulebook_parser.add_argument("rulebook_name", help="The name of the rulebook")
    add_rulebook_parser.add_argument("system", help="The game system (e.g., D&D 5e)")
    add_rulebook_parser.set_defaults(func=add_rulebook)

    # Get personality command
    get_personality_parser = subparsers.add_parser(
        "get-personality",
        help="Get the personality for a rulebook",
        description="Retrieves the AI personality for a given rulebook.",
        epilog="Example: python cli.py get-personality \"My Awesome Rulebook\""
    )
    get_personality_parser.add_argument("rulebook_name", help="The name of the rulebook")
    get_personality_parser.set_defaults(func=get_personality)

    # Get character creation rules command
    get_char_rules_parser = subparsers.add_parser(
        "get-char-rules",
        help="Get character creation rules",
        description="Retrieves the character creation rules from a rulebook.",
        epilog="Example: python cli.py get-char-rules \"My Awesome Rulebook\""
    )
    get_char_rules_parser.add_argument("rulebook_name", help="The name of the rulebook")
    get_char_rules_parser.set_defaults(func=get_char_creation_rules)

    # Generate backstory command
    gen_backstory_parser = subparsers.add_parser(
        "gen-backstory",
        help="Generate a character backstory",
        description="Generates a backstory for a character based on the rulebook's vibe.",
        epilog="Example: python cli.py gen-backstory \"My Awesome Rulebook\" '{\"name\": \"Aragorn\"}' --player_params \"Loves the color blue\""
    )
    gen_backstory_parser.add_argument("rulebook_name", help="The name of the rulebook")
    gen_backstory_parser.add_argument("character_details", help="The character's details (in JSON format)")
    gen_backstory_parser.add_argument("--player_params", help="Any additional parameters from the player")
    gen_backstory_parser.set_defaults(func=generate_backstory)

    # Generate NPC command
    gen_npc_parser = subparsers.add_parser(
        "gen-npc",
        help="Generate an NPC",
        description="Generates an NPC with stats appropriate for the players' level.",
        epilog="Example: python cli.py gen-npc \"My Awesome Rulebook\" 5 \"A grumpy blacksmith\""
    )
    gen_npc_parser.add_argument("rulebook_name", help="The name of the rulebook")
    gen_npc_parser.add_argument("player_level", type=int, help="The average level of the player characters")
    gen_npc_parser.add_argument("npc_description", help="A brief description of the NPC")
    gen_npc_parser.set_defaults(func=generate_npc)

    # Interactive character creation command
    gen_char_parser = subparsers.add_parser(
        "gen-char",
        help="Interactively create a character",
        description="Starts an interactive session to create a new player character.",
        epilog="Example: python cli.py gen-char \"My Awesome Rulebook\" \"my-campaign\""
    )
    gen_char_parser.add_argument("rulebook_name", help="The name of the rulebook to use for character creation")
    gen_char_parser.add_argument("campaign_id", help="The ID of the campaign to save the character to")
    gen_char_parser.set_defaults(func=interactive_char_creation)

    # Interactive NPC creation command
    gen_npc_interactive_parser = subparsers.add_parser(
        "gen-npc-interactive",
        help="Interactively create an NPC",
        description="Starts an interactive session to create a new non-player character.",
        epilog="Example: python cli.py gen-npc-interactive \"My Awesome Rulebook\" \"my-campaign\""
    )
    gen_npc_interactive_parser.add_argument("rulebook_name", help="The name of the rulebook to use for NPC creation")
    gen_npc_interactive_parser.add_argument("campaign_id", help="The ID of the campaign to save the NPC to")
    gen_npc_interactive_parser.set_defaults(func=interactive_npc_creation)


    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
