# Bugs

1. Blinks:
    Un blink ne contiendra aucune entry (à part début et fin). Mais il peut y avoir une réponse :
    ```
    SBLINK R 3273090
    3273090	   .	   .	    0.0	...
    ...
    MSG	3273314 {"Le sujet a repondu"}
    3273314	   .	   .	    0.0	...
    ...
    EBLINK R 3273090	3273354	268
    ```
    Dans ce cas, le temps de début 3273090 n'est pas 3273314, et le temps de fin 3273354 non plus.
