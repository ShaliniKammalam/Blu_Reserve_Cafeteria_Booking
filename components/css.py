import streamlit as st

def add_custom_css():
    st.markdown("""
    <style>
   
    
    .form-container input, .form-container select {
        width: 100%;
        padding: 12px;
        margin-bottom: 12px;
        border-radius: 5px;
        border: 1px solid #ddd;
    }
    
    .form-container button {
        background-color: #4CAF50;
        color: white;
        padding: 15px;
        width: 100%;
        border: none;
        border-radius: 5px;
        cursor: pointer;
    }
    
    .form-container button:hover {
        background-color: #45a049;
    }
    
    .form-container h2 {
        text-align: center;
        color: #fff;
    }
    </style>
    """, unsafe_allow_html=True)
