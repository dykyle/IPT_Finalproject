# IPT_FinalProject

## Project Description
Basic Financial Forecasting using Python with Allowance as Datasets. This project tracks your daily expenses, calculates your daily allowance based on weekdays, and provides a savings forecast using Streamlit.

## Features
    - Divide monthly allowance according to weekdays in a selected month.
    - Track daily expenses with labels.
    - Undo and redo functionality for expense records.
    - View raw expense logs and daily summaries.
    - Visualize expenses and savings over time using graphs.
    - Forecast savings for the next 5 weekdays.

## Updated Feature
    - Added sidebar for seamless navigation.
    - Added additional Tab intended for "CSV Uploads"
    - Added Quick Stats "Total Spent" and "Savings Rate"
    - Added Clear data button to quickly remove all data inputs.
    - Added "Upload CSV" for uploading existing datasets that will be used for CSV Analyzer Tab.
    - Added Export Data with the same functionality as Download CSV.
    - Updated a premium-like visual of the application.
    
## Installation
    1. Download the project as a ZIP file from GitHub.
    2. Install Python (if not already installed).
    3. Install the required Python libraries using pip:
        - python -m pip install pandas matplotlib streamlit
        - after installing the libraries, run it with python -m streamlit run main.py.
    4. Extract the ZIP file to a folder on your computer.

## Usage
    1. Open a terminal or command prompt in the project folder.
    2. Run the Streamlit app:
    3. A web app will open in your browser:
        - Enter your monthly allowance.
        - Select the year and month.
        - Add your daily expenses.
        - View the daily summary, expense/savings graph, and forecast for the next 5 weekdays.

## Notes
    - Make sure all required libraries are installed before running the app.
    - The app automatically computes allowance tracking, visualizations, and forecasting for you.

## License
    This project is open for educational purposes.
