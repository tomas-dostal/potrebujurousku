#!/bin/bash
python $1/main2.py
DIFF=$(diff $1/v_databazi.txt $1/aktualni.txt)
 
if [ "$DIFF" != "" ] 
then
    echo "Došlo ke změně!" 
    echo ""
    echo "Databaze \t Aktuální opatření z internetu" 
    colordiff -y v_databazi.txt aktualni.txt
    echo ""

else
  echo "Aktuální!"

fi

