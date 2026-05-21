<?xml version="1.0"?>
<!--
Schematron jpylyzer schema for KB lossless preservation master (A.K.A. KB_MASTER_LOSSLESS_21/05/2026)
TODO: formalize to spec with proper name/identifier, e.g. "Middeleeuwse Handschriften", "Beeldstudio"
on "Metamorfoze"
-->
<s:schema xmlns:s="http://purl.oclc.org/dsdl/schematron">
<s:ns uri="adobe:ns:meta/" prefix="x"/>
<s:ns uri="http://www.w3.org/1999/02/22-rdf-syntax-ns#" prefix="rdf"/>
<s:ns uri="http://ns.adobe.com/exif/1.0/" prefix="exif"/>
<s:ns uri="http://ns.adobe.com/tiff/1.0/" prefix="tiff"/>
<s:ns uri="http://ns.adobe.com/photoshop/1.0/" prefix="photoshop"/>

<s:pattern>
    <s:title>KB master JP2 2026, generic (no colour/resolution requirements)</s:title>

    <!-- check that the jpylyzer element exists -->
    <s:rule context="/">
        <s:assert test="file">no file element found</s:assert>
    </s:rule>

    <!-- top-level Jpylyzer checks -->
    <s:rule context="/file">

        <!-- check that success value equals 'True' -->
        <s:assert test="statusInfo/success = 'True'">jpylyzer did not run successfully</s:assert>

        <!-- check that isValid element exists with the text 'True' -->
        <s:assert test="isValid = 'True'">not valid JP2</s:assert>
    </s:rule>

    <!-- Top-level properties checks -->
    <s:rule context="/file/properties">

        <!-- check that UUID box with XMP metadata exists -->
        <s:assert test="uuidBox and uuidBox/x:xmpmeta">no UUID box with XMP metadata</s:assert>

    </s:rule>

    <!-- check that resolution box exists -->
    <s:rule context="/file/properties/jp2HeaderBox">
        <s:assert test="resolutionBox">no resolution box</s:assert>
    </s:rule>

    <!-- check that resolution box contains capture resolution box -->
    <s:rule context="/file/properties/jp2HeaderBox/resolutionBox">
        <s:assert test="captureResolutionBox">no capture resolution box</s:assert>
    </s:rule>

    <!-- check that METH equals 'Restricted ICC' -->
    <s:rule context="/file/properties/jp2HeaderBox/colourSpecificationBox">
        <s:assert test="meth = 'Restricted ICC'">METH not 'Restricted ICC'</s:assert>
    </s:rule>

    <!-- check X- and Y- tile sizes -->
    <s:rule context="/file/properties/contiguousCodestreamBox/siz">
        <s:assert test="xTsiz = '1024'">wrong X Tile size</s:assert>
        <s:assert test="yTsiz = '1024'">wrong Y Tile size</s:assert>
    </s:rule>

    <!-- checks on codestream COD parameters -->

    <s:rule context="/file/properties/contiguousCodestreamBox/cod">

        <!-- Error resilience features: sop, eph and segmentation symbols -->
        <s:assert test="sop = 'yes'">no start-of-packet headers</s:assert>
        <s:assert test="eph = 'yes'">no end-of-packet headers</s:assert>
        <s:assert test="segmentationSymbols = 'yes'">no segmentation symbols</s:assert>

        <!-- Progression order -->
        <s:assert test="order = 'RPCL'">wrong progression order</s:assert>

        <!-- Layers -->
        <s:assert test="layers = '11'">wrong number of layers</s:assert>

        <!-- Colour transformation (only for RGB images, i.e. number of components = 3)-->
        <s:assert test="(multipleComponentTransformation = 'yes') and
                        (../../jp2HeaderBox/imageHeaderBox/nC = '3') or
                        (multipleComponentTransformation = 'no') and
                        (../../jp2HeaderBox/imageHeaderBox/nC = '1')">no colour transformation</s:assert>

        <!-- Decomposition levels -->
        <s:assert test="levels = '5'">wrong number of decomposition levels</s:assert>

        <!-- Codeblock size -->
        <s:assert test="codeBlockWidth = '64'">wrong codeblock width</s:assert>
        <s:assert test="codeBlockHeight = '64'">wrong codeblock height</s:assert>

        <!-- Transformation (irreversible vs reversible) -->
        <s:assert test="transformation = '5-3 reversible'">wrong transformation</s:assert>

        <!-- checks on X- and Y- precinct sizes: 256x256 for 2 highest resolution levels,
              128x128 for remaining ones  -->
        <s:assert test="precinctSizeX[1] = '128'">precinctSizeX doesn't match profile</s:assert>
        <s:assert test="precinctSizeX[2] = '128'">precinctSizeX doesn't match profile</s:assert>
        <s:assert test="precinctSizeX[3] = '128'">precinctSizeX doesn't match profile</s:assert>
        <s:assert test="precinctSizeX[4] = '128'">precinctSizeX doesn't match profile</s:assert>
        <s:assert test="precinctSizeX[5] = '256'">precinctSizeX doesn't match profile</s:assert>
        <s:assert test="precinctSizeX[6] = '256'">precinctSizeX doesn't match profile</s:assert>
        <s:assert test="precinctSizeY[1] = '128'">precinctSizeY doesn't match profile</s:assert>
        <s:assert test="precinctSizeY[2] = '128'">precinctSizeY doesn't match profile</s:assert>
        <s:assert test="precinctSizeY[3] = '128'">precinctSizeY doesn't match profile</s:assert>
        <s:assert test="precinctSizeY[4] = '128'">precinctSizeY doesn't match profile</s:assert>
        <s:assert test="precinctSizeY[5] = '256'">precinctSizeY doesn't match profile</s:assert>
        <s:assert test="precinctSizeY[6] = '256'">precinctSizeY doesn't match profile</s:assert>

    </s:rule>

    <!-- Check specs reference as codestream comment -->
    <!-- Rule looks for one exact match, additional codestream comments are permitted -->
    <s:rule context="/file/properties/contiguousCodestreamBox">
        <s:assert test="count(com/comment[text()='KB_MASTER_LOSSLESS_01/01/2015']) =1">Expected codestream comment string missing</s:assert>
      </s:rule>

      <!-- Metadata checks -->
      <s:rule context="/file/properties/uuidBox/x:xmpmeta">

          <!-- Check that RDF element exists -->
          <s:assert test="rdf:RDF">missing RDF element</s:assert>

      </s:rule>

      <s:rule context="/file/properties/uuidBox/x:xmpmeta/rdf:RDF">

          <!-- Check that RDF element contains one or more Description elements -->
          <s:assert test="count(rdf:Description) &gt; 0">missing Description element(s)</s:assert>

          <!-- Checks on RDF representations of TIFF tags -->
          <s:assert test="count(rdf:Description/tiff:Software) &gt; 0">missing Software element</s:assert>
          <s:assert test="rdf:Description/tiff:Software != ''">empty Software element</s:assert>
          <s:assert test="count(rdf:Description/tiff:Model) &gt; 0">missing Model element</s:assert>
          <s:assert test="rdf:Description/tiff:Model != ''">empty Model element</s:assert>

          <!-- Checks on RDF representations of EXIF tags -->
          <s:assert test="count(rdf:Description/exif:DateTimeOriginal) &gt; 0">missing DateTimeOriginal element</s:assert>
          <s:assert test="rdf:Description/exif:DateTimeOriginal != ''">empty DateTimeOriginal element</s:assert>
          <s:assert test="count(rdf:Description/exif:ShutterSpeedValue) &gt; 0">missing ShutterSpeedValue element</s:assert>
          <s:assert test="rdf:Description/exif:ShutterSpeedValue != ''">empty ShutterSpeedValue element</s:assert>
          <s:assert test="count(rdf:Description/exif:ApertureValue) &gt; 0">missing ApertureValue element</s:assert>
          <s:assert test="rdf:Description/exif:ApertureValue != ''">empty ApertureValue element</s:assert>
          <s:assert test="count(rdf:Description/exif:ISOSpeedRatings) &gt; 0">missing ISOSpeedRatings element</s:assert>
          <s:assert test="count(rdf:Description/exif:ISOSpeedRatings/rdf:Seq) &gt; 0">missing ISOSpeedRatings Sequence element</s:assert>
          <s:assert test="count(rdf:Description/exif:ISOSpeedRatings/rdf:Seq/rdf:li) &gt; 0">missing ISOSpeedRatings li element</s:assert>
          <s:assert test="rdf:Description/exif:ISOSpeedRatings/rdf:Seq/rdf:li != ''">empty missing ISOSpeedRatings li element</s:assert>

          <!-- Checks on RDF representations of Photoshop tags -->
          <s:assert test="count(rdf:Description/photoshop:Headline) &gt; 0">missing Headline element</s:assert>
          <s:assert test="rdf:Description/photoshop:Headline != ''">empty Headline element</s:assert>
          <s:assert test="count(rdf:Description/photoshop:Credit) &gt; 0">missing Credit element</s:assert>
          <s:assert test="rdf:Description/photoshop:Credit != ''">empty Credit element</s:assert>

</s:rule>



</s:pattern>
</s:schema>

