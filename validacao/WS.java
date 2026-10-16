import ij.*; import ij.process.*; import ij.plugin.filter.*; import ij.measure.*; import ij.io.*;
public class WS {
  public static void main(String[] a) {
    Prefs.blackBackground = true;
    ImagePlus imp = IJ.openImage(a[0]);
    ByteProcessor ip = (ByteProcessor) imp.getProcessor();
    new EDM().toWatershed(ip);
    new FileSaver(new ImagePlus("ws", ip)).saveAsTiff(a[1]);
    ResultsTable rt = new ResultsTable();
    ParticleAnalyzer pa = new ParticleAnalyzer(0, Measurements.AREA, rt, 0, Double.POSITIVE_INFINITY);
    ip.setThreshold(255, 255, ImageProcessor.NO_LUT_UPDATE);
    pa.analyze(new ImagePlus("ws", ip));
    System.out.println("particulas " + rt.size());
  }
}
