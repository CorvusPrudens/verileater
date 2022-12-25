import json

class Node:

    def __init__(self, src: 'dict', dest: 'dict', type: 'str', delay: 'float', net: 'str'=None):
        self.src = src
        self.dest = dest
        self.net = net
        self.type = type
        self.delay = delay


class Connection:

    columns = ["coord", "src_block", "dest_block", "logic", "net", "signal"]
    @classmethod
    def get_block(cls, cell: 'str'):
        types = [
            'LUT4', 'DFFE', 'RAM'
        ]
        for type in types:
            if type in cell:
                return type
        return ''

    def __init__(self, logic_node: 'Node', net_node: 'Node'=None):
        self.logic_node = logic_node
        self.net_node = net_node

    def get_row(self):
        return {
            "coord": f'{self.logic_node.src["loc"][0]}, {self.logic_node.src["loc"][1]}',
            "src_block": Connection.get_block(self.logic_node.src["cell"]),
            "dest_block": Connection.get_block(self.net_node.dest["cell"]) if self.net_node is not None else '',
            "logic": f'{self.logic_node.delay:.1f}',
            "net": f'{self.net_node.delay:.1f}' if self.net_node is not None else '',
            "signal": self.net_node.net if self.net_node is not None else self.logic_node.dest["cell"],
        }

    def get_logic_delay(self):
        return self.logic_node.delay

    def get_net_delay(self):
        return self.net_node.delay if self.net_node is not None else 0

    def get_total_delay(self):
        logic_delay = self.logic_node.delay
        net_delay = self.net_node.delay if self.net_node is not None else 0
        return logic_delay + net_delay


class Path:

    @classmethod
    def from_json(cls, filepath):
        with open(filepath, 'r') as file:
            data = json.load(file)

        return [Path(p["from"], p["to"], p["path"]) for p in data["critical_paths"]]

    def __init__(self, src: 'str', dest: 'str', path_dict: 'list[dict]'):
        self.src = src
        self.dest = dest
        self.connections = []
        for i in range(0, len(path_dict), 2):
            logic_node = Node(path_dict[i]["from"], path_dict[i]["to"], path_dict[i]["type"], path_dict[i]["delay"])
            net_node = None
            if i + 1 < len(path_dict):
                net_node = Node(path_dict[i+1]["from"], path_dict[i+1]["to"], path_dict[i+1]["type"], path_dict[i+1]["delay"], net=path_dict[i+1]["net"])
            self.connections.append(Connection(logic_node, net_node))

        column_names = [p[0] for p in self.connections[0].get_row().items()]
        self.column_widths = {n: 0 for n in column_names}
        self.get_column_widths()

    def get_column_widths(self):
        for connection in self.connections:
            row = connection.get_row()
            for key, item in row.items():
                if len(item) > self.column_widths[key]:
                    self.column_widths[key] = len(item)
        for key in self.column_widths:
            if len(key) > self.column_widths[key]:
                self.column_widths[key] = len(key)

    def format_cell(self, value, column_name):
        return value + " " + " " * (self.column_widths[column_name] - len(value))

    def get_path_string(self):
        logic_delay = sum(map(lambda c: c.get_logic_delay(), self.connections))
        net_delay = sum(map(lambda c: c.get_net_delay(), self.connections))
        total_delay = logic_delay + net_delay

        rows = []
        rows.append([self.format_cell(key, key) for key, _ in self.column_widths.items()])
        rows.append(['-'*width + ' ' for _, width in self.column_widths.items()])
        for conn in self.connections:
            rows.append([self.format_cell(row, col) for col, row in conn.get_row().items()])

        rows.append(['-'*width + ' ' for _, width in self.column_widths.items()])
        rown_items = {"logic": f'{logic_delay:.1f}', "net": f'{net_delay:.1f}', "signal": f'{total_delay:.1f}'}

        rown = []
        for col, width in self.column_widths.items():
            value = rown_items.get(col, '')
            rown.append(self.format_cell(value, col))
        rows.append(rown)

        output_string = f'{self.src} -> {self.dest}' + '\n'
        output_string += '\n'.join([''.join(row) for row in rows])

        return output_string

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Present nextpnr timing analysis in a readable format')
    parser.add_argument('file', help="report JSON file")
    parser.add_argument('-o', help="output file name", default=None, type=str, dest="outfile")

    args = parser.parse_args()

    paths = Path.from_json(args.file)

    output = '\n\n'.join([p.get_path_string() for p in paths])

    if args.outfile is not None:
        with open(args.outfile, 'w') as file:
            file.write(output)
    else:
        print(output)



