import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
import pickle
import os
import re

# --- PREPROCESS FUNCTION (Supports Hindi) ---
def preprocess(text):
    text = str(text).lower().strip()
    # Keep English letters, numbers, spaces AND Devanagari (Hindi) characters
    text = re.sub(r"[^a-z0-9\u0900-\u097F\s]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, "intents.csv")

# 1. Load dataset
if not os.path.exists(csv_path):
    print("[ERROR] intents.csv file not found!")
    print("Please create intents.csv with training data.")
    exit()

print("[INFO] Loading training data...")
data = pd.read_csv(csv_path)
data.dropna(inplace=True)  # Remove empty rows

# 2. APPLY PREPROCESS
print("[INFO] Cleaning data (supporting Hindi & English)...")
data["text"] = data["text"].apply(preprocess)

print(f"[OK] Training with {len(data)} samples...")
print(f"[INFO] Unique intents found: {data['label'].nunique()}")
print(f"[INFO] Intent distribution:\n{data['label'].value_counts()}\n")

# 3. Train vectorizer + model
vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
X = vectorizer.fit_transform(data["text"])
y = data["label"]

# SVM with RBF kernel - Best for text classification
model = SVC(kernel='rbf', probability=True, gamma='scale', C=10)
model.fit(X, y)

# 4. Save pickle files
print("[INFO] Saving model files...")
with open(os.path.join(BASE_DIR, "model.pkl"), "wb") as f:
    pickle.dump(model, f)

with open(os.path.join(BASE_DIR, "vectorizer.pkl"), "wb") as f:
    pickle.dump(vectorizer, f)

print("\n" + "="*50)
print("[SUCCESS] Model trained and saved successfully!")
print("="*50)
print("\nFiles created:")
print("  ✓ model.pkl")
print("  ✓ vectorizer.pkl")
print("\nYou can now run: python app.py")
print("="*50 + "\n")