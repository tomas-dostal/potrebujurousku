#!/bin/bash

OUT=sitemap.xml

# Předpokládejme, že mám dostatečná práva na zápis do souboru atd... 
# Chtěl jsem to mít jenom rychle napsané 

echo "<?xml version="1.0" encoding="UTF-8"?>" > $OUT 
echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' >> $OUT
echo '<url>' >> $OUT
echo '  <loc>https://potrebujurousku.cz/</loc>' >> $OUT
echo '  <changefreq>hourly</changefreq>' >> $OUT
echo '</url>' >> $OUT

echo '<url>' >> $OUT
echo '  <loc>https://potrebujurousku.cz/aktualnost/</loc>' >> $OUT
echo '  <changefreq>hourly</changefreq>' >> $OUT
echo '</url>' >> $OUT

echo '<url>' >> $OUT
echo '  <loc>https://potrebujurousku.cz/opatreni/</loc>' >> $OUT
echo '  <changefreq>hourly</changefreq>' >> $OUT
echo '</url>' >> $OUT

echo '<url>' >> $OUT
echo '  <loc>https://potrebujurousku.cz/opatreni/</loc>' >> $OUT
echo '  <changefreq>hourly</changefreq>' >> $OUT
echo '</url>' >> $OUT

echo '<url>' >> $OUT
echo '  <loc>https://potrebujurousku.cz/celostatni-opatreni/</loc>' >> $OUT
echo '  <changefreq>hourly</changefreq>' >> $OUT
echo '</url>' >> $OUT

echo '<url>' >> $OUT
echo '  <loc>https://potrebujurousku.cz/o-projektu/</loc>' >> $OUT
echo '  <changefreq>hourly</changefreq>' >> $OUT
echo '</url>' >> $OUT

echo '<url>' >> $OUT
echo '  <loc>https://potrebujurousku.cz/home/</loc>' >> $OUT
echo '  <changefreq>hourly</changefreq>' >> $OUT
echo '</url>' >> $OUT


for i in {1..14}
do
   echo "  <url>" >> $OUT
   echo "    <loc>https://potrebujurousku.cz/opatreni/?kraj_id=$i</loc>"  >> $OUT
   echo "    <changefreq>hourly</changefreq>"  >> $OUT
   echo "  </url>"  >> $OUT 
done
for i in {1..77}
do
   echo "Generuju okres_id (1-$i)"
   echo "  <url>" >> $OUT
   echo "    <loc>https://potrebujurousku.cz/opatreni/?okres_id=$i</loc>"  >> $OUT
   echo "    <changefreq>hourly</changefreq>"  >> $OUT
   echo "  </url>"  >> $OUT 
done

for i in {1..206}
do
   echo "Generuju nuts3_id (1-$i)"
   echo "  <url>" >> $OUT
   echo "    <loc>https://potrebujurousku.cz/opatreni/?nuts3_id=$i</loc>"  >> $OUT
   echo "    <changefreq>hourly</changefreq>"  >> $OUT
   echo "  </url>"  >> $OUT 
done


for i in {1..15105}
do
   echo "Generuju obecmesto_id (1-$i)"
   echo "  <url>" >> $OUT
   echo "    <loc>https://potrebujurousku.cz/opatreni/?obecmesto_id=$i</loc>"  >> $OUT
   echo "    <changefreq>hourly</changefreq>"  >> $OUT
   echo "  </url>"  >> $OUT 
done


echo "</urlset>" >> $OUT 
