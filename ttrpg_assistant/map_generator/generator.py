import svgwrite

class MapGenerator:
    def __init__(self, width, height, grid_size=20):
        self.width = width
        self.height = height
        self.grid_size = grid_size
        self.dwg = svgwrite.Drawing(size=(width * grid_size, height * grid_size))
        self.dwg.add(self.dwg.rect(insert=(0, 0), size=('100%', '100%'), fill='white'))

    def add_grid(self):
        for x in range(self.width + 1):
            self.dwg.add(self.dwg.line(
                start=(x * self.grid_size, 0),
                end=(x * self.grid_size, self.height * self.grid_size),
                stroke=svgwrite.rgb(200, 200, 200, '%')
            ))
        for y in range(self.height + 1):
            self.dwg.add(self.dwg.line(
                start=(0, y * self.grid_size),
                end=(self.width * self.grid_size, y * self.grid_size),
                stroke=svgwrite.rgb(200, 200, 200, '%')
            ))

    def generate_map(self, map_description: str):
        # This is a very simple implementation. A real implementation would use more
        # sophisticated logic to parse the description and generate the map.
        self.add_grid()
        
        # Add a simple room in the center of the map
        room_width = self.width // 2
        room_height = self.height // 2
        room_x = (self.width - room_width) // 2
        room_y = (self.height - room_height) // 2

        self.dwg.add(self.dwg.rect(
            insert=(room_x * self.grid_size, room_y * self.grid_size),
            size=(room_width * self.grid_size, room_height * self.grid_size),
            fill='lightgrey',
            stroke='black'
        ))

        return self.dwg.tostring()
