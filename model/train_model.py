import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_squared_error
import joblib
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='logs/model_training.log'
)
logger = logging.getLogger(__name__)

def preprocess_data(df):
    """Clean and prepare data for training"""
    try:
        # Convert categorical features
        color_mapping = {'Red': 0, 'Green': 1, 'Violet': 2, 'Blue': 3, 'Yellow': 4}
        size_mapping = {'Small': 0, 'Big': 1}
        
        df['ColorCode'] = df['Color'].map(color_mapping).fillna(-1).astype(int)
        df['SizeCode'] = df['Size'].map(size_mapping).fillna(-1).astype(int)
        
        # Ensure numerical values
        df['Number'] = pd.to_numeric(df['Number'], errors='coerce').fillna(0).astype(int)
        
        # Feature engineering
        df['EvenOdd'] = df['Number'] % 2
        df['PrevColor'] = df['ColorCode'].shift(1).fillna(-1)
        df['PrevSize'] = df['SizeCode'].shift(1).fillna(-1)
        
        return df.dropna()
    except Exception as e:
        logger.error(f"Data preprocessing failed: {str(e)}")
        raise

def train_color_size_model(X, y):
    """Train model for color and size prediction"""
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=42,
            class_weight='balanced'
        )
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        logger.info(f"Color+Size model accuracy: {accuracy:.2%}")
        
        return model, accuracy
    except Exception as e:
        logger.error(f"Color/Size model training failed: {str(e)}")
        raise

def train_number_model(X, y):
    """Train model for number prediction"""
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        logger.info(f"Number model MSE: {mse:.4f}")
        
        return model, mse
    except Exception as e:
        logger.error(f"Number model training failed: {str(e)}")
        raise

def save_model(model, path, metadata=None):
    """Save trained model with metadata"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            'model': model,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }, path)
        logger.info(f"Model saved to {path}")
    except Exception as e:
        logger.error(f"Failed to save model: {str(e)}")
        raise

def load_model(path):
    """Load trained model with validation"""
    try:
        if not os.path.exists(path):
            logger.warning(f"Model file not found: {path}")
            return None
            
        model_data = joblib.load(path)
        if not isinstance(model_data, dict) or 'model' not in model_data:
            raise ValueError("Invalid model format")
            
        logger.info(f"Model loaded from {path} (created {model_data.get('timestamp')})")
        return model_data
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        return None

def train_model(data_path):
    """Main training pipeline"""
    try:
        logger.info(f"Starting model training with data from {data_path}")
        
        # Load and prepare data
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Data file not found: {data_path}")
            
        df = pd.read_csv(data_path)
        if len(df) < 10:
            raise ValueError(f"Insufficient data: only {len(df)} records available")
            
        processed_df = preprocess_data(df)
        
        # Prepare features and targets
        features = ['ColorCode', 'SizeCode', 'EvenOdd', 'PrevColor', 'PrevSize']
        X = processed_df[features]
        
        # Train Color+Size model (combined target)
        y_color_size = processed_df['Color'] + '_' + processed_df['Size']
        color_size_model, color_size_acc = train_color_size_model(X, y_color_size)
        
        # Train Number model
        y_number = processed_df['Number']
        number_model, number_mse = train_number_model(X, y_number)
        
        # Save models
        save_model(
            color_size_model,
            "model/bdg_model.pkl",
            {'accuracy': color_size_acc, 'features': features}
        )
        
        save_model(
            number_model,
            "model/number_model.pkl",
            {'mse': number_mse, 'features': features}
        )
        
        logger.info("✅ Training completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Training failed: {str(e)}")
        return False

if __name__ == "__main__":
    train_model("data/bdg_data.csv")