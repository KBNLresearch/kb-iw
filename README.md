# KB Image Workflow Tool

## About this software

Kb-iw converts image files in digitisation batches to JP2 (JPEG 2000 Part 1) format using the [Grok](https://github.com/GrokImageCompression/grok) codec. It clones the structure of the input directory, and then replicates it in the output directory. The JP2 images are then subjected to the following quality checks:

1. Pixel comparison between each pair of source and destination images (using [libvips](https://www.libvips.org/) and [pyvips](https://libvips.github.io/pyvips/)).
2. Check of extracted technical properties (using [jpylyzer](https://jpylyzer.openpreservation.org/)) against a user-defined [Schematron](http://en.wikipedia.org/wiki/Schematron) profile.

The software also generates checksums of all converted images.

## Dependencies

- Python (tested with versions 3.12.3 and 3.14.5)
- [Grok JPEG 2000 codec](https://github.com/GrokImageCompression/grok) (tested with version ??)
- [Libvips](https://www.libvips.org/)

## Installation of dependencies

### Grok (all platforms)

1. Download the latest binaries of the Grok image compression software for your platform from:

  <https://github.com/GrokImageCompression/grok/releases>

2. Extract the ZIP file to your local file system, and make a note of the installation location. You'll need to enter this later in the kb-iw configuration file.

### Libvips

#### Linux (Ubuntu, Linux Mint)

Install libvips using:

```
sudo apt install libvips-dev --no-install-recommends
```

#### macOS

TODO

#### Windows

1. Download the latest release from the [build-win64-mxe repository](https://github.com/libvips/build-win64-mxe/releases). For a 64 bit Windows system you need the ZIP file that follows the "vips-dev-x64-all-x.y.z.zip" naming pattern (e.g. vips-dev-x64-all-8.18.2.zip).

2. Extract the ZIP file to your hard disk, and make a note of the installation location (e.g. "C:\vips-dev"). You'll need to enter this later in the kb-iw configuration file.

### ExifTool

#### Linux (Ubuntu, Linux Mint)

Install ExifTool using:

```
sudo apt install libimage-exiftool-perl
```

#### macOS

TODO

#### Windows

1. Download the 64-bit Windows executable from the [ExifTool website](https://exiftool.org/index.html)

2. Extract the ZIP file to your hard disk

3. In the extracted folder, rename the file "exiftool(-k).exe" to "exiftool.exe

4. Make a note of the installation location (e.g. "C:\exiftool"). You'll need to enter this later in the kb-iw configuration file.

## Installation of kb-iw

As of 2026, [uv](https://docs.astral.sh/uv/) appears to be the most straightforward tool for installing Python applications on a variety of platforms (Linux, MacOS, Windows).

### uv installation

First, check if uv is installed on your system by typing the uv command in a terminal:

```
uv
```

If this results in a help message, uv is installed, and you can skip directly to the "imgquad installation" section below. If not, you first need to install uv.

On Linux and MacOS you can install uv with the following command:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Alternatively, you can use wget if your system doesn't have curl installed:

```
wget -qO- https://astral.sh/uv/install.sh | sh
```

To install uv on Windows, open a Powershell terminal, and run the following command:

```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Regardless of the operating system, in some cases the installation script will update your system's configuration to make the location of the uv executable globally accessible. If this happens, just close your current terminal, and open a new one for these changes to take effect. Pay attention to the screen output of the installation script for any details on this.

### kb-iw installation

Use the following command to install kb-iw (all platforms):

```
uv tool install kb-iw
```

Then run kb-iw once:

```
kb-iw
```

Depending on your system, kb-iw will now create a configuration folder (see next section).

## Configuration

Before you can use kb-iw, you need to edit the configuration file, which is located in the configuration folder. The configuration folder has the name "kb-iw", and its location depends on your operating system:

- For Linux and MacOS, the configuration folder is a subdirectory of the location defined by the environment variable *$XDG_CONFIG_HOME*. If this variable is not set, it will be a subdirectory of the *.config* directory in the user's home folder (e.g. `/home/johan/.config/kb-iw`). Note that the *.config* directory is hidden by default.
- For Windows, the configuration folder is a subdirectory of of the *AppData\Local* folder (e.g. `C:\Users\johan\AppData\Local\kb-iw`).

Open the configuration file ("config.json") in a text editor, and edit the following values:

|Variable|Meaning|Examples|
|:--|:--||
|grokDir|Grok installation directory|`C:/Grok` (Windows); `~/grok` (Linux)|
|exifToolExecutable|ExifTool executable|`C:/exiftool/exiftool.exe` (Windows); `/bin/exiftool` (Linux)|
|vipsBinDir|Libvips binary dir (only needed on Windows, ignored on Linux/macOS)|`C:/vips-dev/bin` (windows)|

Here's an example for a Windows system:


```json
{
  "grokDir": "`C:/Grok",
  "exifToolExecutable": "C:/exiftool/exiftool.exe",
  "vipsBinDir": "C:/vips-dev/bin",
  :
}
```

## upgrade kb-iw

Use the following command to upgrade an existing kb-iw installation to the latest version:

```
uv tool upgrade kb-iw
```

<!---

## Command-line syntax

The general syntax of imgquad is:

```
usage: imgquad [-h] [--version] {process,list,copyps} ...
```

Imgquad has three sub-commands:

|Command|Description|
|:-----|:--|
|process|Process a batch.|
|list|List available profiles and schemas.|
|copyps|Copy default profiles and schemas to user directory.|



### process command

Run imgquad with the *process* command to process a batch. The syntax is:

```
usage: imgquad process [-h] [--prefixout PREFIXOUT] [--outdir OUTDIR]
                       [--delimiter DELIMITER] [--verbose]
                       profile batchDir
```

The *process* command expects the following positional arguments: 

|Argument|Description|
|:-----|:--|
|profile|This defines the validation profile. Note that any file paths entered here will be ignored, as Imgquad only accepts  profiles from the profiles directory. You can just enter the file name without the path. Use the *list* command to list all available profiles.|
|batchDir|This defines the batch directory that will be analyzed.|

In addition, the following optional arguments are available:

|Argument|Description|
|:-----|:--|
|--prefixout, -p|This defines a text prefix on which the names of the output files are based (default: "pq").|
|--outdir, -o|This defines the directory where output is written (default: current working directory from which imgquad is launched).|
|--delimiter, -d|This defines the delimiter that is used in the output summary file (default: ';')|
|--verbose, -b|This tells imgquad to report Schematron output in verbose format.|

In the simplest case, we can call imgquad with the profile and the batch directory as the only arguments:

```
imgquad process beeldstudio-retro.xml ./mybatch
```

Imgquad will now recursively traverse all directories and files inside the "mybatch" directory, and analyse all image files (based on a file extension match).

### list command

Run imgquad with the *list* command to get a list of the available profiles and schemas, as well as their locations. For example:

```
imgquad list
```

Results in:

```
Available profiles (directory /home/johan/.config/imgquad/profiles):
  - mh-2025-tiff.xml
Available schemas (directory /home/johan/.config/imgquad/schemas):
  - mh-2025-tiff-600.sch
```



## Schemas

Schemas contain the Schematron rules on which the quality assessment is based. Some background information about this type of rule-based validation can be found in [this blog post](https://www.bitsgalore.org/2012/09/04/automated-assessment-jp2-against-technical-profile). Currently the following schemas are included:

### mh-2025-tiff-600.sch

This is a schema for digitised medieval manuscripts. It includes the following checks:

|Check|Value|
|:---|:---|
|Image format|TIFF|
|ICC profile name|eciRGB v2|
|XResolution TIFF tag|tag exists|
|YResolution TIFF tag|tag exists|
|XResolution value|600 (+/- 1) |
|YResolution value|600 (+/- 1) |
|ResolutionUnit TIFF tag|tag exists|
|ResolutionUnit value|2 (inches)|
|ImageWidth TIFF tag|tag exists|
|ImageLength TIFF tag|tag exists|
|BitsPerSample TIFF tag|tag exists|
|BitsPerSample value|'8 8 8'|
|ICCProfile TIFF tag|tag exists|
|Copyright TIFF tag|tag exists|
|NewSubfileType TIFF tag|at most 1 instance of this tag|
|SubIFDs TIFF tag|tag does not exist|
|Compression EXIF tag|tag exists|
|Compression|1 (Uncompressed)|
|Software EXIF tag|tag exists|
|Software value|not empty|
|DateTimeOriginal EXIF tag|tag exists|
|DateTimeOriginal value|not empty|
|Model EXIF tag|tag exists|
|Model value|not empty|
|Make EXIF tag|tag exists|
|Make value|not empty|
|ShutterSpeedValue EXIF tag|tag exists|
|ShutterSpeedValue value|not empty|
|ApertureValue EXIF tag|tag exists|
|ApertureValue value|not empty|
|ISOSpeedRatings EXIF tag|tag exists|
|ISOSpeedRatings value|not empty|
|photoshop:Headline|defined in XMP metadata as either element `rdf:RDF/rdf:Description/photoshop:Headline`, or attribute `rdf:RDF/rdf:Description/@photoshop:Headline`|
|photoshop:Headline value|not empty|
|photoshop:Credit|defined in XMP metadata as either element `rdf:RDF/rdf:Description/photoshop:Credit`, or attribute `rdf:RDF/rdf:Description/@photoshop:Credit`|
|photoshop:Credit value|not empty|

The schema also includes an additional check on any exceptions that occurred while parsing the image, as this may indicate a corrupted file.

### mh-2025-tiff-300.sch

This schema is identical to the mh-2025-tiff-600.sch schema, except for the checks on the XResolution and YResolution values:

|Check|Value|
|:---|:---|
|XResolution value|300 (+/- 1) |
|YResolution value|300 (+/- 1) |

## Output

Imgquad reports the following output:

### Comprehensive output file (XML)

For each batch, Imgquad generates one comprehensive output file in XML format. This file contains, for each image, all extracted properties, as well as the Schematron report and the assessment status.

### Summary file (CSV)

This is a comma-delimited text file that summarises the analysis. At the minimum, Imgquad reports the following columns for each image:

|Column|Description|
|:-----|:--|
|file|Full path to the image file.|
|validationSuccess|Flag with value *True* if Schematron validation was succesful, and *False* if not. A value *False* indicates that the file could not be validated (e.g. because no matching schema was found, or the validation resulted in an unexpected exception)|
|validationOutcome|The outcome of the Schematron validation/assessment. Value is *Pass* if file passed all tests, and *Fail* otherwise. Note that it is automatically set to *Fail* if the Schematron validation was unsuccessful (i.e. "validationSuccess" is *False*)|
|validationErrors|List of validation errors (separated by "\|" characters).|

In addition, the summary file contains additional columns with the properties that are defined by the *summaryProperty* elements in the profile.

-->

## Licensing

KB-iw is released under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0). Parts of the code were inspired by the Bodeleian's [Image Processing](https://github.com/bodleian/image-processing) library.



