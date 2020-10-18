#!/usr/bin/env python
# coding: utf-8

# In[2]:


import tensorflow as tf
import os
import gzip
import numpy as np
import argparse
from tensorflow.python.keras.callbacks import Callback

class MyFashionMnist(object):

  def train(self):
    
    # 학습수행결과 모델을 save_model
    parser = argparse.ArgumentParser()
    parser.add_argument('--learning_rate', required=False, type=float, default=0.001)
    parser.add_argument('--dropout_rate', required=False, type=float, default=0.3)
    parser.add_argument('--epoch', required=False, type=int, default=5)    
    parser.add_argument('--act', required=False, type=str, default='relu')        
    parser.add_argument('--layer', required=False, type=int, default=1)      
    parser.add_argument('--model_version', required=False, type=str, default='0001')    
    parser.add_argument('--checkpoint_dir', required=False, default='/reuslt/training_checkpoints')
    parser.add_argument('--saved_model_dir', required=False, default='/result/saved_model')        
    parser.add_argument('--tensorboard_log', required=False, default='/result/log')     
    args = parser.parse_args()    
    
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.fashion_mnist.load_data()
    
    x_train, x_test = x_train / 255.0, x_test / 255.0

    model = tf.keras.models.Sequential()
    model.add(tf.keras.layers.Flatten(input_shape=(28, 28)))
    
    for i in range(int(args.layer)):    
        model.add(tf.keras.layers.Dense(128, activation=args.act))
        if(i > 2) :
            model.add(tf.keras.layers.Dropout(args.dropout_rate))
        
    model.add(tf.keras.layers.Dense(10, activation='softmax'))
    
    model.compile(optimizer=tf.keras.optimizers.Adam(lr=args.learning_rate),
                  loss='sparse_categorical_crossentropy',
                  metrics=['acc'])
    
    model.summary()    
    
    # 체크포인트를 저장할 체크포인트 디렉터리를 지정합니다.
    checkpoint_dir = args.checkpoint_dir
    # 체크포인트 파일의 이름
    checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt_{epoch}")        

    model.fit(x_train, y_train,
              verbose=0,
              validation_data=(x_test, y_test),
              epochs=args.epoch,
              callbacks=[KatibMetricLog(),
                        tf.keras.callbacks.TensorBoard(log_dir=args.tensorboard_log),
                        tf.keras.callbacks.ModelCheckpoint(filepath=checkpoint_prefix,
                               save_weights_only=True)
                        ])
    
    path = args.saved_model_dir + "/" + args.model_version        
    model.save(path, save_format='tf')

class KatibMetricLog(Callback):
    def on_batch_end(self, batch, logs={}):
        print("batch=" + str(batch),
              "accuracy=" + str(logs.get('acc')),
              "loss=" + str(logs.get('loss')))
    def on_epoch_begin(self, epoch, logs={}):
        print("epoch " + str(epoch) + ":")
    
    def on_epoch_end(self, epoch, logs={}):
        print("Validation-accuracy=" + str(logs.get('val_acc')),
              "Validation-loss=" + str(logs.get('val_loss')))
        return

if __name__ == '__main__':
    if os.getenv('FAIRING_RUNTIME', None) is None:
        from kubeflow import fairing
        from kubeflow.fairing.kubernetes import utils as k8s_utils

        DOCKER_REGISTRY = 'kubeflow-registry.default.svc.cluster.local:30000'
        fairing.config.set_builder(
            'append',
            image_name='serving-job',
            base_image='brightfly/kubeflow-jupyter-lab:tf2.0-cpu', # here
            registry=DOCKER_REGISTRY, 
            push=True)
        # cpu 1, memory 5GiB
        fairing.config.set_deployer('job',
                                    namespace='admin',  # here namespace
                                    pod_spec_mutators=[
                                        k8s_utils.mounting_pvc(pvc_name="fashion-mnist", 
                                                              pvc_mount_path="/result"),
                                        k8s_utils.get_resource_mutator(cpu=1,
                                                                       memory=5)]
                                   )
        fairing.config.run()
    else:
        remote_train = MyFashionMnist()
        remote_train.train()


# In[ ]:





# In[ ]:




