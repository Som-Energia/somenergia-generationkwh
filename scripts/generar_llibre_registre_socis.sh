#!/bin/bash
REPORT_PATH='/tmp/reports/'
cd $REPORT_PATH
rm llibre_registre_socis_vol_1.pdf llibre_registre_socis_vol_2.pdf
foo=($(ls))
n_elements=${#foo[@]}
primer=$(( $n_elements / 2 ))
pdfunite "${foo[@]:0:$primer}"  llibre_registre_socis_vol_1.pdf
pdfunite "${foo[@]:$primer}"  llibre_registre_socis_vol_2.pdf
#rm *.pdf
