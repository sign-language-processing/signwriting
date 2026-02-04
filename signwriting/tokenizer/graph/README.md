# Symbols Graph

Download some SignWriting data:
```
wget https://raw.githubusercontent.com/sign-language-processing/signbank-plus/refs/heads/main/data/raw.csv
```

Create a graph from the data:
```shell
python signwriting_to_graph.py --input raw.csv --output signwriting_graph.mmd
```