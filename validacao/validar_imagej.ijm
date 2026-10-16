// Roda o ImageJ (o mesmo motor do Fiji) sem janela e salva a tabela de referência.
// Uso: java -Djava.awt.headless=true -jar ij.jar -batch validar_imagej.ijm "<imagem>|<saida.csv>|<metodo>"
args = split(getArgument(), "|");
open(args[0]);
run("8-bit");
setAutoThreshold(args[2] + " dark");
getThreshold(lower, upper);
print("LIMIAR " + lower + " " + upper);
run("Set Measurements...", "area centroid perimeter shape display redirect=None decimal=4");
run("Analyze Particles...", "size=0-Infinity display clear");
print("CONTAGEM " + nResults);
saveAs("Results", args[1]);
