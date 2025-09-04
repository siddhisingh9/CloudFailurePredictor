# 🚀 Task Failure Prediction using Google Cloud Trace Data  

This project predicts **task failures** using **Google Cloud Trace data**, helping optimize resource usage by identifying high-risk tasks before execution. It combines **machine learning**, **API deployment**, and **real-time dashboards** into an end-to-end cloud-based solution.  

---

## 📌 Features  

- **Machine Learning Model**  
  - Preprocessed Google Cloud Trace dataset with feature engineering and leakage removal  
  - Achieved **93% accuracy** and **0.93 F1 score** using a Random Forest classifier  

- **Deployment**  
  - Model **dockerized** and deployed via **FastAPI**  
  - REST API for predictions  

- **Interactive Dashboard**  
  - Built with **Streamlit**  
  - Supports CSV uploads or demo mode with preloaded data  
  - **Redis Pub/Sub** for real-time streaming of predictions  

- **Visualizations**  
  - Task failure probabilities  
  - CPU and memory usage  
  - Historical failure trends  

- **Cloud Hosting**  
  - End-to-end system deployed on **Render**  

---

## ⚙️ Tech Stack  

- **Machine Learning**: scikit-learn, pandas  
- **API**: FastAPI, Docker  
- **Dashboard**: Streamlit  
- **Messaging**: Redis Pub/Sub  
- **Hosting**: Render  

---

## 📂 Project Structure  

