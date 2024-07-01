# HamNoSys

HamNoSys is another phonetic notation system for sign languages.

From Susanne Bentele at the university of Hamburg: https://www.signwriting.org/forums/linguistics/ling007.html
> The purpose of HamNoSys, unlike SignWriting, has never been an everyday use to 
> communicate (e.g. in letters) in sign language. 
> It was designed to fit a research setting and should be applicable to every sign language in the world.

To show multiple signs in both SignWriting and HamNoSys, you can look at:
https://www.signwriting.org/forums/linguistics/ling001.html
https://www.signwriting.org/forums/linguistics/ling002.html
https://www.signwriting.org/forums/linguistics/ling003.html

## Translation of HamNoSys to SignWriting

Around 2012, an effort from Sarah Ebling and Penny Boyes Braem was made to analyze HamNoSys and SignWriting.
In order to not lose their progress, we have organized and saved their work in this repository.
To our eyes, their attempt was to transcribe signs both in HamNoSys and SignWriting, and then compare the two,
using frequency analysis to find patterns and similarities.

Therefore, the parts of their work we are interested in keeping are:
- The general mapping between HamNoSys and SignWriting categories
- The parallel database of signs they have collected in HamNoSys and SignWriting

There is currently no translation "model" from HamNoSys to SignWriting, 
but with the help of the parallel database they have created, we can train a model to do so.

### Category Mapping

```mermaid
flowchart LR
    subgraph SignWriting
        A[Category 1: Hands]
        B[Category 2: Movement]
        C[Category 3: Dynamics]
        D[Category 4: Head & Faces]
        E[Category 5: Body]
        F[Category 6: Detailed Location]
        G[Category 7: Punctuation]
    end
    
    subgraph HamNoSys
        H[handshape]
        I[hand orientation <palm orientation, extended finger direction>]
        K[movement]
        J[location]
        L[NMF <two-letter codes>]
        M[other]
    end
    
    A --> H & I
    B --> K
    D --> J & L
    E --> J & L
    F --> J
    G --> M
    C --> M
```

### Parallel Database

We store the database as a JSON file (`parallel.json`), combined from multiple files:
1. We extract glosses and links to signpuddle from `urls_glosses.txt`
2. We go over the `SW_signs_IDs` and convert each `layout.txt` file to FSW.
3. We go over `SW_signs_glosses` and convert each `layout.txt` file to FSW to match the gloss to the ID from `SW_signs_IDs`.
4. We add `HNS_alternative.txt` and `db_glossen_IDs_mit_HNS.txt`, match the ID or the gloss, and add the HamNoSys.