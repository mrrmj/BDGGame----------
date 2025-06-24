from model.train_model import train_model
import os

def main():
    data_file = "data/bdg_data.csv"
    
    if not os.path.exists(data_file):
        print("🛑 Training data not found. Please scrape the data first.")
        return
    
    print("🔧 Starting training for BDG prediction models...")
    result = train_model(data_file)
    
    if result:
        print("✅ All models trained and saved successfully.")
    else:
        print("❌ Model training failed.")

if __name__ == "__main__":
    main()
