import argparse
import requests
import json
from ttrpg_assistant.logger import logger

def main():
    parser = argparse.ArgumentParser(description="TTRPG Assistant Command-Line Interface")
    subparsers = parser.add_subparsers(dest="command")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for a rule or item")
    search_parser.add_argument("query", help="The search query")

    # Character generation command
    gen_char_parser = subparsers.add_parser("gen-char", help="Generate a character")
    gen_char_parser.add_argument("rulebook", help="The rulebook to use for character generation")
    gen_char_parser.add_argument("campaign_id", help="The ID of the campaign")

    # NPC generation command
    gen_npc_parser = subparsers.add_parser("gen-npc", help="Generate an NPC")
    gen_npc_parser.add_argument("rulebook", help="The rulebook to use for NPC generation")
    gen_npc_parser.add_argument("campaign_id", help="The ID of the campaign")

    args = parser.parse_args()

    if args.command == "search":
        logger.info(f"Performing search for '{args.query}'")
        response = requests.post("http://localhost:8000/tools/search", json={"query": args.query})
        print(json.dumps(response.json(), indent=2))

    elif args.command == "gen-char":
        logger.info(f"Generating character for rulebook '{args.rulebook}' in campaign '{args.campaign_id}'")
        # This would be a more complex, interactive process
        print("Character generation is not yet implemented in the CLI.")

    elif args.command == "gen-npc":
        logger.info(f"Generating NPC for rulebook '{args.rulebook}' in campaign '{args.campaign_id}'")
        # This would be a more complex, interactive process
        print("NPC generation is not yet implemented in the CLI.")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
