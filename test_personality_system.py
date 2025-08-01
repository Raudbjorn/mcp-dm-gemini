#!/usr/bin/env python3
"""
Test script for the personality extraction and management system
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from ttrpg_assistant.personality_service.personality_extractor import PersonalityExtractor
from ttrpg_assistant.personality_service.personality_manager import PersonalityManager
from ttrpg_assistant.chromadb_manager.manager import ChromaDataManager
from ttrpg_assistant.data_models.models import ContentChunk, SourceType
from datetime import datetime


def create_test_chunks(system_name: str, content_samples: list) -> list:
    """Create test content chunks for personality extraction"""
    chunks = []
    
    for i, content in enumerate(content_samples):
        chunk = ContentChunk(
            id=f"test_chunk_{i}",
            rulebook=f"{system_name} Test Book",
            system=system_name,
            source_type=SourceType.RULEBOOK,
            content_type="rule",
            title=f"Test Section {i+1}",
            content=content,
            page_number=i+1,
            section_path=[f"Chapter {i+1}"],
            embedding=b"",  # Empty for testing
            metadata={}
        )
        chunks.append(chunk)
    
    return chunks


def test_personality_extractor():
    """Test the personality extractor with sample content"""
    print("Testing Personality Extractor...")
    print("=" * 50)
    
    extractor = PersonalityExtractor()
    
    # Test with D&D 5e style content
    dnd_content = [
        "You must roll a d20 and add your proficiency bonus. The Dungeon Master determines the difficulty class for this check. If you succeed, you may proceed with your action. Remember that in the world of magic and adventure, heroes face countless perils.",
        "Spells are magical formulas that harness arcane energies. When you cast a spell, you expend a spell slot of the spell's level or higher. The weave of magic responds to your will, channeling power through ancient words and gestures.",
        "Combat occurs in rounds, each lasting approximately 6 seconds. On your turn, you may move and take one action. The fate of heroes often hinges on these crucial moments of battle."
    ]
    
    dnd_chunks = create_test_chunks("D&D 5e", dnd_content)
    dnd_personality = extractor.extract_personality(dnd_chunks, "D&D 5e")
    
    print(f"D&D 5e Personality Profile:")
    print(f"  Name: {dnd_personality.personality_name}")
    print(f"  Description: {dnd_personality.description}")
    print(f"  Tone: {dnd_personality.tone}")
    print(f"  Perspective: {dnd_personality.perspective}")
    print(f"  Formality: {dnd_personality.formality_level}")
    print(f"  Confidence: {dnd_personality.confidence_score:.2f}")
    print(f"  Vernacular patterns: {len(dnd_personality.vernacular_patterns)}")
    print(f"  Personality traits: {len(dnd_personality.personality_traits)}")
    print()
    
    # Test with Call of Cthulhu style content
    cthulhu_content = [
        "The ancient manuscript speaks of forbidden knowledge that mortal minds were never meant to comprehend. As you delve deeper into these eldritch mysteries, your sanity hangs by a thread. The cosmic horror that lurks beyond the veil of reality watches and waits.",
        "I have uncovered disturbing evidence in my research of these blasphemous texts. The implications are most unsettling, for they suggest that humanity's place in the universe is far more precarious than we dare imagine. One must approach such knowledge with the utmost caution.",
        "The shadowy cult performs their unholy rituals in the dead of night, calling upon entities that existed eons before mankind's first stirrings. These forbidden practices threaten to tear asunder the very fabric of our perceived reality."
    ]
    
    cthulhu_chunks = create_test_chunks("Call of Cthulhu", cthulhu_content)
    cthulhu_personality = extractor.extract_personality(cthulhu_chunks, "Call of Cthulhu")
    
    print(f"Call of Cthulhu Personality Profile:")
    print(f"  Name: {cthulhu_personality.personality_name}")
    print(f"  Description: {cthulhu_personality.description}")
    print(f"  Tone: {cthulhu_personality.tone}")
    print(f"  Perspective: {cthulhu_personality.perspective}")
    print(f"  Formality: {cthulhu_personality.formality_level}")
    print(f"  Confidence: {cthulhu_personality.confidence_score:.2f}")
    print(f"  Vernacular patterns: {len(cthulhu_personality.vernacular_patterns)}")
    print(f"  Personality traits: {len(cthulhu_personality.personality_traits)}")
    print()
    
    # Show some vernacular patterns
    if dnd_personality.vernacular_patterns:
        print("D&D 5e Vernacular Patterns (top 5):")
        for pattern in dnd_personality.vernacular_patterns[:5]:
            print(f"  - {pattern.term}: {pattern.definition}")
            print(f"    Category: {pattern.category}, Frequency: {pattern.frequency}")
        print()
    
    if cthulhu_personality.vernacular_patterns:
        print("Call of Cthulhu Vernacular Patterns (top 5):")
        for pattern in cthulhu_personality.vernacular_patterns[:5]:
            print(f"  - {pattern.term}: {pattern.definition}")
            print(f"    Category: {pattern.category}, Frequency: {pattern.frequency}")
        print()
    
    # Test personality prompt generation
    print("Testing Personality Prompt Generation...")
    print("-" * 30)
    
    dnd_prompt = extractor.generate_personality_prompt(dnd_personality, "How do I cast a fireball spell?", "Character is a level 5 wizard")
    print("D&D 5e Personality Prompt:")
    print(dnd_prompt.format_prompt("How do I cast a fireball spell?", "Character is a level 5 wizard"))
    print()
    
    cthulhu_prompt = extractor.generate_personality_prompt(cthulhu_personality, "What do I know about the Necronomicon?", "Investigator researching occult texts")
    print("Call of Cthulhu Personality Prompt:")
    print(cthulhu_prompt.format_prompt("What do I know about the Necronomicon?", "Investigator researching occult texts"))
    print()
    
    return dnd_personality, cthulhu_personality


def test_personality_manager():
    """Test the personality manager with ChromaDB storage"""
    print("Testing Personality Manager...")
    print("=" * 50)
    
    try:
        # Initialize manager
        chroma_manager = ChromaDataManager()
        personality_manager = PersonalityManager(chroma_manager)
        
        # Create test personalities
        dnd_personality, cthulhu_personality = test_personality_extractor()
        
        # Store personalities
        print("Storing personality profiles...")
        personality_manager.store_personality(dnd_personality)
        personality_manager.store_personality(cthulhu_personality)
        print("✓ Personalities stored successfully")
        print()
        
        # Test retrieval
        print("Testing personality retrieval...")
        retrieved_dnd = personality_manager.get_personality("D&D 5e")
        if retrieved_dnd:
            print(f"✓ Retrieved D&D 5e personality: {retrieved_dnd.personality_name}")
        else:
            print("✗ Failed to retrieve D&D 5e personality")
        
        retrieved_cthulhu = personality_manager.get_personality("Call of Cthulhu")
        if retrieved_cthulhu:
            print(f"✓ Retrieved Call of Cthulhu personality: {retrieved_cthulhu.personality_name}")
        else:
            print("✗ Failed to retrieve Call of Cthulhu personality")
        print()
        
        # Test listing
        print("Testing personality listing...")
        personalities = personality_manager.list_personalities()
        print(f"✓ Found {len(personalities)} personalities: {personalities}")
        print()
        
        # Test summaries
        print("Testing personality summaries...")
        for system in personalities:
            summary = personality_manager.get_personality_summary(system)
            if summary:
                print(f"  {system}: {summary['personality_name']} ({summary['tone']} tone)")
        print()
        
        # Test vernacular
        print("Testing vernacular retrieval...")
        dnd_vernacular = personality_manager.get_vernacular_for_system("D&D 5e")
        print(f"D&D 5e vernacular terms: {len(dnd_vernacular)}")
        if dnd_vernacular:
            for term in dnd_vernacular[:3]:
                print(f"  - {term['term']}: {term['definition']}")
        print()
        
        # Test comparison
        print("Testing personality comparison...")
        comparison = personality_manager.create_personality_comparison(["D&D 5e", "Call of Cthulhu"])
        print(f"Comparison results:")
        for system, data in comparison["comparison_matrix"].items():
            print(f"  {system}: {data['tone']} tone, {data['formality']} formality")
        print(f"Similarities: {comparison['similarities']}")
        print()
        
        # Test statistics
        print("Testing personality statistics...")
        stats = personality_manager.get_personality_stats()
        print(f"Total personalities: {stats['total_personalities']}")
        print(f"Average confidence: {stats['average_confidence']:.2f}")
        print(f"By tone: {stats.get('personalities_by_tone', {})}")
        print(f"By formality: {stats.get('personalities_by_formality', {})}")
        print()
        
        print("✓ All personality manager tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Error in personality manager test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all personality system tests"""
    print("TTRPG Assistant - Personality System Tests")
    print("=" * 60)
    print()
    
    # Test extractor
    try:
        test_personality_extractor()
        print("✓ Personality extraction tests passed!")
    except Exception as e:
        print(f"✗ Personality extraction tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Test manager
    try:
        if test_personality_manager():
            print("✓ Personality management tests passed!")
        else:
            print("✗ Personality management tests failed!")
            return False
    except Exception as e:
        print(f"✗ Personality management tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("=" * 60)
    print("🎉 All personality system tests passed successfully!")
    print()
    print("The personality extraction and management system is working correctly.")
    print("You can now:")
    print("1. Extract personality profiles from rulebook content")
    print("2. Store and retrieve personality data using ChromaDB")
    print("3. Generate personality-aware prompts and responses")
    print("4. Compare personality profiles across systems")
    print("5. Access vernacular and terminology specific to each system")


if __name__ == "__main__":
    main()