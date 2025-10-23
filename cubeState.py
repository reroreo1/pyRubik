import copy

class CubeState:
    # Edge and corner names (standard Singmaster notation)
    corner_names = ['URF','UFL','ULB','UBR','DFR','DLF','DBL','DRB']
    edge_names = ['UR','UF','UL','UB','DR','DF','DL','DB','FR','FL','BL','BR']

    def __init__(self):
        # Each corner/edge position index matches its correct position
        self.corner_positions = list(range(8))
        self.corner_orientations = [0]*8  # 0,1,2
        self.edge_positions = list(range(12))
        self.edge_orientations = [0]*12   # 0,1

    def copy(self):
        return copy.deepcopy(self)

    def move(self, move):
        """Apply one move (U, R, F, D, L, B and their variants)"""
        if move.endswith("2"):
            self._apply_move(move[0])
            self._apply_move(move[0])
        elif move.endswith("'"):
            self._apply_move(move[0])
            self._apply_move(move[0])
            self._apply_move(move[0])
        else:
            self._apply_move(move[0])

    def _apply_move(self, move):
        """Core move transformation tables"""
        # Edge and corner mappings for each face turn
        # These define how positions and orientations rotate
        if move == 'U':
            self._cycle(self.corner_positions, (0,1,2,3))
            self._cycle(self.edge_positions, (0,1,2,3))
        elif move == 'D':
            self._cycle(self.corner_positions, (4,7,6,5))
            self._cycle(self.edge_positions, (4,7,6,5))
        elif move == 'F':
            self._cycle(self.corner_positions, (0,4,5,1))
            self._cycle(self.edge_positions, (1,9,5,8))
            for i in [0,1,4,5]:
                self.corner_orientations[i] = (self.corner_orientations[i] + (1 if i in (0,5) else 2)) % 3
            for i in [1,5,8,9]:
                self.edge_orientations[i] ^= 1
        elif move == 'B':
            self._cycle(self.corner_positions, (2,3,7,6))
            self._cycle(self.edge_positions, (3,11,7,10))
            for i in [2,3,6,7]:
                self.corner_orientations[i] = (self.corner_orientations[i] + (1 if i in (3,6) else 2)) % 3
            for i in [3,7,10,11]:
                self.edge_orientations[i] ^= 1
        elif move == 'R':
            self._cycle(self.corner_positions, (0,3,7,4))
            self._cycle(self.edge_positions, (0,11,4,8))
            for i in [0,3,4,7]:
                self.corner_orientations[i] = (self.corner_orientations[i] + (1 if i in (0,7) else 2)) % 3
        elif move == 'L':
            self._cycle(self.corner_positions, (1,5,6,2))
            self._cycle(self.edge_positions, (2,9,6,10))
            for i in [1,2,5,6]:
                self.corner_orientations[i] = (self.corner_orientations[i] + (1 if i in (2,5) else 2)) % 3

    def _cycle(self, arr, idxs):
        temp = arr[idxs[0]]
        for i in range(3):
            arr[idxs[i]] = arr[idxs[i+1]]
        arr[idxs[3]] = temp

    def is_solved(self):
        return (self.corner_positions == list(range(8)) and
                self.corner_orientations == [0]*8 and
                self.edge_positions == list(range(12)) and
                self.edge_orientations == [0]*12)
