## Quick context

- This repository implements an LV2 guitar-to-MIDI plugin (C++/CMake) alongside a set of Python notebooks and scripts for neural-net based analysis and training.
- Two major areas of work: the plugin/audio DSP (root `src/`, `AnalysisApp/`) and the ML tooling (Python under `python/neuralnetmodelling/`).

## Architecture & important boundaries

- Plugin / DSP: C++ code lives in `src/` and builds via CMake. The plugin target installs an LV2 bundle (`guitarmidi.lv2`) into the install prefix (default `~/.lv2`). See top-level [README.md](../README.md).
- Analysis / GUI: `AnalysisApp/` is a JUCE-based app (Projucer project + generated code) for local testing and visualization.
- ML / Training: `python/neuralnetmodelling/` contains notebooks, `model.py`, `common.py` and `fretboard.py`. The ML pipeline builds spectrogram-like filterbank inputs (IIR filter bank implemented in `fretboard.py`) and trains multi-label classifiers in `model.py`.

## Developer workflows (commands/examples)

- Build plugin (Ninja recommended):

  mkdir build
  cd build
  cmake -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$HOME/.lv2 ..
  cmake --build .
  cmake --install .

- Run JUCE AnalysisApp: open `AnalysisApp/NewProject.jucer` in Projucer or build the CMake project under `AnalysisApp/Builds`.

- Run training headless (notebook example present): from `python/neuralnetmodelling/` the notebook shows:

  screen jupyter nbconvert --to notebook --execute training-with-prefiltering.ipynb --output=output_notebook.ipynb --ExecutePreprocessor.timeout=-1

- Train script notes: models save weights to `python/neuralnetmodelling/guitarmidi.weights.h5` and checkpoints to `checkpoints/guitarmidi_epoch{epoch:02d}_valAcc{val_accuracy:.4f}.weights.h5` — see the notebook for exact filenames.

## Key project-specific conventions & patterns

- Filterbank-first pipeline: audio is pre-filtered by the IIR-based `FretBoard` (`python/neuralnetmodelling/fretboard.py`) producing a per-filter time-series input. ML code expects inputs shaped via `common.INPUT_SHAPE`.
- Mixed-precision training: notebooks enable `tf.keras.mixed_precision.set_global_policy('mixed_float16')` when GPUs are detected. Models explicitly cast final outputs to `float32` to avoid numeric issues.
- TFRecords and mapping: data is stored as TFRecords under `python/neuralnetmodelling/data_slices/`. Loading is done with `tf.data.TFRecordDataset` and custom parsing in `common.tf_load_sample_from_files` or notebook-local loaders.
- Multi-label output: model outputs are sigmoid-activated multi-label vectors (notes), not softmax. Loss used is `BinaryCrossentropy`.

## Integration points / hotspots to inspect first

- `src/` — plugin DSP and LV2 integration.
- `AnalysisApp/` — JUCE test harness and generated code for plugin debugging.
- `python/neuralnetmodelling/model.py` — model architecture and entrypoints for building the network.
- `python/neuralnetmodelling/common.py` — shapes, feature decoding, TFRecord parsing, utility helpers.
- `python/neuralnetmodelling/fretboard.py` — core signal processing IIR filterbank used for ML input.

## When you edit code, keep these practical constraints in mind

- Real-time constraints: audio DSP must remain low-latency. Avoid blocking allocations or heavy Python-like abstractions in DSP code.
- Deterministic shapes: TF Dataset pipelines in the notebooks set shapes explicitly (`.set_shape(...)`) and rely on stable dimensions — keep hard-coded shapes in sync (`INPUT_SHAPE`, `INPUT_SHAPE_AUDIO`).
- GPU vs CPU behavior: notebooks enable memory growth and mixed precision for GPUs; tests on CPU can behave differently (dtype, performance).

## How to extend or debug quickly

- To reproduce training errors, run the notebook with `--ExecutePreprocessor.timeout=-1` so long-running ops won't time out.
- Inspect saved images and model summaries output by the `PlotLoss` callback in the notebook (`training.png`, `model_summary.txt`).
- To probe the filterbank outputs interactively, call `FretBoard.process` on a short WAV slice and visualize with `common.plot_heatmap`.

## Examples (search these files for context)

- Build & install: [README.md](../README.md)
- Model architecture: [python/neuralnetmodelling/model.py](../python/neuralnetmodelling/model.py)
- TFRecord parsing and shapes: [python/neuralnetmodelling/common.py](../python/neuralnetmodelling/common.py)
- Filterbank implementation: [python/neuralnetmodelling/fretboard.py](../python/neuralnetmodelling/fretboard.py)
- Training notebook (entrypoint and training settings): [python/neuralnetmodelling/training-with-prefiltering.ipynb](../python/neuralnetmodelling/training-with-prefiltering.ipynb)

-- End of agent guidance. If you'd like I can tighten any section (e.g., add exact cmake targets, a small test runner, or CI tips). Please tell me which area to expand.
