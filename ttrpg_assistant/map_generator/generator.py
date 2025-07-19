import svgwrite
from ttrpg_assistant.logger import logger

class MapGenerator:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

    def generate_map(self, description: str) -> str:
        logger.info(f"Generating a {self.width}x{self.height} map with description: '{description}'")
        dwg = svgwrite.Drawing(profile='tiny', size=(self.width * 20, self.height * 20))
        
        # Add a grid
        for x in range(self.width):
            for y in range(self.height):
                dwg.add(dwg.rect(insert=(x * 20, y * 20), size=(20, 20), fill='white', stroke='gray'))

        # This is a very basic implementation. A real implementation would use NLP
        # to parse the description and draw features on the map.
        if "cave" in description:
            dwg.add(dwg.circle(center=(100, 100), r=50, fill='gray'))
        elif "tavern" in description:
            dwg.add(dwg.rect(insert=(50, 50), size=(100, 100), fill='brown'))
        
        return dwg.tostring()