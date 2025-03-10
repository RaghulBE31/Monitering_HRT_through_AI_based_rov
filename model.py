import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import plotly.express as px

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report, r2_score

import tensorflow as tf

# Define dataset directories
positive_dir = Path(r'C:\Users\moham\Desktop\Image\DataSets\Positive')
negative_dir = Path(r'C:\Users\moham\Desktop\Image\DataSets\Negative')

def generate_df(img_dir, label):
    file_paths = pd.Series(list(img_dir.glob(r'*.jpg')), name='Filepath').astype(str)
    labels = pd.Series(label, name='Label', index=file_paths.index)
    df = pd.concat([file_paths, labels], axis=1)
    return df

# Generate dataframes for positive and negative images
positive_df = generate_df(positive_dir, 'POSITIVE')
negative_df = generate_df(negative_dir, 'NEGATIVE')

# Concatenate both dataframes
all_df = pd.concat([positive_df, negative_df], axis=0).sample(frac=1, random_state=1).reset_index(drop=True)

# Split dataset into training and testing
train_df, test_df = train_test_split(all_df.sample(6000, random_state=1), train_size=0.7, shuffle=True, random_state=1)

# Define image data generators
train_gen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1./255, validation_split=0.2)
test_gen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1./255)

# Prepare training, validation, and test datasets
train_data = train_gen.flow_from_dataframe(train_df, x_col='Filepath', y_col='Label', target_size=(120,120), color_mode='rgb', class_mode='binary', batch_size=32, shuffle=True, seed=42, subset='training')

val_data = train_gen.flow_from_dataframe(train_df, x_col='Filepath', y_col='Label', target_size=(120,120), color_mode='rgb', class_mode='binary', batch_size=32, shuffle=True, seed=42, subset='validation')

test_data = test_gen.flow_from_dataframe(test_df, x_col='Filepath', y_col='Label', target_size=(120,120), color_mode='rgb', class_mode='binary', batch_size=32, shuffle=False, seed=42)

# Build CNN model
inputs = tf.keras.Input(shape=(120,120,3))
x = tf.keras.layers.Conv2D(filters=16, kernel_size=(3,3), activation='relu')(inputs)
x = tf.keras.layers.MaxPool2D(pool_size=(2,2))(x)
x = tf.keras.layers.Conv2D(filters=32, kernel_size=(3,3), activation='relu')(x)
x = tf.keras.layers.MaxPool2D(pool_size=(2,2))(x)
x = tf.keras.layers.GlobalAveragePooling2D()(x)
outputs = tf.keras.layers.Dense(1, activation='sigmoid')(x)
model = tf.keras.Model(inputs=inputs, outputs=outputs)

# Compile the model
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

def evaluate_model(model, test_data):
    results = model.evaluate(test_data, verbose=0)
    loss = results[0]
    accuracy = results[1]
    print(f'Test Loss {loss:.5f}')
    print(f'Test Accuracy {accuracy * 100:.2f} %')
    
    # Predicted values
    y_pred = np.squeeze((model.predict(test_data) >= 0.5).astype(int))
    conf_matr = confusion_matrix(test_data.labels, y_pred)
    class_report = classification_report(test_data.labels, y_pred, target_names=['NEGATIVE', 'POSITIVE'])
    
    plt.figure(figsize=(6,6))
    sns.heatmap(conf_matr, fmt='g', annot=True, cbar=False, vmin=0, cmap='Blues')
    plt.xticks(ticks=np.arange(2) + 0.5, labels=['NEGATIVE', 'POSITIVE'])
    plt.yticks(ticks=np.arange(2) + 0.5, labels=['NEGATIVE', 'POSITIVE'])
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title('Confusion Matrix')
    plt.show()
    
    print('r2 Score : ', r2_score(test_data.labels, y_pred))
    print('Classification Report :\n......................\n', class_report)

evaluate_model(model, test_data)

# Function to test new images
def test_new_data(dir_path):
    new_test_dir = Path(dir_path)
    df_new = generate_df(new_test_dir, 'Testing')
    test_data_new = test_gen.flow_from_dataframe(df_new, x_col='Filepath', y_col='Label', target_size=(120,120), color_mode='rgb', batch_size=5, shuffle=False, seed=42)
    
    y_pred = np.squeeze((model.predict(test_data_new) >= 0.5).astype(int))
    y_certain = model.predict(test_data_new).round(6)
    
    y_out = ['Negative (Not Crack)' if i == 0 else 'Positive (Crack)' for i in y_pred]
    result = pd.DataFrame(np.c_[y_out, y_certain], columns=['Result', 'Confidence of being Cracked'])
    return result

# Test new dataset
results = test_new_data(r'C:\Users\moham\Desktop\new\check')
results.to_csv('final_results.csv')
