import ujson as json


class Node:
    def __init__(self, name, children, metrics):
        self.name = name
        self.children = children
        self.metrics = metrics

    def __str__(self):
        return ('{' +
                ('"name":"{0}","children":[{1}],"metrics":{2}'
                 .format(self.name,
                         ','.join([str(child) for child in self.children]),
                         json.dumps(self.metrics))) +
                '}')


def build_tree(root, properties, metrics):
    matching_child = list(filter(lambda child: child.name == properties[0], root.children))
    if len(matching_child) == 0:
        if len(properties) == 1:
            node = Node(properties[0], [], metrics)
            root.children.append(node)
        else:
            node = Node(properties[0], [], None)
            root.children.append(node)
            build_tree(node, properties[1:], metrics)
    else:
        build_tree(matching_child[0], properties[1:], metrics)


def get_total_index(children):
    for ind, child in enumerate(children):
        if child.name == '$total':
            return ind


def sort_tree(root, cmp_met):
    if root.metrics is not None:
        return root.metrics
    for child in root.children:
        ret = sort_tree(child, cmp_met)
        if child.name == '$total':
            root.metrics = ret
    sor = sorted(root.children, key=lambda k: k.metrics[cmp_met])
    index = get_total_index(sor)
    root.children = sor[:index] + sor[index + 1:] + [sor[index]]
    root.children = root.children[::-1]
    return root.metrics


def hierarchical_sort(entries, property_name):
    root = Node('', [], None)
    for entry in entries:
        build_tree(root, entry[0], entry[1])
    sort_tree(root, property_name)
    return root


def print_tree(root, acc, metric_names, out_file=None):
    if len(root.children) == 0:
        res = acc + [str(root.metrics[metric]) for metric in metric_names]
        if out_file is not None:
            out_file.write('|'.join(res) + '\n')
        else:
            print('|'.join(res))
    else:
        for child in root.children:
            print_tree(child, acc + [child.name], metric_names, out_file=out_file)


def parse_header(header):
    fields = header.split('|')
    metrics = [field for field in fields if not field.startswith('property')]
    return len(fields) - len(metrics), metrics


def main():
    entries = []
    with open('data.tsv') as input_file:
        header = input_file.readline().rstrip()
        num_properties, metric_names = parse_header(header)
        for line in input_file:
            fields = line.rstrip().split('|')
            properties = fields[:num_properties]
            metrics = {
                metric_name: float(value)
                for metric_name, value in zip(metric_names, fields[num_properties:])
            }
            entries.append((properties, metrics))

    sorted_data = hierarchical_sort(entries, "net_sales")

    with open('output.tsv', 'w') as out_file:
        out_file.write(header + '\n')
        print_tree(sorted_data, [], metric_names, out_file)


if __name__ == '__main__':
    main()
