import re

class GCodeParser:
    def __init__(self):
        self.current_system = None
        self.moves = []
        self.current_position = {'X': 0, 'Y': 0, 'Z': 0, 'A': 0, 'B': 0, 'F': 0}
        self.current_layer = 1 #Gcode currently starts at layer 1

    def parse_file(self, filename):
        with open(filename, 'r') as file:
            for line_number, line in enumerate(file, 1):
                self.parse_line(line.strip(), line_number)

    def parse_line(self, line, line_number):
        if line.startswith(';Layer'):
            match = re.search(r';Layer (\d+) of', line)
            if match:
                self.current_layer = int(match.group(1))
        elif line.startswith('G55'):
            self.current_system = 'polymer'
        elif line.startswith('G58'):
            self.current_system = 'ceramic'
        elif line.startswith('G0') or line.startswith('G1'):
            self.parse_move(line, line_number)

    def parse_move(self, line, line_number):
        parts = line.split()
        move = self.current_position.copy()
        move['system'] = self.current_system
        move['layer'] = self.current_layer
        
        has_extrusion = False
        for part in parts[1:]:
            if part[0] in 'XYZABF':
                move[part[0]] = float(part[1:])
                if part[0] in 'AB':
                    has_extrusion = True
        
        move['type'] = 'print' if has_extrusion else 'travel'
        
        self.moves.append(move)
        self.current_position = {k: v for k, v in move.items() if k not in ['type', 'system', 'layer']}

    def get_moves(self):
        return self.moves

# Usage example
if __name__ == "__main__":
    parser = GCodeParser()
    parser.parse_file('path/to/your/gcode/file.gcode')
    moves = parser.get_moves()
    
    print(f"Total moves parsed: {len(moves)}")
    print("First 5 moves:")
    for move in moves[:5]:
        print(move)