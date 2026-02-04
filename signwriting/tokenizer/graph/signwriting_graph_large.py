from itertools import chain

from tqdm import tqdm
import networkx as nx
import matplotlib.pyplot as plt

from signwriting.formats.fsw_to_swu import fsw2swu
import csv

from signwriting.tokenizer import normalize_signwriting


with open('/Users/amitmoryossef/dev/sign-language-processing/signwriting/signwriting/tokenizer/graph/raw.csv', 'r', encoding='utf-8') as f:
    csv.field_size_limit(2 ** 20)
    reader = csv.DictReader(f)
    sign_writings = (row['sign_writing'] for row in reader)
    normalized = (normalize_signwriting(fsw) for fsw in sign_writings)
    fsw_signs = list(tqdm(chain.from_iterable(fsw.split() for fsw in normalized)))

    with open("all_signs.txt", "w", encoding="utf-8") as all_signs_file:
        for fsw in tqdm(fsw_signs):
            all_signs_file.write(fsw2swu(fsw) + "\n")

# signs = [fsw_to_sign(sign) for sign in tqdm(fsw_signs)]
#
# G = nx.DiGraph()
#
# for sign in signs:
#     for symbol in sign['symbols']:
#         node_id = symbol['symbol']
#         node_label = fsw2swu(symbol['symbol'])
#         G.add_node(node_id, label=node_label)
#
# edge_data = {}
#
# for sign in signs:
#     for i, symbol1 in enumerate(sign['symbols']):
#         for j, symbol2 in enumerate(sign['symbols']):
#             if i != j:
#                 if symbol1['position'][0] > symbol2['position'][0]:
#                     edge_key = (symbol1['symbol'], symbol2['symbol'])
#                     if edge_key not in edge_data:
#                         edge_data[edge_key] = {'x_offsets': [], 'y_offsets': []}
#
#                     relative_position_x = symbol2['position'][0] - symbol1['position'][0]
#                     relative_position_y = symbol2['position'][1] - symbol1['position'][1]
#
#                     edge_data[edge_key]['x_offsets'].append(relative_position_x)
#                     edge_data[edge_key]['y_offsets'].append(relative_position_y)
#
# for (source, target), data in edge_data.items():
#     G.add_edge(source, target,
#               count=len(data['x_offsets']),
#               x_offsets=data['x_offsets'],
#               y_offsets=data['y_offsets'])
#
# print(sum(len(data['x_offsets']) for data in edge_data.values()), "edge instances processed")
# print(f"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
#
# nx.write_multiline_adjlist(G, 'signwriting_graph.graph')

G = nx.read_multiline_adjlist('signwriting_graph.graph')

# Count different types of edge combinations
exact_edge_counts = {}
node_pair_counts = {}
rounded_edge_counts = {}

for source, target, edge_attrs in tqdm(G.edges(data=True)):
    x_offsets = edge_attrs['x_offsets']
    y_offsets = edge_attrs['y_offsets']
    
    # Count node pairs (A, B)
    node_pair_key = (source, target)
    node_pair_counts[node_pair_key] = node_pair_counts.get(node_pair_key, 0) + len(x_offsets)
    
    for x_off, y_off in zip(x_offsets, y_offsets):
        # Exact match
        exact_key = (source, target, x_off, y_off)
        exact_edge_counts[exact_key] = exact_edge_counts.get(exact_key, 0) + 1
        
        # Rounded (remove one significant digit)
        x_rounded = int(x_off // 10) if x_off != 0 else 0
        y_rounded = int(y_off // 10) if y_off != 0 else 0
        rounded_key = (source, target, x_rounded, y_rounded)
        rounded_edge_counts[rounded_key] = rounded_edge_counts.get(rounded_key, 0) + 1

# Sort all three types by frequency
exact_sorted = sorted(exact_edge_counts.items(), key=lambda x: x[1], reverse=True)
node_pair_sorted = sorted(node_pair_counts.items(), key=lambda x: x[1], reverse=True)
rounded_sorted = sorted(rounded_edge_counts.items(), key=lambda x: x[1], reverse=True)

# Extract frequencies
exact_frequencies = [count for _, count in exact_sorted]
node_pair_frequencies = [count for _, count in node_pair_sorted]
rounded_frequencies = [count for _, count in rounded_sorted]

print(f"Exact combinations: {len(exact_frequencies)} (top: {exact_frequencies[0]}, low: {exact_frequencies[-1]})")
print(f"Node pairs: {len(node_pair_frequencies)} (top: {node_pair_frequencies[0]}, low: {node_pair_frequencies[-1]})")
print(f"Rounded combinations: {len(rounded_frequencies)} (top: {rounded_frequencies[0]}, low: {rounded_frequencies[-1]})")

# Create comparison plot
plt.figure(figsize=(15, 10))
plt.semilogy(range(len(exact_frequencies)), exact_frequencies, 'b-', linewidth=1, label='Exact (source, target, x, y)', alpha=0.8)
plt.semilogy(range(len(node_pair_frequencies)), node_pair_frequencies, 'r-', linewidth=1.5, label='Node pairs (source, target)', alpha=0.8)
plt.semilogy(range(len(rounded_frequencies)), rounded_frequencies, 'g-', linewidth=1, label='Rounded positions (source, target, x/10, y/10)', alpha=0.8)

# Add endpoint dots to show where each line ends
plt.semilogy(len(exact_frequencies) - 1, exact_frequencies[-1], 'bo', markersize=8, label='_nolegend_')
plt.semilogy(len(node_pair_frequencies) - 1, node_pair_frequencies[-1], 'ro', markersize=8, label='_nolegend_')
plt.semilogy(len(rounded_frequencies) - 1, rounded_frequencies[-1], 'go', markersize=8, label='_nolegend_')

plt.ylabel('Frequency (log scale)', fontsize=12)
plt.xlabel('Rank (sorted by frequency)', fontsize=12)
plt.title('Edge Frequency Distributions: Exact vs Node Pairs vs Rounded Positions', fontsize=14)
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('edge_frequency_comparison.png', dpi=300, bbox_inches='tight')
plt.show()

