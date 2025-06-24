import pandas as pd
import joblib
import os
from datetime import datetime

class PredictionError(Exception):
    """Custom exception for prediction failures"""
    pass

def verify_prediction(predicted, actual):
    """Compare predicted vs actual results"""
    if not actual or not predicted:
        return False
    
    # Convert both to same format (e.g., "Red_Small")
    predicted_parts = predicted.split("_")
    if len(predicted_parts) != 2:
        return False
        
    return (predicted_parts[0] == actual["Color"] and 
            predicted_parts[1] == actual["Size"])

def predict_next():
    try:
        # --- Data Validation ---
        if not os.path.exists("data/bdg_data.csv"):
            raise PredictionError("Training data not found")
            
        df = pd.read_csv("data/bdg_data.csv")
        if df.empty or len(df) < 10:
            raise PredictionError("Insufficient training data")
            
        # --- Model Loading ---
        model_files = {
            "color_size": "model/bdg_model.pkl",
            "number": "model/number_model.pkl"
        }
        
        models = {}
        for name, path in model_files.items():
            if not os.path.exists(path):
                print(f"⚠️ {name} model not found")
                continue
            try:
                models[name] = joblib.load(path)
            except Exception as e:
                raise PredictionError(f"Failed to load {name} model: {str(e)}")
        
        if not models:
            raise PredictionError("No valid models available")
        
        # --- Prediction ---
        latest = df.iloc[-1]
        
        # Color+Size Prediction
        if "color_size" in models:
            try:
                X_cls = pd.DataFrame([[latest["ColorCode"], latest["SizeCode"]]], 
                                    columns=["ColorCode", "SizeCode"])
                predicted_class = models["color_size"].predict(X_cls)[0]
                print(f"🎯 Predicted: {predicted_class}")
                
                # Verification with next actual result
                if verify_prediction(predicted_class, latest):
                    print("✅ Prediction verified")
                else:
                    print("⚠️ Prediction mismatch")
                    
            except Exception as e:
                raise PredictionError(f"Color/Size prediction failed: {str(e)}")
        
        # Number Prediction
        if "number" in models:
            try:
                X_num = pd.DataFrame([[latest["Number"]]], columns=["Number"])
                number_pred = models["number"].predict(X_num)[0]
                print(f"🔢 Predicted Number: {number_pred}")
            except Exception as e:
                raise PredictionError(f"Number prediction failed: {str(e)}")
                
        # Log results
        with open("prediction_log.txt", "a") as f:
            f.write(f"{datetime.now()},{predicted_class},{number_pred}\n")
            
    except PredictionError as pe:
        print(f"❌ Prediction Error: {pe}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    return True
def get_last_prediction():
    """
    Gets the latest prediction in the format expected by the verification system
    Returns: dict {'color': str, 'number': int, 'size': str}
    """
    try:
        # Load latest prediction from log
        if os.path.exists("prediction_log.txt"):
            df_log = pd.read_csv("prediction_log.txt", 
                               header=None, 
                               names=["timestamp", "color_size", "number"])
            last_pred = df_log.iloc[-1]
            
            # Parse color_size (format "Color_Size")
            color, size = last_pred["color_size"].split("_")
            
            return {
                "color": color,
                "number": int(last_pred["number"]),
                "size": size
            }
        
        # Fallback to current model prediction
        df = pd.read_csv("data/bdg_data.csv")
        latest = df.iloc[-1]
        
        return {
            "color": latest["Color"],
            "number": int(latest["Number"]),
            "size": latest["Size"]
        }
        
    except Exception as e:
        print(f"⚠️ Error getting last prediction: {e}")
        return {
            "color": "Error", 
            "number": -1, 
            "size": "Error"
        }
if __name__ == "__main__":
    predict_next()