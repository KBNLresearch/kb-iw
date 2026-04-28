<?xml version="1.0"?>
<!--
Schematron jpylyzer schema for KB lossy access copy (A.K.A. KB_ACCESS_LOSSY_01/01/2015)
-->
<s:schema xmlns:s="http://purl.oclc.org/dsdl/schematron">

<s:pattern>
    <s:title>KB access JP2 2015, generic (no colour/resolution requirements)</s:title>

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

        <!-- check that xml box exists -->
        <s:assert test="xmlBox">no XML box</s:assert>

        <!-- check if compression ratio doesn't exceed threshold value (a bit tricky as for images that 
         don't contain much information very high compression ratios may be obtained without losing quality)  
          -->
        <s:assert test="compressionRatio &lt; 25">compression ratio too high</s:assert>
        
        <!-- check if compression ratio not smaller than threshold value -->
        <s:assert test="compressionRatio &gt; 15">compression ratio too low</s:assert>
    
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
        <s:assert test="layers = '8'">wrong number of layers</s:assert>

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
        <s:assert test="transformation = '9-7 irreversible'">wrong transformation</s:assert>

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
        <s:assert test="count(com/comment[text()='KB_ACCESS_LOSSY_01/01/2015']) =1">Expected codestream comment string missing</s:assert>
      </s:rule>
</s:pattern>
</s:schema>

