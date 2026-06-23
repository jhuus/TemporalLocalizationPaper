## Introduction
This repository contains supporting files for the paper *Improving Temporal Localization in Bioacoustic Recognizers*. Cite as:

TBD

## Installation
Clone the repository:
```
git clone https://github.com/jhuus/TemporalLocalizationPaper.git
```
It is best to create a virtual environment, such as a [Python venv](https://docs.python.org/3/library/venv.html). Once you have that set up, install version 1.5.0 of the BriteKit package using pip:
```
pip install britekit==1.5.0
```
In Windows environments, you then need to uninstall and reinstall PyTorch:
```
pip uninstall -y torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```
Note that cu126 refers to CUDA 12.6. You can check that the BriteKit installation was successful by typing:
```
britekit --help
```
Then download the recordings used in the IoU test:
```
python scripts/download_iou.py
```
## Contents
This repository does not contain training data. Since we ran 78 training runs (39 each for VovNet and HGNet-v2), saved 6 checkpoints for each run and created three ensembles, the total number of checkpoints generated was 486. Therefore we elected to keep only one ensemble and the outputs of 8 training runs in this repository as examples.

- The files hgnet-scores.ods and vovnet-scores.ods are LibreOffice spreadsheets that contain the detailed results of all PR and IoU test runs.
- The data directory contains a complete list of classes (classes.csv), and the lists of classes to be excluded during inference (exclude-pr.txt and exclude-iou.txt). It also contains checkpoints for ensemble3, the third VovNet ensemble reported in the results.
- The logs-hgnet and logs-vovnet directory contain the complete output from four training runs each:
  - v0: MLP classifier head
  - v3: SED classifier head with segment labels
  - v9: SED classifier head with frame labels (frame-label weight = 0.1)
  - v36: SED classifier head with frame labels (frame-label weight = 1.0)
- The reports directory contains hgnet and vovnet subdirectories. Each contains the complete output of the BriteKit rpt-iou and rpt-test commands, as summarized in the hgnet-scores.ods and vovnet-scores.ods spreadsheets.
- The scripts directory contains download_iou.py, which downloads the iNaturalist and Xeno-Canto recordings used in the IoU test.
- The tests directory contains the IoU and PR tests. For each test, that includes recordings, annotations and test output from all runs.
- The yaml directory contains the yaml files used as input to the BriteKit train and analyze commands.
## Replicating Results
You can use BriteKit to run inference and report on inference results. For example, to run inference on the PR test using the models in data/ensemble3, type the following:
```
britekit analyze tests/PR -c yaml/infer-pr-offsets-0.5.yaml --ckpt data/ensemble3 -o tests/PR/hgnet/my-ensemble-output
```
That uses the inference parameters defined in yaml/infer-pr-offsets-0.5.yaml and saves the output in tests/PR/hgnet/my-ensemble-output. To generate detailed and summary reports from that inference output, type:
```
britekit rpt-test -a tests/PR/annotations.csv -l hgnet/my-ensemble-output -o reports/my-pr-test-report
```
In this example -a is short for --annotations, -l is short for --labels and -o is short for --output.
Here are corresponding commands for the IoU test:
```
britekit analyze tests/IoU -c yaml/infer-iou-offsets-0.5.yaml --ckpt data/ensemble3 -o tests/IoU/vovnet/my-ensemble-output
britekit rpt-iou -a tests/IoU/annotations.csv -l vovnet/my-ensemble-output -o reports/vovnet/my-iou-test-report
```