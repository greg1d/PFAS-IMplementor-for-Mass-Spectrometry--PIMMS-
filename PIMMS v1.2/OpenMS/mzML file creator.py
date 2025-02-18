<mzML xmlns="http://psi.hupo.org/ms/mzml" version="1.1.0">
  <run id="example_run" defaultInstrumentConfigurationRef="IC1">
    <instrumentConfigurationList count="1">
      <instrumentConfiguration id="IC1">
        <cvParam cvRef="MS" accession="MS:1000031" name="instrument model" value="Example Mass Spectrometer"/>
      </instrumentConfiguration>
    </instrumentConfigurationList>
    <spectrumList count="1">
      <spectrum index="73860" id="scanId=76164" defaultArrayLength="11" dataProcessingRef="pwiz_Reader_Agilent_conversion">
        <cvParam cvRef="MS" accession="MS:1000129" name="negative scan" value=""/>
        <cvParam cvRef="MS" accession="MS:1000511" name="ms level" value="2"/>
        <cvParam cvRef="MS" accession="MS:1000580" name="MSn spectrum" value=""/>
        <cvParam cvRef="MS" accession="MS:1000285" name="total ion current" value="32.0" unitCvRef="MS" unitAccession="MS:1000131" unitName="number of detector counts"/>
        <cvParam cvRef="MS" accession="MS:1000127" name="centroid spectrum" value=""/>
        <cvParam cvRef="MS" accession="MS:1000505" name="base peak intensity" value="12.0" unitCvRef="MS" unitAccession="MS:1000131" unitName="number of detector counts"/>
        <cvParam cvRef="MS" accession="MS:1000504" name="base peak m/z" value="536.894554538179" unitCvRef="MS" unitAccession="MS:1000040" unitName="m/z"/>
        <cvParam cvRef="MS" accession="MS:1000528" name="lowest observed m/z" value="536.894554538179" unitCvRef="MS" unitAccession="MS:1000040" unitName="m/z"/>
        <cvParam cvRef="MS" accession="MS:1000527" name="highest observed m/z" value="1559.04651756742" unitCvRef="MS" unitAccession="MS:1000040" unitName="m/z"/>
        <cvParam cvRef="MS" accession="MS:1000796" name="spectrum title" value="69 Paired 97.76164.76164. File:&quot;69 Paired 97.d&quot;, NativeID:&quot;scanId=76164&quot;"/>
        <scanList count="1">
          <cvParam cvRef="MS" accession="MS:1000795" name="no combination" value=""/>
          <scan>
            <cvParam cvRef="MS" accession="MS:1000016" name="scan start time" value="3.29135" unitCvRef="UO" unitAccession="UO:0000031" unitName="minute"/>
            <cvParam cvRef="MS" accession="MS:1002476" name="ion mobility drift time" value="1.437408" unitCvRef="UO" unitAccession="UO:0000028" unitName="millisecond"/>
            <scanWindowList count="1">
              <scanWindow>
                <cvParam cvRef="MS" accession="MS:1000501" name="scan window lower limit" value="49.95886030672" unitCvRef="MS" unitAccession="MS:1000040" unitName="m/z"/>
                <cvParam cvRef="MS" accession="MS:1000500" name="scan window upper limit" value="1559.04651756742" unitCvRef="MS" unitAccession="MS:1000040" unitName="m/z"/>
              </scanWindow>
            </scanWindowList>
          </scan>
        </scanList>
        <precursorList count="1">
          <precursor>
            <isolationWindow>
              <cvParam cvRef="MS" accession="MS:1000827" name="isolation window target m/z" value="804.50268893707" unitCvRef="MS" unitAccession="MS:1000040" unitName="m/z"/>
              <cvParam cvRef="MS" accession="MS:1000828" name="isolation window lower offset" value="754.54382863035" unitCvRef="MS" unitAccession="MS:1000040" unitName="m/z"/>
              <cvParam cvRef="MS" accession="MS:1000829" name="isolation window upper offset" value="754.54382863035" unitCvRef="MS" unitAccession="MS:1000040" unitName="m/z"/>
            </isolationWindow>
            <selectedIonList count="1">
              <selectedIon>
                <cvParam cvRef="MS" accession="MS:1000744" name="selected ion m/z" value="804.50268893707" unitCvRef="MS" unitAccession="MS:1000040" unitName="m/z"/>
              </selectedIon>
            </selectedIonList>
            <activation>
              <cvParam cvRef="MS" accession="MS:1000133" name="collision-induced dissociation" value=""/>
              <cvParam cvRef="MS" accession="MS:1000045" name="collision energy" value="60.0" unitCvRef="UO" unitAccession="UO:0000266" unitName="electronvolt"/>
            </activation>
          </precursor>
        </precursorList>
        <binaryDataArrayList count="2">
          <binaryDataArray encodedLength="40">
            <cvParam cvRef="MS" accession="MS:1000523" name="64-bit float" value=""/>
            <cvParam cvRef="MS" accession="MS:1000574" name="zlib compression" value=""/>
            <cvParam cvRef="MS" accession="MS:1000515" name="intensity array" value="" unitCvRef="MS" unitAccession="MS:1000131" unitName="number of detector counts"/>
            <binary>eJxjYEAGZg4MWIEMDnEOHOICOMQ/2AMAX4MCmg==</binary>
          </binaryDataArray>
        </binaryDataArrayList>
      </spectrum>
    </spectrumList>
  </run>
</mzML>
"""

# Define the file path
mzml_debug_file = r"D:\Twins Sample Run\Data\Demultiplexed\Raw\debug_test.mzML"

# Write the content to a file
with open(mzml_debug_file, "w", encoding="utf-8") as f:
    f.write(mzml_content)

print(f"✅ Debug mzML file created with corrected XML: {mzml_debug_file}")
