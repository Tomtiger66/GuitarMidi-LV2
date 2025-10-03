use python/neuralnetmodelling/savecompletemodel.ipynb to export the model to keras
then  

conda activate guitarmidi_nn311
and 

ext/frugally-deep/keras_export/convert_model.py python/neuralnetmodelling/model_dir/guitarmidi-model-and-weights.keras python/neuralnetmodelling/model_dir/guitarmidi-model-and-weights.json

To convert the frugally deep json