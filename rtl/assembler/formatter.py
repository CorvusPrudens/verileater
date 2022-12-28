
def format_bytes(data: 'list[int]', width: 'int', binary: 'bool'=False, addresses: 'bool'=False, address_width: 'int'=4) -> 'str':

    if binary:
        data_formatter = f'{{:0{width * 8}b}}'
        addr_formatter = f'{{:0{address_width}b}}'
    else:
        data_formatter = f'{{:0{width * 2}X}}'
        addr_formatter = f'{{:0{address_width // 4}X}}'

    lines = []

    if addresses:
        for i, value in enumerate(data):
            lines.append(f'{addr_formatter.format(i)}: {data_formatter.format(value)}')
    else:
        for i in range(0, len(data), 8):
            lines.append(' '.join([data_formatter.format(v) for v in data[i:i+8]]))
    
    return '\n'.join(lines)
