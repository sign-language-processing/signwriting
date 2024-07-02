from signwriting.fingerspelling.fingerspelling import spell
from signwriting.mouthing.mouthing import mouth
from signwriting.utils.join_signs import join_signs_vertical

text = "Hello SignWriting List"
for word in text.split(" "):
    mouthing = mouth(word, language="eng-Latn")
    spelling = spell(word, language="en-us-ase-asl", vertical=False)
    sign = join_signs_vertical(mouthing, spelling, spacing=5)
    print(sign)
