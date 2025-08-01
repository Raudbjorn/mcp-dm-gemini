"""
Configuration utilities for the TTRPG Assistant
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any


def find_config_file(filename: str = "config.yaml") -> str:
    """
    Find a config file by looking up the directory tree from the current file
    
    Args:
        filename: Name of the config file to find
        
    Returns:
        str: Path to the config file
        
    Raises:
        FileNotFoundError: If config file cannot be found
    """
    # Try different possible locations
    possible_paths = [
        # Relative to current working directory
        f"config/{filename}",
        f"./{filename}",
        filename,
    ]
    
    # Also try looking up the directory tree
    current_dir = Path.cwd()
    for _ in range(5):  # Don't go up more than 5 levels
        for subdir in ["config", "."]:
            config_path = current_dir / subdir / filename
            if config_path.exists():
                return str(config_path)
        current_dir = current_dir.parent
    
    # Try relative to this module's location
    module_dir = Path(__file__).parent
    for _ in range(5):  # Don't go up more than 5 levels
        config_path = module_dir / "config" / filename
        if config_path.exists():
            return str(config_path)
        module_dir = module_dir.parent
    
    # Check all possible paths
    for path in possible_paths:
        if Path(path).exists():
            return path
    
    # If not found, return the most likely location for error reporting
    return f"config/{filename}"


def load_config(filename: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Args:
        filename: Name of the config file to load
        
    Returns:
        Dict[str, Any]: Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file cannot be found
        yaml.YAMLError: If config file is invalid YAML
    """
    config_path = find_config_file(filename)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            if config is None:
                return {}
            return config
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Configuration file not found. Looked for '{filename}' in:\n"
            f"- Current directory: {Path.cwd()}\n"
            f"- Config subdirectory: {Path.cwd() / 'config'}\n"
            f"- Module directory: {Path(__file__).parent}\n"
            f"Please ensure the config file exists in one of these locations."
        )
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in config file '{config_path}': {e}")


def load_config_safe(filename: str = "config.yaml", default: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file with fallback to default
    
    Args:
        filename: Name of the config file to load
        default: Default configuration to use if file not found
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    if default is None:
        default = {}
    
    try:
        return load_config(filename)
    except (FileNotFoundError, yaml.YAMLError):
        return default