import ij.*; import ij.process.*; import ij.measure.*; import ij.plugin.filter.ParticleAnalyzer;
public class Validar {
  public static void main(String[] a) {
    ImagePlus imp = IJ.openImage(a[0]);
    if (imp.getType() != ImagePlus.GRAY8) new ImageConverter(imp).convertToGray8();
    ImageProcessor ip = imp.getProcessor();
    ip.setAutoThreshold(a[2]);
    System.out.println("LIMIAR " + ip.getMinThreshold() + " " + ip.getMaxThreshold());
    int med = Measurements.AREA | Measurements.CENTROID | Measurements.PERIMETER | Measurements.SHAPE_DESCRIPTORS;
    ResultsTable rt = new ResultsTable();
    ParticleAnalyzer pa = new ParticleAnalyzer(0, med, rt, 0, Double.POSITIVE_INFINITY);
    pa.setHideOutputImage(true);
    pa.analyze(imp, ip);
    System.out.println("CONTAGEM " + rt.size());
    rt.save(a[1]);
  }
}
